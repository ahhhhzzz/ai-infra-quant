from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, replace
from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest
from paqs_e_support import MemoryCredentials
from test_paqs_e_model_gateway import REGISTRY, SENTINEL, Transport, envelope, research_response
from test_paqs_e_runtime import _result, _snapshot

from ai_infra_quant.application.paqs_e_models import ModelCredentials, ModelDescriptor
from ai_infra_quant.application.paqs_e_runtime import (
    PaqsEReasoningRuntime,
    build_reasoning_request,
    load_prompt_package,
    load_strategy_package,
    project_snapshot_price_facts,
    validate_reasoning_result,
)
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import CanonicalMarketState
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    FreshnessStatus,
    PaqsEValidationFailure,
    PriceSessionType,
    ValidatedPaqsEResult,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.integrations.openai_reasoning.gateway import ModelGateway, normalize_research


@pytest.mark.parametrize(
    "actions",
    [
        [],
        ["open_page"],
        ["open_page", "find_in_page"],
        ["open_page", "find_in_page"] * 4 + ["open_page"],
    ],
)
def test_deepseek_documented_page_actions_keep_native_evidence(actions: list[str]) -> None:
    model = REGISTRY.resolve("deepseek-v4-flash")
    response = research_response(model.model_id)
    for index, action in enumerate(actions, start=1):
        response["output"].insert(
            index,
            {
                "type": "web_search_call",
                "status": "completed",
                "action": {
                    "type": action,
                    "url": "https://untrusted.example/ignored",
                    "query": "ignored page query",
                    "sources": [{"url": "https://untrusted.example/ignored"}],
                },
            },
        )
    snapshot = _snapshot()
    items = normalize_research(response, model, snapshot, snapshot.as_of_timestamp, "synthetic")
    provenance = json.loads(items[0].provenance or "{}")
    assert provenance["queries"] == ["synthetic company earnings"]
    assert provenance["url"] == "https://example.org/earnings"
    assert "untrusted" not in canonical_json(asdict(items[0]))
    assert "synthetic-discarded-trace" not in canonical_json(asdict(items[0]))
    assert items[0].source_timestamp is None
    assert provenance["publication_time"] == "unknown"
    assert "cannot be independently confirmed" in provenance["limitation"]


@pytest.mark.parametrize(
    "fault",
    [
        "queries",
        "actions",
        "unknown",
        "no_search",
        "smuggle",
        "future",
        "raw_sources",
        "other_provider",
        "incomplete",
    ],
)
def test_deepseek_compatibility_does_not_relax_provenance_or_bounds(fault: str) -> None:
    model = REGISTRY.resolve("deepseek-v4-flash")
    response = research_response(model.model_id)
    search = response["output"][0]
    page: dict[str, Any] = {
        "type": "web_search_call",
        "status": "completed",
        "action": {
            "type": "open_page",
            "url": "https://untrusted.example/smuggled",
            "sources": [{"url": "https://untrusted.example/smuggled"}],
        },
    }
    response["output"].insert(1, page)
    if fault == "queries":
        search["action"]["queries"] = ["query"] * 5
    elif fault == "actions":
        response["output"][1:1] = [copy.deepcopy(page) for _ in range(9)]
    elif fault == "unknown":
        page["action"]["type"] = "arbitrary"
    elif fault == "no_search":
        response["output"].remove(search)
    elif fault == "smuggle":
        response["output"][-1]["content"][0]["text"] = json.dumps(
            {"items": [{"url": page["action"]["url"], "summary": "invented"}]}
        )
    elif fault == "future":
        search["action"]["sources"][0]["published_at"] = (
            _snapshot().as_of_timestamp + timedelta(seconds=1)
        ).isoformat()
    elif fault == "raw_sources":
        search["action"]["sources"] *= 65
    elif fault == "other_provider":
        model = REGISTRY.resolve("qwen3.8-max")
    elif fault == "incomplete":
        page["status"] = "incomplete"
    snapshot = _snapshot()
    with pytest.raises(ValueError):
        normalize_research(response, model, snapshot, snapshot.as_of_timestamp, "synthetic")


@pytest.mark.parametrize("model", REGISTRY.models, ids=lambda model: model.model_key)
def test_strict_parse_then_projection_fixes_factual_echoes_for_every_model(
    model: ModelDescriptor,
) -> None:
    request = build_reasoning_request(
        snapshot=_snapshot(), model_provider=model.provider_id, model_id=model.model_id
    )
    original = _result(request)
    bad = replace(
        original,
        price_references=replace(
            original.price_references,
            current_price_reference=replace(
                original.price_references.current_price_reference,
                price=Decimal("999"),
                timestamp=request.snapshot_as_of_timestamp - timedelta(days=1),
                freshness_status=FreshnessStatus.STALE,
                session_type=PriceSessionType.POST,
            ),
        ),
    )
    direct = validate_reasoning_result(request=request, result=bad)
    assert isinstance(direct, PaqsEValidationFailure)
    assert {
        "CURRENT_PRICE_FACT_MISMATCH",
        "CURRENT_PRICE_FRESHNESS_MISMATCH",
        "CURRENT_PRICE_SESSION_MISMATCH",
    } <= {issue.code for issue in direct.issues}
    store = MemoryCredentials()
    store.save(model.credential_slot, SENTINEL)
    transport = Transport(envelope(canonical_json(asdict(bad)), model.api_surface, model.model_id))
    gateway = ModelGateway(REGISTRY, ModelCredentials(REGISTRY, store), transport)
    result = PaqsEReasoningRuntime(gateway).reason(
        request=request, strategy=load_strategy_package(), prompt=load_prompt_package()
    )
    assert isinstance(result, ValidatedPaqsEResult)
    assert result.result == original
    assert bad.price_references.current_price_reference.freshness_status is FreshnessStatus.STALE
    assert len(transport.calls) == 1


def test_projection_changes_only_current_and_eligible_entry_four_fact_fields() -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="synthetic")
    original = _result(request)
    for eligible in (False, True):
        entry = replace(
            original.price_references.executable_entry_reference,
            eligible=eligible,
            price=Decimal("999"),
            timestamp=None,
            session_type=PriceSessionType.POST,
            freshness_status=FreshnessStatus.STALE,
        )
        bad = replace(
            original,
            price_references=replace(original.price_references, executable_entry_reference=entry),
        )
        projected = project_snapshot_price_facts(request=request, result=bad)
        assert replace(projected, price_references=bad.price_references) == bad
        effective = projected.price_references.executable_entry_reference
        assert effective.eligible is eligible and effective.policy_basis == entry.policy_basis
        if eligible:
            current = projected.price_references.current_price_reference
            assert (
                effective.price,
                effective.timestamp,
                effective.session_type,
                effective.freshness_status,
            ) == (current.price, current.timestamp, current.session_type, current.freshness_status)
        else:
            assert effective == entry


def test_deepseek_page_research_is_frozen_before_tool_free_reasoning() -> None:
    model = REGISTRY.resolve("deepseek-v4-flash")
    snapshot = _snapshot()
    response = research_response(model.model_id)
    response["output"].insert(
        1, {"type": "web_search_call", "status": "completed", "action": {"type": "open_page"}}
    )
    store = MemoryCredentials()
    store.save(model.credential_slot, SENTINEL)
    transport = Transport(response)
    gateway = ModelGateway(REGISTRY, ModelCredentials(REGISTRY, store), transport)
    auxiliary = gateway.research(model=model, snapshot=snapshot)
    request = build_reasoning_request(
        snapshot=snapshot,
        model_provider=model.provider_id,
        model_id=model.model_id,
        auxiliary_context=auxiliary,
    )
    transport.response = envelope(
        canonical_json(asdict(_result(request))), model.api_surface, model.model_id
    )
    result = PaqsEReasoningRuntime(gateway).reason(
        request=request, strategy=load_strategy_package(), prompt=load_prompt_package()
    )
    assert isinstance(result, ValidatedPaqsEResult)
    assert len(transport.calls) == 2
    body = transport.calls[-1][2]
    assert body["tools"] == [] and body["tool_choice"] == "none"
    assert request.auxiliary_context == auxiliary
    user_input = body["input"][-1]["content"]
    assert json.loads(user_input)["auxiliary_context"] == json.loads(canonical_json(auxiliary))


@pytest.mark.parametrize("status", list(DataAvailabilityStatus))
@pytest.mark.parametrize("state", [None, *CanonicalMarketState])
def test_projection_matches_validator_mapping_and_cannot_grant_market_eligibility(
    status: DataAvailabilityStatus, state: CanonicalMarketState | None
) -> None:
    snapshot = _snapshot()
    quote = replace(snapshot.current_price_reference, status=status)
    market = replace(
        snapshot.market_state_reference,
        canonical_state=state,
        provider_state=state.value if state else None,
        status=DataAvailabilityStatus.AVAILABLE if state else DataAvailabilityStatus.UNAVAILABLE,
    )
    payload = snapshot.canonical_hash_payload()
    payload.update(current_price_reference=quote, market_state_reference=market)
    snapshot = replace(
        snapshot,
        current_price_reference=quote,
        market_state_reference=market,
        snapshot_hash=hashlib.sha256(canonical_json(payload).encode()).hexdigest(),
    )
    request = build_reasoning_request(snapshot=snapshot, model_id="synthetic")
    original = _result(request)
    original = replace(
        original,
        price_references=replace(
            original.price_references,
            executable_entry_reference=replace(
                original.price_references.executable_entry_reference, eligible=True
            ),
        ),
    )
    projected = project_snapshot_price_facts(request=request, result=original)
    validation = validate_reasoning_result(request=request, result=projected)
    codes = (
        {issue.code for issue in validation.issues}
        if isinstance(validation, PaqsEValidationFailure)
        else set()
    )
    assert not any(code.startswith("CURRENT_PRICE_") for code in codes)
    assert (
        projected.price_references.executable_entry_reference.eligible
        == original.price_references.executable_entry_reference.eligible
    )
    if original.price_references.executable_entry_reference.eligible:
        if state is not CanonicalMarketState.OPEN:
            assert "EXECUTABLE_ENTRY_MARKET_NOT_OPEN" in codes
        if status is not DataAvailabilityStatus.AVAILABLE:
            assert "EXECUTABLE_ENTRY_FACT_MISMATCH" in codes
            assert "EXECUTABLE_ENTRY_NOT_FRESH" in codes
