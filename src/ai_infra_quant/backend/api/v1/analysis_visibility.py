"""Explicit reversible history cleanup through the local mutation boundary."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import StrictBool
from sqlalchemy.exc import SQLAlchemyError

from ai_infra_quant.backend.api.errors import problem_response
from ai_infra_quant.backend.api.v1.paqs_e import _credential_boundary
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.common import StrictSchema
from ai_infra_quant.database.repositories.analysis_visibility import set_deleted

router = APIRouter(prefix="/analysis-history", tags=["analysis-history"])


class VisibilityWrite(StrictSchema):
    security_id: UUID
    deleted: StrictBool


@router.put("/{kind}/{record_id}/visibility", dependencies=[Depends(_credential_boundary)])
def change_visibility(
    kind: Literal["Q", "E"],
    record_id: UUID,
    payload: VisibilityWrite,
    request: Request,
    container: ContainerDep,
) -> JSONResponse:
    try:
        return JSONResponse(
            content=set_deleted(
                container.session_factory,
                kind,
                str(record_id),
                str(payload.security_id),
                payload.deleted,
            )
        )
    except (LookupError, PermissionError, SQLAlchemyError) as exc:
        status, code = (
            (404, "ANALYSIS_NOT_FOUND")
            if isinstance(exc, LookupError)
            else (409, "ANALYSIS_SECURITY_MISMATCH")
            if isinstance(exc, PermissionError)
            else (500, "ANALYSIS_VISIBILITY_ERROR")
        )
        return problem_response(
            request,
            status=status,
            code=code,
            title=code,
            detail="历史可见性操作未完成; 请核对证券与记录后重试。",
        )
