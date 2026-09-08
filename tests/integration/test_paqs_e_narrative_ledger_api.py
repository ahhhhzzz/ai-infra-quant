from __future__ import annotations

import json
from dataclasses import asdict, replace
from typing import Any
from uuid import uuid4

import pytest
from alembic import command
from sqlalchemy import Engine, event, insert, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from test_migrations import _alembic_config
from test_paqs_e_analysis_api import AnalysisHarness
from test_paqs_e_analysis_api import analysis as analysis_fixture
from test_paqs_e_ledger import NOW, SECURITY_ID, _record, _snapshot
from test_paqs_e_ledger import ledger as ledger_fixture

from ai_infra_quant.application.paqs_e_narrative import (
    NarrativeAnalysisService,
    build_narrative_request,
    load_narrative_prompt,
)
from ai_infra_quant.application.paqs_e_runtime import load_strategy_package
from ai_infra_quant.core.domain.paqs_e_ledger import LedgerPersistenceError, payload_sha256
from ai_infra_quant.core.domain.paqs_e_narrative import NarrativeFailure, NarrativeSuccess
from ai_infra_quant.core.domain.paqs_e_narrative import NarrativeFailureKind as Kind
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.database.models.paqs_e_narrative import results, runs
from ai_infra_quant.database.repositories.paqs_e_ledger import SQLAlchemyPaqsELedger
from ai_infra_quant.database.repositories.paqs_e_narrative import SQLAlchemyNarrativeLedger

analysis = analysis_fixture
ledger = ledger_fixture

PROSE = '  # 最终分析\nContext 尚待确认;Trigger 与 Followthrough 分开。\n{"advisory":"自由文本"}\n'


def record(
    store: SQLAlchemyNarrativeLedger,
    *,
    model: str = "gpt-5.6-luna",
    strategy: Any = None,
    outcome: Any = None,
) -> Any:
    strategy = strategy or load_strategy_package()
    prompt = load_narrative_prompt()
    return store.record(
        request=build_narrative_request(
            snapshot=_snapshot(),
            model_provider="openai",
            model_id=model,
            strategy=strategy,
            prompt=prompt,
        ),
        strategy=strategy,
        prompt=prompt,
        outcome=outcome or NarrativeSuccess(PROSE, "synthetic"),
        started_at=NOW,
        completed_at=NOW,
    )


def legacy_evidence(engine: Engine) -> Any:
    with engine.connect() as connection:
        tables = ("paqs_e_runtime_artifacts", "paqs_e_analysis_runs", "paqs_e_decisions")
        return (
            connection.execute(
                text(
                    "SELECT type,name,tbl_name,sql FROM sqlite_master "
                    "WHERE tbl_name IN ('paqs_e_runtime_artifacts',"
                    "'paqs_e_analysis_runs','paqs_e_decisions') "
                    "ORDER BY type,name"
                )
            ).all(),
            {
                table: connection.execute(text(f"SELECT * FROM {table} ORDER BY id")).all()
                for table in tables
            },
        )


def test_upgrade_from_0002_preserves_legacy_bytes_and_downgrade_removes_only_narrative(
    ledger: SQLAlchemyPaqsELedger,
    migrated_engine: Engine,
    database_url: str,
    session_factory: sessionmaker[Session],
) -> None:
    legacy = _record(ledger)
    config = _alembic_config(database_url)
    command.downgrade(config, "0002_task007b_paqs_e_ledger")
    before = legacy_evidence(migrated_engine)
    tables = set(inspect(migrated_engine).get_table_names())
    command.upgrade(config, "head")
    assert set(inspect(migrated_engine).get_table_names()) - tables == {runs.name, results.name}
    assert legacy_evidence(migrated_engine) == before
    assert ledger.get_decision(legacy.decision.id) == legacy.decision
    store = SQLAlchemyNarrativeLedger(session_factory)
    first = record(store)
    assert first.result.revision_no == 1  # independent of the existing legacy revision 1
    second = record(store, model="gpt-5.6-sol")
    assert second.result.revision_no == 2
    assert second.result.supersedes_narrative_result_id == first.result.narrative_result_id
    assert first.result.response_text == PROSE
    assert first.result.response_text_sha256 == payload_sha256(PROSE)
    assert store.get_result(first.result.narrative_result_id) == first.result
    # Only immutable new prompt artifact is additive; every prior row is unchanged.
    after = legacy_evidence(migrated_engine)
    assert after[0] == before[0]
    for table, rows in before[1].items():
        assert all(row in after[1][table] for row in rows)
    legacy_after_write = legacy_evidence(migrated_engine)
    command.downgrade(config, "0002_task007b_paqs_e_ledger")
    assert set(inspect(migrated_engine).get_table_names()) == tables
    assert legacy_evidence(migrated_engine) == legacy_after_write
    assert ledger.get_decision(legacy.decision.id) == legacy.decision


def test_revision_scope_failure_and_frozen_request_roundtrip(
    ledger: SQLAlchemyPaqsELedger,
    session_factory: sessionmaker[Session],
) -> None:
    store = SQLAlchemyNarrativeLedger(session_factory)
    first = record(store)
    failed = record(store, outcome=NarrativeFailure(Kind.PROVIDER_INCOMPLETE))
    assert failed.result is None
    assert store.get_run(failed.run.narrative_run_id) == failed.run
    second = record(store, model="gpt-5.6-terra")
    assert second.result.revision_no == 2
    alternative = replace(load_strategy_package(), strategy_id="fixture-alternative")
    other = record(store, strategy=alternative)
    assert other.result.revision_no == 1
    assert len(store.history(SECURITY_ID)) == 3
    assert len(store.history(SECURITY_ID, alternative.strategy_id)) == 1
    assert len(store.history(SECURITY_ID, limit=1)) == 1
    payload = json.loads(first.run.request_payload_json)
    assert canonical_json(payload) == first.run.request_payload_json
    assert payload["market_snapshot"] == json.loads(canonical_json(_snapshot()))
    assert first.run.request_payload_sha256 == payload_sha256(first.run.request_payload_json)
    assert "validator_version" not in asdict(first.run)
    assert "result" not in asdict(first.result)


@pytest.mark.parametrize("table", [runs, results], ids=["runs", "results"])
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_narrative_rows_are_append_only(
    ledger: SQLAlchemyPaqsELedger,
    session_factory: sessionmaker[Session],
    migrated_engine: Engine,
    table: Any,
    operation: str,
) -> None:
    record(SQLAlchemyNarrativeLedger(session_factory))
    statement = (
        f"{operation} {table.name} SET symbol=symbol"
        if operation == "UPDATE"
        else f"DELETE FROM {table.name}"
    )
    with pytest.raises(IntegrityError), migrated_engine.begin() as connection:
        connection.execute(text(statement))


@pytest.mark.parametrize(
    "change",
    ["failed-parent", "duplicate", "wrong-identity", "wrong-predecessor", "wrong-revision"],
)
def test_database_rejects_invalid_result_parent_and_lineage(
    ledger: SQLAlchemyPaqsELedger,
    session_factory: sessionmaker[Session],
    migrated_engine: Engine,
    change: str,
) -> None:
    store = SQLAlchemyNarrativeLedger(session_factory)
    first = record(store)
    row = asdict(first.result)
    row["narrative_result_id"] = str(uuid4())
    if change != "duplicate":
        parent = asdict(first.run)
        parent["narrative_run_id"] = str(uuid4())
        with migrated_engine.begin() as connection:
            connection.execute(insert(runs).values(**parent))
        row.update(
            narrative_run_id=parent["narrative_run_id"],
            revision_no=2,
            supersedes_narrative_result_id=first.result.narrative_result_id,
        )
    if change == "failed-parent":
        failed = record(store, outcome=NarrativeFailure(Kind.PROVIDER_REFUSAL))
        row["narrative_run_id"] = failed.run.narrative_run_id
    elif change == "wrong-identity":
        row["model_id"] = "gpt-5.6-sol"
    elif change == "wrong-predecessor":
        row.update(revision_no=2, supersedes_narrative_result_id=str(uuid4()))
    elif change == "wrong-revision":
        row["revision_no"] = 8
    with pytest.raises(IntegrityError), migrated_engine.begin() as connection:
        connection.execute(insert(results).values(**row))


def test_insert_failure_rolls_back_run_result_and_artifacts(
    ledger: SQLAlchemyPaqsELedger, session_factory: sessionmaker[Session], migrated_engine: Engine
) -> None:
    def reject(
        connection: Any, cursor: Any, statement: str, parameters: Any, context: Any, many: Any
    ) -> None:
        if statement.startswith("INSERT INTO paqs_e_narrative_results"):
            raise IntegrityError("synthetic", {}, Exception("synthetic"))

    event.listen(migrated_engine, "before_cursor_execute", reject)
    try:
        with pytest.raises(LedgerPersistenceError):
            record(SQLAlchemyNarrativeLedger(session_factory))
    finally:
        event.remove(migrated_engine, "before_cursor_execute", reject)
    with migrated_engine.connect() as connection:
        assert connection.execute(select(runs)).all() == []
        assert connection.execute(select(results)).all() == []
        assert connection.scalar(text("SELECT COUNT(*) FROM paqs_e_runtime_artifacts")) == 0


class TextProvider:
    def __init__(self, outcome: Any = None) -> None:
        self.outcome = outcome or NarrativeSuccess(PROSE, "synthetic-api")
        self.requests: list[Any] = []

    def reason_text(self, *, request: Any, strategy: Any, prompt: Any) -> Any:
        self.requests.append(request)
        return self.outcome


def install(analysis: AnalysisHarness, provider: TextProvider) -> None:
    container = analysis.container
    container.narrative_analysis_service = NarrativeAnalysisService(
        analysis.snapshots,
        provider,
        container.narrative_ledger,
        container.narrative_analysis_service.models,
        container.narrative_analysis_service.research,
        now=lambda: NOW,
    )


def test_normal_api_persists_exact_text_reads_history_and_disables_legacy_post(
    analysis: AnalysisHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = TextProvider()
    install(analysis, provider)
    analysis.app.state.legacy_analysis_enabled = False

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Legacy semantic validator must not run")

    monkeypatch.setattr(
        "ai_infra_quant.application.paqs_e_runtime.validate_reasoning_result", forbidden
    )
    assert (
        analysis.client.post("/api/v1/paqs-e/analyses", json=analysis.payload()).status_code == 410
    )
    assert "/api/v1/paqs-e/analyses" not in analysis.client.get("/openapi.json").json()["paths"]
    response = analysis.client.post("/api/v1/paqs-e/narrative-analyses", json=analysis.payload())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["response_text"] == PROSE and body["status"] == "SUCCEEDED"
    assert len(provider.requests) == 1 and len(analysis.snapshots.snapshots) == 1
    run = analysis.client.get(
        "/api/v1/paqs-e/narrative-analyses/" + body["narrative_run_id"]
    ).json()
    assert run["request_payload_json"] == canonical_json(provider.requests[0])
    result = analysis.client.get(
        "/api/v1/paqs-e/narrative-results/" + body["narrative_result_id"]
    ).json()
    assert result == {key: value for key, value in body.items() if key != "status"}
    history = analysis.client.get(
        f"/api/v1/paqs-e/securities/{analysis.security_id}/narrative-results"
    ).json()
    assert history["items"][0]["preview"] == PROSE[:160]
    assert "response_text" not in history["items"][0]
    assert (
        analysis.client.get(
            f"/api/v1/paqs-e/securities/{analysis.security_id}/narrative-results?limit=101"
        ).status_code
        == 422
    )
    assert (
        analysis.client.get("/api/v1/paqs-e/narrative-results/" + str(uuid4())).status_code == 404
    )
    assert len(provider.requests) == 1


@pytest.mark.parametrize("kind", list(Kind))
def test_narrative_api_failure_creates_only_safe_run(analysis: AnalysisHarness, kind: Kind) -> None:
    provider = TextProvider(NarrativeFailure(kind))
    install(analysis, provider)
    response = analysis.client.post("/api/v1/paqs-e/narrative-analyses", json=analysis.payload())
    assert response.status_code == (
        503 if kind in {Kind.CONFIGURATION_ERROR, Kind.PROVIDER_UNAVAILABLE} else 502
    ), response.text
    body = response.json()
    assert body["failure_kind"] == kind.value and body["analysis_status"] == "PROVIDER_FAILED"
    run = analysis.client.get(
        "/api/v1/paqs-e/narrative-analyses/" + body["narrative_run_id"]
    ).json()
    assert run["failure_reason"] == NarrativeFailure(kind).reason
    assert analysis.container.narrative_ledger.history(analysis.security_id) == ()
    assert len(provider.requests) == 1


def test_narrative_research_freezes_before_reasoning_and_failure_does_not_fall_back(
    analysis: AnalysisHarness,
) -> None:
    from test_paqs_e_multi_model import Research

    provider = TextProvider()
    install(analysis, provider)
    research = Research(analysis)
    analysis.container.narrative_analysis_service.research = research
    for model_key, enabled in [
        ("deepseek-v4-flash", True),
        ("qwen3.8-max", True),
        ("kimi-k3", False),
    ]:
        response = analysis.client.post(
            "/api/v1/paqs-e/narrative-analyses",
            json=analysis.payload(model_key=model_key, web_research=enabled),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        request = provider.requests[-1]
        assert request.web_research is enabled
        assert len(request.auxiliary_context) == (1 if enabled else 0)
        if enabled:
            assert request.market_snapshot is research.snapshots[-1]
        run = analysis.container.narrative_ledger.get_run(body["narrative_run_id"])
        assert run is not None and run.request_payload_json == canonical_json(request)
    entries = analysis.container.narrative_ledger.history(analysis.security_id)
    assert [item.revision_no for item in entries] == [3, 2, 1]
    assert [item.model_provider for item in entries] == ["kimi", "alibaba", "deepseek"]
    research.fail = True
    response = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses",
        json=analysis.payload(model_key="deepseek-v4-flash", web_research=True),
    )
    assert response.status_code == 422 and "narrative_run_id" not in response.json()
    assert len(provider.requests) == 3
    assert analysis.container.narrative_ledger.history(analysis.security_id) == entries


@pytest.mark.parametrize("model", ["glm-5.2", "kimi-k3", "hy4-preview"])
def test_narrative_unsupported_research_never_dispatches_or_creates_run(
    analysis: AnalysisHarness,
    model: str,
) -> None:
    provider = TextProvider()
    install(analysis, provider)
    response = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses",
        json=analysis.payload(model_key=model, web_research=True),
    )
    assert response.status_code == 422
    assert response.json()["failure_kind"] == "CONFIGURATION_ERROR"
    assert not provider.requests
    assert analysis.container.narrative_ledger.history(analysis.security_id) == ()


def test_concurrent_narrative_revisions_are_serialized(
    ledger: SQLAlchemyPaqsELedger, session_factory: sessionmaker[Session]
) -> None:
    from concurrent.futures import ThreadPoolExecutor

    store = SQLAlchemyNarrativeLedger(session_factory)
    with ThreadPoolExecutor(max_workers=3) as pool:
        committed = list(
            pool.map(
                lambda model: record(store, model=model),
                ["gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"],
            )
        )
    assert sorted(item.result.revision_no for item in committed) == [1, 2, 3]
    history = store.history(SECURITY_ID)
    assert history[0].supersedes_narrative_result_id == history[1].narrative_result_id
    assert history[1].supersedes_narrative_result_id == history[2].narrative_result_id


@pytest.mark.parametrize("column,value", [("response_text", "tampered"), ("model_id", "wrong")])
def test_narrative_reads_reject_corrupted_evidence(
    ledger: SQLAlchemyPaqsELedger,
    session_factory: sessionmaker[Session],
    migrated_engine: Engine,
    column: str,
    value: str,
) -> None:
    from ai_infra_quant.core.domain.paqs_e_ledger import LedgerIntegrityError

    store = SQLAlchemyNarrativeLedger(session_factory)
    first = record(store)
    with migrated_engine.begin() as connection:
        connection.execute(text("DROP TRIGGER paqs_e_narrative_results_update"))
        connection.execute(
            text(f"UPDATE paqs_e_narrative_results SET {column}=:value"), {"value": value}
        )
    with pytest.raises(LedgerIntegrityError):
        store.get_result(first.result.narrative_result_id)
    with pytest.raises(LedgerIntegrityError):
        store.history(SECURITY_ID)


def test_actual_narrative_gateway_never_persists_credential_or_reasoning_trace(
    analysis: AnalysisHarness,
    migrated_engine: Engine,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import importlib

    from paqs_e_support import MemoryCredentials

    from ai_infra_quant.application.paqs_e_models import ModelCredentials, ModelRegistry
    from ai_infra_quant.integrations.openai_reasoning.narrative import NarrativeGateway

    fixtures = importlib.import_module("tests.unit.test_paqs_e_model_gateway")
    registry = ModelRegistry()
    model = registry.resolve("deepseek-v4-flash")
    store = MemoryCredentials()
    store.values[model.credential_slot] = fixtures.SENTINEL
    transport = fixtures.Transport(fixtures.envelope(PROSE, model.api_surface, model.model_id))
    gateway = NarrativeGateway(registry, ModelCredentials(registry, store), transport)
    install(analysis, TextProvider())
    analysis.container.narrative_analysis_service.provider = gateway
    first = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses", json=analysis.payload(model_key=model.model_key)
    )
    assert first.status_code == 201, first.text
    transport.response = fixtures.envelope(fixtures.SENTINEL, model.api_surface, model.model_id)
    failed = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses", json=analysis.payload(model_key=model.model_key)
    )
    assert failed.status_code == 502 and failed.json()["failure_kind"] == "INVALID_FINAL_TEXT"
    with migrated_engine.connect() as connection:
        stored = repr(connection.execute(select(runs)).all()) + repr(
            connection.execute(select(results)).all()
        )
    exposed = stored + first.text + failed.text + caplog.text
    assert fixtures.SENTINEL not in exposed
    assert "synthetic-discarded-trace" not in exposed
    assert len(transport.calls) == 2
