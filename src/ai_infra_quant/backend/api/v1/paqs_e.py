from __future__ import annotations

import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from ai_infra_quant.application.market_data_queries import (
    MarketDataSecurityMetadataConflict,
    MarketDataSecurityNotFound,
    MarketDataSecurityNotSupported,
)
from ai_infra_quant.application.paqs_e_runtime import RuntimePackageError
from ai_infra_quant.backend.api.errors import problem_response
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.common import Problem
from ai_infra_quant.backend.schemas.paqs_e import (
    AnalysisProblem,
    AnalysisRunRead,
    AnalyzeCreate,
    AnalyzeCreated,
    DecisionHistoryRead,
    DecisionRead,
    analysis_run_read,
    analyze_created,
    decision_read,
    decision_summary_read,
)
from ai_infra_quant.core.domain.paqs_e_ledger import (
    AnalysisRun,
    AnalysisStatus,
    LedgerIntegrityError,
    LedgerPersistenceError,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningFailureKind

router = APIRouter(prefix="/paqs-e", tags=["paqs-e"])


def _ledger_error(request: Request) -> JSONResponse:
    return problem_response(
        request,
        status=500,
        code="PAQS_E_LEDGER_ERROR",
        title="PAQS-E ledger unavailable",
        detail="The analysis evidence could not be committed or verified.",
    )


def _not_found(request: Request, entity: str) -> JSONResponse:
    return problem_response(
        request,
        status=404,
        code=f"{entity}_NOT_FOUND",
        title="Record not found",
        detail="The requested record was not found.",
    )


def _failed_analysis(request: Request, run: AnalysisRun) -> JSONResponse:
    context = {
        "analysis_run_id": str(run.id),
        "status": run.status.value,
        "failure_kind": run.failure_kind,
        "validator_version": run.validator_version,
        "validation_issues": json.loads(canonical_json(run.validation_issues)),
    }
    provider_failure = run.status is AnalysisStatus.PROVIDER_FAILED
    status = (
        503
        if run.failure_kind
        in {ReasoningFailureKind.CONFIGURATION_ERROR, ReasoningFailureKind.PROVIDER_UNAVAILABLE}
        else 502
    )
    return problem_response(
        request,
        status=status,
        code="PAQS_E_PROVIDER_FAILED" if provider_failure else "PAQS_E_VALIDATION_FAILED",
        title="PAQS-E analysis failed",
        detail=(
            run.failure_reason or "The reasoning provider could not produce a valid result."
            if provider_failure
            else "The reasoning result did not satisfy deterministic validation."
        ),
        extra={
            "analysis_run_id": str(run.id),
            "analysis_status": run.status.value,
            "failure_kind": run.failure_kind,
            "validator_version": run.validator_version,
            "validation_issues": context["validation_issues"],
            "analysis_run": context,
        },
    )


@router.post(
    "/analyses",
    response_model=AnalyzeCreated,
    status_code=201,
    responses={
        404: {"model": Problem},
        409: {"model": Problem},
        422: {"model": Problem},
        500: {"model": Problem},
        502: {"model": AnalysisProblem},
        503: {"model": AnalysisProblem},
    },
)
def analyze(
    payload: AnalyzeCreate, request: Request, container: ContainerDep
) -> AnalyzeCreated | JSONResponse:
    try:
        persisted = container.paqs_e_analysis_service.analyze(
            security_id=str(payload.security_id),
            model_id=payload.model_id,
            strategy_id=payload.strategy_id,
        )
    except MarketDataSecurityNotFound:
        return _not_found(request, "SECURITY")
    except MarketDataSecurityMetadataConflict:
        return problem_response(
            request,
            status=409,
            code="SECURITY_METADATA_CONFLICT",
            title="Security metadata conflict",
            detail="Stored Security metadata conflicts with the supported market contract.",
        )
    except MarketDataSecurityNotSupported:
        return problem_response(
            request,
            status=422,
            code="PAQS_MARKET_SNAPSHOT_SECURITY_NOT_SUPPORTED",
            title="PAQS market snapshot Security not supported",
            detail="PAQS market snapshots support enabled US/HK equities only.",
        )
    except RuntimePackageError:
        return problem_response(
            request,
            status=422,
            code="PAQS_E_RUNTIME_PACKAGE_UNAVAILABLE",
            title="PAQS-E runtime package unavailable",
            detail="The selected registered strategy or server prompt could not be loaded.",
        )
    except (LedgerIntegrityError, LedgerPersistenceError):
        return _ledger_error(request)
    except ValueError:
        return problem_response(
            request,
            status=422,
            code="PAQS_E_ANALYSIS_PRECONDITION_FAILED",
            title="PAQS-E analysis precondition failed",
            detail="A valid immutable reasoning request could not be formed.",
        )
    if persisted.run.status is not AnalysisStatus.SUCCEEDED:
        return _failed_analysis(request, persisted.run)
    return analyze_created(persisted)


@router.get("/analyses/{analysis_run_id}", response_model=AnalysisRunRead)
def get_analysis(
    analysis_run_id: UUID, request: Request, container: ContainerDep
) -> AnalysisRunRead | JSONResponse:
    try:
        run = container.paqs_e_ledger.get_analysis(analysis_run_id)
    except (LedgerIntegrityError, LedgerPersistenceError):
        return _ledger_error(request)
    return _not_found(request, "ANALYSIS_RUN") if run is None else analysis_run_read(run)


@router.get("/decisions/{decision_id}", response_model=DecisionRead)
def get_decision(
    decision_id: UUID, request: Request, container: ContainerDep
) -> DecisionRead | JSONResponse:
    try:
        decision = container.paqs_e_ledger.get_decision(decision_id)
    except (LedgerIntegrityError, LedgerPersistenceError):
        return _ledger_error(request)
    return _not_found(request, "DECISION") if decision is None else decision_read(decision)


@router.get("/securities/{security_id}/decisions", response_model=DecisionHistoryRead)
def list_decisions(
    security_id: UUID,
    request: Request,
    container: ContainerDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    strategy_id: Annotated[str | None, Query(min_length=1)] = None,
) -> DecisionHistoryRead | JSONResponse:
    try:
        container.security_service.get(str(security_id))
        decisions = container.paqs_e_ledger.list_decisions(
            security_id, limit=limit, strategy_id=strategy_id
        )
    except LookupError:
        return _not_found(request, "SECURITY")
    except (LedgerIntegrityError, LedgerPersistenceError):
        return _ledger_error(request)
    return DecisionHistoryRead(items=[decision_summary_read(decision) for decision in decisions])
