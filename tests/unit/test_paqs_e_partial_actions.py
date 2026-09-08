from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from paqs_e_partial_action_support import partial_actions
from test_paqs_e_model_gateway import SENTINEL
from test_paqs_e_native_research import MEMO, MODEL, native
from test_paqs_e_research_continuation import TRACE, adapter, memo
from test_paqs_e_runtime import _snapshot

from ai_infra_quant.application.paqs_e_research import (
    RESEARCH_BOUNDARY_CODES,
    ResearchDiagnostic,
    ResearchFailure,
)
from ai_infra_quant.integrations.openai_reasoning.deepseek_research import parse_native_search
from ai_infra_quant.integrations.openai_reasoning.deepseek_research_diagnostics import (
    NativeParseFailure,
    observed_counts,
)


def mixed(*, direct: bool = False) -> dict[str, Any]:
    response = memo()
    response["output"] = partial_actions() + (response["output"] if direct else [])
    return response


@pytest.mark.parametrize("direct", [False, True])
def test_live_sixteen_seven_twentyfour_partial_actions(direct: bool) -> None:
    response = mixed(direct=direct)
    original = copy.deepcopy(response)
    response["output"].append({"type": "reasoning", "summary": TRACE})
    gateway, transport = adapter([response, memo()])
    (item,) = gateway.research(MODEL, _snapshot())
    provenance = json.loads(item.provenance or "")
    expected = {
        "web_search_call_count": 16,
        "search_action_count": 7,
        "completed_action_count": 13,
        "incomplete_action_count": 1,
        "failed_action_count": 1,
        "in_progress_action_count": 1,
        "cancelled_action_count": 0,
        "completed_search_count": 6,
        "non_completed_search_count": 1,
        "provider_exposed_query_count": 24,
    }
    assert {key: provenance[key] for key in expected} == expected
    assert provenance["native_action_count"] == 13
    assert len(provenance["action_types"]) == 13
    assert len(provenance["queries"]) == 16 and provenance["query_capture_complete"] is False
    assert provenance["sources"] == []
    assert item.content == MEMO and len(transport.calls) == (1 if direct else 2)
    assert provenance["research_http_request_count"] == len(transport.calls)
    assert all(
        value not in repr(item) for value in [TRACE, "private-", "opaque-", "web_search_call'"]
    )
    assert response["output"][:-1] == original["output"]
    if not direct:
        body = transport.calls[1][2]
        accepted = [v for v in original["output"] if v["status"] == "completed"]
        assert body["input"][1:-1] == accepted
        assert body["input"][0]["content"] == transport.calls[0][2]["input"]
        assert body["tools"] == [] and body["tool_choice"] == "none"
        assert body["reasoning"] == transport.calls[0][2]["reasoning"] == {"effort": "none"}
        assert not {"previous_response_id", "conversation"} & body.keys()
        parsed = parse_native_search(
            response, MODEL, _snapshot(), _snapshot().as_of_timestamp, "intent"
        )
        parsed.calls[0]["action"]["queries"].append("changed transient copy")
        assert response["output"][0] == original["output"][0]


@pytest.mark.parametrize("status", ["in_progress", "incomplete", "failed", "cancelled"])
@pytest.mark.parametrize("kind", ["search", "open_page", "find_in_page"])
def test_each_partial_status_ignores_untrusted_payload(status: str, kind: str) -> None:
    response = native(("search", kind, "search"))
    response["output"] = response["output"][:3]
    response["output"][1]["status"] = status
    response["output"][1]["action"].update(
        queries=[None, True, "bad\ud800"], sources=[{"url": "javascript:private"}] * 65
    )
    gateway, transport = adapter([response, memo()])
    (item,) = gateway.research(MODEL, _snapshot())
    assert len(transport.calls) == 2
    assert transport.calls[1][2]["input"][1:-1] == [response["output"][0], response["output"][2]]
    assert "private" not in repr(item)
    provenance = json.loads(item.provenance or "")
    assert provenance[status + "_action_count"] == 1
    assert provenance["completed_search_count"] == 2
    assert provenance["provider_exposed_query_count"] == 0


@pytest.mark.parametrize("status", ["unknown-private", None, 7, True, {}, [], "missing"])
def test_unknown_missing_or_malformed_status_fails(status: Any) -> None:
    response = mixed()
    response["output"][8]["status"] = status
    if status == "missing":
        del response["output"][8]["status"]
    assert_failure(response, "ACTION_STATUS")


def assert_failure(response: Any, code: str, synthesis: Any = None) -> ResearchDiagnostic:
    gateway, transport = adapter([response] + ([synthesis] if synthesis is not None else []))
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(MODEL, _snapshot())
    diagnostic = caught.value.diagnostic
    assert diagnostic is not None and diagnostic.boundary_code == code
    assert len(transport.calls) == (2 if synthesis is not None else 1)
    assert all(
        value not in json.dumps(diagnostic.as_dict())
        for value in [SENTINEL, TRACE, MEMO, "private", "query 0-"]
    )
    return diagnostic


@pytest.mark.parametrize(
    "case,code",
    [
        ("status", "SEARCH_ENVELOPE"),
        ("model", "SEARCH_ENVELOPE"),
        ("id", "SEARCH_ENVELOPE"),
        ("output", "SEARCH_OUTPUT_SHAPE"),
        ("item", "SEARCH_OUTPUT_SHAPE"),
        ("unknown-output", "SEARCH_OUTPUT_SHAPE"),
        ("action", "ACTION_SHAPE"),
        ("action-type", "ACTION_TYPE"),
        ("no-search", "NO_COMPLETED_SEARCH"),
        ("no-completed", "NO_COMPLETED_SEARCH"),
        ("query-shape", "QUERY_STRUCTURE"),
        ("query-invalid", "QUERY_INTEGRITY"),
        ("query-utf8", "QUERY_INTEGRITY"),
        ("query-count", "QUERY_STRUCTURAL_BOUND"),
        ("query-text", "QUERY_STRUCTURAL_BOUND"),
        ("source-shape", "SOURCE_STRUCTURE"),
        ("source-title", "SOURCE_STRUCTURE"),
        ("source-count", "SOURCE_BOUND"),
        ("source-url", "SOURCE_URL"),
        ("source-utf8", "SOURCE_URL"),
        ("source-port", "SOURCE_URL"),
        ("message-shape", "MESSAGE_SHAPE"),
        ("message-integrity", "MESSAGE_INTEGRITY"),
        ("provenance", "PROVENANCE_BOUND"),
        ("passback", "PASSBACK_BOUND"),
        ("action-count", "ACTION_BOUND"),
    ],
)
def test_exact_parser_failure_boundary(case: str, code: str) -> None:
    response = mixed()
    action = response["output"][0]["action"]
    if case == "status":
        response["status"] = "incomplete"
    elif case == "model":
        response["model"] = "private-model"
    elif case == "id":
        response["id"] = "private/id"
    elif case == "output":
        response["output"] = {}
    elif case == "item":
        response["output"].append(None)
    elif case == "unknown-output":
        response["output"].append({"type": "private-tool"})
    elif case == "action":
        response["output"][8]["action"] = None
    elif case == "action-type":
        response["output"][9]["action"]["type"] = "private-tool"
    elif case == "no-search":
        for item in response["output"]:
            item["action"]["type"] = "open_page"
    elif case == "no-completed":
        for item in response["output"][:7]:
            item["status"] = "incomplete"
    elif case == "query-shape":
        action["queries"] = "private-query"
    elif case == "query-invalid":
        action["queries"] = [True]
    elif case == "query-utf8":
        action["queries"] = ["private\ud800"]
    elif case == "query-count":
        action["queries"] = ["q"] * 257
    elif case == "query-text":
        action["queries"] = ["x" * 500] * 129
    elif case == "source-shape":
        action["sources"] = [None]
    elif case == "source-title":
        action["sources"] = [{"url": "https://example.com", "title": "private\ud800"}]
    elif case == "source-count":
        action["sources"] = [{}] * 65
    elif case == "source-url":
        action["sources"] = [{"url": "javascript:private"}]
    elif case == "source-utf8":
        action["sources"] = [{"url": "https://example.com/private\ud800"}]
    elif case == "source-port":
        action["sources"] = [{"url": "https://private.example:bad"}]
    elif case.startswith("message"):
        message = memo()["output"][-1]
        if case == "message-shape":
            message["content"] = []
        else:
            message["content"][0]["text"] = "private\x00"
        response["output"].append(message)
    elif case == "provenance":
        action["sources"] = [
            {"url": f"https://example.com/{i}", "title": "x" * 500} for i in range(64)
        ]
    elif case == "passback":
        response["output"][0]["opaque_restore_token"] = ""
        size = len(json.dumps(response, ensure_ascii=False).encode())
        response["output"][0]["opaque_restore_token"] = "x" * (1_999_900 - size)
    elif case == "action-count":
        response["output"] += [copy.deepcopy(response["output"][0])] * 49
    diagnostic = assert_failure(response, code)
    assert diagnostic.stage == "SEARCH" and diagnostic.synthesis_attempted is False
    if case == "action":
        assert diagnostic.malformed_action_count == 1
    if case == "action-type":
        assert diagnostic.unknown_action_count == 1
    if case.startswith("query-i") or case == "query-utf8":
        assert diagnostic.invalid_query_value_count == 1
    if case == "source-count":
        assert diagnostic.raw_source_record_count == 65
    if case == "unknown-output":
        assert diagnostic.unexpected_output_item_count == 1


@pytest.mark.parametrize(
    "case,code",
    [
        ("envelope", "SYNTHESIS_ENVELOPE"),
        ("output", "SYNTHESIS_OUTPUT_SHAPE"),
        ("message", "SYNTHESIS_MESSAGE"),
        ("memo", "SYNTHESIS_MEMO_INTEGRITY"),
    ],
)
def test_exact_synthesis_boundaries(case: str, code: str) -> None:
    synthesis = memo()
    if case == "envelope":
        synthesis["status"] = "failed"
    elif case == "output":
        synthesis["output"] = {}
    elif case == "message":
        synthesis["output"] = [{"type": "web_search_call"}]
    else:
        synthesis["output"][-1]["content"][0]["text"] = ""
    assert assert_failure(mixed(), code, synthesis).stage == "SYNTHESIS"


def test_failure_metadata_matches_rule_and_mixed_counts() -> None:
    response = mixed()
    response["output"][0]["action"]["queries"][0] = True
    diagnostic = assert_failure(response, "QUERY_INTEGRITY")
    assert diagnostic.web_search_call_count == 16 and diagnostic.search_action_count == 7
    assert diagnostic.completed_action_count == 13
    assert (
        diagnostic.incomplete_action_count
        == diagnostic.failed_action_count
        == diagnostic.in_progress_action_count
        == 1
    )
    assert diagnostic.cancelled_action_count == 0
    assert diagnostic.completed_search_count == 6 and diagnostic.non_completed_search_count == 1
    assert diagnostic.provider_exposed_query_count == 24
    assert diagnostic.raw_source_record_count == diagnostic.unknown_action_count == 0
    with pytest.raises(NativeParseFailure) as caught:
        parse_native_search(response, MODEL, _snapshot(), _snapshot().as_of_timestamp, "intent")
    assert caught.value.boundary_code == diagnostic.boundary_code
    assert caught.value.counts["invalid_query_value_count"] == 1


def test_secret_tainted_body_is_not_reparsed(monkeypatch: pytest.MonkeyPatch) -> None:
    response = mixed()
    response["private"] = SENTINEL
    from ai_infra_quant.integrations.openai_reasoning import deepseek_research_flow as flow

    original = observed_counts

    def guarded(value: object) -> dict[str, int]:
        assert value is None
        return original(value)

    monkeypatch.setattr(flow, "observed_counts", guarded)
    gateway, transport = adapter([response])
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(MODEL, _snapshot())
    diagnostic = caught.value.diagnostic
    assert diagnostic is not None and len(transport.calls) == 1
    assert diagnostic.failure_class == "UNSAFE_RESPONSE" and diagnostic.boundary_code is None
    assert diagnostic.completed_action_count is diagnostic.provider_exposed_query_count is None


@pytest.mark.parametrize("value", [True, -1, 1025, "private", {}, 1.5])
def test_new_diagnostic_fields_reject_untrusted_values(value: Any) -> None:
    for field in [
        "completed_action_count",
        "in_progress_action_count",
        "incomplete_action_count",
        "failed_action_count",
        "cancelled_action_count",
        "completed_search_count",
        "non_completed_search_count",
        "missing_or_unknown_status_count",
        "invalid_query_value_count",
        "malformed_action_count",
        "unexpected_output_item_count",
    ]:
        with pytest.raises(ValueError):
            ResearchDiagnostic(
                "SEARCH", "INVALID_RESPONSE", "deepseek", MODEL.model_id, False, 1, **{field: value}
            )
    with pytest.raises(ValueError):
        ResearchDiagnostic(
            "SEARCH", "INVALID_RESPONSE", "deepseek", MODEL.model_id, False, 1, boundary_code=value
        )


def test_all_boundary_codes_are_explicitly_allowlisted() -> None:
    for code in RESEARCH_BOUNDARY_CODES:
        diagnostic = ResearchDiagnostic(
            "SEARCH", "INVALID_RESPONSE", "deepseek", MODEL.model_id, False, 1, boundary_code=code
        )
        assert diagnostic.as_dict()["boundary_code"] == code
