from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ai_infra_quant.application.security_service import SecurityAlreadyExists
from ai_infra_quant.backend.api.errors import problem_response
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.security import (
    SecurityCreateV1,
    SecurityReadV1,
    security_read_from_domain,
)

router = APIRouter()


@router.post("/securities", response_model=SecurityReadV1, status_code=201)
def create_security(
    payload: SecurityCreateV1,
    request: Request,
    container: ContainerDep,
) -> SecurityReadV1 | JSONResponse:
    try:
        security = container.security_service.create(
            market=payload.market,
            symbol=payload.symbol,
            currency=payload.currency,
            instrument_type=payload.instrument_type,
            display_name=payload.display_name,
        )
    except SecurityAlreadyExists as exc:
        return problem_response(
            request,
            status=409,
            code="SECURITY_ALREADY_EXISTS",
            title="Security already exists",
            detail="The normalized market and symbol already identify a canonical security.",
            extra={"security_id": exc.security_id},
        )
    return security_read_from_domain(security)


@router.get("/securities/{security_id}", response_model=SecurityReadV1)
def get_security(
    security_id: UUID,
    request: Request,
    container: ContainerDep,
) -> SecurityReadV1 | JSONResponse:
    try:
        return security_read_from_domain(container.security_service.get(str(security_id)))
    except LookupError:
        return problem_response(
            request,
            status=404,
            code="SECURITY_NOT_FOUND",
            title="Security not found",
            detail="Security was not found.",
        )
