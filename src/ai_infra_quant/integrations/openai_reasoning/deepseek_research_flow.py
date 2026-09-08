"""One SEARCH and, only for valid tool-only output, one stateless SYNTHESIS."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime
from typing import Any, Literal

from ai_infra_quant.application.paqs_e_models import ModelDescriptor
from ai_infra_quant.application.paqs_e_research import ResearchDiagnostic, ResearchFailure
from ai_infra_quant.core.domain.paqs_e_reasoning import AuxiliaryContextItem
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningFailureKind as Kind
from ai_infra_quant.integrations.openai_reasoning.deepseek_research import (
    final_memo,
    freeze_native_memo,
    memo_provenance,
    parse_native_search,
)

MEMO_INSTRUCTION = (
    "Return one concise factual company/news/earnings/public-event research memo, at most "
    "24000 characters, using only the supplied Security and original Snapshot As-Of intent. "
    "Exclude publications after that cutoff. Frozen Snapshot market facts take precedence; "
    "web prices are not authoritative Snapshot facts. Do not output chain-of-thought, "
    "trading advice or PAQS-E Setup/Trigger/entry analysis. Do not output application JSON "
    "merely to satisfy a schema."
)
SYNTHESIS_INSTRUCTION = (
    "Synthesize the factual memo using only the restored native search results and original "
    "intent. " + MEMO_INSTRUCTION
)


def _safe_id(value: object) -> str | None:
    return (
        value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", value) else None
    )


def _search_counts(response: object) -> dict[str, int]:
    """Count exposed slots, never copy their text. Omit totals with unknowable shapes."""
    if not isinstance(response, dict) or not isinstance(response.get("output"), list):
        return {}
    output = response["output"]
    if len(output) > 128 or any(not isinstance(item, dict) for item in output):
        return {}
    queries = sources = unknown = 0
    queries_known = sources_known = actions_known = True
    for item in output:
        if item.get("type") == "web_search_call":
            action = item.get("action")
            if not isinstance(action, dict):
                queries_known = sources_known = actions_known = False
                continue
            if action.get("type") not in ("search", "open_page", "find_in_page"):
                unknown += 1
            if action.get("type") == "search":
                for field, value in action.items():
                    if field == "queries":
                        if isinstance(value, list):
                            queries = min(1024, queries + len(value))
                        else:
                            queries_known = False
                    elif field == "query":
                        queries = min(1024, queries + 1)
                records = action.get("sources", [])
                if isinstance(records, list):
                    sources = min(1024, sources + len(records))
                else:
                    sources_known = False
        elif item.get("type") == "message":
            parts = item.get("content")
            if not isinstance(parts, list) or len(parts) > 1024:
                sources_known = False
                continue
            for part in parts:
                if not isinstance(part, dict):
                    sources_known = False
                    continue
                annotations = part.get("annotations", [])
                if not isinstance(annotations, list) or len(annotations) > 1024:
                    sources_known = False
                    continue
                for annotation in annotations:
                    if not isinstance(annotation, dict):
                        sources_known = False
                    elif annotation.get("type") == "url_citation":
                        sources = min(1024, sources + 1)
    result = {}
    if queries_known:
        result["provider_exposed_query_count"] = queries
    if sources_known:
        result["raw_source_record_count"] = sources
    if actions_known:
        result["unknown_action_count"] = unknown
    return result


def _diagnostic(
    model: ModelDescriptor,
    stage: Literal["SEARCH", "SYNTHESIS"],
    failure_class: Literal["TRANSPORT_ERROR", "INVALID_RESPONSE", "UNSAFE_RESPONSE", "REFUSAL"],
    response: object,
    count: int,
) -> ResearchDiagnostic:
    # Tainted envelopes are never inspected here. Cap counts; omit unknown strings entirely.
    envelope = response if isinstance(response, dict) else {}
    output = envelope.get("output")
    items = [v for v in output[:129] if isinstance(v, dict)] if isinstance(output, list) else []
    status = envelope.get("status")
    incomplete = envelope.get("incomplete_details")
    reason = incomplete.get("reason") if isinstance(incomplete, dict) else None
    search_counts = _search_counts(response)
    return ResearchDiagnostic(
        stage=stage,
        failure_class=failure_class,
        provider_id=model.provider_id,
        model_id=model.model_id,
        synthesis_attempted=count == 2,
        research_http_request_count=count,
        provider_status=status
        if isinstance(status, str) and status in {"completed", "incomplete", "failed", "cancelled"}
        else None,
        provider_response_id=_safe_id(envelope.get("id")),
        web_search_call_count=sum(v.get("type") == "web_search_call" for v in items),
        search_action_count=sum(
            v.get("type") == "web_search_call"
            and isinstance(v.get("action"), dict)
            and v["action"].get("type") == "search"
            for v in items
        ),
        message_count=sum(v.get("type") == "message" for v in items),
        incomplete_reason=reason
        if isinstance(reason, str) and reason in {"max_output_tokens", "content_filter"}
        else None,
        provider_exposed_query_count=search_counts.get("provider_exposed_query_count"),
        raw_source_record_count=search_counts.get("raw_source_record_count"),
        unknown_action_count=search_counts.get("unknown_action_count"),
    )


def research_native(
    model: ModelDescriptor,
    snapshot: PaqsMarketSnapshot,
    intent: str,
    secret: str,
    post: Callable[[str, str, dict[str, Any]], dict[str, Any]],
    contains_secret: Callable[[object, str], bool],
    now: Callable[[], datetime],
) -> tuple[AuxiliaryContextItem, ...]:
    assert model.research_endpoint is not None
    endpoint = model.research_endpoint
    stage: Literal["SEARCH", "SYNTHESIS"] = "SEARCH"
    count = 0
    safe_response: object = None

    def request(body: dict[str, Any]) -> dict[str, Any]:
        nonlocal count, safe_response
        # Include original intent and instructions in the request-size bound too.
        if len(json.dumps(body, ensure_ascii=False, allow_nan=False).encode()) > 2_000_000:
            raise ValueError("Research request bound")
        count += 1
        safe_response = None
        try:
            value = post(endpoint, secret, body)
        except Exception:
            raise ResearchFailure(
                Kind.PROVIDER_UNAVAILABLE,
                _diagnostic(model, stage, "TRANSPORT_ERROR", None, count),
            ) from None
        if contains_secret(value, secret):
            raise ResearchFailure(
                Kind.INVALID_STRUCTURED_OUTPUT,
                _diagnostic(model, stage, "UNSAFE_RESPONSE", None, count),
            ) from None
        safe_response = value
        if (
            not isinstance(value, dict)
            or value.get("status") != "completed"
            or value.get("error")
            or value.get("model", model.model_id) != model.model_id
            or (value.get("id") is not None and _safe_id(value.get("id")) is None)
        ):
            raise ValueError("Invalid research envelope")
        if value.get("refusal"):
            raise PermissionError("Refusal")
        if len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode()) > 2_000_000:
            raise ValueError("Research response bound")
        return value

    common: dict[str, Any] = {
        "model": model.model_id,
        "store": False,
        "stream": False,
        "reasoning": {"effort": "none"},
    }
    try:
        search_response = request(
            {
                **common,
                "tools": [{"type": "web_search"}],
                "tool_choice": {"type": "web_search"},
                "max_output_tokens": 6000,
                "instructions": "Research with at most four search queries. " + MEMO_INSTRUCTION,
                "input": intent,
            }
        )
        search = parse_native_search(search_response, model, snapshot, now(), intent)
        if search.memo is not None:
            return freeze_native_memo(search, search.memo, synthesis_id=None, synthesis_used=False)
        # Invalid/oversized SEARCH provenance must fail before any further paid request.
        if len(memo_provenance(search, synthesis_id=None, synthesis_used=True)) + 32 >= 24_000:
            raise ValueError("Search provenance bound")
        # No malformed/empty/refused message can reach this branch: parser rejects it.
        stage = "SYNTHESIS"
        synthesis = request(
            {
                **common,
                "tools": [],
                "tool_choice": "none",
                "max_output_tokens": 4000,
                "instructions": SYNTHESIS_INSTRUCTION,
                "input": [
                    {"role": "user", "content": intent},
                    *search.calls,
                    {"role": "user", "content": SYNTHESIS_INSTRUCTION},
                ],
            }
        )
        output = synthesis.get("output")
        if not isinstance(output, list) or len(output) > 128:
            raise ValueError("Synthesis output bound")
        messages = []
        for item in output:
            if not isinstance(item, dict):
                raise ValueError("Malformed synthesis")
            if item.get("type") == "reasoning":
                continue
            # final_memo rejects any tool/unknown output, refusal, or malformed message.
            messages.append(final_memo(item))
        if len(messages) != 1:
            raise ValueError("Expected one synthesis message")
        return freeze_native_memo(
            search, messages[0], synthesis_id=_safe_id(synthesis.get("id")), synthesis_used=True
        )
    except ResearchFailure:
        raise
    except PermissionError:
        raise ResearchFailure(
            Kind.PROVIDER_REFUSAL, _diagnostic(model, stage, "REFUSAL", safe_response, count)
        ) from None
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError):
        raise ResearchFailure(
            Kind.INVALID_STRUCTURED_OUTPUT,
            _diagnostic(model, stage, "INVALID_RESPONSE", safe_response, max(1, count)),
        ) from None
