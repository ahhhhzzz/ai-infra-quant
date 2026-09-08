from __future__ import annotations

import copy
import json
from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from paqs_e_support import MemoryCredentials
from test_paqs_e_runtime import _result, _snapshot

from ai_infra_quant.application.paqs_e_models import ModelCredentials, ModelRegistry
from ai_infra_quant.application.paqs_e_research import ResearchFailure
from ai_infra_quant.application.paqs_e_runtime import (
    PaqsEReasoningRuntime,
    build_reasoning_request,
    load_prompt_package,
    load_strategy_package,
)
from ai_infra_quant.core.domain.paqs_e_reasoning import PaqsEValidationFailure, ValidatedPaqsEResult
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.core.ports.credentials import CredentialStoreUnavailable
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningFailureKind as Kind
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningProviderFailure
from ai_infra_quant.integrations.openai_reasoning.gateway import ModelGateway, normalize_research
from ai_infra_quant.integrations.windows_credentials import WindowsCredentialStore

REGISTRY = ModelRegistry()
SENTINEL = "synthetic-007c1-never-a-real-credential"


class Transport:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.error = False

    def post(self, endpoint: str, secret: str, body: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((endpoint, secret, body))
        if self.error:
            raise RuntimeError(SENTINEL)
        return self.response


def envelope(text: str, surface: str, model_id: str) -> dict[str, Any]:
    if surface == "chat":
        return {
            "id": "synthetic-response",
            "model": model_id,
            "choices": [{"finish_reason": "stop", "message": {"content": text}}],
        }
    return {
        "id": "synthetic-response",
        "model": model_id,
        "status": "completed",
        "output": [
            {"type": "reasoning", "content": [{"text": "synthetic-discarded-trace"}]},
            {"type": "message", "content": [{"type": "output_text", "text": text}]},
        ],
    }


def research_response(model_id: str = "qwen3.8-max") -> dict[str, Any]:
    response = envelope(
        json.dumps(
            {
                "items": [
                    {
                        "url": "https://example.org/earnings",
                        "summary": (
                            "Synthetic source-specific earnings context; "
                            "no market-price replacement."
                        ),
                    }
                ]
            }
        ),
        "responses",
        model_id,
    )
    response["output"].insert(
        0,
        {
            "type": "web_search_call",
            "status": "completed",
            "action": {
                "type": "search",
                "query": "synthetic company earnings",
                "sources": [
                    {
                        "type": "url",
                        "url": "https://example.org/earnings",
                        "title": "Synthetic earnings",
                    }
                ],
            },
        },
    )
    return response


def test_exact_catalog_single_source_routes_slots_and_default() -> None:
    assert [item.display_name for item in REGISTRY.models] == [
        "DeepSeek V4 Flash",
        "DeepSeek V4 Pro",
        "Qwen3.8 Flash",
        "Qwen3.8 Max",
        "Qwen3.7 Plus",
        "GLM-5.2",
        "Kimi K3",
        "Hy4 Preview",
        "GPT-5.6 Luna",
        "GPT-5.6 Terra",
        "GPT-5.6 Sol",
    ]
    assert REGISTRY.default_model_key == "deepseek-v4-flash"
    assert len({item.model_key for item in REGISTRY.models}) == 11
    assert len({item.credential_slot for item in REGISTRY.models}) == 6
    assert all(item.enabled for item in REGISTRY.models)
    for invalid in ("gpt-unapproved", "https://evil.example", "OPENAI", "", "qwen3.8-max "):
        with pytest.raises(ValueError):
            REGISTRY.resolve(invalid)


@pytest.mark.parametrize("model", REGISTRY.models, ids=lambda model: model.model_key)
@pytest.mark.parametrize(
    "scenario", ["success", "malformed", "identity", "refusal", "network", "secret"]
)
def test_every_selected_route_strict_stateless_outcomes(model: Any, scenario: str) -> None:
    request = build_reasoning_request(
        snapshot=_snapshot(), model_id=model.model_id, model_provider=model.provider_id
    )
    result = _result(request)
    if scenario == "identity":
        result = replace(result, identity=replace(result.identity, model_provider="wrong-provider"))
    response = envelope(canonical_json(result), model.api_surface, model.model_id)
    if scenario == "malformed":
        response = envelope(
            '{"explanation":"not a PAQS-E result"}', model.api_surface, model.model_id
        )
    if scenario == "secret":
        response["id"] = SENTINEL
    if scenario == "refusal":
        if model.api_surface == "chat":
            response["choices"][0]["message"]["refusal"] = "declined"
        else:
            response["output"][-1]["content"] = [{"type": "refusal", "refusal": "declined"}]
    transport = Transport(response)
    transport.error = scenario == "network"
    store = MemoryCredentials()
    store.values[model.credential_slot] = SENTINEL
    gateway = ModelGateway(REGISTRY, ModelCredentials(REGISTRY, store), transport)
    outcome = PaqsEReasoningRuntime(gateway).reason(
        request=request, strategy=load_strategy_package(), prompt=load_prompt_package()
    )
    if scenario == "success":
        assert isinstance(outcome, ValidatedPaqsEResult)
        assert outcome.result.identity.model_provider == model.provider_id
    elif scenario == "identity":
        assert isinstance(outcome, PaqsEValidationFailure)
        assert any(issue.code == "IDENTITY_MISMATCH" for issue in outcome.issues)
    else:
        assert isinstance(outcome, ReasoningProviderFailure)
        assert (
            outcome.kind
            == {
                "network": Kind.PROVIDER_UNAVAILABLE,
                "refusal": Kind.PROVIDER_REFUSAL,
                "secret": Kind.INVALID_STRUCTURED_OUTPUT,
                "malformed": Kind.INVALID_STRUCTURED_OUTPUT,
            }[scenario]
        )
    assert len(transport.calls) == 1
    endpoint, secret, body = transport.calls[0]
    assert (endpoint, secret, body["model"]) == (model.endpoint, SENTINEL, model.model_id)
    assert body["tools"] == [] and body["tool_choice"] == "none"
    assert not {"previous_response_id", "conversation", "background"} & body.keys()
    if model.api_surface == "responses":
        assert body["store"] is False
        assert body["text"]["format"]["strict"] is True
        assert body["text"]["format"]["schema"]["additionalProperties"] is False
    else:
        if model.structured_output_mode == "json_schema":
            assert body["response_format"]["type"] == "json_schema"
            assert body["response_format"]["json_schema"]["strict"] is True
            assert body["enable_search"] is False
        else:
            assert body["response_format"] == {"type": "json_object"}
    assert SENTINEL not in json.dumps(body) + str(outcome)
    assert "synthetic-discarded-trace" not in str(outcome)


@pytest.mark.parametrize("model", REGISTRY.models, ids=lambda model: model.model_key)
def test_missing_key_and_unknown_route_never_call_provider(model: Any) -> None:
    transport = Transport({})
    gateway = ModelGateway(REGISTRY, ModelCredentials(REGISTRY, MemoryCredentials()), transport)
    request = build_reasoning_request(
        snapshot=_snapshot(), model_id=model.model_id, model_provider=model.provider_id
    )
    outcome = gateway.reason(
        request=request, strategy=load_strategy_package(), prompt=load_prompt_package()
    )
    assert (
        isinstance(outcome, ReasoningProviderFailure) and outcome.kind == Kind.CONFIGURATION_ERROR
    )
    outcome = gateway.reason(
        request=replace(request, model_id="arbitrary"),
        strategy=load_strategy_package(),
        prompt=load_prompt_package(),
    )
    assert isinstance(outcome, ReasoningProviderFailure)
    assert transport.calls == []


def test_shared_credential_slot_delete_update_and_read_only_openai_fallback() -> None:
    store = MemoryCredentials()
    credentials = ModelCredentials(REGISTRY, store, openai_fallback="synthetic-env-fallback")
    credentials.save("deepseek-v4-flash", SENTINEL)
    assert credentials.secret("deepseek-v4-pro") == SENTINEL
    assert not credentials.status("qwen3.8-max").credential_configured
    credentials.save("deepseek-v4-pro", "synthetic-updated")
    assert credentials.secret("deepseek-v4-flash") == "synthetic-updated"
    credentials.delete("deepseek-v4-flash")
    assert not credentials.status("deepseek-v4-pro").credential_configured
    credentials.save("gpt-5.6-sol", SENTINEL)
    credentials.delete("gpt-5.6-terra")
    assert credentials.secret("gpt-5.6-luna") == "synthetic-env-fallback"
    assert credentials.status("gpt-5.6-sol").credential_source == "server_environment_read_only"
    before = list(store.writes)
    assert SENTINEL not in str(credentials.projection())
    assert store.writes == before


def test_unavailable_windows_backend_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ai_infra_quant.integrations.windows_credentials.sys.platform", "linux")
    store = WindowsCredentialStore(frozenset({"synthetic-slot"}))
    actions: tuple[Callable[[], object], ...] = (
        lambda: store.read("synthetic-slot"),
        lambda: store.save("synthetic-slot", SENTINEL),
        lambda: store.delete("synthetic-slot"),
    )
    for action in actions:
        with pytest.raises(CredentialStoreUnavailable):
            action()
    with pytest.raises(ValueError):
        store.read("unregistered-slot")


def test_research_freezes_auditable_unknown_time_and_excludes_future_sources() -> None:
    model = REGISTRY.resolve("qwen3.8-max")
    snapshot = _snapshot()
    response = research_response()
    now = snapshot.as_of_timestamp + timedelta(seconds=20)
    context = normalize_research(response, model, snapshot, now, "company news")
    assert len(context) == 1
    item = context[0]
    assert item.provenance is not None
    assert item.category == "web_research" and item.as_of_compatible
    assert item.source_timestamp is None and '"publication_time": "unknown"' in item.provenance
    assert "Publication time unknown" in item.provenance
    assert now.isoformat() in item.provenance
    assert "synthetic-discarded-trace" not in canonical_json(context)
    assert (
        normalize_research(response, model, snapshot, now, "company news")[0].context_id
        == item.context_id
    )
    source = response["output"][0]["action"]["sources"][0]
    source["published_at"] = (snapshot.as_of_timestamp - timedelta(hours=1)).isoformat()
    known = normalize_research(response, model, snapshot, now, "news")
    assert known[0].source_timestamp == snapshot.as_of_timestamp - timedelta(hours=1)
    source["published_at"] = now.isoformat()
    with pytest.raises(ValueError, match="No compatible"):
        normalize_research(response, model, snapshot, now, "news")


@pytest.mark.parametrize(
    "corruption",
    ["queries", "calls", "items", "content", "timestamp", "url", "missing", "tool", "duplicate"],
)
def test_research_bounds_and_provenance_fail_closed(corruption: str) -> None:
    response = research_response()
    action = response["output"][0]["action"]
    summary = {"url": "https://example.org/earnings", "summary": "synthetic context"}
    items = [summary]
    if corruption == "queries":
        action["queries"] = ["q"] * 5
    if corruption == "calls":
        response["output"] = [copy.deepcopy(response["output"][0])] * 5 + response["output"][1:]
    if corruption == "items":
        items *= 9
    if corruption == "content":
        summary["summary"] = "x" * 1601
    if corruption == "timestamp":
        action["sources"][0]["published_at"] = "2026-01-01"
    if corruption == "url":
        summary["url"] = "https://invented.example/"
    if corruption == "missing":
        action["sources"] = []
    if corruption == "tool":
        response["output"].insert(0, {"type": "function_call"})
    if corruption == "duplicate":
        items *= 2
    response["output"][-1]["content"][0]["text"] = json.dumps({"items": items})
    with pytest.raises(ValueError):
        normalize_research(
            response, REGISTRY.resolve("qwen3.8-max"), _snapshot(), datetime.now(UTC), "news"
        )


@pytest.mark.parametrize("model", REGISTRY.models, ids=lambda model: model.model_key)
def test_research_selected_model_only_no_retries_and_no_hidden_reasoning_tools(model: Any) -> None:
    transport = Transport(research_response(model.model_id))
    store = MemoryCredentials()
    store.values[model.credential_slot] = SENTINEL
    gateway = ModelGateway(REGISTRY, ModelCredentials(REGISTRY, store), transport)
    if not model.web_research_supported:
        with pytest.raises(ResearchFailure) as caught:
            gateway.research(model, _snapshot())
        assert caught.value.kind == Kind.CONFIGURATION_ERROR and transport.calls == []
        return
    context = gateway.research(model, _snapshot())
    assert len(context) == 1
    assert transport.calls[0][0] == model.research_endpoint
    assert transport.calls[0][2]["model"] == model.model_id
    assert transport.calls[0][2]["tools"] == [{"type": "web_search"}]
    request = build_reasoning_request(
        snapshot=_snapshot(),
        model_id=model.model_id,
        model_provider=model.provider_id,
        auxiliary_context=context,
    )
    transport.response = envelope(
        canonical_json(_result(request)), model.api_surface, model.model_id
    )
    gateway.reason(request=request, strategy=load_strategy_package(), prompt=load_prompt_package())
    assert transport.calls[1][2]["tools"] == []
    assert transport.calls[1][2]["input" if model.api_surface == "responses" else "messages"][-1][
        "content"
    ] == canonical_json(request)
    transport.error = True
    with pytest.raises(ResearchFailure) as caught:
        gateway.research(model, _snapshot())
    assert caught.value.kind == Kind.PROVIDER_UNAVAILABLE
    assert len(transport.calls) == 3 and SENTINEL not in str(caught.value)


@pytest.mark.parametrize(
    "corruption",
    [
        "duplicate",
        "identity",
        "default",
        "shape",
        "field",
        "url",
        "research_url",
        "disabled",
        "missing",
    ],
)
def test_invalid_registry_fails_safely(
    corruption: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data: dict[str, Any] = {
        "default_model_key": REGISTRY.default_model_key,
        "models": [asdict(item) for item in REGISTRY.models],
    }
    model = data["models"][0]
    if corruption == "duplicate":
        data["models"].append(dict(model))
    if corruption == "identity":
        data["models"][1]["model_id"] = model["model_id"]
    if corruption == "default":
        data["default_model_key"] = "unknown"
    if corruption == "shape":
        data["unapproved"] = True
    if corruption == "field":
        model["unapproved"] = True
    if corruption == "url":
        model["endpoint"] = "http://unsafe.example"
    if corruption == "research_url":
        model["research_endpoint"] = "https://different.example/responses"
    if corruption == "disabled":
        model["enabled"] = False
    path = tmp_path / "resources/paqs_e/model_registry.json"
    path.parent.mkdir(parents=True)
    if corruption != "missing":
        path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr("ai_infra_quant.application.paqs_e_models.files", lambda package: tmp_path)
    with pytest.raises(ValueError, match="Model registry is unavailable or invalid") as caught:
        ModelRegistry()
    assert str(tmp_path) not in str(caught.value)


def test_native_citation_only_sources_and_raw_source_bound() -> None:
    response = research_response()
    response["output"][0]["action"]["sources"] = []
    response["output"][-1]["content"][0]["annotations"] = [
        {"type": "url_citation", "url": "https://example.org/earnings", "title": "Native title"}
    ]
    context = normalize_research(
        response, REGISTRY.resolve("deepseek-v4-flash"), _snapshot(), datetime.now(UTC), "news"
    )
    assert context[0].source_label == "Native title"
    response["output"][0]["action"]["sources"] = [
        {"url": f"https://example.org/{index}"} for index in range(65)
    ]
    with pytest.raises(ValueError, match="source bound"):
        normalize_research(
            response, REGISTRY.resolve("deepseek-v4-flash"), _snapshot(), datetime.now(UTC), "news"
        )


@pytest.mark.parametrize("future_place", ["source", "citation"])
def test_conflicting_native_metadata_cannot_erase_future_cutoff(future_place: str) -> None:
    snapshot = _snapshot()
    response = research_response()
    source = response["output"][0]["action"]["sources"][0]
    citation = {**source, "type": "url_citation"}
    source["published_at"] = (snapshot.as_of_timestamp - timedelta(hours=1)).isoformat()
    citation["published_at"] = source["published_at"]
    selected = source if future_place == "source" else citation
    selected["published_at"] = (snapshot.as_of_timestamp + timedelta(seconds=1)).isoformat()
    response["output"][-1]["content"][0]["annotations"] = [citation]
    with pytest.raises(ValueError, match="No compatible"):
        normalize_research(
            response, REGISTRY.resolve("qwen3.8-max"), snapshot, datetime.now(UTC), "news"
        )
