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
from ai_infra_quant.backend.schemas.common import Page
from ai_infra_quant.backend.schemas.paqs_input import PaqsInputStatusRead, paqs_input_status_read
from ai_infra_quant.backend.schemas.status import StrategyDefinitionRead

router = APIRouter()


@router.get("/strategies", response_model=Page[StrategyDefinitionRead])
def get_strategies(
    container: ContainerDep,
) -> Page[StrategyDefinitionRead]:
    definitions = container.portfolio_queries.strategies()
    items = [
        StrategyDefinitionRead(
            id=definition.id,
            name=definition.name,
            version=definition.version,
            implementation_status=definition.implementation_status,
            research_status=definition.research_status,
            enabled=definition.enabled,
            required_data_status=definition.required_data_status,
        )
        for definition in definitions
    ]
    return Page(items=items)


@router.get(
    "/strategies/paqs/securities/{security_id}/input-status",
    response_model=PaqsInputStatusRead,
)
def get_paqs_input_status(
    security_id: UUID,
    request: Request,
    container: ContainerDep,
) -> PaqsInputStatusRead | JSONResponse:
    try:
        return paqs_input_status_read(container.paqs_input_queries.current_bundle(str(security_id)))
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
            code="PAQS_INPUT_SECURITY_NOT_SUPPORTED",
            title="PAQS input Security not supported",
            detail="PAQS input preparation supports enabled US/HK equities only.",
        )
