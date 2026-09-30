"""Synthetic transport only; real immutable ledgers/API and no user DB or paid calls."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from test_paqs_e_analysis_api import AnalysisHarness
from test_paqs_e_analysis_api import analysis as analysis_fixture
from test_paqs_e_narrative_ledger_api import NOW

from ai_infra_quant.application.external_research import SavedExternalResearch
from ai_infra_quant.application.paqs_e_narrative import NarrativeAnalysisService
from ai_infra_quant.application.paqs_e_research import ExternalResearchFailure
from ai_infra_quant.core.domain.paqs_e_ledger import LedgerPersistenceError
from ai_infra_quant.core.domain.paqs_e_narrative import TAVILY_PROMPT_VERSION, NarrativeSuccess
from ai_infra_quant.core.domain.paqs_e_reasoning import AuxiliaryContextItem
from ai_infra_quant.database.models.external_research import searches
from ai_infra_quant.integrations.openai_reasoning.narrative import NarrativeGateway
from ai_infra_quant.integrations.tavily_research import TavilyResearch

analysis = analysis_fixture
PATH = "/api/v1/paqs-e/narrative-analyses"


class Search:
    def __init__(self, failure: str | None = None) -> None:
        self.calls = 0
        self.failure = failure

    def research(self, model: Any, snapshot: Any) -> tuple[AuxiliaryContextItem, ...]:
        self.calls += 1
        if self.failure:
            raise ExternalResearchFailure(self.failure, {"requests": [], "status": "FAILED"})
        provenance = {
            "schema_version": "paqs-e-tavily-evidence-v1",
            "provider": "tavily",
            "snapshot_as_of": snapshot.as_of_timestamp.isoformat(),
            "retrieved_at": NOW.isoformat(),
            "requests": [{"query": "US AVGO Broadcom recent announcements", "status": "SUCCEEDED"}],
            "sources": [
                {
                    "source_id": "T1",
                    "title": "Synthetic Broadcom release",
                    "url": "https://investors.broadcom.com/fixture",
                    "content": "Synthetic public fact",
                    "published_at": None,
                }
            ],
        }
        return (
            AuxiliaryContextItem(
                "tavily",
                "web_research",
                "Tavily",
                None,
                json.dumps(provenance),
                True,
                "[T1] Synthetic public fact",
            ),
        )


class TextModel:
    def __init__(
        self, app: AnalysisHarness, prose: str = "合成研究参考 [T1];不代表真实结论。"
    ) -> None:
        self.app, self.prose = app, prose
        self.requests: list[Any] = []

    def reason_text(self, *, request: Any, strategy: Any, prompt: Any) -> NarrativeSuccess:
        self.requests.append(request)
        if request.web_research:
            research_id = json.loads(request.auxiliary_context[0].provenance)["research_id"]
            # The actual committed search evidence exists before the model is dispatched.
            assert self.app.container.search_evidence.get(research_id)["status"] == "SUCCEEDED"
            assert "untrusted DATA" in prompt.content
            assert request.prompt_version == TAVILY_PROMPT_VERSION
        return NarrativeSuccess(self.prose, "synthetic-final")


def install(app: AnalysisHarness, search: Search, model: TextModel) -> None:
    c = app.container
    prior = c.narrative_analysis_service
    c.narrative_analysis_service = NarrativeAnalysisService(
        app.snapshots,
        model,
        c.narrative_ledger,
        prior.models,
        prior.research,
        external_research=SavedExternalResearch(search, c.search_evidence),
        now=lambda: NOW,
    )


def test_external_success_off_and_history_are_separate(analysis: AnalysisHarness) -> None:
    search, model = Search(), TextModel(analysis)
    install(analysis, search, model)
    c, app = analysis.client, analysis.container
    payload = analysis.payload(model_key="deepseek-flash")
    off = c.post(PATH, json=payload)
    assert off.status_code == 201 and search.calls == 0
    on = c.post(PATH, json={**payload, "web_research": True})
    assert on.status_code == 201, on.text
    assert search.calls == 1 and len(model.requests) == 2
    result = on.json()
    run = c.get(f"/api/v1/paqs-e/narrative-analyses/{result['narrative_run_id']}").json()
    request = json.loads(run["request_payload_json"])
    provenance = json.loads(request["auxiliary_context"][0]["provenance"])
    rid = provenance["research_id"]
    receipt = c.get(f"/api/v1/paqs-e/external-research/{rid}").json()
    assert receipt["payload"]["auxiliary_context"] == request["auxiliary_context"]
    assert receipt["snapshot_hash"] == result["snapshot_hash"]
    assert provenance["sources"][0]["published_at"] is None
    assert "Synthetic public fact" in model.requests[-1].auxiliary_context[0].content
    for record in [off.json(), result]:
        assert (
            c.get(f"/api/v1/paqs-e/narrative-results/{record['narrative_result_id']}").json()[
                "response_text"
            ]
            == model.prose
        )
    c.get(f"/api/v1/paqs-e/securities/{analysis.security_id}/narrative-results")
    c.get("/api/v1/paqs-e/configuration")
    assert search.calls == 1 and len(model.requests) == 2
    with pytest.raises(IntegrityError), app.engine.begin() as conn:
        conn.execute(text("DELETE FROM paqs_e_external_research"))


@pytest.mark.parametrize(
    "failure",
    [
        "NOT_CONFIGURED",
        "AUTHENTICATION_FAILED",
        "RATE_LIMITED",
        "TIMEOUT",
        "EMPTY_RESULTS",
        "INVALID_RESPONSE",
        "PROVIDER_UNAVAILABLE",
    ],
)
def test_failed_search_is_recorded_without_final_call(
    analysis: AnalysisHarness, failure: str
) -> None:
    search, model = Search(failure), TextModel(analysis)
    install(analysis, search, model)
    response = analysis.client.post(
        PATH, json=analysis.payload(model_key="deepseek-flash", web_research=True)
    )
    assert response.status_code == 422
    info = response.json()["external_research"]
    assert info["failure_code"] == failure and not model.requests
    receipt = analysis.container.search_evidence.get(info["research_id"])
    assert receipt["status"] == "FAILED"
    assert receipt["payload"]["failure_code"] == failure
    with analysis.container.engine.connect() as conn:
        assert conn.scalar(text("SELECT COUNT(*) FROM paqs_e_narrative_runs")) == 0


@pytest.mark.parametrize(
    "prose", ["Uncited facts", "Wrong source [T99]", "Valid and wrong [T1] [T2]"]
)
def test_invalid_citations_do_not_create_success(analysis: AnalysisHarness, prose: str) -> None:
    search, model = Search(), TextModel(analysis, prose)
    install(analysis, search, model)
    response = analysis.client.post(
        PATH, json=analysis.payload(model_key="deepseek-flash", web_research=True)
    )
    assert response.status_code == 502
    assert response.json()["failure_kind"] == "INVALID_FINAL_TEXT"
    with analysis.container.engine.connect() as conn:
        assert conn.scalar(select(searches.c.status)) == "SUCCEEDED"
        assert conn.scalar(text("SELECT COUNT(*) FROM paqs_e_narrative_results")) == 0


def test_frozen_snapshot_cannot_launch_current_search(analysis: AnalysisHarness) -> None:
    search, model = Search(), TextModel(analysis)
    install(analysis, search, model)
    snapshot = analysis.snapshots.current_snapshot(analysis.security_id)
    with pytest.raises(ExternalResearchFailure) as error:
        analysis.container.narrative_analysis_service.analyze_frozen(
            security_id=analysis.security_id,
            snapshot=snapshot,
            model_key="deepseek-flash",
            strategy_id="paqs-e-master",
            web_research=True,
        )
    assert error.value.failure_code == "FROZEN_SNAPSHOT_EXTERNAL_RESEARCH_BLOCKED"
    assert not search.calls and not model.requests


def test_search_configuration_is_separate_and_secret_free(analysis: AnalysisHarness) -> None:
    # MemoryCredentials is supplied by the existing global test fixture.
    with TestClient(
        analysis.app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 50000)
    ) as c:
        path = "/api/v1/paqs-e/research-credentials/tavily"
        assert c.get(path).json() == {"credential_configured": False}
        secret = "synthetic-tavily-credential-only"
        assert c.put(path, json={"secret": secret}).status_code == 403
        response = c.put(path, json={"secret": secret}, headers={"Origin": "http://127.0.0.1:8000"})
        assert response.status_code == 200 and secret not in response.text
        assert response.json() == {"credential_configured": True}
        cfg = c.get("/api/v1/paqs-e/configuration").json()
        assert cfg["external_research"] == {"provider": "tavily", "credential_configured": True}
        model = next(m for m in cfg["models"] if m["model_key"] == "deepseek-flash")
        assert not model["web_research_supported"] and model["external_web_research_supported"]
        assert secret not in json.dumps(cfg)
        assert c.request(
            "DELETE", path, json={}, headers={"Origin": "http://127.0.0.1:8000"}
        ).json() == {"credential_configured": False}


def test_actual_adapters_with_mock_http_and_final_transport(analysis: AnalysisHarness) -> None:
    calls = []
    final_bodies = []

    def search(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "US.AVGO Broadcom synthetic release",
                        "url": "https://investors.broadcom.com/fixture",
                        "content": "NASDAQ: AVGO Synthetic announcement content",
                        "published_date": None,
                    }
                ]
            },
        )

    class FinalTransport:
        def post(self, endpoint: str, secret: str, body: dict[str, Any]) -> dict[str, Any]:
            final_bodies.append(body)
            capsule = json.loads(body["input"][-1]["content"])["auxiliary_context"][0]
            provenance = json.loads(capsule["provenance"])
            assert (
                analysis.container.search_evidence.get(provenance["research_id"])["status"]
                == "SUCCEEDED"
            )
            assert "Synthetic announcement content" in capsule["content"]
            assert secret == "synthetic-model-key"
            return {
                "model": "deepseek-flash",
                "status": "completed",
                "id": "synthetic-final",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "Synthetic observation [T1]"}],
                    }
                ],
            }

    c = analysis.container
    c.paqs_e_credentials.save("deepseek-flash", "synthetic-model-key")
    with httpx.Client(transport=httpx.MockTransport(search)) as client:
        provider = TavilyResearch(lambda: "synthetic-search-key", client=client, now=lambda: NOW)
        prior = c.narrative_analysis_service
        c.narrative_analysis_service = NarrativeAnalysisService(
            analysis.snapshots,
            NarrativeGateway(prior.models, c.paqs_e_credentials, FinalTransport()),
            c.narrative_ledger,
            prior.models,
            prior.research,
            now=lambda: NOW,
            external_research=SavedExternalResearch(provider, c.search_evidence),
        )
        response = analysis.client.post(
            PATH, json=analysis.payload(model_key="deepseek-flash", web_research=True)
        )
    assert response.status_code == 201, response.text
    assert len(calls) == 2 and len(final_bodies) == 1
    assert all(x["search_depth"] == "basic" and not x["auto_parameters"] for x in calls)
    assert response.json()["response_text"] == "Synthetic observation [T1]"


def test_evidence_commit_failure_stops_final_model(
    analysis: AnalysisHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    search, model = Search(), TextModel(analysis)
    install(analysis, search, model)

    def fail(*args: Any, **kwargs: Any) -> None:
        raise LedgerPersistenceError("synthetic store failure")

    monkeypatch.setattr(analysis.container.search_evidence, "record", fail)
    response = analysis.client.post(
        PATH, json=analysis.payload(model_key="deepseek-flash", web_research=True)
    )
    assert response.status_code == 500 and not model.requests
