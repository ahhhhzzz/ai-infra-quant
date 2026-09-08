from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.core.domain.common import canonical_uuid, require_utc
from ai_infra_quant.core.domain.paqs_e_ledger import (
    LedgerIntegrityError,
    LedgerPersistenceError,
    payload_sha256,
    verified_json,
)
from ai_infra_quant.core.domain.paqs_e_narrative import (
    NarrativeFailure,
    NarrativeFailureKind,
    NarrativeIdentity,
    NarrativeRequest,
    NarrativeResult,
    NarrativeRun,
    NarrativeSuccess,
    PersistedNarrative,
    check_final_text,
)
from ai_infra_quant.core.domain.paqs_e_reasoning import PromptPackage, StrategyPackage
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.database.models.paqs_e_ledger import PaqsERuntimeArtifactModel
from ai_infra_quant.database.models.paqs_e_narrative import results, runs
from ai_infra_quant.database.models.security import SecurityModel
from ai_infra_quant.database.repositories.paqs_e_ledger import SQLAlchemyPaqsELedger


class SQLAlchemyNarrativeLedger:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.sessions = session_factory

    def record(
        self,
        *,
        request: NarrativeRequest,
        strategy: StrategyPackage,
        prompt: PromptPackage,
        outcome: NarrativeSuccess | NarrativeFailure,
        started_at: datetime,
        completed_at: datetime,
    ) -> PersistedNarrative:
        if (
            strategy.strategy_id,
            strategy.content_sha256,
            prompt.prompt_version,
            prompt.content_sha256,
        ) != (
            request.primary_strategy_id,
            request.primary_strategy_content_sha256,
            request.prompt_version,
            request.prompt_content_sha256,
        ):
            raise LedgerIntegrityError("Narrative artifact identity mismatch")
        if require_utc(completed_at) < require_utc(started_at):
            raise LedgerIntegrityError("Narrative time order mismatch")
        payload = canonical_json(request)
        try:
            with self.sessions() as session, session.begin():
                if session.get_bind().dialect.name == "sqlite":
                    session.connection().exec_driver_sql("BEGIN IMMEDIATE")
                else:
                    session.execute(
                        select(SecurityModel.id)
                        .where(SecurityModel.id == request.security_id)
                        .with_for_update()
                    ).scalar_one()
                created = datetime.now(UTC)
                # Reuse the existing immutable artifact store, without changing legacy records.
                strategy_row = SQLAlchemyPaqsELedger._artifact(session, strategy, created)
                prompt_row = SQLAlchemyPaqsELedger._artifact(session, prompt, created)
                identity = {
                    field.name: getattr(request, field.name)
                    for field in fields(NarrativeIdentity)
                    if field.name
                    not in {
                        "strategy_id",
                        "strategy_content_sha256",
                        "strategy_artifact_id",
                        "prompt_artifact_id",
                    }
                }
                identity.update(
                    strategy_id=strategy.strategy_id,
                    strategy_content_sha256=strategy.content_sha256,
                    strategy_artifact_id=strategy_row.id,
                    prompt_artifact_id=prompt_row.id,
                )
                run_id = str(uuid4())
                succeeded = isinstance(outcome, NarrativeSuccess)
                session.execute(
                    insert(runs).values(
                        narrative_run_id=run_id,
                        **identity,
                        request_payload_json=payload,
                        request_payload_sha256=payload_sha256(payload),
                        status="SUCCEEDED" if succeeded else "PROVIDER_FAILED",
                        provider_response_id=outcome.provider_response_id
                        if isinstance(outcome, NarrativeSuccess)
                        else None,
                        failure_kind=outcome.kind.value
                        if isinstance(outcome, NarrativeFailure)
                        else None,
                        failure_reason=outcome.reason
                        if isinstance(outcome, NarrativeFailure)
                        else None,
                        started_at=started_at,
                        completed_at=completed_at,
                        created_at=created,
                    )
                )
                result_id = None
                if isinstance(outcome, NarrativeSuccess):
                    check_final_text(outcome.text)
                    previous = (
                        session.execute(
                            select(results)
                            .where(
                                results.c.security_id == request.security_id,
                                results.c.strategy_id == strategy.strategy_id,
                            )
                            .order_by(results.c.revision_no.desc())
                            .limit(1)
                        )
                        .mappings()
                        .one_or_none()
                    )
                    if previous is not None:
                        self._result(session, dict(previous))
                    result_id = str(uuid4())
                    session.execute(
                        insert(results).values(
                            narrative_result_id=result_id,
                            narrative_run_id=run_id,
                            **identity,
                            revision_no=previous["revision_no"] + 1 if previous else 1,
                            supersedes_narrative_result_id=previous["narrative_result_id"]
                            if previous
                            else None,
                            response_text=outcome.text,
                            response_text_sha256=payload_sha256(outcome.text),
                            created_at=created,
                        )
                    )
                run = self._run(
                    session,
                    dict(
                        session.execute(select(runs).where(runs.c.narrative_run_id == run_id))
                        .mappings()
                        .one()
                    ),
                )
                result = (
                    self._result(
                        session,
                        dict(
                            session.execute(
                                select(results).where(results.c.narrative_result_id == result_id)
                            )
                            .mappings()
                            .one()
                        ),
                    )
                    if result_id
                    else None
                )
                persisted = PersistedNarrative(run, result)
            return persisted
        except LedgerIntegrityError:
            raise
        except (SQLAlchemyError, TypeError, ValueError) as exc:
            raise LedgerPersistenceError("Narrative evidence could not be committed") from exc

    @staticmethod
    def _run(session: Session, row: dict[str, Any]) -> NarrativeRun:
        payload = verified_json(row["request_payload_json"], row["request_payload_sha256"])
        for field in fields(NarrativeIdentity):
            if field.name in {"strategy_artifact_id", "prompt_artifact_id"}:
                continue
            name = {
                "strategy_id": "primary_strategy_id",
                "strategy_content_sha256": "primary_strategy_content_sha256",
            }.get(field.name, field.name)
            if canonical_json(row[field.name]) != canonical_json(payload.get(name)):
                raise LedgerIntegrityError("Narrative request identity mismatch")
        snapshot = payload["market_snapshot"]
        if (
            snapshot["security"]["security_id"] != row["security_id"]
            or snapshot["snapshot_hash"] != row["snapshot_hash"]
        ):
            raise LedgerIntegrityError("Narrative Snapshot identity mismatch")
        for kind, key, digest, artifact_id in [
            (
                "STRATEGY",
                row["strategy_id"],
                row["strategy_content_sha256"],
                row["strategy_artifact_id"],
            ),
            (
                "PROMPT",
                row["prompt_version"],
                row["prompt_content_sha256"],
                row["prompt_artifact_id"],
            ),
        ]:
            artifact = session.get(PaqsERuntimeArtifactModel, artifact_id)
            if artifact is None or (
                artifact.artifact_kind,
                artifact.artifact_key,
                artifact.content_sha256,
                payload_sha256(artifact.content_text),
            ) != (kind, key, digest, digest):
                raise LedgerIntegrityError("Narrative runtime artifact mismatch")
        children = session.execute(
            select(results.c.narrative_result_id).where(
                results.c.narrative_run_id == row["narrative_run_id"]
            )
        ).all()
        if row["status"] == "SUCCEEDED":
            if (
                len(children) != 1
                or row["failure_kind"] is not None
                or row["failure_reason"] is not None
            ):
                raise LedgerIntegrityError("Narrative success requires one result")
        elif row["status"] == "PROVIDER_FAILED":
            if (
                children
                or row["failure_reason"]
                != NarrativeFailure(NarrativeFailureKind(row["failure_kind"])).reason
            ):
                raise LedgerIntegrityError("Invalid narrative failure evidence")
        else:
            raise LedgerIntegrityError("Invalid narrative status")
        return NarrativeRun(**row)

    @classmethod
    def _result(cls, session: Session, row: dict[str, Any]) -> NarrativeResult:
        check_final_text(row["response_text"])
        if payload_sha256(row["response_text"]) != row["response_text_sha256"]:
            raise LedgerIntegrityError("Narrative response hash mismatch")
        parent = (
            session.execute(select(runs).where(runs.c.narrative_run_id == row["narrative_run_id"]))
            .mappings()
            .one_or_none()
        )
        if (
            parent is None
            or parent["status"] != "SUCCEEDED"
            or any(parent[field.name] != row[field.name] for field in fields(NarrativeIdentity))
        ):
            raise LedgerIntegrityError("Narrative result parent mismatch")
        cls._run(session, dict(parent))
        predecessor_id = row["supersedes_narrative_result_id"]
        if row["revision_no"] == 1:
            if predecessor_id is not None:
                raise LedgerIntegrityError("Invalid narrative first revision")
        else:
            previous = (
                session.execute(
                    select(results).where(results.c.narrative_result_id == predecessor_id)
                )
                .mappings()
                .one_or_none()
            )
            if previous is None or (
                previous["security_id"],
                previous["strategy_id"],
                previous["revision_no"],
            ) != (row["security_id"], row["strategy_id"], row["revision_no"] - 1):
                raise LedgerIntegrityError("Narrative lineage mismatch")
        return NarrativeResult(**row)

    def get_run(self, run_id: str) -> NarrativeRun | None:
        canonical_uuid(run_id)
        with self.sessions() as session:
            row = (
                session.execute(select(runs).where(runs.c.narrative_run_id == run_id))
                .mappings()
                .one_or_none()
            )
            return self._run(session, dict(row)) if row else None

    def get_result(self, result_id: str) -> NarrativeResult | None:
        canonical_uuid(result_id)
        with self.sessions() as session:
            row = (
                session.execute(select(results).where(results.c.narrative_result_id == result_id))
                .mappings()
                .one_or_none()
            )
            return self._result(session, dict(row)) if row else None

    def history(
        self, security_id: str, strategy_id: str | None = None, limit: int = 20
    ) -> tuple[NarrativeResult, ...]:
        canonical_uuid(security_id)
        if not 1 <= limit <= 100:
            raise ValueError("Invalid narrative history limit")
        query = select(results).where(results.c.security_id == security_id)
        if strategy_id is not None:
            query = query.where(results.c.strategy_id == strategy_id)
        with self.sessions() as session:
            rows = (
                session.execute(
                    query.order_by(
                        results.c.created_at.desc(), results.c.narrative_result_id.desc()
                    ).limit(limit)
                )
                .mappings()
                .all()
            )
            return tuple(self._result(session, dict(row)) for row in rows)
