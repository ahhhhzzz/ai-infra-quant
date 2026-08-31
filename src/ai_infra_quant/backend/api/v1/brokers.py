from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ai_infra_quant.backend.api.errors import problem_response
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.status import AdapterListRead, AdapterStatusRead, CapabilityRead
from ai_infra_quant.core.domain.providers import AdapterDescriptor

router = APIRouter()


def descriptor_schema(descriptor: AdapterDescriptor) -> AdapterStatusRead:
    return AdapterStatusRead(
        name=descriptor.name,
        implementation_status=descriptor.implementation_status,
        connection_status=descriptor.connection_status,
        environment=None if descriptor.environment is None else descriptor.environment.value,
        last_checked_at=None,
        message=descriptor.message,
        capabilities=[
            CapabilityRead(name=item.name, status=item.status, reason=item.reason)
            for item in descriptor.capabilities
        ],
    )


@router.get("/brokers", response_model=AdapterListRead)
def get_brokers(container: ContainerDep) -> AdapterListRead:
    return AdapterListRead(
        items=[descriptor_schema(item) for item in container.status_queries.brokers()]
    )


@router.get("/brokers/{broker}/status", response_model=AdapterStatusRead)
def get_broker_status(
    broker: str,
    request: Request,
    container: ContainerDep,
) -> AdapterStatusRead | JSONResponse:
    try:
        return descriptor_schema(container.status_queries.broker(broker))
    except LookupError:
        return problem_response(
            request,
            status=404,
            code="BROKER_NOT_FOUND",
            title="Broker not found",
            detail="The broker descriptor is not registered.",
        )
