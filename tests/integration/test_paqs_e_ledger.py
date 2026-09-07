from __future__ import annotations

import importlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
from threading import Barrier
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, event, func, insert, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.application.paqs_e_runtime import (
    build_reasoning_request,
    load_prompt_package,
    load_strategy_package,
    validate_reasoning_result,
)
from ai_infra_quant.core.domain.paqs_e_ledger import (
    AnalysisStatus,
    LedgerIntegrityError,
    LedgerPersistenceError,
    payload_sha256,
)
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    PaqsEValidationFailure,
    ValidatedPaqsEResult,
    ValidationIssue,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.core.ports.paqs_e_reasoning import (
    ReasoningFailureKind,
    ReasoningProviderFailure,
)
from ai_infra_quant.database.models.paqs_e_ledger import (
    PaqsEAnalysisRunModel,
    PaqsEDecisionModel,
    PaqsERuntimeArtifactModel,
)
from ai_infra_quant.database.models.security import SecurityModel
from ai_infra_quant.database.repositories.paqs_e_ledger import SQLAlchemyPaqsELedger

_runtime_fixtures = importlib.import_module("tests.unit.test_paqs_e_runtime")
NOW = _runtime_fixtures.NOW
SECURITY_ID = _runtime_fixtures.SECURITY_ID
_ready_long = _runtime_fixtures._ready_long
_result = _runtime_fixtures._result
_snapshot = _runtime_fixtures._snapshot


@pytest.fixture
def ledger(session_factory: sessionmaker[Session]) -> SQLAlchemyPaqsELedger:
    with session_factory.begin() as session:
        session.add(
            SecurityModel(
                id=SECURITY_ID,
                symbol="AVGO",
                market="US",
                currency="USD",
                display_name="AVGO",
                instrument_type="EQUITY",
                enabled=True,
                fractional_supported=False,
                metadata_status="UNAVAILABLE",
                record_source="SYSTEM_SEED",
                verification_status="SYSTEM_SEED_UNVERIFIED",
                tradability_status="UNVERIFIED",
                created_at=NOW,
                updated_at=NOW,
                version=1,
            )
        )
    return SQLAlchemyPaqsELedger(session_factory)


def _record(
    ledger: SQLAlchemyPaqsELedger,
    *,
    model: str = "fixture-model",
    strategy: Any = None,
    prompt: Any = None,
    outcome: Any = None,
    ready: bool = False,
) -> Any:
    strategy = strategy or load_strategy_package()
    prompt = prompt or load_prompt_package()
    request = build_reasoning_request(
        snapshot=_snapshot(), model_id=model, strategy=strategy, prompt=prompt
    )
    if outcome is None:
        result = _result(request)
        if ready:
            result = _ready_long(result)
        outcome = validate_reasoning_result(
            request=request, result=result, provider_response_id="fixture-response"
        )
        assert isinstance(outcome, ValidatedPaqsEResult)
    capsule = canonical_json(request)
    return ledger.record(
        request=request,
        strategy=strategy,
        prompt=prompt,
        outcome=outcome,
        request_payload_json=capsule,
        request_payload_sha256=payload_sha256(capsule),
        started_at=NOW,
        completed_at=NOW,
    )


def _counts(factory: Any) -> Any:
    with factory() as session:
        return tuple(
            session.scalar(select(func.count()).select_from(model))
            for model in (
                PaqsERuntimeArtifactModel,
                PaqsEAnalysisRunModel,
                PaqsEDecisionModel,
            )
        )


def test_success_capsules_exact_artifacts_summaries_and_decimal_roundtrip(
    ledger: Any,
    session_factory: sessionmaker[Session],
    migrated_engine: Engine,
) -> None:
    persisted = _record(ledger, ready=True)
    assert _counts(session_factory) == (2, 1, 1)
    run = ledger.get_analysis(persisted.run.id)
    decision = persisted.decision
    assert run == persisted.run and decision is not None
    assert ledger.get_decision(decision.id) == decision
    assert run.status is AnalysisStatus.SUCCEEDED
    assert payload_sha256(run.request_payload_json) == run.request_payload_sha256
    assert json.loads(run.request_payload_json)["market_snapshot"] == json.loads(
        canonical_json(_snapshot())
    )
    assert payload_sha256(decision.result_payload_json) == decision.result_payload_sha256
    assert canonical_json(decision.result) == decision.result_payload_json
    assert decision.one_line_thesis == decision.result.one_line_thesis
    assert decision.entry_advisory == decision.result.entry.advisory
    assert decision.rr_t1 == Decimal("2")
    assert "OPENAI_API_KEY" not in run.request_payload_json
    with session_factory() as session:
        artifacts = session.scalars(select(PaqsERuntimeArtifactModel)).all()
        by_kind = {item.artifact_kind: item for item in artifacts}
        for kind, package in (
            ("STRATEGY", load_strategy_package()),
            ("PROMPT", load_prompt_package()),
        ):
            assert by_kind[kind].content_text == package.content
            assert by_kind[kind].content_sha256 == payload_sha256(package.content)
            assert by_kind[kind].source_path == package.source_path
    with migrated_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT typeof(rr_t1) FROM paqs_e_decisions")).scalar()
            == "text"
        )


@pytest.mark.parametrize("kind", list(ReasoningFailureKind))
def test_all_provider_failure_kinds_persist_without_decision(
    ledger: Any, session_factory: sessionmaker[Session], kind: ReasoningFailureKind
) -> None:
    persisted = _record(ledger, outcome=ReasoningProviderFailure(kind, "Safe provider failure."))
    assert persisted.decision is None
    assert persisted.run.status is AnalysisStatus.PROVIDER_FAILED
    assert persisted.run.failure_kind == kind.value
    assert persisted.run.failure_reason == "Safe provider failure."
    assert persisted.run.validator_version is None
    assert ledger.get_analysis(persisted.run.id) == persisted.run
    assert _counts(session_factory) == (2, 1, 0)


def test_validation_failure_preserves_exact_issues(
    ledger: Any, session_factory: sessionmaker[Session]
) -> None:
    failure = PaqsEValidationFailure(
        "paqs-e-validator-v1",
        (ValidationIssue("IDENTITY_MISMATCH", "identity", "result identity must match request"),),
    )
    persisted = _record(ledger, outcome=failure)
    assert persisted.decision is None
    assert persisted.run.status is AnalysisStatus.VALIDATION_FAILED
    assert ledger.get_analysis(persisted.run.id).validation_issues == failure.issues
    assert _counts(session_factory) == (2, 1, 0)


def test_revisions_continue_across_model_and_content_changes(
    ledger: Any, session_factory: sessionmaker[Session]
) -> None:
    first = _record(ledger).decision
    original_bytes = first.result_payload_json
    second = _record(ledger, model="another-model").decision
    strategy = load_strategy_package()
    revised = replace(
        strategy,
        content=strategy.content + "\n",
        content_sha256=payload_sha256(strategy.content + "\n"),
    )
    third = _record(ledger, strategy=revised).decision
    distinct = _record(ledger, strategy=replace(strategy, strategy_id="fixture-other")).decision
    assert [
        (d.revision_no, d.supersedes_decision_id) for d in (first, second, third, distinct)
    ] == [
        (1, None),
        (2, first.id),
        (3, second.id),
        (1, None),
    ]
    assert first.snapshot_hash == second.snapshot_hash == third.snapshot_hash
    assert third.strategy_content_sha256 != first.strategy_content_sha256
    assert ledger.get_decision(first.id).result_payload_json == original_bytes
    assert _counts(session_factory) == (4, 4, 4)
    history = ledger.list_decisions(UUID(SECURITY_ID), strategy_id=strategy.strategy_id)
    assert [d.id for d in history] == [third.id, second.id, first.id]
    assert len(ledger.list_decisions(UUID(SECURITY_ID), limit=1)) == 1


def test_prompt_artifact_new_hash_creates_distinct_version(
    ledger: Any, session_factory: sessionmaker[Session]
) -> None:
    _record(ledger)
    prompt = load_prompt_package()
    changed = replace(
        prompt, content=prompt.content + "\n", content_sha256=payload_sha256(prompt.content + "\n")
    )
    second = _record(ledger, prompt=changed)
    assert second.run.prompt_content_sha256 == changed.content_sha256
    assert _counts(session_factory) == (3, 2, 2)


def test_concurrent_explicit_submissions_produce_distinct_contiguous_revisions(
    ledger: Any, session_factory: sessionmaker[Session]
) -> None:
    barrier = Barrier(4)

    def record_one(_: Any) -> Any:
        barrier.wait(timeout=10)
        return _record(SQLAlchemyPaqsELedger(session_factory)).decision

    with ThreadPoolExecutor(max_workers=4) as executor:
        decisions = sorted(
            executor.map(record_one, range(4)), key=lambda decision: decision.revision_no
        )
    assert [d.revision_no for d in decisions] == [1, 2, 3, 4]
    assert [d.supersedes_decision_id for d in decisions] == [None] + [d.id for d in decisions[:-1]]
    assert _counts(session_factory) == (2, 4, 4)


@pytest.mark.parametrize(
    "table", ["paqs_e_runtime_artifacts", "paqs_e_analysis_runs", "paqs_e_decisions"]
)
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_all_ledger_rows_reject_update_delete(
    ledger: Any, migrated_engine: Engine, table: str, operation: str
) -> None:
    _record(ledger)
    with migrated_engine.begin() as connection, pytest.raises(IntegrityError, match="immutable"):
        connection.execute(
            text(f"UPDATE {table} SET id = id" if operation == "UPDATE" else f"DELETE FROM {table}")
        )


def test_failed_run_is_immutable(ledger: Any, migrated_engine: Engine) -> None:
    _record(
        ledger, outcome=ReasoningProviderFailure(ReasoningFailureKind.PROVIDER_REFUSAL, "Refused.")
    )
    with migrated_engine.begin() as connection, pytest.raises(IntegrityError, match="immutable"):
        connection.execute(text("DELETE FROM paqs_e_analysis_runs"))


@pytest.mark.parametrize("target", ["request", "result", "summary", "artifact", "artifact_reuse"])
def test_corrupt_evidence_fails_closed(ledger: Any, migrated_engine: Engine, target: str) -> None:
    persisted = _record(ledger)
    with migrated_engine.begin() as connection:
        table = {
            "request": "paqs_e_analysis_runs",
            "result": "paqs_e_decisions",
            "summary": "paqs_e_decisions",
            "artifact": "paqs_e_runtime_artifacts",
            "artifact_reuse": "paqs_e_runtime_artifacts",
        }[target]
        connection.execute(text(f"DROP TRIGGER {table}_immutable_update"))
        column = {
            "request": "request_payload_json",
            "result": "result_payload_json",
            "summary": "one_line_thesis",
            "artifact": "content_text",
            "artifact_reuse": "content_text",
        }[target]
        connection.execute(text(f"UPDATE {table} SET {column} = 'tampered'"))
    with pytest.raises(LedgerIntegrityError):
        if target == "request":
            ledger.get_analysis(persisted.run.id)
        elif target == "artifact_reuse":
            _record(ledger)
        else:
            ledger.get_decision(persisted.decision.id)


@pytest.mark.parametrize("failure_point", ["insert", "commit"])
def test_failed_success_transaction_rolls_back_artifacts_run_and_decision(
    ledger: Any,
    session_factory: sessionmaker[Session],
    failure_point: str,
) -> None:
    def fail(*_: Any) -> None:
        raise IntegrityError("forced persistence failure", {}, Exception("fixture"))

    target, event_name = (
        (PaqsEDecisionModel, "before_insert")
        if failure_point == "insert"
        else (Session, "before_commit")
    )
    event.listen(target, event_name, fail)
    try:
        with pytest.raises(LedgerPersistenceError):
            _record(ledger)
    finally:
        event.remove(target, event_name, fail)
    assert _counts(session_factory) == (0, 0, 0)


def test_database_enforces_unique_analysis_run_and_revision(
    ledger: Any, migrated_engine: Engine
) -> None:
    _record(ledger)
    with migrated_engine.connect() as connection:
        row = dict(connection.execute(select(PaqsEDecisionModel.__table__)).mappings().one())
        run_row = dict(connection.execute(select(PaqsEAnalysisRunModel.__table__)).mappings().one())
    row["id"] = str(uuid4())
    with migrated_engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(insert(PaqsEDecisionModel).values(**row))
    run_row["id"] = str(uuid4())
    row["analysis_run_id"] = run_row["id"]
    with pytest.raises(IntegrityError, match="UNIQUE"), migrated_engine.begin() as connection:
        connection.execute(insert(PaqsEAnalysisRunModel).values(**run_row))
        connection.execute(insert(PaqsEDecisionModel).values(**row))
    assert {
        tuple(item["column_names"])
        for item in inspect(migrated_engine).get_unique_constraints("paqs_e_decisions")
    } >= {
        ("analysis_run_id",),
        ("security_id", "strategy_id", "revision_no"),
    }


def test_invalid_supplied_artifact_hash_rejected_without_writes(
    ledger: Any, session_factory: sessionmaker[Session]
) -> None:
    strategy = replace(load_strategy_package(), content="changed without updating hash")
    with pytest.raises(LedgerIntegrityError, match="SHA-256"):
        _record(ledger, strategy=strategy)
    assert _counts(session_factory) == (0, 0, 0)


def test_decision_read_rejects_parent_run_metadata_corruption(
    ledger: Any, migrated_engine: Engine
) -> None:
    persisted = _record(ledger)
    with migrated_engine.begin() as connection:
        connection.execute(text("DROP TRIGGER paqs_e_analysis_runs_immutable_update"))
        connection.execute(text("UPDATE paqs_e_analysis_runs SET model_id = 'tampered-model'"))
    with pytest.raises(LedgerIntegrityError):
        ledger.get_decision(persisted.decision.id)
    with pytest.raises(LedgerIntegrityError):
        ledger.list_decisions(UUID(SECURITY_ID))


def test_high_significance_financial_value_survives_result_capsule(ledger: Any) -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="fixture-model")
    exact = Decimal("12345678901234567890.123456789012345678")
    result = _result(request)
    result = replace(result, invalidation=replace(result.invalidation, calculation_reference=exact))
    validated = validate_reasoning_result(request=request, result=result)
    assert isinstance(validated, ValidatedPaqsEResult)
    persisted = _record(ledger, outcome=validated)
    loaded = ledger.get_decision(persisted.decision.id)
    assert loaded.result.invalidation.calculation_reference == exact
    assert str(exact) in loaded.result_payload_json
