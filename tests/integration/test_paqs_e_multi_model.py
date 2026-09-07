from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient
from paqs_e_support import MemoryCredentials
from sqlalchemy import Engine
from test_paqs_e_analysis_api import ANALYSES, AnalysisHarness, _counts
from test_paqs_e_analysis_api import analysis as analysis_fixture

from ai_infra_quant.application.paqs_e_analysis import PaqsEAnalysisService
from ai_infra_quant.application.paqs_e_models import (
    ModelCredentials,
    ModelDescriptor,
    ModelRegistry,
)
from ai_infra_quant.application.paqs_e_research import ResearchFailure
from ai_infra_quant.application.paqs_e_runtime import PaqsEReasoningRuntime
from ai_infra_quant.core.domain.paqs_e_reasoning import AuxiliaryContextItem
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningFailureKind

ORIGIN = "http://127.0.0.1"
analysis = analysis_fixture
PATH = "/api/v1/paqs-e/credentials/"
SENTINEL = "synthetic-007c1-security-sentinel"


def setup_credentials(analysis: AnalysisHarness) -> MemoryCredentials:
    store = MemoryCredentials()
    analysis.container.paqs_e_credentials = ModelCredentials(ModelRegistry(), store)
    return store


def test_credential_crud_shared_status_has_no_db_provider_or_secret_leaks(
    analysis: AnalysisHarness, migrated_engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    store = setup_credentials(analysis)
    before = _counts(migrated_engine)
    with TestClient(analysis.app, base_url=ORIGIN, client=("127.0.0.1", 5000)) as client:
        url = PATH + "qwen3.8-flash"
        assert client.get(url).json()["credential_configured"] is False
        saved = client.put(url, json={"secret": SENTINEL}, headers={"Origin": ORIGIN})
        assert saved.status_code == 200
        assert saved.json() == {
            "credential_configured": True,
            "credential_source": "secure_store",
            "secure_storage_available": True,
        }
        assert store.values == {"dashscope": SENTINEL}
        status = client.get(PATH + "qwen3.8-max")
        config = client.get("/api/v1/paqs-e/configuration")
        assert status.json()["credential_configured"] is True
        configured = [
            item["model_key"] for item in config.json()["models"] if item["credential_configured"]
        ]
        assert configured == ["qwen3.8-flash", "qwen3.8-max", "qwen3.7-plus"]
        assert SENTINEL not in saved.text + status.text + config.text + caplog.text
        deleted = client.request(
            "DELETE", PATH + "qwen3.7-plus", json={}, headers={"Origin": ORIGIN}
        )
        assert deleted.status_code == 200 and store.values == {}
        assert not client.get(url).json()["credential_configured"]
    assert before == _counts(migrated_engine)
    assert analysis.provider.requests == [] and analysis.snapshots.snapshots == []


@pytest.mark.parametrize(
    "case",
    [
        "cross-origin",
        "null-origin",
        "no-origin",
        "fetch-site",
        "form",
        "text",
        "query",
        "unknown",
        "slot",
        "empty",
        "long",
        "whitespace",
        "extra",
    ],
)
def test_credential_mutations_reject_unsafe_input_without_secret_echo(
    analysis: AnalysisHarness, case: str, caplog: pytest.LogCaptureFixture
) -> None:
    store = setup_credentials(analysis)
    headers = {"Origin": ORIGIN, "Content-Type": "application/json"}
    body: dict[str, Any] = {"secret": SENTINEL}
    url = PATH + "deepseek-v4-flash"
    if case == "cross-origin":
        headers["Origin"] = "https://evil.example"
    if case == "null-origin":
        headers["Origin"] = "null"
    if case == "no-origin":
        del headers["Origin"]
    if case == "fetch-site":
        headers["Sec-Fetch-Site"] = "cross-site"
    if case == "form":
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if case == "text":
        headers["Content-Type"] = "text/plain"
    if case == "query":
        url += "?unexpected=true"
    if case == "unknown":
        url = PATH + "unregistered-model"
    if case == "slot":
        body["credential_slot"] = "arbitrary"
    if case == "empty":
        body["secret"] = ""
    if case == "long":
        body["secret"] = SENTINEL * 200
    if case == "whitespace":
        body["secret"] = " " + SENTINEL
    if case == "extra":
        body["provider_url"] = "https://evil.example"
    with TestClient(analysis.app, base_url=ORIGIN, client=("127.0.0.1", 5000)) as client:
        response = client.put(url, content=json.dumps(body), headers=headers)
    assert response.status_code in {400, 403, 413, 422}
    assert store.values == {} and store.writes == []
    assert SENTINEL not in response.text + caplog.text


@pytest.mark.parametrize(
    "host,peer", [("http://evil.example", "127.0.0.1"), (ORIGIN, "192.0.2.1"), (ORIGIN, "invalid")]
)
def test_credential_boundary_rejects_nonloopback_hosts_and_peers(
    analysis: AnalysisHarness, host: str, peer: str
) -> None:
    store = setup_credentials(analysis)
    with TestClient(analysis.app, base_url=host, client=(peer, 5000)) as client:
        for method in ("GET", "PUT", "DELETE"):
            response = client.request(
                method,
                PATH + "deepseek-v4-flash",
                json={"secret": SENTINEL},
                headers={"Origin": host},
            )
            assert response.status_code == 403
    assert store.writes == []


def test_unavailable_secure_store_has_truthful_safe_status_and_mutation_failure(
    analysis: AnalysisHarness,
) -> None:
    store = setup_credentials(analysis)
    store.available = False
    with TestClient(analysis.app, base_url=ORIGIN, client=("127.0.0.1", 5000)) as client:
        url = PATH + "deepseek-v4-flash"
        assert client.get(url).json() == {
            "credential_configured": False,
            "credential_source": "missing",
            "secure_storage_available": False,
        }
        assert (
            client.put(url, json={"secret": SENTINEL}, headers={"Origin": ORIGIN}).status_code
            == 503
        )
        assert client.request("DELETE", url, json={}, headers={"Origin": ORIGIN}).status_code == 503
    assert store.writes == []


@pytest.mark.parametrize(
    "changes",
    [
        {"model_id": "gpt-5.6-luna"},
        {"model_provider": "openai"},
        {"provider_url": "https://evil.example"},
        {"web_research": "true"},
        {"web_research": 1},
        {"model_key": "unknown"},
    ],
)
def test_analyze_exact_four_fields_and_no_unregistered_routes(
    analysis: AnalysisHarness, migrated_engine: Engine, changes: dict[str, Any]
) -> None:
    before = _counts(migrated_engine)
    assert analysis.client.post(ANALYSES, json=analysis.payload(**changes)).status_code == 422
    assert analysis.provider.requests == []
    assert _counts(migrated_engine) == before


class Research:
    def __init__(self, analysis: AnalysisHarness, *, fail: bool = False) -> None:
        self.analysis, self.fail = analysis, fail
        self.snapshots: list[PaqsMarketSnapshot] = []
        self.models: list[ModelDescriptor] = []

    def research(
        self, model: ModelDescriptor, snapshot: PaqsMarketSnapshot
    ) -> tuple[AuxiliaryContextItem, ...]:
        assert self.analysis.snapshots.snapshots[-1] is snapshot
        self.snapshots.append(snapshot)
        self.models.append(model)
        if self.fail:
            raise ResearchFailure(ReasoningFailureKind.PROVIDER_UNAVAILABLE)
        return (
            AuxiliaryContextItem(
                "web-synthetic",
                "web_research",
                "Synthetic earnings source",
                None,
                "https://example.org/earnings; publication time unknown; retrieved after freeze",
                True,
                "Synthetic event context. Snapshot prices win.",
            ),
        )


def test_cross_provider_revision_chain_frozen_web_capsule_and_failed_run_gap(
    analysis: AnalysisHarness, migrated_engine: Engine
) -> None:
    research = Research(analysis)
    analysis.container.paqs_e_analysis_service = PaqsEAnalysisService(
        analysis.snapshots,
        PaqsEReasoningRuntime(analysis.provider),
        analysis.container.paqs_e_ledger,
        research=research,
    )
    decisions = []
    for key in ("deepseek-v4-flash", "qwen3.8-max", "kimi-k3"):
        response = analysis.client.post(
            ANALYSES, json=analysis.payload(model_key=key, web_research=key != "kimi-k3")
        )
        assert response.status_code == 201, response.text
        decisions.append(response.json())
    assert [item["revision_no"] for item in decisions] == [1, 2, 3]
    assert [item["model_provider"] for item in decisions] == ["deepseek", "alibaba", "kimi"]
    assert decisions[1]["supersedes_decision_id"] == decisions[0]["decision_id"]
    assert decisions[2]["supersedes_decision_id"] == decisions[1]["decision_id"]
    for index, decision in enumerate(decisions):
        run = analysis.client.get(ANALYSES + "/" + decision["analysis_run_id"]).json()
        payload = json.loads(run["request_payload_json"])
        assert payload["model_provider"] == decision["model_provider"]
        assert payload["model_id"] == decision["model_id"]
        assert len(payload["auxiliary_context"]) == (0 if index == 2 else 1)
        if index < 2:
            assert analysis.provider.requests[index].market_snapshot is research.snapshots[index]
            assert "publication time unknown" in payload["auxiliary_context"][0]["provenance"]
    before = _counts(migrated_engine)
    frozen_runs = [
        analysis.client.get(ANALYSES + "/" + item["analysis_run_id"]).json() for item in decisions
    ]
    analysis.client.get(f"/api/v1/market-data/securities/{analysis.security_id}/state")
    assert [
        analysis.client.get(ANALYSES + "/" + item["analysis_run_id"]).json() for item in decisions
    ] == frozen_runs
    research.fail = True
    failed = analysis.client.post(
        ANALYSES, json=analysis.payload(model_key="qwen3.8-max", web_research=True)
    )
    assert failed.status_code == 422
    assert failed.json()["failure_kind"] == "PROVIDER_UNAVAILABLE"
    assert "analysis_run_id" not in failed.json() and _counts(migrated_engine) == before
    assert len(analysis.provider.requests) == 3


@pytest.mark.parametrize("key", ["glm-5.2", "kimi-k3", "hy4-preview"])
def test_unsupported_research_is_precondition_failure_with_no_reasoning(
    analysis: AnalysisHarness, migrated_engine: Engine, key: str
) -> None:
    before = _counts(migrated_engine)
    response = analysis.client.post(
        ANALYSES, json=analysis.payload(model_key=key, web_research=True)
    )
    assert response.status_code == 422
    assert response.json()["failure_kind"] == "CONFIGURATION_ERROR"
    assert "analysis_run_id" not in response.json()
    assert analysis.provider.requests == [] and _counts(migrated_engine) == before
