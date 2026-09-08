"""Bounded numeric observations and rule-originated failures; no provider text escapes."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from types import MappingProxyType

from ai_infra_quant.application.paqs_e_research import RESEARCH_BOUNDARY_CODES

ACTION_TYPES = ("search", "open_page", "find_in_page")
ACTION_STATUSES = ("completed", "in_progress", "incomplete", "failed", "cancelled")


class NativeParseFailure(ValueError):
    def __init__(self, boundary_code: str, counts: Mapping[str, int] | None = None) -> None:
        if boundary_code not in RESEARCH_BOUNDARY_CODES:
            raise ValueError("Unknown application boundary")
        self.boundary_code = boundary_code
        self.counts = MappingProxyType(dict(counts or {}))
        super().__init__(boundary_code)


@contextmanager
def boundary(code: str, counts: Mapping[str, int] | None = None) -> Iterator[None]:
    """Bind implicit encoding/URL/shape errors to the rule currently being enforced."""
    try:
        yield
    except NativeParseFailure:
        raise
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError):
        raise NativeParseFailure(code, counts) from None


def invalid_query(value: object) -> bool:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 500
        or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", value)
    ):
        return True
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError:
        return True
    return False


def observed_counts(response: object) -> dict[str, int]:
    """Whole bounded output counts, before validation; never infer trusted evidence.

    Query/source slots are inspected only on completed searches. Invalid containers
    make the corresponding total unknown. Large numeric observations saturate at
    1024. No partial query/source payload is visited, including for diagnostics.
    """
    if not isinstance(response, dict) or not isinstance(response.get("output"), list):
        return {}
    output = response["output"]
    if len(output) > 128:
        return {}
    result = dict.fromkeys(
        [
            "web_search_call_count",
            "search_action_count",
            "message_count",
            "completed_search_count",
            "non_completed_search_count",
            "missing_or_unknown_status_count",
            "malformed_action_count",
            "unexpected_output_item_count",
            "unknown_action_count",
        ],
        0,
    )
    result.update({status + "_action_count": 0 for status in ACTION_STATUSES})
    queries = sources = invalid = 0
    queries_known = sources_known = invalid_known = True
    for item in output:
        if not isinstance(item, dict):
            result["unexpected_output_item_count"] += 1
            queries_known = sources_known = invalid_known = False
            continue
        kind = item.get("type")
        if kind == "web_search_call":
            result["web_search_call_count"] += 1
            status = item.get("status")
            if isinstance(status, str) and status in ACTION_STATUSES:
                result[status + "_action_count"] += 1
            else:
                result["missing_or_unknown_status_count"] += 1
            action = item.get("action")
            if not isinstance(action, dict):
                result["malformed_action_count"] += 1
                continue
            action_type = action.get("type")
            if action_type not in ACTION_TYPES:
                result["unknown_action_count"] += 1
            if action_type != "search":
                continue
            result["search_action_count"] += 1
            if status == "completed":
                result["completed_search_count"] += 1
            elif isinstance(status, str) and status in ACTION_STATUSES:
                result["non_completed_search_count"] += 1
            if status != "completed":
                continue
            for field, value in action.items():
                if field not in ("queries", "query"):
                    continue
                values = [value] if field == "query" else value
                if not isinstance(values, list):
                    queries_known = invalid_known = False
                    continue
                queries = min(1024, queries + len(values))
                if len(values) > 1024:
                    invalid_known = False
                else:
                    invalid = min(1024, invalid + sum(invalid_query(v) for v in values))
            records = action.get("sources", [])
            if isinstance(records, list):
                sources = min(1024, sources + len(records))
            else:
                sources_known = False
        elif kind == "message":
            result["message_count"] += 1
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
        elif kind != "reasoning":
            result["unexpected_output_item_count"] += 1
    if queries_known:
        result["provider_exposed_query_count"] = queries
    if sources_known:
        result["raw_source_record_count"] = sources
    if invalid_known:
        result["invalid_query_value_count"] = invalid
    return result
