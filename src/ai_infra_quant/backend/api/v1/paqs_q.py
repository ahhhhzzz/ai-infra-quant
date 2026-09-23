"""Explicit PAQS-Q analysis and read-only Q/E comparison endpoints."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from ai_infra_quant.application.market_data_queries import (
    MarketDataSecurityMetadataConflict,
    MarketDataSecurityNotFound,
    MarketDataSecurityNotSupported,
)
from ai_infra_quant.backend.api.errors import problem_response
from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.core.domain.paqs_e_ledger import LedgerIntegrityError, LedgerPersistenceError
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.database.repositories.paqs_q_analysis import (
    PaqsQAnalysisIntegrityError,
    PaqsQAnalysisPersistenceError,
)

router = APIRouter(prefix="/paqs-q", tags=["paqs-q"])


class AnalyzeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    security_id: UUID


def _error(request: Request, status: int, code: str, detail: str) -> JSONResponse:
    return problem_response(
        request,
        status=status,
        code=code,
        title=code.replace("_", " ").title(),
        detail=detail,
    )


@router.post("/analyses", status_code=201, response_model=None)
def analyze(payload: AnalyzeCreate, request: Request, container: ContainerDep) -> JSONResponse:
    try:
        record = container.paqs_q_analysis_service.analyze(str(payload.security_id))
    except MarketDataSecurityNotFound:
        return _error(request, 404, "SECURITY_NOT_FOUND", "Security not found")
    except MarketDataSecurityMetadataConflict:
        return _error(request, 409, "SECURITY_METADATA_CONFLICT", "Security metadata conflict")
    except MarketDataSecurityNotSupported:
        return _error(
            request, 422, "PAQS_Q_SECURITY_UNSUPPORTED", "Q supports enabled US/HK equities"
        )
    except (PaqsQAnalysisIntegrityError, PaqsQAnalysisPersistenceError):
        return _error(
            request, 500, "PAQS_Q_LEDGER_ERROR", "Analysis could not be committed or verified"
        )
    except ValueError:
        return _error(
            request, 422, "PAQS_Q_INPUT_INVALID", "Market capture cannot form a Q analysis"
        )
    return JSONResponse(status_code=201, content=record)


@router.get("/analyses/{analysis_id}", response_model=None)
def get_analysis(analysis_id: UUID, request: Request, container: ContainerDep) -> JSONResponse:
    try:
        record = container.paqs_q_analysis_ledger.get(str(analysis_id))
    except (PaqsQAnalysisIntegrityError, PaqsQAnalysisPersistenceError, ValueError):
        return _error(
            request, 500, "PAQS_Q_LEDGER_ERROR", "Frozen analysis failed integrity verification"
        )
    if record is None:
        return _error(request, 404, "PAQS_Q_ANALYSIS_NOT_FOUND", "Q analysis not found")
    return JSONResponse(content=record)


@router.get("/securities/{security_id}/analyses", response_model=None)
def history(
    security_id: UUID,
    request: Request,
    container: ContainerDep,
    limit: int = Query(default=20, ge=1, le=100),
) -> JSONResponse:
    try:
        items = container.paqs_q_analysis_ledger.history(str(security_id), limit=limit)
    except (PaqsQAnalysisIntegrityError, PaqsQAnalysisPersistenceError, ValueError):
        return _error(
            request, 500, "PAQS_Q_LEDGER_ERROR", "Q history failed integrity verification"
        )
    return JSONResponse(content={"items": items})


@router.get("/analyses/{analysis_id}/compare/{narrative_result_id}", response_model=None)
def compare(
    analysis_id: UUID,
    narrative_result_id: UUID,
    request: Request,
    container: ContainerDep,
) -> JSONResponse:
    """Read frozen Q/E evidence; never invoke either engine or an E provider."""
    try:
        q = container.paqs_q_analysis_ledger.get(str(analysis_id))
        e = container.narrative_ledger.get_result(str(narrative_result_id))
        run = container.narrative_ledger.get_run(e.narrative_run_id) if e is not None else None
    except (
        PaqsQAnalysisIntegrityError,
        PaqsQAnalysisPersistenceError,
        LedgerIntegrityError,
        LedgerPersistenceError,
        ValueError,
        TypeError,
        KeyError,
    ):
        return _error(
            request, 500, "COMPARISON_LEDGER_ERROR", "Frozen evidence failed integrity verification"
        )
    if q is None or e is None or run is None:
        return _error(request, 404, "COMPARISON_RECORD_NOT_FOUND", "Q or E result not found")
    request_payload = json.loads(run.request_payload_json)
    q_snapshot = q["payload"]["market_snapshot"]
    e_snapshot = request_payload.get("market_snapshot")
    same_snapshot = (
        q["security_id"] == e.security_id
        and q["snapshot_hash"] == e.snapshot_hash
        and q_snapshot == e_snapshot
        and canonical_json(q_snapshot) == canonical_json(e_snapshot)
    )
    return JSONResponse(
        content={
            "same_snapshot": same_snapshot,
            "reason": "IDENTICAL_FROZEN_SNAPSHOT"
            if same_snapshot
            else "DIFFERENT_SNAPSHOT_NOT_DIRECTLY_COMPARABLE",
            "q_analysis": q,
            "e_narrative": {
                "narrative_result_id": e.narrative_result_id,
                "narrative_run_id": e.narrative_run_id,
                "snapshot_hash": e.snapshot_hash,
                "strategy_id": e.strategy_id,
                "model_provider": e.model_provider,
                "model_id": e.model_id,
                "web_research": e.web_research,
                "auxiliary_context": request_payload.get("auxiliary_context", []),
                "market_snapshot": e_snapshot,
                "response_text": e.response_text,
                "response_text_sha256": e.response_text_sha256,
            },
            "structural_agreement": "UNDETERMINED_UNSTRUCTURED_E_NARRATIVE",
        }
    )
