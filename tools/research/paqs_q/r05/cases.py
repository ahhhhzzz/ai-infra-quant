"""Pre-result deterministic case selection; completed candles only."""

from decimal import localcontext
from typing import Any

from ..types import CONTEXT, digest


def choose(
    base: dict[str, Any],
    candidate: dict[str, Any],
    delta: dict[str, Any],
    bm: dict[str, Any],
    am: dict[str, Any],
    dependencies: list[dict[str, Any]],
    selected: dict[str, Any],
) -> None:
    if base["status"] != "VALID" or base["mode"] != "OBSERVATIONAL":
        return
    proposals: list[tuple[str, tuple[Any, ...], int, int]] = []
    bkeys = {e["key"]: e for e in base["events"]}
    akeys = {e["key"]: e for e in candidate["events"]}
    additions = {r["endpoint"] for r in delta["added"]}
    for r in delta["added"]:
        j = r["index"]
        proposals.append(("first-added", (base["cutoff"], j), j, j))
        if r["restored_more_extreme"]:
            with localcontext(CONTEXT):
                gap = abs(r["A1_event"]["price"] - bkeys[r["baseline_omission_reference"]]["price"])
            proposals.append(("restored-extreme", (-gap, base["cutoff"], j), j, j))
    for chain in am["unit_gap_alternating_chains"]:
        if additions.intersection(chain):
            first, last = akeys[chain[0]]["index"], akeys[chain[-1]]["index"]
            proposals.append(("unit-gap-chain", (-len(chain), base["cutoff"], first), first, last))
    bpairs = {(p["left"], p["right"]) for p in bm["pairs"]}
    for p in am["pairs"]:
        if p["same_kind"] and (p["left"], p["right"]) not in bpairs:
            first, last = akeys[p["left"]]["index"], akeys[p["right"]]["index"]
            proposals.append(("new-same-kind-pair", (base["cutoff"], first, last), first, last))
    for d in dependencies:
        j = d["index"]
        proposals.append(("triple-only-non-event", (not d["active"], base["cutoff"], j), j, j))
    for category, rank, first, last in proposals:
        if category in selected and selected[category]["rank"] <= rank:
            continue
        left, right = max(0, first - 5), min(len(base["bars"]), last + 7)
        bars = base["bars"][left:right]
        assert all(b.completed_at <= base["cutoff"] for b in bars)
        selected[category] = {
            "rank": rank,
            "case": {
                "timeframe": base["timeframe"],
                "mode": base["mode"],
                "security": base["security"],
                "quality": base["quality"],
                "cutoff": base["cutoff"],
                "categories": [category],
                "first_window_index": left,
                "focus_first": first,
                "focus_last": last,
                "bars": bars,
                "census_B0": base["census"][left:right],
                "census_A1": candidate["census"][left:right],
                "events_B0": [e for e in base["events"] if left <= e["index"] < right],
                "events_A1": [e for e in candidate["events"] if left <= e["index"] < right],
                "dependency_diagnostics": [d for d in dependencies if left <= d["index"] < right],
                "window_hash": base["window_hash"],
                "calendar_hash": base["calendar_hash"],
                "future_candles": 0,
            },
        }


def finalize(selected: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    unique: dict[str, Any] = {}
    for category in sorted(selected):
        case = selected[category]["case"]
        key = digest(
            "r05-case", (case["timeframe"], case["cutoff"], case["focus_first"], case["focus_last"])
        )
        if key in unique:
            unique[key]["categories"].append(category)
        else:
            unique[key] = dict(case, case_id=key)
    counts = {
        k: int(k in selected)
        for k in (
            "first-added",
            "restored-extreme",
            "unit-gap-chain",
            "new-same-kind-pair",
            "triple-only-non-event",
        )
    }
    assert len(unique) <= 5
    return [unique[k] for k in sorted(unique)], counts
