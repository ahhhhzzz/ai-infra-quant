from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ai_infra_quant.application.market_data_queries import (
    MarketDataSecurityMetadataConflict,
    MarketDataSecurityNotFound,
    MarketDataSecurityNotSupported,
)
from ai_infra_quant.backend.api.errors import problem_response
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.paqs_market_snapshot import (
    PaqsMarketSnapshotRead,
    paqs_market_snapshot_read,
)

router = APIRouter(prefix="/paqs/securities", tags=["paqs"])


@router.get("/{security_id}/market-snapshot", response_model=PaqsMarketSnapshotRead)
def get_paqs_market_snapshot(
    security_id: UUID,
    request: Request,
    container: ContainerDep,
) -> PaqsMarketSnapshotRead | JSONResponse:
    try:
        return paqs_market_snapshot_read(
            container.paqs_market_snapshot_queries.current_snapshot(str(security_id))
        )
    except MarketDataSecurityNotFound:
        return problem_response(
            request,
            status=404,
            code="SECURITY_NOT_FOUND",
            title="Security not found",
            detail="Security was not found.",
        )
    except MarketDataSecurityMetadataConflict as exc:
        return problem_response(
            request,
            status=409,
            code="SECURITY_METADATA_CONFLICT",
            title="Security metadata conflict",
            detail=str(exc),
        )
    except MarketDataSecurityNotSupported:
        return problem_response(
            request,
            status=422,
            code="PAQS_MARKET_SNAPSHOT_SECURITY_NOT_SUPPORTED",
            title="PAQS market snapshot Security not supported",
            detail="PAQS market snapshots support enabled US/HK equities only.",
        )
