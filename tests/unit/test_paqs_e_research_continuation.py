from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from paqs_e_support import MemoryCredentials
from test_paqs_e_model_gateway import REGISTRY, SENTINEL, envelope
from test_paqs_e_native_research import MEMO, MODEL, native
from test_paqs_e_runtime import _snapshot

from ai_infra_quant.application.paqs_e_models import ModelCredentials
from ai_infra_quant.application.paqs_e_research import ResearchDiagnostic, ResearchFailure
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.integrations.openai_reasoning.gateway import ModelGateway

TRACE = "synthetic-hidden-reasoning-never-retained"


def tool_only() -> dict[str, Any]:
    response = native(("search",) + ("open_page", "find_in_page") * 5)
    response["output"] = [v for v in response["output"] if v["type"] == "web_search_call"]
    for index, item in enumerate(response["output"]):
        item.update(id=f"synthetic-call-{index}", opaque_restore_token=f"native-token-{index}")
    response["output"].append({"type": "reasoning", "encrypted_content": TRACE})
    return response


def memo() -> dict[str, Any]:
    response = envelope(MEMO, "responses", MODEL.model_id)
    response["id"] = "synthetic-synthesis-id"
    response["output"].insert(0, {"type": "reasoning", "summary": TRACE})
    return response


class SequenceTransport:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def post(self, endpoint: str, secret: str, body: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((endpoint, secret, copy.deepcopy(body)))
        value = self.responses[len(self.calls) - 1]
        if isinstance(value, Exception):
            raise value
        return value  # type: ignore[no-any-return]


def adapter(responses: list[Any]) -> tuple[ModelGateway, SequenceTransport]:
    store = MemoryCredentials()
    store.values[MODEL.credential_slot] = SENTINEL
    transport = SequenceTransport(responses)
    return ModelGateway(REGISTRY, ModelCredentials(REGISTRY, store), transport), transport


@pytest.mark.parametrize("count", [1, 11, 64])
def test_direct_memo_accepts_local_action_bound_without_synthesis(count: int) -> None:
    gateway, transport = adapter([native(("search",) + ("open_page",) * (count - 1))])
    (item,) = gateway.research(MODEL, _snapshot())
    provenance = json.loads(item.provenance or "")
    assert item.content == MEMO and len(transport.calls) == 1
    assert provenance["web_search_call_count"] == count
    assert provenance["search_action_count"] == 1
    assert provenance["synthesis_used"] is False
    assert provenance["research_http_request_count"] == 1


def test_observed_eleven_tool_only_calls_pass_back_as_is_once_and_freeze_only_memo() -> None:
    search = tool_only()
    original = copy.deepcopy(search)
    gateway, transport = adapter([search, memo()])
    (item,) = gateway.research(MODEL, _snapshot())
    assert search == original and len(transport.calls) == 2
    first, second = [call[2] for call in transport.calls]
    assert first["tools"] == [{"type": "web_search"}]
    assert first["tool_choice"] == {"type": "web_search"}
    assert first["max_output_tokens"] == 6000
    assert second["tools"] == [] and second["tool_choice"] == "none"
    assert second["max_output_tokens"] == 4000
    assert second["input"][0] == {"role": "user", "content": first["input"]}
    assert second["input"][1:-1] == search["output"][:-1]
    assert second["input"][-1]["role"] == "user"
    assert "restored native search results" in second["input"][-1]["content"]
    for endpoint, secret, body in transport.calls:
        assert endpoint == MODEL.research_endpoint and secret == SENTINEL
        assert body["model"] == MODEL.model_id
        assert body["reasoning"] == {"effort": "none"}
        assert body["store"] is False and body["stream"] is False
        assert (
            not {"previous_response_id", "conversation", "background", "text", "response_format"}
            & body.keys()
        )
        assert TRACE not in json.dumps(body)
    assert item.content == MEMO
    evidence = canonical_json(item)
    assert all(
        value not in evidence
        for value in [TRACE, SENTINEL, "opaque_restore_token", 'web_search_call"']
    )
    provenance = json.loads(item.provenance or "")
    assert provenance["web_search_call_count"] == 11
    assert provenance["search_action_count"] == 1
    assert provenance["search_response_status"] == "completed"
    assert provenance["search_provider_response_id"] == search["id"]
    assert provenance["synthesis_provider_response_id"] == "synthetic-synthesis-id"
    assert provenance["synthesis_used"] is True and provenance["research_http_request_count"] == 2


def corrupt(response: dict[str, Any], case: str) -> object:
    if case == "network":
        return RuntimeError(SENTINEL + TRACE + MEMO)
    if case == "not-object":
        return []
    if case in {"incomplete", "failed", "cancelled"}:
        response["status"] = case
        response["incomplete_details"] = {"reason": "max_output_tokens"}
    elif case == "error":
        response["error"] = {"message": "synthetic-raw-provider-body"}
    elif case == "model":
        response["model"] = "other-model"
    elif case == "id":
        response["id"] = "unsafe\nresponse"
    elif case == "secret":
        response["id"] = SENTINEL
    elif case == "tool":
        response["output"].insert(0, {"type": "function_call", "arguments": "raw-provider-body"})
    elif case == "refusal":
        response["refusal"] = "synthetic-refusal-body"
    elif case == "output-limit":
        response["output"] += [{"type": "reasoning", "summary": TRACE}] * 129
    elif case == "action-limit":
        response["output"] = [copy.deepcopy(response["output"][0])] * 65
    elif case == "no-search":
        response["output"][0]["action"]["type"] = "open_page"
    elif case == "unknown-action":
        response["output"][0]["action"]["type"] = "unknown"
    elif case == "action-incomplete":
        response["output"][0]["status"] = "incomplete"
    elif case == "query-limit":
        response["output"][0]["action"]["queries"] = ["actual"] * 5
    elif case == "passback-limit":
        response["output"][0]["restore"] = "x" * 2_000_001
    elif case == "source-limit":
        response["output"][0]["action"]["sources"] = [{"url": "https://example.org"}] * 65
    elif case == "missing":
        response["output"] = []
    elif case == "multiple":
        response["output"].append(copy.deepcopy(response["output"][-1]))
    elif case == "empty-message":
        response["output"][-1]["content"] = []
    elif case == "role":
        response["output"][-1]["role"] = "user"
    elif case == "message-incomplete":
        response["output"][-1]["status"] = "incomplete"
    elif case == "part-refusal":
        response["output"][-1]["content"] = [{"type": "refusal", "refusal": "private"}]
    elif case in {"empty", "oversize", "capsule", "control", "utf8"}:
        response["output"][-1]["content"][0]["text"] = {
            "empty": " \n",
            "oversize": "x" * 24001,
            "capsule": "中" * 24000,
            "control": "bad\x00text",
            "utf8": "bad\ud800text",
        }[case]
    return response


COMMON = [
    "network",
    "not-object",
    "incomplete",
    "failed",
    "cancelled",
    "error",
    "model",
    "id",
    "secret",
    "tool",
    "refusal",
    "output-limit",
]
MEMO_CASES = [
    "missing",
    "multiple",
    "empty-message",
    "role",
    "message-incomplete",
    "part-refusal",
    "empty",
    "oversize",
    "capsule",
    "control",
    "utf8",
]


@pytest.mark.parametrize(
    "case",
    COMMON
    + MEMO_CASES
    + [
        "action-limit",
        "no-search",
        "unknown-action",
        "action-incomplete",
        "query-limit",
        "passback-limit",
        "source-limit",
    ],
)
def test_invalid_search_never_synthesizes_and_has_safe_diagnostic(case: str) -> None:
    gateway, transport = adapter([corrupt(native(), case)])
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(MODEL, _snapshot())
    assert len(transport.calls) == 1
    assert caught.value.diagnostic is not None
    diagnostic = caught.value.diagnostic.as_dict()
    assert diagnostic["stage"] == "SEARCH" and diagnostic["research_http_request_count"] == 1
    assert diagnostic["synthesis_attempted"] is False
    assert all(
        value not in json.dumps(diagnostic)
        for value in [SENTINEL, TRACE, MEMO, "raw-provider-body", "synthetic-refusal-body"]
    )
    if case == "secret":
        assert "provider_response_id" not in diagnostic


@pytest.mark.parametrize("case", COMMON + MEMO_CASES + ["web-tool"])
def test_invalid_synthesis_fails_without_retry_or_final_reasoning(case: str) -> None:
    response = memo()
    if case == "web-tool":
        response["output"].insert(0, tool_only()["output"][0])
    gateway, transport = adapter([tool_only(), corrupt(response, case)])
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(MODEL, _snapshot())
    assert len(transport.calls) == 2
    assert caught.value.diagnostic is not None
    diagnostic = caught.value.diagnostic.as_dict()
    assert diagnostic["stage"] == "SYNTHESIS"
    assert diagnostic["synthesis_attempted"] is True
    assert diagnostic["research_http_request_count"] == 2
    assert all(
        value not in json.dumps(diagnostic)
        for value in [SENTINEL, TRACE, MEMO, "raw-provider-body", "synthetic-refusal-body"]
    )


@pytest.mark.parametrize(
    "reason", ["max_output_tokens", "content_filter", "raw-body", TRACE, "x" * 81, ["bad"]]
)
def test_only_fixed_incomplete_reasons_enter_diagnostics(reason: Any) -> None:
    response = tool_only()
    response.update(status="incomplete", incomplete_details={"reason": reason})
    gateway, _ = adapter([response])
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(MODEL, _snapshot())
    assert caught.value.diagnostic is not None
    expected = reason if reason in ("max_output_tokens", "content_filter") else None
    assert caught.value.diagnostic.incomplete_reason == expected


def test_diagnostic_is_immutable_and_rejects_unbounded_fields() -> None:
    with pytest.raises(ValueError):
        ResearchDiagnostic(
            "SEARCH", "INVALID_RESPONSE", "deepseek", MODEL.model_id, False, 1, message_count=130
        )
