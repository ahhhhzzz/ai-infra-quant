"""Bounded native DeepSeek research memo; never infer source authority from prose."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from ai_infra_quant.application.paqs_e_models import ModelDescriptor
from ai_infra_quant.core.domain.paqs_e_reasoning import AuxiliaryContextItem
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot

LIMITATION = (
    "Provider-native web research memo. Source URLs and/or publication times were not fully "
    "exposed by the provider response; cutoff compliance was requested but cannot be "
    "independently verified for every memo statement. Frozen Snapshot market facts take precedence."
)


@dataclass(frozen=True)
class NativeSearch:
    memo: str | None
    provenance: dict[str, Any]
    calls: list[dict[str, Any]]  # Transient transport items; never part of frozen evidence.


def final_memo(item: dict[str, Any]) -> str:
    if item.get("refusal"):
        raise PermissionError("Refusal")
    if (
        item.get("type") != "message"
        or item.get("status", "completed") != "completed"
        or item.get("role", "assistant") != "assistant"
        or item.get("tool_calls")
        or item.get("function_call")
    ):
        raise ValueError("Unexpected message")
    parts = item.get("content")
    if not isinstance(parts, list) or len(parts) != 1 or not isinstance(parts[0], dict):
        raise ValueError("Expected one visible memo")
    part = parts[0]
    if part.get("type") == "refusal":
        raise PermissionError("Refusal")
    text = part.get("text")
    if (
        part.get("type") not in {"output_text", "text"}
        or not isinstance(text, str)
        or not text.strip()
        or len(text) > 24_000
        or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", text)
    ):
        raise ValueError("Memo integrity bound")
    text.encode("utf-8", errors="strict")
    return text


def parse_native_search(
    response: dict[str, Any],
    model: ModelDescriptor,
    snapshot: PaqsMarketSnapshot,
    retrieved_at: datetime,
    intent: str,
) -> NativeSearch:
    if response.get("status") != "completed" or response.get("error"):
        raise ValueError("Incomplete research")
    response_id = response.get("id")
    if response_id is not None and (
        not isinstance(response_id, str)
        or re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", response_id) is None
    ):
        raise ValueError("Unsafe response identity")
    output = response.get("output")
    if not isinstance(output, list) or len(output) > 128:
        raise ValueError("Malformed research")
    texts: list[str] = []
    actions: list[str] = []
    queries: list[str] = []
    query_count = query_characters = captured_characters = 0
    query_capture_complete = True
    records: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []

    def capture_queries(values: object) -> None:
        nonlocal query_count, query_characters, captured_characters, query_capture_complete
        if not isinstance(values, list) or query_count + len(values) > 256:
            raise ValueError("Structural query count bound")
        for query in values:
            if (
                not isinstance(query, str)
                or not query.strip()
                or len(query) > 500
                or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", query)
            ):
                raise ValueError("Query integrity bound")
            query.encode("utf-8", errors="strict")
            query_count += 1
            query_characters += len(query)
            if query_characters > 64_000:
                raise ValueError("Structural query character bound")
            # Capture a whole-query prefix only; validate/count even after capture stops.
            if (
                query_capture_complete
                and len(queries) < 16
                and captured_characters + len(query) <= 4000
            ):
                queries.append(query)
                captured_characters += len(query)
            else:
                query_capture_complete = False

    def remember(values: object) -> None:
        if not isinstance(values, list) or any(not isinstance(v, dict) for v in values):
            raise ValueError("Malformed sources")
        records.extend(values)
        if len(records) > 64:
            raise ValueError("Raw source bound")

    for item in output:
        if not isinstance(item, dict):
            raise ValueError("Malformed output")
        kind = item.get("type")
        if kind == "reasoning":
            continue  # Deliberately omit hidden reasoning and encrypted transcripts.
        if kind == "web_search_call":
            action = item.get("action")
            if item.get("status") != "completed" or not isinstance(action, dict):
                raise ValueError("Incomplete action")
            action_type = action.get("type")
            if action_type not in {"search", "open_page", "find_in_page"}:
                raise ValueError("Unknown action")
            actions.append(action_type)
            if len(actions) > 64:
                raise ValueError("Action bound")
            calls.append(deepcopy(item))
            if action_type == "search":
                # Both native forms count when exposed; preserve their received order.
                for field, value in action.items():
                    if field == "queries":
                        capture_queries(value)
                    elif field == "query":
                        capture_queries([value])
                remember(action.get("sources", []))
            continue
        texts.append(final_memo(item))
        for part in item["content"]:
            annotations = part.get("annotations", [])
            if not isinstance(annotations, list):
                raise ValueError("Malformed annotations")
            for annotation in annotations:
                if not isinstance(annotation, dict) or annotation.get("type") != "url_citation":
                    raise ValueError("Unexpected annotation")
                remember([annotation])
    if "search" not in actions or len(texts) > 1:
        raise ValueError("Missing search or final memo")
    sources: dict[str, dict[str, str]] = {}
    future: set[str] = set()
    for record in records:
        url = record.get("url")
        if (
            not isinstance(url, str)
            or not 0 < len(url) <= 1000
            or re.search(r"[\s\x00-\x1f\x7f\\]", url)
        ):
            raise ValueError("Unsafe source URL")
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError("Unsafe source URL")
        _ = parsed.port  # Reject malformed ports, too.
        hostname = parsed.hostname
        if ":" in hostname:
            ipaddress.IPv6Address(hostname)
        else:
            encoded_host = hostname.encode("idna").decode("ascii").rstrip(".")
            if len(encoded_host) > 253 or any(
                re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label) is None
                for label in encoded_host.split(".")
            ):
                raise ValueError("Malformed source hostname")
        source = sources.setdefault(url, {"url": url})
        title = record.get("title")
        if title is not None:
            if not isinstance(title, str) or len(title) > 500:
                raise ValueError("Source title bound")
            source["title"] = title
        for field in ("published_at", "publication_date"):
            value = record.get(field)
            if not isinstance(value, str):
                continue
            try:
                published = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                continue
            if published.tzinfo is None or published.utcoffset() is None:
                continue
            if published > snapshot.as_of_timestamp:
                future.add(url)
            else:
                source["publication_time"] = published.astimezone(UTC).isoformat()
    return NativeSearch(
        memo=texts[0] if texts else None,
        calls=calls,
        provenance={
            "provider": model.provider_id,
            "model": model.model_id,
            "provider_response_id": response_id,
            "retrieved_at": retrieved_at.isoformat(),
            "intent": intent,
            "snapshot_as_of": snapshot.as_of_timestamp.isoformat(),
            "native_action_count": len(actions),
            "search_response_status": "completed",
            "search_provider_response_id": response_id,
            "web_search_call_count": len(actions),
            "search_action_count": actions.count("search"),
            "action_types": actions,
            "queries": queries,
            "provider_exposed_query_count": query_count,
            "query_capture_complete": query_capture_complete,
            "sources": [source for url, source in sources.items() if url not in future],
            "excluded_future_source_count": len(future),
            "limitation": LIMITATION,
        },
    )


def memo_provenance(search: NativeSearch, *, synthesis_id: str | None, synthesis_used: bool) -> str:
    return json.dumps(
        {
            **search.provenance,
            "synthesis_used": synthesis_used,
            "synthesis_provider_response_id": synthesis_id,
            "research_http_request_count": 2 if synthesis_used else 1,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def freeze_native_memo(
    search: NativeSearch, memo: str, *, synthesis_id: str | None, synthesis_used: bool
) -> tuple[AuxiliaryContextItem, ...]:
    provenance = memo_provenance(search, synthesis_id=synthesis_id, synthesis_used=synthesis_used)
    # The old research capsule budget includes memo + provenance + label; never truncate.
    label = "DeepSeek native web research memo"
    if len(memo) + len(provenance) + len(label) > 24_000:
        raise ValueError("Auxiliary capsule bound")
    return (
        AuxiliaryContextItem(
            context_id="web-" + hashlib.sha256((memo + provenance).encode()).hexdigest()[:24],
            category="web_research",
            source_label=label,
            source_timestamp=None,
            provenance=provenance,
            as_of_compatible=True,
            content=memo,
        ),
    )
