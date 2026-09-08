from __future__ import annotations

import copy
import json
from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from test_paqs_e_model_gateway import SENTINEL
from test_paqs_e_native_research import MEMO, MODEL, native
from test_paqs_e_research_continuation import TRACE, adapter, memo
from test_paqs_e_runtime import _snapshot

from ai_infra_quant.application.paqs_e_research import ResearchDiagnostic, ResearchFailure


def live_like(*, direct: bool = False) -> dict[str, Any]:
    response = native(("search",) * 6 + ("open_page", "find_in_page") * 7)
    for index, item in enumerate(response["output"][:20]):
        item["id"] = f"native-call-{index}"
        if index < 6:
            item["action"]["queries"] = [f"synthetic query {index}"]
    if not direct:
        response["output"] = response["output"][:20]
    return response


@pytest.mark.parametrize("direct", [False, True])
def test_live_like_twenty_calls_six_searches_six_queries(direct: bool) -> None:
    search = live_like(direct=direct)
    original = copy.deepcopy(search)
    gateway, transport = adapter([search, memo()])
    (item,) = gateway.research(MODEL, _snapshot())
    assert item.content == MEMO and search == original
    provenance = json.loads(item.provenance or "")
    assert provenance["web_search_call_count"] == 20
    assert provenance["search_action_count"] == 6
    assert provenance["provider_exposed_query_count"] == 6
    assert provenance["query_capture_complete"] is True
    assert provenance["queries"] == [f"synthetic query {i}" for i in range(6)]
    assert provenance["synthesis_used"] is (not direct)
    assert len(transport.calls) == provenance["research_http_request_count"] == (1 if direct else 2)
    if not direct:
        body = transport.calls[1][2]
        assert body["input"][1:-1] == original["output"]
        assert body["input"][0]["content"] == transport.calls[0][2]["input"]
        assert body["tools"] == [] and body["tool_choice"] == "none"
        assert body["reasoning"] == {"effort": "none"}
        assert not {"previous_response_id", "conversation"} & body.keys()


@pytest.mark.parametrize(
    "queries,retained,complete",
    [
        ([], [], True),
        (["duplicate"] * 6, ["duplicate"] * 6, True),
        ([str(i) for i in range(16)], [str(i) for i in range(16)], True),
        ([str(i) for i in range(37)], [str(i) for i in range(16)], False),
        (["中" * 500] * 8, ["中" * 500] * 8, True),
        (["x" * 500] * 8 + ["next", "q"], ["x" * 500] * 8, False),
        (["x" * 499] * 8 + ["cannot-fit", "q"], ["x" * 499] * 8, False),
        (["q"] * 256, ["q"] * 16, False),
        (["x" * 500] * 128, ["x" * 500] * 8, False),
    ],
)
def test_capture_is_truthful_complete_query_prefix(
    queries: list[str], retained: list[str], complete: bool
) -> None:
    response = native()
    response["output"][0]["action"]["queries"] = queries
    gateway, transport = adapter([response])
    (item,) = gateway.research(MODEL, _snapshot())
    provenance = json.loads(item.provenance or "")
    assert provenance["provider_exposed_query_count"] == len(queries)
    assert provenance["queries"] == retained
    assert provenance["query_capture_complete"] is complete
    assert len(transport.calls) == 1


def test_both_native_query_forms_count_in_received_order_without_deduplication() -> None:
    response = native()
    response["output"][0]["action"].update(query="first", queries=["second", "first"])
    gateway, _ = adapter([response])
    (item,) = gateway.research(MODEL, _snapshot())
    provenance = json.loads(item.provenance or "")
    assert provenance["queries"] == ["first", "second", "first"]
    assert provenance["provider_exposed_query_count"] == 3


@pytest.mark.parametrize(
    "value", [None, 1, True, {}, [], "", " \n", "x" * 501, "bad\x00", "bad\x85", "bad\ud800"]
)
@pytest.mark.parametrize("after_capture", [False, True])
def test_every_individual_query_is_validated_even_after_capture_stops(
    value: Any, after_capture: bool
) -> None:
    response = live_like()
    response["output"][0]["action"]["queries"] = (["valid"] * 17 if after_capture else []) + [value]
    gateway, transport = adapter([response])
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(MODEL, _snapshot())
    assert len(transport.calls) == 1
    diagnostic = caught.value.diagnostic
    assert diagnostic is not None and diagnostic.stage == "SEARCH"
    # Failure diagnostics count exposed slots even when one slot has invalid contents.
    assert diagnostic.provider_exposed_query_count == (23 if after_capture else 6)
    assert diagnostic.raw_source_record_count == diagnostic.unknown_action_count == 0
    assert "synthetic query" not in json.dumps(diagnostic.as_dict())


@pytest.mark.parametrize(
    "case",
    [
        "query-count",
        "query-characters",
        "source-count",
        "unknown",
        "actions",
        "output",
        "no-search",
    ],
)
def test_structural_limits_fail_once_with_safe_numeric_counts(case: str) -> None:
    response = live_like()
    first = response["output"][0]["action"]
    if case == "query-count":
        first["queries"] = ["q"] * 257
    elif case == "query-characters":
        first["queries"] = ["x" * 500] * 129
    elif case == "source-count":
        first["sources"] = [{"url": "https://synthetic.example/private-source"}] * 65
    elif case == "unknown":
        response["output"][-1]["action"]["type"] = "synthetic-unknown-private-action"
    elif case == "actions":
        response["output"] += [copy.deepcopy(response["output"][-1])] * 45
    elif case == "output":
        response["output"] += [{"type": "reasoning", "summary": TRACE}] * 109
    elif case == "no-search":
        for item in response["output"]:
            item["action"]["type"] = "open_page"
    gateway, transport = adapter([response])
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(MODEL, _snapshot())
    assert len(transport.calls) == 1
    diagnostic = caught.value.diagnostic
    assert diagnostic is not None
    if case in {"query-count", "query-characters"}:
        assert diagnostic.provider_exposed_query_count == (262 if case == "query-count" else 134)
    if case == "source-count":
        assert diagnostic.raw_source_record_count == 65
    if case == "unknown":
        assert diagnostic.unknown_action_count == 1
    encoded = json.dumps(diagnostic.as_dict())
    assert all(
        value not in encoded
        for value in [TRACE, SENTINEL, "private-source", "synthetic query", "private-action"]
    )


def test_synthesis_failure_counts_and_secret_tainted_counts_omitted() -> None:
    response = memo()
    response["status"] = "incomplete"
    gateway, transport = adapter([live_like(), response])
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(MODEL, _snapshot())
    diagnostic = caught.value.diagnostic
    assert diagnostic is not None and diagnostic.stage == "SYNTHESIS"
    assert (
        diagnostic.provider_exposed_query_count
        == diagnostic.raw_source_record_count
        == diagnostic.unknown_action_count
        == 0
    )
    assert len(transport.calls) == 2
    tainted = live_like()
    tainted["output"][0]["action"]["queries"] = [SENTINEL]
    gateway, _ = adapter([tainted])
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(MODEL, _snapshot())
    assert caught.value.diagnostic is not None
    assert caught.value.diagnostic.provider_exposed_query_count is None


@pytest.mark.parametrize("value", [-1, True, "6", 1025])
def test_diagnostic_new_counts_are_exact_bounded_integers(value: Any) -> None:
    for field in [
        "provider_exposed_query_count",
        "raw_source_record_count",
        "unknown_action_count",
    ]:
        with pytest.raises(ValueError):
            ResearchDiagnostic(
                "SEARCH", "INVALID_RESPONSE", "deepseek", MODEL.model_id, False, 1, **{field: value}
            )


def test_diagnostic_saturation_omission_and_immutability() -> None:
    response = live_like()
    response["output"][0]["action"].update(queries=["q"] * 1100, sources=[{}] * 1100)
    gateway, _ = adapter([response])
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(MODEL, _snapshot())
    diagnostic = caught.value.diagnostic
    assert diagnostic is not None
    assert diagnostic.provider_exposed_query_count == diagnostic.raw_source_record_count == 1024
    with pytest.raises(FrozenInstanceError):
        diagnostic.unknown_action_count = 3  # type: ignore[misc]
    response["output"][0]["action"].update(queries="malformed", sources=None)
    gateway, _ = adapter([response])
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(MODEL, _snapshot())
    assert caught.value.diagnostic is not None
    assert caught.value.diagnostic.provider_exposed_query_count is None
    assert caught.value.diagnostic.raw_source_record_count is None
