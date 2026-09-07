from __future__ import annotations

import json
from dataclasses import fields
from datetime import UTC, datetime
from enum import Enum
from typing import Any, get_type_hints
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.core.domain.enums import InstrumentType
from ai_infra_quant.core.domain.paqs_e_ledger import (
    AnalysisRun,
    AnalysisStatus,
    Decision,
    LedgerIdentity,
    LedgerIntegrityError,
    LedgerPersistenceError,
    PersistedAnalysis,
    payload_sha256,
    result_summary,
    verified_json,
)
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    AnalysisMode,
    PaqsEReasoningRequestV1,
    PaqsEValidationFailure,
    PromptPackage,
    StrategyPackage,
    ValidatedPaqsEResult,
    ValidationIssue,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.core.ports.paqs_e_ledger import AnalysisOutcome
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningProviderFailure
from ai_infra_quant.database.models.paqs_e_ledger import (
    PaqsEAnalysisRunModel,
    PaqsEDecisionModel,
    PaqsERuntimeArtifactModel,
)
from ai_infra_quant.database.models.security import SecurityModel


class SQLAlchemyPaqsELedger:
    """Bounded terminal-outcome UoW. No session exists during provider reasoning."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def record(
        self,
        *,
        request: PaqsEReasoningRequestV1,
        strategy: StrategyPackage,
        prompt: PromptPackage,
        outcome: AnalysisOutcome,
        request_payload_json: str,
        request_payload_sha256: str,
        started_at: datetime,
        completed_at: datetime,
    ) -> PersistedAnalysis:
        verified_json(request_payload_json, request_payload_sha256)
        if canonical_json(request) != request_payload_json:
            raise LedgerIntegrityError("PAQS-E request capsule differs from runtime request")
        if (
            strategy.strategy_id != request.primary_strategy_id
            or strategy.content_sha256 != request.primary_strategy_content_sha256
            or prompt.prompt_version != request.prompt_version
            or prompt.content_sha256 != request.prompt_content_sha256
        ):
            raise LedgerIntegrityError("PAQS-E runtime artifacts disagree with request identity")
        try:
            with self._session_factory() as session, session.begin():
                # Acquire writer serialization only after the terminal provider outcome exists.
                # SQLite cannot lock a missing revision row; BEGIN IMMEDIATE serializes the
                # artifact lookup and next-revision selection across processes/connections.
                if session.get_bind().dialect.name == "sqlite":
                    session.connection().exec_driver_sql("BEGIN IMMEDIATE")
                else:
                    session.execute(
                        select(SecurityModel.id)
                        .where(
                            SecurityModel.id == str(request.market_snapshot.security.security_id)
                        )
                        .with_for_update()
                    ).scalar_one()
                created_at = datetime.now(UTC)
                strategy_row = self._artifact(session, strategy, created_at)
                prompt_row = self._artifact(session, prompt, created_at)
                identity: dict[str, Any] = {
                    "security_id": str(request.market_snapshot.security.security_id),
                    "symbol": request.symbol,
                    "market": request.market,
                    "instrument_type": request.instrument_type.value,
                    "snapshot_hash": request.snapshot_hash,
                    "snapshot_as_of_timestamp": request.snapshot_as_of_timestamp,
                    "analysis_mode": request.analysis_mode.value,
                    "request_schema_version": request.request_schema_version,
                    "output_schema_version": request.output_schema_version,
                    "runtime_config_version": request.runtime_config_version,
                    "validator_version": None
                    if isinstance(outcome, ReasoningProviderFailure)
                    else outcome.validator_version,
                    "model_provider": request.model_provider,
                    "model_id": request.model_id,
                    "strategy_id": request.primary_strategy_id,
                    "strategy_content_sha256": request.primary_strategy_content_sha256,
                    "strategy_artifact_id": strategy_row.id,
                    "prompt_version": request.prompt_version,
                    "prompt_content_sha256": request.prompt_content_sha256,
                    "prompt_artifact_id": prompt_row.id,
                }
                if isinstance(outcome, ReasoningProviderFailure):
                    status = AnalysisStatus.PROVIDER_FAILED
                elif isinstance(outcome, PaqsEValidationFailure):
                    status = AnalysisStatus.VALIDATION_FAILED
                elif isinstance(outcome, ValidatedPaqsEResult):
                    status = AnalysisStatus.SUCCEEDED
                else:
                    raise LedgerIntegrityError("unsupported PAQS-E terminal outcome")
                run_model = PaqsEAnalysisRunModel(
                    id=str(uuid4()),
                    **identity,
                    request_payload_json=request_payload_json,
                    request_payload_sha256=request_payload_sha256,
                    status=status.value,
                    provider_response_id=outcome.provider_response_id
                    if isinstance(outcome, ValidatedPaqsEResult)
                    else None,
                    failure_kind=outcome.kind.value
                    if isinstance(outcome, ReasoningProviderFailure)
                    else None,
                    failure_reason=outcome.reason
                    if isinstance(outcome, ReasoningProviderFailure)
                    else None,
                    validation_issues_json=canonical_json(outcome.issues)
                    if isinstance(outcome, PaqsEValidationFailure)
                    else "[]",
                    started_at=started_at,
                    completed_at=completed_at,
                    created_at=created_at,
                )
                session.add(run_model)
                session.flush()
                run = self._run(session, run_model)
                decision = None
                if isinstance(outcome, ValidatedPaqsEResult):
                    previous = session.execute(
                        select(PaqsEDecisionModel)
                        .where(
                            PaqsEDecisionModel.security_id == identity["security_id"],
                            PaqsEDecisionModel.strategy_id == identity["strategy_id"],
                        )
                        .order_by(PaqsEDecisionModel.revision_no.desc())
                        .limit(1)
                    ).scalar_one_or_none()
                    if previous is not None:
                        self._decision(session, previous)
                    result_json = canonical_json(outcome.result)
                    decision_model = PaqsEDecisionModel(
                        id=str(uuid4()),
                        analysis_run_id=run_model.id,
                        **identity,
                        revision_no=1 if previous is None else previous.revision_no + 1,
                        supersedes_decision_id=None if previous is None else previous.id,
                        result_payload_json=result_json,
                        result_payload_sha256=payload_sha256(result_json),
                        **result_summary(outcome.result),
                        created_at=created_at,
                    )
                    session.add(decision_model)
                    session.flush()
                    decision = self._decision(session, decision_model)
                persisted = PersistedAnalysis(run, decision)
            # Exiting session.begin() has committed before the caller receives identities.
            return persisted
        except LedgerIntegrityError:
            raise
        except (SQLAlchemyError, ValueError, TypeError) as exc:
            raise LedgerPersistenceError(
                "PAQS-E ledger transaction could not be committed"
            ) from exc

    @staticmethod
    def _artifact(
        session: Session,
        package: StrategyPackage | PromptPackage,
        created_at: datetime,
    ) -> PaqsERuntimeArtifactModel:
        if payload_sha256(package.content) != package.content_sha256:
            raise LedgerIntegrityError("PAQS-E runtime artifact content SHA-256 mismatch")
        kind = "STRATEGY" if isinstance(package, StrategyPackage) else "PROMPT"
        key = (
            package.strategy_id if isinstance(package, StrategyPackage) else package.prompt_version
        )
        existing = session.execute(
            select(PaqsERuntimeArtifactModel).where(
                PaqsERuntimeArtifactModel.artifact_kind == kind,
                PaqsERuntimeArtifactModel.artifact_key == key,
                PaqsERuntimeArtifactModel.content_sha256 == package.content_sha256,
            )
        ).scalar_one_or_none()
        if existing is not None:
            if (
                payload_sha256(existing.content_text) != existing.content_sha256
                or existing.content_text != package.content
            ):
                raise LedgerIntegrityError("PAQS-E stored runtime artifact is corrupt")
            return existing
        row = PaqsERuntimeArtifactModel(
            id=str(uuid4()),
            artifact_kind=kind,
            artifact_key=key,
            display_name=package.display_name if isinstance(package, StrategyPackage) else None,
            source_path=package.source_path,
            content_sha256=package.content_sha256,
            content_text=package.content,
            created_at=created_at,
        )
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def _identity(
        session: Session, row: PaqsEAnalysisRunModel | PaqsEDecisionModel
    ) -> dict[str, Any]:
        identity = {field.name: getattr(row, field.name) for field in fields(LedgerIdentity)}
        for kind, key, digest, artifact_id in (
            ("STRATEGY", row.strategy_id, row.strategy_content_sha256, row.strategy_artifact_id),
            ("PROMPT", row.prompt_version, row.prompt_content_sha256, row.prompt_artifact_id),
        ):
            artifact = session.get(PaqsERuntimeArtifactModel, artifact_id)
            if artifact is None or (
                artifact.artifact_kind != kind
                or artifact.artifact_key != key
                or artifact.content_sha256 != digest
                or payload_sha256(artifact.content_text) != digest
            ):
                raise LedgerIntegrityError("PAQS-E runtime artifact evidence is corrupt")
        for name in ("security_id", "strategy_artifact_id", "prompt_artifact_id"):
            identity[name] = UUID(identity[name])
        identity["instrument_type"] = InstrumentType(identity["instrument_type"])
        identity["analysis_mode"] = AnalysisMode(identity["analysis_mode"])
        return identity

    @classmethod
    def _run(cls, session: Session, row: PaqsEAnalysisRunModel) -> AnalysisRun:
        issues = json.loads(row.validation_issues_json)
        if not isinstance(issues, list) or canonical_json(issues) != row.validation_issues_json:
            raise LedgerIntegrityError("PAQS-E stored validation issues are invalid")
        parsed_issues = []
        for issue in issues:
            if (
                not isinstance(issue, dict)
                or set(issue) != {"code", "field", "message"}
                or not all(isinstance(value, str) for value in issue.values())
            ):
                raise LedgerIntegrityError("PAQS-E stored validation issue is invalid")
            parsed_issues.append(ValidationIssue(**issue))
        return AnalysisRun(
            id=UUID(row.id),
            **cls._identity(session, row),
            request_payload_json=row.request_payload_json,
            request_payload_sha256=row.request_payload_sha256,
            status=AnalysisStatus(row.status),
            provider_response_id=row.provider_response_id,
            failure_kind=row.failure_kind,
            failure_reason=row.failure_reason,
            validation_issues=tuple(parsed_issues),
            started_at=row.started_at,
            completed_at=row.completed_at,
            created_at=row.created_at,
        )

    @classmethod
    def _decision(cls, session: Session, row: PaqsEDecisionModel) -> Decision:
        identity = cls._identity(session, row)
        predecessor_id = row.supersedes_decision_id
        if predecessor_id is not None:
            predecessor = session.get(PaqsEDecisionModel, predecessor_id)
            if predecessor is None or (
                predecessor.security_id != row.security_id
                or predecessor.strategy_id != row.strategy_id
                or predecessor.revision_no != row.revision_no - 1
            ):
                raise LedgerIntegrityError("PAQS-E Decision revision lineage is corrupt")
        parent = session.execute(
            select(
                PaqsEAnalysisRunModel.status,
                *(getattr(PaqsEAnalysisRunModel, field.name) for field in fields(LedgerIdentity)),
            ).where(PaqsEAnalysisRunModel.id == row.analysis_run_id)
        ).one_or_none()
        expected_parent = (
            "SUCCEEDED",
            *(getattr(row, field.name) for field in fields(LedgerIdentity)),
        )
        if parent is None or tuple(parent) != expected_parent:
            raise LedgerIntegrityError("PAQS-E Decision Analysis Run relationship is corrupt")
        values = {
            field.name: getattr(row, field.name)
            for field in fields(Decision)
            if field.name not in identity
        }
        values["id"] = UUID(row.id)
        values["analysis_run_id"] = UUID(row.analysis_run_id)
        values["supersedes_decision_id"] = None if predecessor_id is None else UUID(predecessor_id)
        for name, annotation in get_type_hints(Decision).items():
            if name in values and isinstance(annotation, type) and issubclass(annotation, Enum):
                values[name] = annotation(values[name])
        return Decision(**identity, **values)

    def get_analysis(self, analysis_run_id: UUID) -> AnalysisRun | None:
        try:
            with self._session_factory() as session:
                row = session.get(PaqsEAnalysisRunModel, str(analysis_run_id))
                if row is None:
                    return None
                run = self._run(session, row)
                decision_ids = session.scalars(
                    select(PaqsEDecisionModel.id).where(
                        PaqsEDecisionModel.analysis_run_id == row.id,
                    )
                ).all()
                if (run.status is AnalysisStatus.SUCCEEDED) != (len(decision_ids) == 1):
                    raise LedgerIntegrityError("PAQS-E Analysis Run Decision pairing is corrupt")
                return run
        except (SQLAlchemyError, ValueError, TypeError) as exc:
            raise LedgerIntegrityError("PAQS-E Analysis Run evidence could not be read") from exc

    def get_decision(self, decision_id: UUID) -> Decision | None:
        try:
            with self._session_factory() as session:
                row = session.get(PaqsEDecisionModel, str(decision_id))
                return None if row is None else self._decision(session, row)
        except (SQLAlchemyError, ValueError, TypeError) as exc:
            raise LedgerIntegrityError("PAQS-E Decision evidence could not be read") from exc

    def list_decisions(
        self,
        security_id: UUID,
        *,
        limit: int = 20,
        strategy_id: str | None = None,
    ) -> tuple[Decision, ...]:
        if isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("PAQS-E history limit must be between 1 and 100")
        try:
            with self._session_factory() as session:
                query = select(PaqsEDecisionModel).where(
                    PaqsEDecisionModel.security_id == str(security_id)
                )
                if strategy_id is not None:
                    query = query.where(PaqsEDecisionModel.strategy_id == strategy_id)
                query = query.order_by(
                    PaqsEDecisionModel.created_at.desc(), PaqsEDecisionModel.id.desc()
                ).limit(limit)
                return tuple(self._decision(session, row) for row in session.scalars(query))
        except (SQLAlchemyError, ValueError, TypeError) as exc:
            raise LedgerIntegrityError(
                "PAQS-E Decision history evidence could not be read"
            ) from exc
