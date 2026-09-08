from __future__ import annotations

import json
from dataclasses import asdict
from ipaddress import ip_address
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from ai_infra_quant.application.market_data_queries import (
    MarketDataSecurityMetadataConflict,
    MarketDataSecurityNotFound,
    MarketDataSecurityNotSupported,
)
from ai_infra_quant.application.paqs_e_research import ResearchFailure
from ai_infra_quant.application.paqs_e_runtime import RuntimePackageError
from ai_infra_quant.backend.api.errors import problem_response
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.common import Problem
from ai_infra_quant.backend.schemas.paqs_e import (
    AnalysisProblem,
    AnalysisRunRead,
    AnalyzeCreate,
    AnalyzeCreated,
    ConfigurationRead,
    CredentialDelete,
    CredentialSave,
    CredentialStatusRead,
    DecisionHistoryRead,
    DecisionRead,
    ModelOptionRead,
    StrategyOptionRead,
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
from ai_infra_quant.core.domain.paqs_e_narrative import NarrativeResult, NarrativeRun
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningFailureKind

router = APIRouter(prefix="/paqs-e", tags=["paqs-e"])


@router.get("/configuration", response_model=ConfigurationRead, responses={503: {"model": Problem}})
def get_configuration(
    request: Request, container: ContainerDep
) -> ConfigurationRead | JSONResponse:
    configuration = container.paqs_e_configuration
    if configuration is None:
        return problem_response(
            request,
            status=503,
            code="PAQS_E_CONFIGURATION_UNAVAILABLE",
            title="PAQS-E configuration unavailable",
            detail="Registered strategy configuration could not be loaded. Restart after repair.",
        )
    return ConfigurationRead(
        default_model_key=container.paqs_e_credentials.registry.default_model_key,
        models=[
            ModelOptionRead.model_validate(item)
            for item in container.paqs_e_credentials.projection()
        ],
        default_strategy_id=configuration.default_strategy_id,
        strategies=tuple(StrategyOptionRead(**asdict(item)) for item in configuration.strategies),
    )


async def _credential_boundary(request: Request) -> None:
    try:
        client_local = request.client is not None and ip_address(request.client.host).is_loopback
        host = request.url.hostname
        host_local = host == "localhost" or (host is not None and ip_address(host).is_loopback)
    except ValueError:
        client_local = host_local = False
    if not client_local or not host_local:
        raise HTTPException(403, "Credential access requires loopback")
    if request.url.query:
        raise HTTPException(400, "Credential requests do not accept query parameters")
    if request.method != "GET":
        expected_origin = f"{request.url.scheme}://{request.url.netloc}"
        if (
            request.headers.get("origin") != expected_origin
            or request.headers.get("sec-fetch-site") not in {None, "same-origin"}
            or request.headers.get("content-type", "").split(";")[0].lower() != "application/json"
        ):
            raise HTTPException(403, "Same-origin JSON credential mutation required")
        if len(await request.body()) > 8192:
            raise HTTPException(413, "Credential request exceeds limit")


def _credential_failure(request: Request, status: int) -> JSONResponse:
    return problem_response(
        request,
        status=status,
        code="PAQS_E_CREDENTIAL_UNAVAILABLE",
        title="Credential operation unavailable",
        detail="Check the registered model and operating-system secure store.",
    )


@router.get(
    "/credentials/{model_key}",
    response_model=CredentialStatusRead,
    dependencies=[Depends(_credential_boundary)],
)
def credential_status(
    model_key: str, request: Request, container: ContainerDep
) -> CredentialStatusRead | JSONResponse:
    try:
        return CredentialStatusRead(**asdict(container.paqs_e_credentials.status(model_key)))
    except ValueError:
        return _credential_failure(request, 422)
    except Exception:
        return _credential_failure(request, 503)


@router.put(
    "/credentials/{model_key}",
    response_model=CredentialStatusRead,
    dependencies=[Depends(_credential_boundary)],
)
def save_credential(
    model_key: str, payload: CredentialSave, request: Request, container: ContainerDep
) -> CredentialStatusRead | JSONResponse:
    try:
        status = container.paqs_e_credentials.save(model_key, payload.secret.get_secret_value())
        return CredentialStatusRead(**asdict(status))
    except ValueError:
        return _credential_failure(request, 422)
    except Exception:
        return _credential_failure(request, 503)


@router.delete(
    "/credentials/{model_key}",
    response_model=CredentialStatusRead,
    dependencies=[Depends(_credential_boundary)],
)
def delete_credential(
    model_key: str, payload: CredentialDelete, request: Request, container: ContainerDep
) -> CredentialStatusRead | JSONResponse:
    del payload
    try:
        return CredentialStatusRead(**asdict(container.paqs_e_credentials.delete(model_key)))
    except ValueError:
        return _credential_failure(request, 422)
    except Exception:
        return _credential_failure(request, 503)


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
    include_in_schema=False,
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
    if not request.app.state.legacy_analysis_enabled:
        return problem_response(
            request,
            status=410,
            code="PAQS_E_STRUCTURED_ANALYZE_DISABLED",
            title="Legacy analysis disabled",
            detail=(
                "Use the narrative analysis endpoint for new analyses. "
                "Historical structured evidence remains readable."
            ),
        )
    try:
        persisted = container.paqs_e_analysis_service.analyze(
            security_id=str(payload.security_id),
            model_key=payload.model_key,
            strategy_id=payload.strategy_id,
            web_research=payload.web_research,
        )
    except ResearchFailure as failure:
        return problem_response(
            request,
            status=422,
            code="PAQS_E_RESEARCH_PRECONDITION_FAILED",
            title="Web research failed",
            detail=str(failure),
            extra={
                "failure_kind": failure.kind.value,
                **(
                    {"research_diagnostic": failure.diagnostic.as_dict()}
                    if failure.diagnostic
                    else {}
                ),
            },
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


@router.post("/narrative-analyses", status_code=201, response_model=None)
def analyze_narrative(
    payload: AnalyzeCreate, request: Request, container: ContainerDep
) -> JSONResponse:
    try:
        persisted = container.narrative_analysis_service.analyze(
            security_id=str(payload.security_id),
            model_key=payload.model_key,
            strategy_id=payload.strategy_id,
            web_research=payload.web_research,
        )
    except ResearchFailure as failure:
        return problem_response(
            request,
            status=422,
            code="PAQS_E_RESEARCH_PRECONDITION_FAILED",
            title="Web research failed",
            detail=str(failure),
            extra={
                "failure_kind": failure.kind.value,
                **(
                    {"research_diagnostic": failure.diagnostic.as_dict()}
                    if failure.diagnostic
                    else {}
                ),
            },
        )
    except MarketDataSecurityNotFound:
        return _not_found(request, "SECURITY")
    except MarketDataSecurityMetadataConflict:
        return problem_response(
            request,
            status=409,
            code="SECURITY_METADATA_CONFLICT",
            title="Security conflict",
            detail="Stored Security metadata conflicts with the market contract.",
        )
    except (MarketDataSecurityNotSupported, RuntimePackageError, ValueError) as error:
        if isinstance(error, LedgerIntegrityError):
            return _ledger_error(request)
        return problem_response(
            request,
            status=422,
            code="PAQS_E_NARRATIVE_PRECONDITION_FAILED",
            title="Narrative precondition failed",
            detail="A valid frozen narrative request could not be formed.",
        )
    except LedgerPersistenceError:
        return _ledger_error(request)
    if persisted.result is None:
        run = persisted.run
        status = 503 if run.failure_kind in {"CONFIGURATION_ERROR", "PROVIDER_UNAVAILABLE"} else 502
        return problem_response(
            request,
            status=status,
            code="PAQS_E_NARRATIVE_PROVIDER_FAILED",
            title="Narrative provider failed",
            detail=run.failure_reason or "Narrative provider failed",
            extra={
                "narrative_run_id": run.narrative_run_id,
                "analysis_status": run.status,
                "failure_kind": run.failure_kind,
            },
        )
    return JSONResponse(
        status_code=201,
        content={**json.loads(canonical_json(persisted.result)), "status": "SUCCEEDED"},
    )


@router.get("/narrative-analyses/{run_id}", response_model=NarrativeRun)
def get_narrative_run(
    run_id: UUID, request: Request, container: ContainerDep
) -> NarrativeRun | JSONResponse:
    try:
        run = container.narrative_ledger.get_run(str(run_id))
        return run if run else _not_found(request, "NARRATIVE_RUN")
    except (LedgerIntegrityError, LedgerPersistenceError, ValueError, TypeError, KeyError):
        return _ledger_error(request)


@router.get("/narrative-results/{result_id}", response_model=NarrativeResult)
def get_narrative_result(
    result_id: UUID, request: Request, container: ContainerDep
) -> NarrativeResult | JSONResponse:
    try:
        result = container.narrative_ledger.get_result(str(result_id))
        return result if result else _not_found(request, "NARRATIVE_RESULT")
    except (LedgerIntegrityError, LedgerPersistenceError, ValueError, TypeError, KeyError):
        return _ledger_error(request)


@router.get("/securities/{security_id}/narrative-results", response_model=None)
def narrative_history(
    security_id: UUID,
    request: Request,
    container: ContainerDep,
    strategy_id: str | None = Query(default=None, min_length=1, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
) -> JSONResponse:
    try:
        entries = container.narrative_ledger.history(str(security_id), strategy_id, limit)
        items = []
        for entry in entries:
            item = json.loads(canonical_json(entry))
            item["preview"] = item.pop("response_text")[:160]
            items.append(item)
        return JSONResponse(content={"items": items})
    except (LedgerIntegrityError, LedgerPersistenceError, ValueError, TypeError, KeyError):
        return _ledger_error(request)


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
