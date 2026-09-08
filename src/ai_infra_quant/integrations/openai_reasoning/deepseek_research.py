"""Bounded native DeepSeek research memo; never infer source authority from prose."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
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


def normalize_native_memo(
    response: dict[str, Any],
    model: ModelDescriptor,
    snapshot: PaqsMarketSnapshot,
    retrieved_at: datetime,
    intent: str,
) -> tuple[AuxiliaryContextItem, ...]:
    if response.get("status") != "completed" or response.get("error"):
        raise ValueError("Incomplete research")
    response_id = response.get("id")
    if response_id is not None and (
        not isinstance(response_id, str)
        or re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", response_id) is None
    ):
        raise ValueError("Unsafe response identity")
    output = response.get("output")
    if not isinstance(output, list):
        raise ValueError("Malformed research")
    texts: list[str] = []
    actions: list[str] = []
    queries: list[str] = []
    records: list[dict[str, Any]] = []

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
            if len(actions) > 10:
                raise ValueError("Action bound")
            if action_type == "search":
                values = action.get("queries", [action["query"]] if "query" in action else [])
                if not isinstance(values, list) or any(
                    not isinstance(q, str) or not q.strip() or len(q) > 500 for q in values
                ):
                    raise ValueError("Query bound")
                queries.extend(values)
                if len(queries) > 4:
                    raise ValueError("Query count")
                remember(action.get("sources", []))
            continue
        if kind != "message" or item.get("status", "completed") != "completed":
            raise ValueError("Unexpected output")
        if item.get("refusal"):
            raise PermissionError("Refusal")
        parts = item.get("content")
        if not isinstance(parts, list):
            raise ValueError("Malformed content")
        for part in parts:
            if not isinstance(part, dict):
                raise ValueError("Malformed content")
            if part.get("type") == "refusal":
                raise PermissionError("Refusal")
            if part.get("type") not in {"output_text", "text"}:
                raise ValueError("Unexpected content")
            text = part.get("text")
            if not isinstance(text, str) or not text.strip() or len(text) > 24_000:
                raise ValueError("Memo bound")
            texts.append(text)
            annotations = part.get("annotations", [])
            if not isinstance(annotations, list):
                raise ValueError("Malformed annotations")
            for annotation in annotations:
                if not isinstance(annotation, dict) or annotation.get("type") != "url_citation":
                    raise ValueError("Unexpected annotation")
                remember([annotation])
    if "search" not in actions or len(texts) != 1:
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
    provenance = json.dumps(
        {
            "provider": model.provider_id,
            "model": model.model_id,
            "provider_response_id": response_id,
            "retrieved_at": retrieved_at.isoformat(),
            "intent": intent,
            "snapshot_as_of": snapshot.as_of_timestamp.isoformat(),
            "native_action_count": len(actions),
            "action_types": actions,
            "queries": queries,
            "sources": [source for url, source in sources.items() if url not in future],
            "excluded_future_source_count": len(future),
            "limitation": LIMITATION,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    # The old research capsule budget includes memo + provenance + label; never truncate.
    label = "DeepSeek native web research memo"
    if len(texts[0]) + len(provenance) + len(label) > 24_000:
        raise ValueError("Auxiliary capsule bound")
    return (
        AuxiliaryContextItem(
            context_id="web-" + hashlib.sha256((texts[0] + provenance).encode()).hexdigest()[:24],
            category="web_research",
            source_label=label,
            source_timestamp=None,
            provenance=provenance,
            as_of_compatible=True,
            content=texts[0],
        ),
    )
