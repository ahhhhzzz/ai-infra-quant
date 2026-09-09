from __future__ import annotations

import json
from typing import Any

import pytest
from paqs_e_support import MemoryCredentials
from sqlalchemy import Engine, select, text
from test_paqs_e_analysis_api import AnalysisHarness
from test_paqs_e_analysis_api import analysis as analysis_fixture
from test_paqs_e_narrative_ledger_api import PROSE, TextProvider, install
from test_paqs_e_research_continuation_api import SECRET, TRACE, ResearchTransport

from ai_infra_quant.application.paqs_e_models import ModelCredentials, ModelRegistry
from ai_infra_quant.core.domain.paqs_e_ledger import payload_sha256
from ai_infra_quant.database.models.paqs_e_narrative import results, runs
from ai_infra_quant.integrations.openai_reasoning.gateway import ModelGateway
from ai_infra_quant.integrations.openai_reasoning.narrative import NarrativeGateway

analysis = analysis_fixture


@pytest.mark.parametrize("mode", ["off", "direct", "tool-only"])
@pytest.mark.parametrize("many_queries", [False, True])
def test_live_multiplicity_freezes_before_narrative_and_preserves_ledger(
    analysis: AnalysisHarness, migrated_engine: Engine, mode: str, many_queries: bool
) -> None:
    registry = ModelRegistry()
    model = registry.resolve("deepseek-v4-flash")
    store = MemoryCredentials()
    store.values[model.credential_slot] = SECRET
    transport = ResearchTransport()
    transport.mode = mode
    native: list[dict[str, Any]] = [
        {
            "type": "web_search_call",
            "status": "completed",
            "id": f"native-{i}",
            "action": {"type": "search", "queries": [f"query {i}"]}
            if i < 6
            else {"type": "find_in_page" if i % 2 else "open_page"},
        }
        for i in range(20)
    ]
    transport.native = native
    if many_queries:
        native[0]["action"]["queries"] = [f"first {i}" for i in range(32)]
    expected_queries = [q for item in native for q in item["action"].get("queries", [])]
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
            == "0004_task006b1_market_archive"
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
        assert provenance["query_capture_complete"] is (not many_queries)
        assert provenance["web_search_call_count"] == 20 and provenance["search_action_count"] == 6
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
    native[0]["action"]["sources"] = [{"url": "https://synthetic.example/private"}] * 65
    failed = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses",
        json=analysis.payload(model_key=model.model_key, web_research=True),
    )
    assert failed.status_code == 422 and len(transport.calls) == 1
    error = failed.json()
    assert "narrative_run_id" not in error and "narrative_result_id" not in error
    diagnostic = error["research_diagnostic"]
    assert diagnostic["provider_exposed_query_count"] == len(expected_queries)
    assert diagnostic["raw_source_record_count"] == 65 and diagnostic["unknown_action_count"] == 0
    assert all(
        value not in failed.text for value in ["synthetic.example", "query 0", SECRET, TRACE]
    )
    with migrated_engine.connect() as connection:
        after = (connection.execute(select(runs)).all(), connection.execute(select(results)).all())
        assert connection.execute(schema_sql).all() == schema
    assert after == before
    assert all(
        value not in repr(after)
        for value in [SECRET, TRACE, "web_search_call", "research_diagnostic"]
    )
