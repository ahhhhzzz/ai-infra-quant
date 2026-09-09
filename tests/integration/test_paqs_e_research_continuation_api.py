from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from paqs_e_support import MemoryCredentials
from sqlalchemy import Engine, select, text
from test_paqs_e_analysis_api import AnalysisHarness
from test_paqs_e_analysis_api import analysis as analysis_fixture
from test_paqs_e_narrative_ledger_api import PROSE, TextProvider, install
from test_paqs_e_native_memo_ledger import envelope

from ai_infra_quant.application.paqs_e_models import ModelCredentials, ModelRegistry
from ai_infra_quant.core.domain.paqs_e_ledger import payload_sha256
from ai_infra_quant.database.models.paqs_e_narrative import results, runs
from ai_infra_quant.integrations.openai_reasoning.gateway import ModelGateway
from ai_infra_quant.integrations.openai_reasoning.narrative import NarrativeGateway

analysis = analysis_fixture
MEMO = "  # Synthetic factual memo\nSnapshot facts take precedence.\n"
SECRET = "synthetic-continuation-api-credential"
TRACE = "synthetic-reasoning-should-never-be-persisted"


class ResearchTransport:
    def __init__(self) -> None:
        self.mode = "off"
        self.failure: str | None = None
        self.calls: list[dict[str, Any]] = []
        self.native = [
            {
                "type": "web_search_call",
                "status": "completed",
                "id": f"synthetic-{index}",
                "action": {"type": "search" if index == 0 else "open_page"},
                "opaque_restore_token": f"native-{index}",
            }
            for index in range(11)
        ]

    def post(self, endpoint: str, secret: str, body: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(copy.deepcopy(body))
        assert endpoint == "https://api.deepseek.com/responses" and secret == SECRET
        model = body["model"]
        if body["tools"]:
            assert len(self.calls) == 1
            result = envelope(MEMO, "responses", model)
            result["output"] = copy.deepcopy(self.native) + (
                result["output"] if self.mode == "direct" else []
            )
            if self.failure == "SEARCH":
                result.update(
                    status="incomplete", incomplete_details={"reason": "max_output_tokens"}
                )
        elif body["input"][-1]["content"].startswith("{"):
            assert len(self.calls) == {"off": 1, "direct": 2, "tool-only": 3}[self.mode]
            frozen = json.loads(body["input"][-1]["content"])
            assert frozen["web_research"] is (self.mode != "off")
            assert bool(frozen["auxiliary_context"]) is (self.mode != "off")
            if self.mode != "off":
                assert frozen["auxiliary_context"][0]["content"] == MEMO
            assert body["tool_choice"] == "none" and "reasoning" not in body
            result = envelope(PROSE, "responses", model)
        else:
            assert self.mode == "tool-only" and len(self.calls) == 2
            assert body["input"][1:-1] == self.native
            assert body["input"][0]["content"] == self.calls[0]["input"]
            assert body["tools"] == [] and body["tool_choice"] == "none"
            assert body["reasoning"] == {"effort": "none"}
            assert not {"previous_response_id", "conversation"} & body.keys()
            result = envelope(MEMO, "responses", model)
            if self.failure == "SYNTHESIS":
                result.update(status="failed", error={"message": "synthetic-raw-error-body"})
        result["output"].append({"type": "reasoning", "summary": TRACE})
        return result


@pytest.mark.parametrize("mode", ["off", "direct", "tool-only"])
@pytest.mark.parametrize("failure_stage", ["SEARCH", "SYNTHESIS"])
def test_lifecycle_hashes_no_failure_rows_or_schema_changes(
    analysis: AnalysisHarness, migrated_engine: Engine, mode: str, failure_stage: str
) -> None:
    registry = ModelRegistry()
    model = registry.resolve("deepseek-v4-flash")
    store = MemoryCredentials()
    store.values[model.credential_slot] = SECRET
    transport = ResearchTransport()
    transport.mode = mode
    gateway = ModelGateway(registry, ModelCredentials(registry, store), transport)
    install(analysis, TextProvider())
    service = analysis.container.narrative_analysis_service
    service.research = gateway
    service.provider = NarrativeGateway(registry, gateway.credentials, transport)
    with migrated_engine.connect() as connection:
        schema = connection.execute(
            text("SELECT type, name, sql FROM sqlite_master ORDER BY name")
        ).all()
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
            == "0004_task006b1_market_archive"
        )
    response = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses",
        json=analysis.payload(model_key=model.model_key, web_research=mode != "off"),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["response_text"] == PROSE and body["response_text_sha256"] == payload_sha256(PROSE)
    run = analysis.client.get(
        "/api/v1/paqs-e/narrative-analyses/" + body["narrative_run_id"]
    ).json()
    assert run["request_payload_sha256"] == payload_sha256(run["request_payload_json"])
    context = json.loads(run["request_payload_json"])["auxiliary_context"]
    if mode != "off":
        provenance = json.loads(context[0]["provenance"])
        assert provenance["research_http_request_count"] == (2 if mode == "tool-only" else 1)
        assert provenance["synthesis_used"] is (mode == "tool-only")
        assert provenance["web_search_call_count"] == 11
    assert len(transport.calls) == {"off": 1, "direct": 2, "tool-only": 3}[mode]
    with migrated_engine.connect() as connection:
        before = (connection.execute(select(runs)).all(), connection.execute(select(results)).all())
    transport.mode = "tool-only"
    transport.failure = failure_stage
    transport.calls.clear()  # A second explicit user action, not a provider retry.
    failed = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses",
        json=analysis.payload(model_key=model.model_key, web_research=True),
    )
    assert failed.status_code == 422, failed.text
    error = failed.json()
    assert error["code"] == "PAQS_E_RESEARCH_PRECONDITION_FAILED"
    assert "narrative_run_id" not in error and "narrative_result_id" not in error
    diagnostic = error["research_diagnostic"]
    assert diagnostic["stage"] == failure_stage
    assert (
        diagnostic["research_http_request_count"]
        == len(transport.calls)
        == (1 if failure_stage == "SEARCH" else 2)
    )
    assert diagnostic["detail_version"] == "paqs-e-research-diagnostic-v1"
    with migrated_engine.connect() as connection:
        after = (connection.execute(select(runs)).all(), connection.execute(select(results)).all())
        assert (
            connection.execute(
                text("SELECT type, name, sql FROM sqlite_master ORDER BY name")
            ).all()
            == schema
        )
    assert after == before
    for value in [
        SECRET,
        TRACE,
        "opaque_restore_token",
        "synthetic-raw-error-body",
        "research_diagnostic",
    ]:
        assert value not in repr(after)
    for value in [SECRET, TRACE, MEMO, "synthetic-raw-error-body"]:
        assert value not in failed.text
