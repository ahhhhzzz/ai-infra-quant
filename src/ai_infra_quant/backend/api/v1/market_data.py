from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from ai_infra_quant.application.market_data_queries import (
    MarketDataSecurityMetadataConflict,
    MarketDataSecurityNotFound,
    MarketDataSecurityNotSupported,
)
from ai_infra_quant.backend.api.errors import problem_response
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.market_data import (
    DailyBarsRead,
    MarketStateRead,
    MinuteBarsRead,
    daily_bars_read,
    market_state_read,
    minute_bars_read,
)

router = APIRouter(prefix="/market-data/securities", tags=["market-data"])


def _security_problem(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, MarketDataSecurityNotFound):
        return problem_response(
            request,
            status=404,
            code="SECURITY_NOT_FOUND",
            title="Security not found",
            detail="Security was not found.",
        )
    if isinstance(exc, MarketDataSecurityMetadataConflict):
        return problem_response(
            request,
            status=409,
            code="SECURITY_METADATA_CONFLICT",
            title="Security metadata conflict",
            detail=str(exc),
        )
    return problem_response(
        request,
        status=422,
        code="MARKET_DATA_SECURITY_NOT_SUPPORTED",
        title="Market-data Security not supported",
        detail="The canonical Security has no approved Futu market-data mapping.",
    )


@router.get("/{security_id}/state", response_model=MarketStateRead)
def get_market_state(
    security_id: UUID,
    request: Request,
    container: ContainerDep,
) -> MarketStateRead | JSONResponse:
    try:
        return market_state_read(container.market_data_queries.state(str(security_id)))
    except (
        MarketDataSecurityNotFound,
        MarketDataSecurityNotSupported,
        MarketDataSecurityMetadataConflict,
    ) as exc:
        return _security_problem(request, exc)


@router.get("/{security_id}/daily-bars", response_model=DailyBarsRead)
def get_daily_bars(
    security_id: UUID,
    request: Request,
    container: ContainerDep,
    limit: int = Query(default=120, ge=1, le=1500),
) -> DailyBarsRead | JSONResponse:
    try:
        return daily_bars_read(container.market_data_queries.daily_bars(str(security_id), limit))
    except (
        MarketDataSecurityNotFound,
        MarketDataSecurityNotSupported,
        MarketDataSecurityMetadataConflict,
    ) as exc:
        return _security_problem(request, exc)


@router.get("/{security_id}/minute-bars", response_model=MinuteBarsRead)
def get_minute_bars(
    security_id: UUID,
    request: Request,
    container: ContainerDep,
    lookback_days: int = Query(default=30, ge=1, le=31),
) -> MinuteBarsRead | JSONResponse:
    try:
        return minute_bars_read(
            container.market_data_queries.minute_bars(str(security_id), lookback_days)
        )
    except (
        MarketDataSecurityNotFound,
        MarketDataSecurityNotSupported,
        MarketDataSecurityMetadataConflict,
    ) as exc:
        return _security_problem(request, exc)
