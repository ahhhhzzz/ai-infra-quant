from __future__ import annotations

import copy
import json
from datetime import timedelta
from typing import Any

import pytest
from paqs_e_support import MemoryCredentials
from test_paqs_e_model_gateway import REGISTRY, SENTINEL, Transport, envelope
from test_paqs_e_runtime import _snapshot

from ai_infra_quant.application.paqs_e_models import ModelCredentials
from ai_infra_quant.application.paqs_e_narrative import (
    build_narrative_request,
    load_narrative_prompt,
)
from ai_infra_quant.application.paqs_e_research import ResearchFailure
from ai_infra_quant.application.paqs_e_runtime import load_strategy_package
from ai_infra_quant.core.domain.paqs_e_narrative import NarrativeSuccess
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.integrations.openai_reasoning.gateway import ModelGateway
from ai_infra_quant.integrations.openai_reasoning.narrative import NarrativeGateway

MODEL = REGISTRY.resolve("deepseek-v4-flash")
MEMO = "  # 合成研究备忘\n事实辅助;价格以 Snapshot 为准。https://prose.example/unverified\n"


def native(actions: tuple[str, ...] = ("search",)) -> dict[str, Any]:
    result = envelope(MEMO, "responses", MODEL.model_id)
    result["output"] = [
        {"type": "web_search_call", "status": "completed", "action": {"type": action}}
        for action in actions
    ] + result["output"]
    return result


def gateway(response: dict[str, Any]) -> tuple[ModelGateway, Transport]:
    store = MemoryCredentials()
    store.values[MODEL.credential_slot] = SENTINEL
    transport = Transport(response)
    return ModelGateway(REGISTRY, ModelCredentials(REGISTRY, store), transport), transport


@pytest.mark.parametrize(
    "actions",
    [
        ("search",),
        ("search", "open_page"),
        ("search", "open_page", "find_in_page"),
        ("search",) + ("open_page",) * 9,
    ],
)
def test_native_memo_without_sources_or_queries(actions: tuple[str, ...]) -> None:
    adapter, transport = gateway(native(actions))
    (item,) = adapter.research(MODEL, _snapshot())
    assert item.content == MEMO and item.source_timestamp is None and item.as_of_compatible
    assert item.source_label == "DeepSeek native web research memo"
    assert item.provenance is not None
    provenance = json.loads(item.provenance)
    assert provenance["action_types"] == list(actions)
    assert provenance["native_action_count"] == len(actions)
    assert provenance["sources"] == provenance["queries"] == []
    assert "cannot be independently verified" in provenance["limitation"]
    assert "synthetic-discarded-trace" not in canonical_json(item)
    endpoint, secret, body = transport.calls[0]
    assert endpoint == MODEL.research_endpoint and secret == SENTINEL
    assert body["tools"] == [{"type": "web_search"}] and body["max_output_tokens"] == 6000
    assert body["store"] is False and body["stream"] is False
    assert "JSON" not in body["instructions"] and "text" not in body
    assert len(transport.calls) == 1


@pytest.mark.parametrize("timestamp", [None, "2026-01-01", "malformed", "past", "future"])
def test_native_optional_citations_queries_and_cutoff(timestamp: str | None) -> None:
    response = native()
    response["output"][0]["action"]["queries"] = ["actual exposed query", "第二个查询"]
    source = {"type": "url_citation", "url": "https://example.org/source", "title": "原始标题"}
    if timestamp in {"past", "future"}:
        source["published_at"] = (
            _snapshot().as_of_timestamp + timedelta(days=1 if timestamp == "future" else -1)
        ).isoformat()
    elif timestamp is not None:
        source["published_at"] = timestamp
    response["output"][-1]["content"][0]["annotations"] = [source]
    adapter, _ = gateway(response)
    (item,) = adapter.research(MODEL, _snapshot())
    assert item.provenance is not None
    provenance = json.loads(item.provenance)
    assert item.content == MEMO
    assert provenance["queries"] == ["actual exposed query", "第二个查询"]
    assert "prose.example" not in item.provenance
    if timestamp == "future":
        assert provenance["sources"] == [] and provenance["excluded_future_source_count"] == 1
    else:
        assert provenance["sources"][0]["url"] == source["url"]
        assert ("publication_time" in provenance["sources"][0]) == (timestamp == "past")
    assert "cutoff compliance was requested" in provenance["limitation"]


@pytest.mark.parametrize(
    "case",
    [
        "actions",
        "unknown",
        "no-search",
        "incomplete",
        "cancelled",
        "failed",
        "refusal",
        "empty",
        "missing",
        "multiple",
        "oversize",
        "secret",
        "model",
        "id",
        "tool",
        "action-status",
        "action-shape",
        "output-shape",
        "part-shape",
        "queries",
        "query-length",
        "url",
        "userinfo",
        "url-length",
        "raw-count",
        "capsule",
        "network",
        "naive-url",
    ],
)
def test_native_memo_fails_closed_without_retry(case: str) -> None:
    response = native()
    action = response["output"][0]["action"]
    part = response["output"][-1]["content"][0]
    if case == "actions":
        response = native(("search",) * 11)
    elif case == "unknown":
        action["type"] = "execute"
    elif case == "no-search":
        action["type"] = "open_page"
    elif case in {"incomplete", "cancelled", "failed"}:
        response["status"] = case
    elif case == "refusal":
        part["type"] = "refusal"
    elif case == "empty":
        part["text"] = " \n"
    elif case == "missing":
        response["output"].pop()
    elif case == "multiple":
        response["output"].append(copy.deepcopy(response["output"][-1]))
    elif case == "oversize":
        part["text"] = "中" * 24001
    elif case == "capsule":
        part["text"] = "中" * 24000
    elif case == "secret":
        part["text"] = SENTINEL
    elif case == "model":
        response["model"] = "unapproved-model"
    elif case == "id":
        response["id"] = "unsafe\nidentity"
    elif case == "tool":
        response["output"].insert(0, {"type": "function_call"})
    elif case == "action-status":
        response["output"][0]["status"] = "in_progress"
    elif case == "action-shape":
        response["output"][0]["action"] = []
    elif case == "output-shape":
        response["output"] = [None]
    elif case == "part-shape":
        response["output"][-1]["content"] = [None]
    elif case == "queries":
        action["queries"] = ["q"] * 5
    elif case == "query-length":
        action["query"] = "q" * 501
    elif case == "url":
        action["sources"] = [{"url": "javascript:alert(1)"}]
    elif case == "userinfo":
        action["sources"] = [{"url": "https://user:pass@example.org"}]
    elif case == "naive-url":
        action["sources"] = [{"url": "https://example.org\\evil"}]
    elif case == "url-length":
        action["sources"] = [{"url": "https://example.org/" + "x" * 1000}]
    elif case == "raw-count":
        action["sources"] = [{"url": "https://example.org"}] * 65
    adapter, transport = gateway(response)
    transport.error = case == "network"
    with pytest.raises(ResearchFailure) as caught:
        adapter.research(MODEL, _snapshot())
    assert len(transport.calls) == 1 and SENTINEL not in str(caught.value)


def test_research_is_frozen_before_unchanged_tool_free_narrative_gateway() -> None:
    adapter, transport = gateway(native())
    context = adapter.research(MODEL, _snapshot())
    strategy, prompt = load_strategy_package(), load_narrative_prompt()
    request = build_narrative_request(
        snapshot=_snapshot(),
        model_id=MODEL.model_id,
        model_provider=MODEL.provider_id,
        strategy=strategy,
        prompt=prompt,
        auxiliary_context=context,
        web_research=True,
    )
    frozen = canonical_json(request)
    transport.response = envelope("# 最终 Narrative\n原样文本", MODEL.api_surface, MODEL.model_id)
    final = NarrativeGateway(REGISTRY, adapter.credentials, transport)
    outcome = final.reason_text(request=request, strategy=strategy, prompt=prompt)
    assert isinstance(outcome, NarrativeSuccess)
    assert len(transport.calls) == 2
    body = transport.calls[1][2]
    assert body["tools"] == [] and body["tool_choice"] == "none"
    assert body["input"][-1]["content"] == frozen
    assert json.loads(frozen)["auxiliary_context"][0]["content"] == MEMO
    assert "text" not in body and "response_format" not in body


def test_native_record_boundary_dedup_and_future_duplicate_cannot_be_promoted() -> None:
    response = native()
    response["output"][0]["action"].update(
        queries=["actual"] * 4,
        sources=[{"url": "https://example.org/source"}] * 63
        + [
            {
                "url": "https://example.org/source",
                "published_at": (_snapshot().as_of_timestamp + timedelta(days=1)).isoformat(),
            }
        ],
    )
    adapter, transport = gateway(response)
    (item,) = adapter.research(MODEL, _snapshot())
    assert item.provenance is not None
    provenance = json.loads(item.provenance)
    assert provenance["sources"] == [] and provenance["excluded_future_source_count"] == 1
    assert provenance["queries"] == ["actual"] * 4
    response["output"][0]["action"]["sources"] = [{"url": "https://example.org/source"}] * 64
    (item,) = adapter.research(MODEL, _snapshot())
    assert item.provenance is not None
    assert json.loads(item.provenance)["sources"] == [{"url": "https://example.org/source"}]
    assert len(transport.calls) == 2  # Two explicit attempts; neither retries internally.


@pytest.mark.parametrize(
    "url", ["https://<invalid>/", "https://a..b/", "https://-bad.org/", "https://example.org:bad/"]
)
def test_native_invalid_hostname_or_port_fails_closed(url: str) -> None:
    response = native()
    response["output"][0]["action"]["sources"] = [{"url": url}]
    adapter, transport = gateway(response)
    with pytest.raises(ResearchFailure):
        adapter.research(MODEL, _snapshot())
    assert len(transport.calls) == 1
