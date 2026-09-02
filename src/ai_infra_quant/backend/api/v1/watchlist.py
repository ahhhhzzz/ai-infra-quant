from uuid import UUID

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from ai_infra_quant.application.supported_security_service import SupportedSecurityAddError
from ai_infra_quant.application.watchlist_service import WatchlistItemView
from ai_infra_quant.backend.api.errors import problem_response
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.security import security_summary_from_domain
from ai_infra_quant.backend.schemas.watchlist import (
    ProviderValidationRead,
    SupportedSecurityAddRequest,
    SupportedSecurityAddResponse,
    WatchlistAddRequestV1,
    WatchlistAddResponse,
    WatchlistItemRead,
    WatchlistRead,
)

router = APIRouter()


def _item_schema(item: WatchlistItemView) -> WatchlistItemRead:
    return WatchlistItemRead(
        security=security_summary_from_domain(item.security),
        added_at=item.added_at.isoformat().replace("+00:00", "Z"),
        display_order=item.display_order,
    )


@router.get("/watchlist", response_model=WatchlistRead)
def get_watchlist(container: ContainerDep) -> WatchlistRead:
    view = container.watchlist_service.get()
    return WatchlistRead(
        id=view.id,
        name=view.name,
        portfolio_id=view.portfolio_id,
        is_default=view.is_default,
        items=[_item_schema(item) for item in view.items],
    )


@router.post("/watchlist", response_model=WatchlistAddResponse)
def add_watchlist_item(
    payload: WatchlistAddRequestV1,
    request: Request,
    response: Response,
    container: ContainerDep,
) -> WatchlistAddResponse | JSONResponse:
    try:
        result = container.watchlist_service.add(str(payload.security_id))
    except LookupError:
        return problem_response(
            request,
            status=404,
            code="SECURITY_NOT_FOUND",
            title="Security not found",
            detail="Security was not found.",
        )
    except PermissionError:
        return problem_response(
            request,
            status=409,
            code="SECURITY_DISABLED",
            title="Security disabled",
            detail="A disabled security cannot be added to the active watchlist.",
        )
    response.status_code = 201 if result.created else 200
    return WatchlistAddResponse(created=result.created, item=_item_schema(result.item))


@router.post("/watchlist/supported-securities", response_model=SupportedSecurityAddResponse)
def add_supported_security(
    payload: SupportedSecurityAddRequest,
    request: Request,
    response: Response,
    container: ContainerDep,
) -> SupportedSecurityAddResponse | JSONResponse:
    try:
        result = container.supported_security_service.add(
            market=payload.market,
            symbol=payload.symbol,
        )
    except SupportedSecurityAddError as exc:
        status = {
            "MARKET_DATA_NOT_ENTITLED": 403,
            "MARKET_DATA_PROVIDER_NOT_CONFIGURED": 503,
            "MARKET_DATA_PROVIDER_UNAVAILABLE": 503,
            "MARKET_DATA_PROVIDER_ERROR": 502,
            "SYMBOL_VALIDATION_FAILED": 422,
            "SECURITY_METADATA_CONFLICT": 409,
            "SUPPORTED_SECURITY_PERSISTENCE_ERROR": 409,
        }.get(exc.code, 500)
        extra: dict[str, object] = {}
        if exc.provider_status is not None:
            extra["provider_validation_status"] = exc.provider_status.value
        if exc.provider is not None:
            extra["provider"] = exc.provider
        if exc.retrieved_at is not None:
            extra["retrieved_at"] = exc.retrieved_at.isoformat().replace("+00:00", "Z")
        return problem_response(
            request,
            status=status,
            code=exc.code,
            title="Supported security could not be added",
            detail=exc.detail,
            extra=extra,
        )
    response.status_code = 201 if result.created_security or result.created_watchlist_item else 200
    validation = result.provider_validation
    return SupportedSecurityAddResponse(
        created_security=result.created_security,
        created_watchlist_item=result.created_watchlist_item,
        item=_item_schema(result.item),
        provider_validation=ProviderValidationRead(
            status=validation.status,
            provider=validation.provider,
            retrieved_at=validation.retrieved_at.isoformat().replace("+00:00", "Z"),
        ),
    )


@router.delete("/watchlist/{security_id}", status_code=204)
def remove_watchlist_item(
    security_id: UUID,
    container: ContainerDep,
) -> Response:
    container.watchlist_service.remove(str(security_id))
    return Response(status_code=204)
