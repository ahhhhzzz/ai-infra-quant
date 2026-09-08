from __future__ import annotations

import json
from dataclasses import replace
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
from ai_infra_quant.application.paqs_e_runtime import load_strategy_package
from ai_infra_quant.core.domain.paqs_e_narrative import NarrativeFailure, NarrativeSuccess
from ai_infra_quant.core.domain.paqs_e_narrative import NarrativeFailureKind as Kind
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.integrations.openai_reasoning.narrative import NarrativeGateway

TEXT = "  # 最终分析\nContext 与 Trigger 尚待确认。{仅是文本}\n<script>alert(1)</script>\n"


def request_for(model: Any) -> Any:
    return build_narrative_request(
        snapshot=_snapshot(),
        model_provider=model.provider_id,
        model_id=model.model_id,
        strategy=load_strategy_package(),
        prompt=load_narrative_prompt(),
    )


def call(
    model: Any, response: Any, *, missing: bool = False, network: bool = False
) -> tuple[Any, Transport]:
    store = MemoryCredentials()
    if not missing:
        store.values[model.credential_slot] = SENTINEL
    transport = Transport(response)
    transport.error = network
    gateway = NarrativeGateway(REGISTRY, ModelCredentials(REGISTRY, store), transport)
    outcome = gateway.reason_text(
        request=request_for(model), strategy=load_strategy_package(), prompt=load_narrative_prompt()
    )
    return outcome, transport


@pytest.mark.parametrize("model", REGISTRY.models, ids=lambda model: model.model_key)
@pytest.mark.parametrize(
    "text",
    [TEXT, '{"not": "a PAQS-E schema"}', "短答。", "文" * 100000],
    ids=["prose", "json-as-text", "short", "max-length"],
)
def test_all_models_return_exact_plain_final_text_without_structured_output(
    model: Any, text: str
) -> None:
    outcome, transport = call(model, envelope(text, model.api_surface, model.model_id))
    assert outcome == NarrativeSuccess(text, "synthetic-response")
    assert len(transport.calls) == 1
    endpoint, secret, body = transport.calls[0]
    assert endpoint == model.endpoint and secret == SENTINEL
    assert body["tools"] == [] and body["tool_choice"] == "none" and body["stream"] is False
    assert (
        not {"response_format", "text", "previous_response_id", "conversation", "background"}
        & body.keys()
    )
    if model.api_surface == "responses":
        assert body["store"] is False
        payload = json.loads(body["input"][-1]["content"])
        assert body["instructions"] == load_narrative_prompt().content
    else:
        payload = json.loads(body["messages"][-1]["content"])
        assert body["messages"][0]["content"] == load_narrative_prompt().content
    assert payload["request_schema_version"] == "paqs-e-narrative-request-v1"
    assert payload["output_format_version"] == "paqs-e-narrative-markdown-v1"
    assert "output_schema_version" not in payload
    assert payload["auxiliary_context"] == []
    assert SENTINEL not in canonical_json(outcome)
    assert "synthetic-discarded-trace" not in canonical_json(outcome)


@pytest.mark.parametrize("model", REGISTRY.models, ids=lambda model: model.model_key)
@pytest.mark.parametrize(
    "scenario",
    [
        "empty",
        "whitespace",
        "oversize",
        "nonstring",
        "control",
        "surrogate",
        "model",
        "secret",
        "secret_id",
        "id",
        "refusal",
        "incomplete",
        "tool",
        "failed",
        "network",
        "missing",
        "no_final",
        "multiple",
        "cancelled",
        "wrong-role",
        "unknown-status",
    ],
)
def test_all_models_fail_closed_without_raw_response_or_retry(model: Any, scenario: str) -> None:
    expected = Kind.INVALID_FINAL_TEXT
    text: Any = {
        "empty": "",
        "whitespace": " \n",
        "oversize": "x" * 100001,
        "nonstring": {},
        "control": "bad\x00text",
        "surrogate": "\ud800",
        "secret": SENTINEL,
    }.get(scenario, TEXT)
    response = envelope(text, model.api_surface, model.model_id)
    if scenario == "model":
        response["model"] = "unapproved"
    if scenario == "secret_id":
        response["id"] = SENTINEL
    if scenario == "id":
        response["id"] = "unsafe\nidentifier"
    if scenario in {"failed", "network"}:
        response["error"] = {"message": "raw provider diagnostic"}
        expected = Kind.PROVIDER_UNAVAILABLE
    if scenario == "missing":
        expected = Kind.CONFIGURATION_ERROR
    if scenario == "refusal":
        expected = Kind.PROVIDER_REFUSAL
        if model.api_surface == "chat":
            response["choices"][0]["message"]["refusal"] = "private refusal"
        else:
            response["output"][-1]["content"] = [{"type": "refusal", "refusal": "private refusal"}]
    if scenario == "incomplete":
        expected = Kind.PROVIDER_INCOMPLETE
        if model.api_surface == "chat":
            response["choices"][0]["finish_reason"] = "length"
        else:
            response["status"] = "incomplete"
    if scenario == "cancelled":
        expected = Kind.PROVIDER_INCOMPLETE
        response["status"] = "cancelled"
    if scenario == "wrong-role":
        if model.api_surface == "chat":
            response["choices"][0]["message"]["role"] = "user"
        else:
            response["output"][-1]["role"] = "user"
    if scenario == "unknown-status":
        if model.api_surface == "chat":
            response["choices"][0]["finish_reason"] = "unknown"
        else:
            response.pop("status")
    if scenario == "tool":
        if model.api_surface == "chat":
            response["choices"][0]["message"]["tool_calls"] = [{}]
        else:
            response["output"].append({"type": "function_call"})
    if scenario == "no_final":
        if model.api_surface == "chat":
            response["choices"][0]["message"] = {"reasoning_content": "hidden"}
        else:
            response["output"] = response["output"][:1]
    if scenario == "multiple":
        if model.api_surface == "chat":
            response["choices"] *= 2
        else:
            response["output"] += response["output"][-1:]
    outcome, transport = call(
        model, response, missing=scenario == "missing", network=scenario == "network"
    )
    assert outcome == NarrativeFailure(expected)
    assert len(transport.calls) == (0 if scenario == "missing" else 1)
    assert SENTINEL not in canonical_json(outcome)
    assert "raw provider diagnostic" not in outcome.reason
    assert "private refusal" not in outcome.reason


@pytest.mark.parametrize(
    "changes",
    [
        dict(symbol="wrong"),
        dict(output_format_version="legacy"),
        dict(request_schema_version="legacy"),
        dict(web_research=True),
        dict(prompt_content_sha256="wrong"),
    ],
)
def test_narrative_request_enforces_frozen_identity_and_version(changes: Any) -> None:
    with pytest.raises(ValueError):
        replace(request_for(REGISTRY.models[0]), **changes)
