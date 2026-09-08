from __future__ import annotations

import hashlib
import importlib
import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from test_paqs_market_snapshot_api import NOW, PROVIDER, SnapshotFakeProvider

from ai_infra_quant.application.market_data_queries import MarketDataQueries
from ai_infra_quant.application.paqs_e_analysis import PaqsEAnalysisService
from ai_infra_quant.application.paqs_e_runtime import (
    PaqsEReasoningRuntime,
    RuntimePackageError,
    load_strategy_package,
)
from ai_infra_quant.application.paqs_input_queries import PaqsInputQueries
from ai_infra_quant.application.paqs_market_snapshot_queries import PaqsMarketSnapshotQueries
from ai_infra_quant.backend.dependencies import AppContainer
from ai_infra_quant.backend.main import create_app
from ai_infra_quant.config import Settings
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    PAQS_E_VALIDATOR_VERSION,
    InputQuality,
    PaqsEReasoningRequestV1,
    PaqsEReasoningResultV1,
    PriceSessionType,
    PromptPackage,
    StrategyPackage,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot, canonical_json
from ai_infra_quant.core.ports.paqs_e_reasoning import (
    ReasoningFailureKind,
    ReasoningProviderFailure,
    ReasoningProviderOutcome,
    ReasoningProviderSuccess,
)
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork
from ai_infra_quant.integrations.openai_reasoning.adapter import OpenAIPaqsEReasoningAdapter

_result = cast(
    Callable[[PaqsEReasoningRequestV1], PaqsEReasoningResultV1],
    importlib.import_module("tests.unit.test_paqs_e_runtime")._result,
)

ANALYSES = "/api/v1/paqs-e/analyses"
DECISIONS = "/api/v1/paqs-e/decisions"
STRATEGY_ID = "paqs-e-master"
MODEL_ID = "gpt-5.6-luna"


class RecordingSnapshots:
    """Wrap the real TASK-006B2 boundary; every acquisition is observable."""

    def __init__(self, queries: PaqsMarketSnapshotQueries) -> None:
        self.queries = queries
        self.snapshots: list[PaqsMarketSnapshot] = []
        self.error: Exception | None = None

    def current_snapshot(self, security_id: str) -> PaqsMarketSnapshot:
        if self.error is not None:
            raise self.error
        snapshot = self.queries.current_snapshot(security_id)
        self.snapshots.append(snapshot)
        return snapshot


class SyntheticReasoningProvider:
    """Deterministic synthetic judgment, still validated by the accepted runtime."""

    def __init__(self) -> None:
        self.requests: list[PaqsEReasoningRequestV1] = []
        self.strategies: list[StrategyPackage] = []
        self.prompts: list[PromptPackage] = []
        self.failure: ReasoningProviderFailure | None = None
        self.invalid_identity = False
        self.on_reason: Callable[[], None] | None = None

    def reason(
        self,
        *,
        request: PaqsEReasoningRequestV1,
        strategy: StrategyPackage,
        prompt: PromptPackage,
    ) -> ReasoningProviderOutcome:
        self.requests.append(request)
        self.strategies.append(strategy)
        self.prompts.append(prompt)
        if self.on_reason is not None:
            self.on_reason()
        if self.failure is not None:
            return self.failure
        result = _result(request)
        result = replace(
            result,
            support=replace(
                result.support,
                input_quality=InputQuality(request.market_snapshot.data_quality.value),
                data_quality_reasons=request.market_snapshot.warnings,
            ),
            price_references=replace(
                result.price_references,
                current_price_reference=replace(
                    result.price_references.current_price_reference,
                    session_type=PriceSessionType.CLOSED_REFERENCE,
                ),
            ),
        )
        if self.invalid_identity:
            result = replace(result, identity=replace(result.identity, model_id="wrong-model"))
        return ReasoningProviderSuccess(
            result=result, provider_response_id=f"resp_synthetic_{len(self.requests)}"
        )


@dataclass
class AnalysisHarness:
    app: FastAPI
    client: TestClient
    container: AppContainer
    snapshots: RecordingSnapshots
    provider: SyntheticReasoningProvider
    market_provider: SnapshotFakeProvider
    security_id: str

    def payload(self, **changes: Any) -> dict[str, Any]:
        return {
            "security_id": self.security_id,
            "model_key": MODEL_ID,
            "strategy_id": STRATEGY_ID,
            "web_research": False,
            **changes,
        }

    def install_service(
        self,
        *,
        runtime: PaqsEReasoningRuntime | None = None,
        strategy_loader: Callable[[str], StrategyPackage] = load_strategy_package,
    ) -> None:
        self.container.paqs_e_analysis_service = PaqsEAnalysisService(
            self.snapshots,
            runtime or PaqsEReasoningRuntime(self.provider),
            self.container.paqs_e_ledger,
            strategy_loader=strategy_loader,
            now=lambda: NOW,
        )


@pytest.fixture
def analysis(
    settings: Settings,
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
) -> Iterator[AnalysisHarness]:
    # Explicit in-process legacy regression only; normal composition keeps this disabled.
    app = create_app(settings, migrated_engine, legacy_analysis_enabled=True)
    container = cast(AppContainer, app.state.container)
    market_provider = SnapshotFakeProvider()
    market_queries = MarketDataQueries(
        lambda: SQLAlchemyUnitOfWork(session_factory),
        provider_name=PROVIDER,
        provider_factory=lambda: market_provider,
        now=lambda: NOW,
    )
    input_queries = PaqsInputQueries(market_queries, provider_name=PROVIDER, now=lambda: NOW)
    queries = PaqsMarketSnapshotQueries(input_queries, market_queries, now=lambda: NOW)
    snapshots = RecordingSnapshots(queries)
    container.market_data_queries = market_queries
    container.paqs_input_queries = input_queries
    container.paqs_market_snapshot_queries = queries
    with TestClient(app, raise_server_exceptions=False) as client:
        items = client.get("/api/v1/watchlist").json()["items"]
        security_id = next(
            item["security"]["id"]
            for item in items
            if item["security"]["display_symbol"] == "US.AVGO"
        )
        harness = AnalysisHarness(
            app,
            client,
            container,
            snapshots,
            SyntheticReasoningProvider(),
            market_provider,
            security_id,
        )
        harness.install_service()
        yield harness


def _counts(engine: Engine) -> tuple[int, int, int]:
    with engine.connect() as connection:
        return cast(
            tuple[int, int, int],
            tuple(
                connection.scalar(text(f"SELECT COUNT(*) FROM {table}"))
                for table in (
                    "paqs_e_runtime_artifacts",
                    "paqs_e_analysis_runs",
                    "paqs_e_decisions",
                )
            ),
        )


def _history(analysis: AnalysisHarness) -> str:
    return f"/api/v1/paqs-e/securities/{analysis.security_id}/decisions"


def test_analyze_uses_one_exact_fresh_snapshot_and_returns_committed_evidence(
    analysis: AnalysisHarness, migrated_engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    # If orchestration called its public snapshot route, this route dependency would fail.
    def no_internal_http(security_id: str) -> PaqsMarketSnapshot:
        raise AssertionError(f"public snapshot query used internally: {security_id}")

    public_queries = analysis.container.paqs_market_snapshot_queries
    analysis.container.paqs_market_snapshot_queries = PaqsMarketSnapshotQueries(
        analysis.container.paqs_input_queries, analysis.container.market_data_queries
    )
    monkeypatch.setattr(
        analysis.container.paqs_market_snapshot_queries, "current_snapshot", no_internal_http
    )
    response = analysis.client.post(ANALYSES, json=analysis.payload())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "SUCCEEDED"
    assert body["revision_no"] == 1
    assert len(analysis.snapshots.snapshots) == len(analysis.provider.requests) == 1
    snapshot = analysis.snapshots.snapshots[0]
    request = analysis.provider.requests[0]
    assert request.market_snapshot is snapshot
    assert request.model_id == body["model_id"] == MODEL_ID
    assert request.auxiliary_context == ()
    assert request.primary_strategy_id == body["strategy_id"] == STRATEGY_ID
    assert analysis.provider.strategies[0] == load_strategy_package(STRATEGY_ID)
    assert analysis.market_provider.events == [
        "daily",
        "minute",
        "calendar",
        "quote",
        "market_state",
    ]
    assert _counts(migrated_engine) == (2, 1, 1)
    run = analysis.client.get(f"{ANALYSES}/{body['analysis_run_id']}").json()
    decision = analysis.client.get(f"{DECISIONS}/{body['decision_id']}").json()
    assert run["status"] == "SUCCEEDED"
    assert run["request_payload_json"] == canonical_json(request)
    assert (
        run["request_payload_sha256"]
        == hashlib.sha256(canonical_json(request).encode()).hexdigest()
    )
    assert json.loads(run["request_payload_json"])["market_snapshot"] == json.loads(
        canonical_json(snapshot)
    )
    assert run["provider_response_id"] == "resp_synthetic_1"
    assert run["validation_issues"] == []
    assert decision["result"] == body["result"]
    assert (
        decision["result_payload_sha256"]
        == hashlib.sha256(canonical_json(body["result"]).encode()).hexdigest()
    )
    assert decision["supersedes_decision_id"] is None
    assert UUID(body["analysis_run_id"]) != UUID(body["decision_id"])
    analysis.container.paqs_market_snapshot_queries = public_queries


def test_repeated_explicit_posts_are_fresh_without_hidden_history_or_deduplication(
    analysis: AnalysisHarness, migrated_engine: Engine
) -> None:
    first = analysis.client.post(ANALYSES, json=analysis.payload()).json()
    first_read = analysis.client.get(f"{DECISIONS}/{first['decision_id']}").content
    second = analysis.client.post(ANALYSES, json=analysis.payload()).json()
    changed_model = analysis.client.post(
        ANALYSES, json=analysis.payload(model_key="qwen3.8-max")
    ).json()
    assert [first["revision_no"], second["revision_no"], changed_model["revision_no"]] == [1, 2, 3]
    assert second["supersedes_decision_id"] == first["decision_id"]
    assert changed_model["supersedes_decision_id"] == second["decision_id"]
    assert (
        len({first["analysis_run_id"], second["analysis_run_id"], changed_model["analysis_run_id"]})
        == 3
    )
    assert first["snapshot_hash"] == second["snapshot_hash"] == changed_model["snapshot_hash"]
    assert len(analysis.snapshots.snapshots) == len(analysis.provider.requests) == 3
    assert analysis.snapshots.snapshots[0] is not analysis.snapshots.snapshots[1]
    assert all(request.auxiliary_context == () for request in analysis.provider.requests)
    assert analysis.provider.requests[-1].model_id == "qwen3.8-max"
    assert all(
        item["result"]["holder"]["prior_decision_id"] is None
        for item in (first, second, changed_model)
    )
    assert analysis.client.get(f"{DECISIONS}/{first['decision_id']}").content == first_read
    assert _counts(migrated_engine) == (2, 3, 3)


def test_strategy_selection_is_independent_and_history_is_bounded_and_filterable(
    analysis: AnalysisHarness,
) -> None:
    master = load_strategy_package()
    alternate = replace(master, strategy_id="synthetic-second-registered-strategy")
    registry = {master.strategy_id: master, alternate.strategy_id: alternate}
    selected: list[str] = []

    def load_registered(strategy_id: str) -> StrategyPackage:
        selected.append(strategy_id)
        if strategy_id not in registry:
            raise RuntimePackageError("strategy is not registered")
        return registry[strategy_id]

    analysis.install_service(strategy_loader=load_registered)
    first = analysis.client.post(ANALYSES, json=analysis.payload()).json()
    alternate_run = analysis.client.post(
        ANALYSES, json=analysis.payload(strategy_id=alternate.strategy_id)
    ).json()
    last = analysis.client.post(
        ANALYSES, json=analysis.payload(model_key="deepseek-v4-flash")
    ).json()
    assert selected == [STRATEGY_ID, alternate.strategy_id, STRATEGY_ID]
    assert [item.strategy_id for item in analysis.provider.strategies] == selected
    assert [first["revision_no"], alternate_run["revision_no"], last["revision_no"]] == [1, 1, 2]
    assert alternate_run["supersedes_decision_id"] is None
    assert alternate_run["model_id"] == first["model_id"] == MODEL_ID
    items = analysis.client.get(_history(analysis)).json()["items"]
    assert [item["decision_id"] for item in items] == [
        last["decision_id"],
        alternate_run["decision_id"],
        first["decision_id"],
    ]
    assert "result" not in items[0] and "request_payload_json" not in items[0]
    assert items[0]["one_line_thesis"] == last["result"]["one_line_thesis"]
    filtered = analysis.client.get(_history(analysis), params={"strategy_id": STRATEGY_ID}).json()[
        "items"
    ]
    assert [item["decision_id"] for item in filtered] == [last["decision_id"], first["decision_id"]]
    assert analysis.client.get(_history(analysis), params={"limit": 1}).json()["items"] == items[:1]
    assert (
        analysis.client.get(_history(analysis), params={"strategy_id": "unregistered"}).json()[
            "items"
        ]
        == []
    )


@pytest.mark.parametrize("limit", [0, -1, 101, "invalid"])
def test_history_rejects_out_of_bounds_limits(analysis: AnalysisHarness, limit: int | str) -> None:
    response = analysis.client.get(_history(analysis), params={"limit": limit})
    assert response.status_code == 422


@pytest.mark.parametrize("limit", [1, 100])
def test_history_accepts_limit_boundaries(analysis: AnalysisHarness, limit: int) -> None:
    response = analysis.client.get(_history(analysis), params={"limit": limit})
    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.parametrize("model_key", ["", " ", " model", "model name", "model\n", None, 123])
def test_invalid_model_rejected_before_snapshot_or_provider(
    analysis: AnalysisHarness, migrated_engine: Engine, model_key: object
) -> None:
    response = analysis.client.post(ANALYSES, json=analysis.payload(model_key=model_key))
    assert response.status_code == 422
    assert not analysis.snapshots.snapshots and not analysis.provider.requests
    assert _counts(migrated_engine) == (0, 0, 0)


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "api_key",
        "runtime_config",
        "prompt",
        "strategy_path",
        "strategy_markdown",
        "short_execution_allowed",
        "auxiliary_context",
        "prior_decision_id",
    ],
)
def test_public_analyze_accepts_only_three_caller_controlled_fields(
    analysis: AnalysisHarness, forbidden_field: str
) -> None:
    response = analysis.client.post(
        ANALYSES, json=analysis.payload(**{forbidden_field: "untrusted-extra"})
    )
    assert response.status_code == 422
    assert not analysis.provider.requests and not analysis.snapshots.snapshots


def test_unregistered_strategy_never_acquires_snapshot_or_calls_provider(
    analysis: AnalysisHarness, migrated_engine: Engine
) -> None:
    response = analysis.client.post(ANALYSES, json=analysis.payload(strategy_id="../strategy.md"))
    assert response.status_code == 422
    assert not analysis.provider.requests and not analysis.snapshots.snapshots
    assert _counts(migrated_engine) == (0, 0, 0)


def test_unknown_and_unsupported_security_do_not_create_formed_request_evidence(
    analysis: AnalysisHarness, migrated_engine: Engine
) -> None:
    unknown = analysis.client.post(ANALYSES, json=analysis.payload(security_id=str(uuid4())))
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "SECURITY_NOT_FOUND"
    created = analysis.client.post(
        "/api/v1/securities",
        json={
            "market": "US",
            "symbol": "UNSUPPORTED",
            "currency": "USD",
            "instrument_type": "UNKNOWN",
        },
    )
    assert created.status_code == 201
    unsupported = analysis.client.post(
        ANALYSES, json=analysis.payload(security_id=created.json()["id"])
    )
    assert unsupported.status_code == 422
    assert "NOT_SUPPORTED" in unsupported.json()["code"]
    assert not analysis.provider.requests and not analysis.snapshots.snapshots
    assert _counts(migrated_engine) == (0, 0, 0)


def test_snapshot_acquisition_failure_does_not_fabricate_a_run(
    analysis: AnalysisHarness, migrated_engine: Engine
) -> None:
    analysis.snapshots.error = ValueError("synthetic snapshot acquisition failure")
    response = analysis.client.post(ANALYSES, json=analysis.payload())
    assert response.status_code >= 400
    assert "analysis_run_id" not in response.json()
    assert analysis.provider.requests == []
    assert _counts(migrated_engine) == (0, 0, 0)


@pytest.mark.parametrize("failure_kind", list(ReasoningFailureKind))
def test_provider_failures_commit_typed_run_and_never_create_decision(
    analysis: AnalysisHarness, migrated_engine: Engine, failure_kind: ReasoningFailureKind
) -> None:
    analysis.provider.failure = ReasoningProviderFailure(
        failure_kind, "Safe synthetic provider failure"
    )
    response = analysis.client.post(ANALYSES, json=analysis.payload())
    assert response.status_code == (
        503
        if failure_kind
        in {ReasoningFailureKind.CONFIGURATION_ERROR, ReasoningFailureKind.PROVIDER_UNAVAILABLE}
        else 502
    )
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["analysis_status"] == body["analysis_run"]["status"] == "PROVIDER_FAILED"
    assert body["failure_kind"] == failure_kind.value
    assert "decision_id" not in body
    assert _counts(migrated_engine) == (2, 1, 0)
    stored = analysis.client.get(f"{ANALYSES}/{body['analysis_run_id']}").json()
    assert stored["status"] == "PROVIDER_FAILED"
    assert stored["failure_kind"] == failure_kind.value
    assert stored["failure_reason"] == "Safe synthetic provider failure"
    assert stored["validator_version"] is None
    assert stored["validation_issues"] == []
    assert analysis.client.get(_history(analysis)).json()["items"] == []


def test_missing_server_credential_uses_accepted_adapter_configuration_failure(
    analysis: AnalysisHarness, migrated_engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    analysis.install_service(runtime=PaqsEReasoningRuntime(OpenAIPaqsEReasoningAdapter()))
    response = analysis.client.post(ANALYSES, json=analysis.payload())
    assert response.status_code == 503
    assert response.json()["failure_kind"] == "CONFIGURATION_ERROR"
    assert response.json()["analysis_status"] == "PROVIDER_FAILED"
    assert _counts(migrated_engine) == (2, 1, 0)


def test_deterministic_validation_failure_persists_exact_issues_without_decision(
    analysis: AnalysisHarness, migrated_engine: Engine
) -> None:
    analysis.provider.invalid_identity = True
    response = analysis.client.post(ANALYSES, json=analysis.payload())
    assert response.status_code == 502
    body = response.json()
    assert body["analysis_status"] == "VALIDATION_FAILED"
    assert body["validator_version"] == PAQS_E_VALIDATOR_VERSION
    assert {issue["code"] for issue in body["validation_issues"]} == {"IDENTITY_MISMATCH"}
    assert "decision_id" not in body
    stored = analysis.client.get(f"{ANALYSES}/{body['analysis_run_id']}").json()
    assert stored["status"] == "VALIDATION_FAILED"
    assert stored["validation_issues"] == body["validation_issues"]
    assert stored["validator_version"] == body["validator_version"]
    assert _counts(migrated_engine) == (2, 1, 0)


def test_provider_exception_secret_is_absent_from_persistence_api_and_logs(
    analysis: AnalysisHarness, migrated_engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    sentinel = "synthetic-007b-secret-sentinel-not-a-real-key"
    transport_details = "synthetic-private-transport-header"

    def fail_parse(**kwargs: Any) -> None:
        raise RuntimeError(f"{sentinel} {transport_details}")

    adapter = OpenAIPaqsEReasoningAdapter(
        api_key=sentinel, client=SimpleNamespace(responses=SimpleNamespace(parse=fail_parse))
    )
    analysis.install_service(runtime=PaqsEReasoningRuntime(adapter))
    response = analysis.client.post(ANALYSES, json=analysis.payload())
    assert response.status_code == 503
    assert response.json()["failure_kind"] == "PROVIDER_UNAVAILABLE"
    run_id = response.json()["analysis_run_id"]
    audit_read = analysis.client.get(f"{ANALYSES}/{run_id}")
    assert audit_read.status_code == 200
    with migrated_engine.connect() as connection:
        persisted = repr(
            [
                connection.execute(text(f"SELECT * FROM {table}")).all()
                for table in (
                    "paqs_e_runtime_artifacts",
                    "paqs_e_analysis_runs",
                    "paqs_e_decisions",
                )
            ]
        )
    exposed = "\n".join(
        [
            response.text,
            audit_read.text,
            persisted,
            analysis.client.get("/openapi.json").text,
            caplog.text,
        ]
    )
    assert sentinel not in exposed
    assert transport_details not in exposed
    assert _counts(migrated_engine) == (2, 1, 0)


@pytest.mark.parametrize("path", [ANALYSES, DECISIONS])
def test_unknown_ledger_ids_are_truthful_not_found(analysis: AnalysisHarness, path: str) -> None:
    response = analysis.client.get(f"{path}/{uuid4()}")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


def test_unknown_security_history_is_not_found(analysis: AnalysisHarness) -> None:
    response = analysis.client.get(f"/api/v1/paqs-e/securities/{uuid4()}/decisions")
    assert response.status_code == 404


def test_market_refresh_and_dashboard_do_not_trigger_reasoning(analysis: AnalysisHarness) -> None:
    for path in (
        "/",
        "/health",
        f"/api/v1/market-data/securities/{analysis.security_id}/state",
        f"/api/v1/paqs/securities/{analysis.security_id}/market-snapshot",
    ):
        assert analysis.client.get(path).status_code == 200, path
    assert not analysis.provider.requests and not analysis.snapshots.snapshots


@pytest.mark.parametrize("failure_stage", ["insert", "commit"])
def test_failed_success_transaction_returns_non_success_and_rolls_back_every_ledger_row(
    analysis: AnalysisHarness, migrated_engine: Engine, failure_stage: str
) -> None:
    def fail_insert(*args: Any) -> None:
        statement = str(args[2]).lower()
        if "insert into paqs_e_decisions" in statement:
            raise SQLAlchemyError("synthetic Decision insertion failure")

    def fail_commit(session: Session) -> None:
        raise SQLAlchemyError("synthetic ledger commit failure")

    target, name, callback = (
        (migrated_engine, "before_cursor_execute", fail_insert)
        if failure_stage == "insert"
        else (Session, "before_commit", fail_commit)
    )
    event.listen(target, name, callback)
    try:
        response = analysis.client.post(ANALYSES, json=analysis.payload())
    finally:
        event.remove(target, name, callback)
    assert response.status_code == 500
    assert "decision_id" not in response.json()
    assert _counts(migrated_engine) == (0, 0, 0)


def test_provider_runs_outside_database_transaction_and_response_follows_commit(
    analysis: AnalysisHarness, migrated_engine: Engine
) -> None:
    active: set[int] = set()
    committed: list[bool] = []

    def begin(connection: Any) -> None:
        active.add(id(connection))

    def end(connection: Any) -> None:
        active.discard(id(connection))

    def provider_observation() -> None:
        assert active == set(), "external runtime must not retain snapshot DB transactions"
        assert _counts(migrated_engine) == (0, 0, 0)

    def before_commit(session: Session) -> None:
        assert _counts(migrated_engine) == (0, 0, 0), "Decision must not be visible before commit"

    def after_commit(session: Session) -> None:
        committed.append(True)

    analysis.provider.on_reason = provider_observation
    listeners = [
        (migrated_engine, "begin", begin),
        (migrated_engine, "commit", end),
        (migrated_engine, "rollback", end),
        (Session, "before_commit", before_commit),
        (Session, "after_commit", after_commit),
    ]
    for target, name, callback in listeners:
        event.listen(target, name, callback)
    try:
        response = analysis.client.post(ANALYSES, json=analysis.payload())
    finally:
        for target, name, callback in listeners:
            event.remove(target, name, callback)
    assert response.status_code == 201, response.text
    assert committed == [True]
    assert _counts(migrated_engine) == (2, 1, 1)


def test_openapi_exposes_bounded_read_only_ledger_contract_without_secret_fields(
    analysis: AnalysisHarness,
) -> None:
    document = analysis.client.get("/openapi.json").json()
    paths = document["paths"]
    expected = {
        "/api/v1/paqs-e/narrative-analyses": {"post"},
        "/api/v1/paqs-e/narrative-analyses/{run_id}": {"get"},
        "/api/v1/paqs-e/narrative-results/{result_id}": {"get"},
        "/api/v1/paqs-e/securities/{security_id}/narrative-results": {"get"},
        f"{ANALYSES}/{{analysis_run_id}}": {"get"},
        f"{DECISIONS}/{{decision_id}}": {"get"},
        "/api/v1/paqs-e/securities/{security_id}/decisions": {"get"},
        "/api/v1/paqs-e/configuration": {"get"},
        "/api/v1/paqs-e/credentials/{model_key}": {"get", "put", "delete"},
    }
    assert {
        path: set(operations) for path, operations in paths.items() if "/paqs-e/" in path
    } == expected
    schema = document["components"]["schemas"]["AnalyzeCreate"]
    assert (
        set(schema["properties"])
        == set(schema["required"])
        == {"security_id", "model_key", "strategy_id", "web_research"}
    )
    assert schema["additionalProperties"] is False
    limit = next(
        item
        for item in paths["/api/v1/paqs-e/securities/{security_id}/decisions"]["get"]["parameters"]
        if item["name"] == "limit"
    )
    assert {key: limit["schema"][key] for key in ("minimum", "maximum", "default")} == {
        "minimum": 1,
        "maximum": 100,
        "default": 20,
    }
    schemas = json.loads(json.dumps(document["components"]["schemas"]))
    # TASK-007C1 allows one write-only secret request; all read/ledger schemas stay secret-free.
    credential = schemas.pop("CredentialSave")
    assert set(credential["properties"]) == {"secret"}
    assert credential["properties"]["secret"]["writeOnly"] is True
    assert credential["properties"]["secret"]["format"] == "password"
    schema_text = json.dumps(schemas).lower()
    for forbidden in (
        "openai_api_key",
        "api_key",
        "authorization",
        "broker_order_id",
        "broker_account_id",
        "executed_quantity",
        "execution_status",
    ):
        assert forbidden not in schema_text
