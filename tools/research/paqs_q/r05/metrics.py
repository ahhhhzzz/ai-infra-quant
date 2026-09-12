"""Frozen structural descriptors; no outcome, forward-price or profitability calculation."""

from collections import Counter
from decimal import Decimal, localcontext
from typing import Any

from ..r04.study import costs
from ..types import CONTEXT, q


def segment(value: str | None) -> str:
    return "UNRESOLVED_SEGMENT" if value is None else value


def metrics(result: dict[str, Any]) -> dict[str, Any]:
    events = result["events"]
    pairs = []
    runs: list[dict[str, Any]] = []
    chains: list[list[str]] = []
    chain: list[str] = []
    for i, event in enumerate(events):
        if i:
            left = events[i - 1]
            pairs.append(
                {
                    "left": left["key"],
                    "right": event["key"],
                    "same_kind": left["kind"] == event["kind"],
                    "separation": event["separation"],
                    "amplitude": event["amplitude_local_range"],
                    "right_segment": segment(event["segment"]),
                }
            )
        if not runs or runs[-1]["kind"] != event["kind"]:
            runs.append({"kind": event["kind"], "length": 0})
        runs[-1]["length"] += 1
        if i and event["separation"] == 1 and event["kind"] != events[i - 1]["kind"]:
            if not chain:
                chain.append(events[i - 1]["key"])
            chain.append(event["key"])
        else:
            if chain:
                chains.append(chain)
            chain = []
    if chain:
        chains.append(chain)
    same = sum(p["same_kind"] for p in pairs)
    with localcontext(CONTEXT):
        rate = q(Decimal(same) / len(pairs)) if pairs else None
        stats = costs(result)
    omissions = [
        {
            "center": r["center"],
            "index": r["index"],
            "reason": r["reason"],
            "reference": r["omission_reference"],
            "price": r["omitted_price"],
            "more_extreme": r["more_extreme"],
            "segment": segment(r["segment"]),
        }
        for r in result["census"]
        if "omission_reference" in r
    ]
    return {
        "costs": stats,
        "pairs": pairs,
        "same_kind_pairs": same,
        "opposite_kind_pairs": len(pairs) - same,
        "same_kind_rate": rate,
        "separation_one_pairs": sum(p["separation"] == 1 for p in pairs),
        "unit_gap_alternating_chains": chains,
        "max_unit_gap_chain_events": max((len(c) for c in chains), default=0),
        "kind_runs": runs,
        "omissions": omissions,
    }


def summarize(records: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    transitions: Counter[str] = Counter()
    segments: dict[str, Counter[str]] = {}
    endpoint_keys: set[str] = set()
    run_lengths: dict[str, Counter[str]] = {"HIGH": Counter(), "LOW": Counter()}
    distributions: dict[str, list[Any]] = {"age": [], "separation": [], "amplitude": []}
    max_chain = 0
    for row in records:
        m = row[arm]["metrics"]
        for k, v in m["costs"].items():
            if type(v) is int:
                counts[k] += v
        for k in ("same_kind_pairs", "opposite_kind_pairs", "separation_one_pairs"):
            counts[k] += m[k]
        reasons.update(m["costs"]["reasons_active"])
        for s, values in m["costs"]["segments"].items():
            segments.setdefault(s, Counter()).update(values)
        endpoint_keys.update(e["key"] for e in row[arm]["events"])
        for run in m["kind_runs"]:
            run_lengths[run["kind"]][str(run["length"])] += 1
        max_chain = max(max_chain, m["max_unit_gap_chain_events"])
        distributions["age"].extend(m["costs"]["ages"])
        distributions["separation"].extend(m["costs"]["separations"])
        distributions["amplitude"].extend(m["costs"]["amplitudes_current_prior_range"])
        if "transition" in row[arm]:
            trans = row[arm]["transition"]
            transitions[trans["status"] + "_pairs"] += 1
            transitions.update({k: v for k, v in trans.items() if type(v) is int})
    with localcontext(CONTEXT):
        rate = (
            q(Decimal(counts["same_kind_pairs"]) / counts["pair_denominator"])
            if counts["pair_denominator"]
            else None
        )
    return {
        "overlapping_cutoff_totals": counts,
        "active_reasons": reasons,
        "deduplicated_endpoint_count": len(endpoint_keys),
        "deduplicated_endpoints": sorted(endpoint_keys),
        "same_kind_rate": rate,
        "max_unit_gap_chain_events": max_chain,
        "kind_run_length_distribution_occurrences": run_lengths,
        "distributions_occurrences": {
            k: {
                "count": len(v),
                "min": min(v) if v else None,
                "max": max(v) if v else None,
                "lower_median": sorted(v)[(len(v) - 1) // 2] if v else None,
            }
            for k, v in distributions.items()
        },
        "segments_occurrences": segments,
        "rolling": transitions,
    }


def disposition(frames: list[dict[str, Any]]) -> str:
    applicable = [f for f in frames if f["mode"] == "OBSERVATIONAL" and f["valid"]]
    increased = []
    undefined = False
    for f in applicable:
        b, a = (f[k]["overlapping_cutoff_totals"] for k in ("B0", "A1"))
        if b["pair_denominator"] and a["pair_denominator"]:
            increased.append(
                a["same_kind_pairs"] * b["pair_denominator"]
                > b["same_kind_pairs"] * a["pair_denominator"]
            )
        else:
            undefined = True
    if any(increased):
        return "REJECT_NO_VETO"
    if undefined:
        return "INCONCLUSIVE"
    if applicable and all(f["deduplicated_restored_more_extreme"] for f in applicable):
        return "RECOMMEND_CROSS_SAMPLE_ONLY"
    return "INCONCLUSIVE"
