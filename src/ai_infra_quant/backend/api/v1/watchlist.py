from uuid import UUID

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from ai_infra_quant.application.watchlist_service import WatchlistItemView
from ai_infra_quant.backend.api.errors import problem_response
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.security import security_summary_from_domain
from ai_infra_quant.backend.schemas.watchlist import (
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


@router.delete("/watchlist/{security_id}", status_code=204)
def remove_watchlist_item(
    security_id: UUID,
    container: ContainerDep,
) -> Response:
    container.watchlist_service.remove(str(security_id))
    return Response(status_code=204)
