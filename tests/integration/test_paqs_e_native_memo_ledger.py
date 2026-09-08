from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest
from paqs_e_support import MemoryCredentials
from sqlalchemy import Engine, select
from test_paqs_e_analysis_api import AnalysisHarness
from test_paqs_e_analysis_api import analysis as analysis_fixture
from test_paqs_e_narrative_ledger_api import PROSE, TextProvider, install

from ai_infra_quant.application.paqs_e_models import ModelCredentials, ModelRegistry
from ai_infra_quant.core.domain.paqs_e_ledger import payload_sha256
from ai_infra_quant.database.models.paqs_e_narrative import results, runs
from ai_infra_quant.integrations.openai_reasoning.gateway import ModelGateway
from ai_infra_quant.integrations.openai_reasoning.narrative import NarrativeGateway

analysis = analysis_fixture


def envelope(prose: str, surface: str, model: str) -> dict[str, Any]:
    assert surface == "responses"
    return {
        "status": "completed",
        "model": model,
        "id": "synthetic-response",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": prose}]}],
    }


class Transport:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def post(self, endpoint: str, secret: str, body: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(body)
        return self.response


@pytest.mark.parametrize("research_on", [False, True])
def test_real_gateway_api_exact_memo_freeze_hash_readback_and_no_failure_run(
    analysis: AnalysisHarness,
    migrated_engine: Engine,
    research_on: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = ModelRegistry()
    model = registry.resolve("deepseek-v4-flash")
    fixtures = SimpleNamespace(
        REGISTRY=registry,
        MODEL=model,
        MEMO="  # Synthetic memo\n",
        SENTINEL="synthetic-native-ledger-credential",
        envelope=envelope,
    )
    native_response = envelope(fixtures.MEMO, "responses", model.model_id)
    native_response["output"].insert(
        0, {"type": "web_search_call", "status": "completed", "action": {"type": "search"}}
    )
    store = MemoryCredentials()
    store.values[model.credential_slot] = fixtures.SENTINEL
    transport = Transport(native_response)
    research = ModelGateway(registry, ModelCredentials(registry, store), transport)
    native_response = transport.response
    original_post = transport.post

    def post(endpoint: str, secret: str, body: dict[str, Any]) -> dict[str, Any]:
        if body["tools"] == []:
            assert len(transport.calls) == (1 if research_on else 0)
            request = json.loads(body["input"][-1]["content"])
            assert request["web_research"] is research_on
            assert bool(request["auxiliary_context"]) is research_on
            if research_on:
                assert request["auxiliary_context"][0]["content"] == fixtures.MEMO
            transport.response = fixtures.envelope(PROSE, "responses", fixtures.MODEL.model_id)
        return original_post(endpoint, secret, body)

    monkeypatch.setattr(transport, "post", post)
    install(analysis, TextProvider())
    service = analysis.container.narrative_analysis_service
    service.research = research
    service.provider = NarrativeGateway(fixtures.REGISTRY, research.credentials, transport)
    response = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses",
        json=analysis.payload(model_key=fixtures.MODEL.model_key, web_research=research_on),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["response_text"] == PROSE
    assert body["response_text_sha256"] == payload_sha256(PROSE)
    run = analysis.client.get(
        "/api/v1/paqs-e/narrative-analyses/" + body["narrative_run_id"]
    ).json()
    assert run["request_payload_sha256"] == payload_sha256(run["request_payload_json"])
    frozen = json.loads(run["request_payload_json"])["auxiliary_context"]
    if research_on:
        assert frozen[0]["content"] == fixtures.MEMO
        assert "cannot be independently verified" in frozen[0]["provenance"]
    else:
        assert frozen == []
    with migrated_engine.connect() as connection:
        before = (connection.execute(select(runs)).all(), connection.execute(select(results)).all())
    native_response["status"] = "incomplete"
    transport.response = native_response
    failed = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses",
        json=analysis.payload(model_key=fixtures.MODEL.model_key, web_research=True),
    )
    assert failed.status_code == 422 and "narrative_run_id" not in failed.json()
    assert len(transport.calls) == (3 if research_on else 2)
    with migrated_engine.connect() as connection:
        after = (connection.execute(select(runs)).all(), connection.execute(select(results)).all())
    assert after == before
    assert fixtures.SENTINEL not in repr(after)
    assert "synthetic-discarded-trace" not in repr(after)
