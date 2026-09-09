"""Explicit capture and strictly local read APIs."""

from ipaddress import ip_address
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from ai_infra_quant.application.market_data_archive import ArchiveUnavailable
from ai_infra_quant.application.market_data_queries import (
    MarketDataSecurityMetadataConflict,
    MarketDataSecurityNotFound,
    MarketDataSecurityNotSupported,
)
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.market_data_archive import ArchiveCaptureCreate
from ai_infra_quant.core.ports.market_data_archive import ArchiveNotFound, ArchivePersistenceError

router = APIRouter(prefix="/market-data/archive", tags=["market-data-archive"])


async def _write_boundary(request: Request) -> None:
    try:
        local = request.client is not None and ip_address(request.client.host).is_loopback
        host = request.url.hostname
        local_host = host == "localhost" or (host is not None and ip_address(host).is_loopback)
    except ValueError:
        local = local_host = False
    if (
        not local
        or not local_host
        or request.headers.get("origin") != f"{request.url.scheme}://{request.url.netloc}"
        or request.headers.get("sec-fetch-site") not in {None, "same-origin"}
        or request.headers.get("content-type", "").split(";")[0].lower() != "application/json"
    ):
        raise HTTPException(403, "Archive capture requires loopback same-origin JSON")
    if request.url.query or len(await request.body()) > 1024:
        raise HTTPException(400, "Invalid archive request bounds")


def _problem(exc: Exception) -> HTTPException:
    if isinstance(exc, ArchiveNotFound | MarketDataSecurityNotFound):
        return HTTPException(404, "Archive capture or Security not found")
    if isinstance(exc, MarketDataSecurityMetadataConflict):
        return HTTPException(409, "Archive requires consistent verified Security metadata")
    if isinstance(exc, MarketDataSecurityNotSupported):
        return HTTPException(422, "Archive Security or provider unavailable")
    if isinstance(exc, ArchivePersistenceError):
        return HTTPException(503, "Local archive persistence or integrity failure")
    return HTTPException(422, "Invalid archive pagination")


@router.post(
    "/captures", status_code=201, dependencies=[Depends(_write_boundary)], response_model=None
)
def capture(body: ArchiveCaptureCreate, container: ContainerDep) -> dict[str, Any] | JSONResponse:
    try:
        return container.market_data_archive.capture(str(body.security_id))
    except ArchiveUnavailable as exc:
        return JSONResponse(
            status_code=503,
            content={"code": "ARCHIVE_UNAVAILABLE", "detail": str(exc), "batches": exc.batches},
        )
    except (
        MarketDataSecurityNotFound,
        MarketDataSecurityMetadataConflict,
        MarketDataSecurityNotSupported,
        ArchivePersistenceError,
    ) as exc:
        raise _problem(exc) from exc


@router.get("/securities/{security_id}/captures")
def list_captures(
    security_id: UUID,
    container: ContainerDep,
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None, max_length=512),
) -> dict[str, Any]:
    try:
        return container.market_data_archive.repository.list_captures(
            str(security_id), limit, cursor
        )
    except (ArchiveNotFound, ArchivePersistenceError, ValueError) as exc:
        raise _problem(exc) from exc


@router.get("/captures/{capture_id}")
def detail(capture_id: UUID, container: ContainerDep) -> dict[str, Any]:
    try:
        return container.market_data_archive.repository.detail(str(capture_id))
    except (ArchiveNotFound, ArchivePersistenceError) as exc:
        raise _problem(exc) from exc


@router.get("/captures/{capture_id}/bars")
def bars(
    capture_id: UUID,
    container: ContainerDep,
    timeframe: Literal["D1", "M1"],
    limit: int = Query(500, ge=1, le=1000),
    cursor: str | None = Query(None, max_length=512),
) -> dict[str, Any]:
    try:
        return container.market_data_archive.repository.read_bars(
            str(capture_id), timeframe, limit, cursor
        )
    except (ArchiveNotFound, ArchivePersistenceError, ValueError) as exc:
        raise _problem(exc) from exc
