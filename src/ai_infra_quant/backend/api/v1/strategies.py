from fastapi import APIRouter

from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.common import Page
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
