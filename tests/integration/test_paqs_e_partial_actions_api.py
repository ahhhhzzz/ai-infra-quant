from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from paqs_e_partial_action_support import partial_actions
from paqs_e_support import MemoryCredentials
from sqlalchemy import Engine, select, text
from test_paqs_e_analysis_api import AnalysisHarness
from test_paqs_e_analysis_api import analysis as analysis_fixture
from test_paqs_e_narrative_ledger_api import PROSE, TextProvider, install
from test_paqs_e_native_memo_ledger import envelope
from test_paqs_e_research_continuation_api import MEMO, SECRET, TRACE, ResearchTransport

from ai_infra_quant.application.paqs_e_models import ModelCredentials, ModelRegistry
from ai_infra_quant.core.domain.paqs_e_ledger import payload_sha256
from ai_infra_quant.database.models.paqs_e_narrative import results, runs
from ai_infra_quant.integrations.openai_reasoning.gateway import ModelGateway
from ai_infra_quant.integrations.openai_reasoning.narrative import NarrativeGateway

analysis = analysis_fixture


class PartialTransport(ResearchTransport):
    def post(self, endpoint: str, secret: str, body: dict[str, Any]) -> dict[str, Any]:
        if not body["tools"] and not body["input"][-1]["content"].startswith("{"):
            self.calls.append(copy.deepcopy(body))
            assert endpoint == "https://api.deepseek.com/responses" and secret == SECRET
            assert self.mode == "tool-only" and len(self.calls) == 2
            assert body["input"][1:-1] == [
                item for item in self.native if item["status"] == "completed"
            ]
            assert body["input"][0]["content"] == self.calls[0]["input"]
            assert body["tools"] == [] and body["tool_choice"] == "none"
            assert body["reasoning"] == self.calls[0]["reasoning"] == {"effort": "none"}
            assert not {"previous_response_id", "conversation"} & body.keys()
            return envelope(MEMO, "responses", body["model"])
        return super().post(endpoint, secret, body)


@pytest.mark.parametrize("mode", ["off", "direct", "tool-only"])
@pytest.mark.parametrize("failure", ["ACTION_STATUS", "QUERY_INTEGRITY", "NO_COMPLETED_SEARCH"])
def test_partial_actions_freeze_before_narrative_and_fail_without_ledger_mutation(
    analysis: AnalysisHarness, migrated_engine: Engine, mode: str, failure: str
) -> None:
    registry = ModelRegistry()
    model = registry.resolve("deepseek-v4-flash")
    store = MemoryCredentials()
    store.values[model.credential_slot] = SECRET
    transport = PartialTransport()
    transport.mode = mode
    native = partial_actions()
    transport.native = native
    expected_queries = [
        q
        for item in native
        if item["status"] == "completed"
        for q in item["action"].get("queries", [])
    ]
    gateway = ModelGateway(registry, ModelCredentials(registry, store), transport)
    install(analysis, TextProvider())
    service = analysis.container.narrative_analysis_service
    service.research = gateway
    service.provider = NarrativeGateway(registry, gateway.credentials, transport)
    schema_sql = text("SELECT type, name, sql FROM sqlite_master ORDER BY name")
    with migrated_engine.connect() as connection:
        schema = connection.execute(schema_sql).all()
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
            == "0003_task007c1_narrative_ledger"
        )
    response = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses",
        json=analysis.payload(model_key=model.model_key, web_research=mode != "off"),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["response_text"] == PROSE
    assert body["response_text_sha256"] == payload_sha256(PROSE)
    run = analysis.client.get(
        "/api/v1/paqs-e/narrative-analyses/" + body["narrative_run_id"]
    ).json()
    assert run["request_payload_sha256"] == payload_sha256(run["request_payload_json"])
    context = json.loads(run["request_payload_json"])["auxiliary_context"]
    if mode != "off":
        provenance = json.loads(context[0]["provenance"])
        assert provenance["provider_exposed_query_count"] == len(expected_queries)
        assert provenance["queries"] == expected_queries[:16]
        assert provenance["query_capture_complete"] is False
        assert provenance["web_search_call_count"] == 16 and provenance["search_action_count"] == 7
        assert (
            provenance["completed_action_count"] == 13 and provenance["completed_search_count"] == 6
        )
        assert provenance["non_completed_search_count"] == 1
        assert provenance["sources"] == []
        assert provenance["synthesis_used"] is (mode == "tool-only")
        assert provenance["research_http_request_count"] == (2 if mode == "tool-only" else 1)
    else:
        assert context == []
    assert len(transport.calls) == {"off": 1, "direct": 2, "tool-only": 3}[mode]
    # The shared R04 transport asserts as-is pass-back, tools off, and freeze before final call.
    with migrated_engine.connect() as connection:
        before = (connection.execute(select(runs)).all(), connection.execute(select(results)).all())
    transport.calls.clear()
    transport.mode = "tool-only"
    if failure == "ACTION_STATUS":
        native[8]["status"] = "private-unknown-status"
    elif failure == "QUERY_INTEGRITY":
        native[0]["action"]["queries"][0] = True
    else:
        for item in native[:7]:
            item["status"] = "incomplete"
    failed = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses",
        json=analysis.payload(model_key=model.model_key, web_research=True),
    )
    assert failed.status_code == 422 and len(transport.calls) == 1
    error = failed.json()
    assert "narrative_run_id" not in error and "narrative_result_id" not in error
    diagnostic = error["research_diagnostic"]
    assert diagnostic["boundary_code"] == failure
    assert diagnostic["provider_exposed_query_count"] == (
        0 if failure == "NO_COMPLETED_SEARCH" else 24
    )
    assert diagnostic["raw_source_record_count"] == 0 and diagnostic["unknown_action_count"] == 0
    assert all(
        value not in failed.text for value in ["synthetic.example", "query 0", SECRET, TRACE]
    )
    with migrated_engine.connect() as connection:
        after = (connection.execute(select(runs)).all(), connection.execute(select(results)).all())
        assert connection.execute(schema_sql).all() == schema
    assert after == before
    assert all(
        value not in repr(after)
        for value in [
            SECRET,
            TRACE,
            "opaque_restore_token",
            "private-query",
            "private-source",
            "research_diagnostic",
        ]
    )
