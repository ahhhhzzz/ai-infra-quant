from fastapi import APIRouter

from ai_infra_quant.backend.api.v1.brokers import descriptor_schema
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.status import AdapterListRead

router = APIRouter()


@router.get("/market-data/providers", response_model=AdapterListRead)
def get_market_data_providers(
    container: ContainerDep,
) -> AdapterListRead:
    return AdapterListRead(
        items=[descriptor_schema(item) for item in container.status_queries.market_data_providers()]
    )


@router.get("/fundamental-data/providers", response_model=AdapterListRead)
def get_fundamental_data_providers(
    container: ContainerDep,
) -> AdapterListRead:
    return AdapterListRead(
        items=[
            descriptor_schema(item)
            for item in container.status_queries.fundamental_data_providers()
        ]
    )


@router.get("/event-data/providers", response_model=AdapterListRead)
def get_event_data_providers(
    container: ContainerDep,
) -> AdapterListRead:
    return AdapterListRead(
        items=[descriptor_schema(item) for item in container.status_queries.event_data_providers()]
    )
