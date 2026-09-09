"""Frozen full-cohort same-input comparisons, no acquisition and no parameter selection."""

import argparse
import json
import platform
import statistics
import time
import tracemalloc
from collections import Counter
from dataclasses import replace
from datetime import datetime
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

from .. import engine as baseline
from ..diagnostics import boundary as baseline_boundary
from ..diagnostics import structural, variants
from ..fixtures import synthetic
from ..temporal import availability_check
from ..types import CONTEXT, Dataset, Parameters, Result, canonical, q
from . import engine as h1
from .boundary import boundary as h1_boundary
from .phase_a import EVIDENCE, case, load_original, write_new


def event_set(decision: dict[str, Any]) -> set[tuple[str, str, str, str]]:
    return {
        (p["kind"], p["price"], p["extreme_ref"], p["confirmed_ref"])
        for p in decision["active_pivots"]
    }


def event_changes(
    old: dict[str, Any],
    new: dict[str, Any],
    active_refs: set[str],
    old_cutoff: datetime,
    times: dict[str, datetime],
) -> dict[str, Any]:
    before, after = event_set(old), event_set(new)
    comparable = {p for p in before if p[2] in active_refs and p[3] in active_refs}
    added = after - before
    return {
        "opportunities": len(comparable),
        "lost": sorted(comparable - after),
        "expired": sorted(before - comparable),
        "rediscovered": sorted(p for p in added if times[p[3]] <= old_cutoff),
        "newly_confirmed": sorted(p for p in added if times[p[3]] > old_cutoff),
    }


def frame(data: Dataset, cutoffs: list[datetime], output: Path) -> dict[str, Any]:
    params = Parameters.default(data.timeframe)
    rows: list[dict[str, Any]] = []
    material_cases = []
    previous: dict[str, Result] = {}
    previous_cutoff: datetime | None = None
    previous_index: int | None = None
    sensitivity: dict[str, dict[str, Counter[str]]] = {
        name: {v: Counter() for v, _ in variants(params)} for name in ("BASELINE", "H1")
    }
    for offset, cutoff in enumerate(cutoffs):
        chosen = baseline.prepare(data, cutoff)
        if len(chosen) < params.total:
            rows.append({"cutoff": cutoff, "status": "INSUFFICIENT", "available": len(chosen)})
            previous = {}
            previous_index = None
            previous_cutoff = None
            continue
        bars = chosen[-params.total :]
        bounded = replace(data, bars=bars)
        results = {
            "BASELINE": baseline.evaluate(bounded, cutoff),
            "H1": h1.evaluate(bounded, cutoff),
        }
        check = availability_check(bars, data, cutoff)
        row: dict[str, Any] = {
            "cutoff": cutoff,
            "status": "VALID",
            "current_availability": check,
            "same_structure": structural(results["BASELINE"]) == structural(results["H1"]),
        }
        for name, evaluator, boundary_func in (
            ("BASELINE", baseline.evaluate, baseline_boundary),
            ("H1", h1.evaluate, h1_boundary),
        ):
            result = results[name]
            document = result.document()
            d = document["decision"]
            diag = document["diagnostics"]
            stats = {
                "regime": d["regime"],
                "reason": d["structure_status"],
                "input_status": d["input_status"],
                "hash": result.semantic_hash,
                "active_count": len(d["active_pivots"]),
                "ambiguity_count": len(diag["ambiguous_indices"]),
                "zone_count": len(d["zones"]),
                "range": d["range"],
                "latest_age": len(bars) - 1 - d["active_pivots"][-1]["extreme"]
                if d["active_pivots"]
                else None,
                "evidence": d["evidence"],
                "comparison_counts": diag["comparison_counts"],
                "origin_equal": evaluator(data, cutoff).semantic_hash == result.semantic_hash,
                "structure": structural(result),
            }
            if previous_cutoff is not None and previous_index == len(chosen) - 2:
                stats["events"] = event_changes(
                    previous[name].document()["decision"],
                    d,
                    {b.ref for b in bars[params.warm :]},
                    previous_cutoff,
                    {b.ref: b.completed_at for b in chosen},
                )
                stats["state_changed"] = (
                    previous[name].document()["decision"]["regime"] != d["regime"]
                )
            if len(chosen) >= params.total + 1:
                boundary = boundary_func(data, chosen[-params.total - 1 :], params)
                stats["boundary"] = {k: v for k, v in boundary.items() if k != "arms"}
                if boundary["material"] and boundary["classification"] == "LEFT_ONLY":
                    causal = case(data, cutoff, candidate=name == "H1")
                    causal["algorithm"] = name
                    material_cases.append(causal)
            for variant, parameters in variants(params):
                other = evaluator(bounded, cutoff, parameters)
                c = sensitivity[name][variant]
                c["pairs"] += 1
                c["regime_disagreements"] += other.document()["decision"]["regime"] != d["regime"]
                c["structure_disagreements"] += structural(other) != structural(result)
            row[name] = stats
        rows.append(row)
        previous = results
        previous_cutoff = cutoff
        previous_index = len(chosen) - 1
        if offset % 20 == 0:
            print(data.timeframe, offset + 1, "/", len(cutoffs), flush=True)
    summary: dict[str, Any] = {
        "security": data.security,
        "timeframe": data.timeframe,
        "scheduled": len(cutoffs),
        "valid": sum(r["status"] == "VALID" for r in rows),
        "sensitivity": sensitivity,
    }
    for name in ("BASELINE", "H1"):
        valid = [r[name] for r in rows if r["status"] == "VALID"]
        transitions = [r for r in valid if "events" in r]
        summary[name] = {
            "regimes": dict(Counter(r["regime"] for r in valid)),
            "reasons": dict(Counter(r["reason"] for r in valid)),
            "ambiguous_evaluations": sum(r["ambiguity_count"] > 0 for r in valid),
            "mean_active_pivots": str(
                q(Decimal(sum(r["active_count"] for r in valid)) / len(valid))
            )
            if valid
            else None,
            "adjacent_transitions": len(transitions),
            "state_changes": sum(r["state_changed"] for r in transitions),
            "opportunities": sum(r["events"]["opportunities"] for r in transitions),
            "lost_events": sum(len(r["events"]["lost"]) for r in transitions),
            "rediscovered_events": sum(len(r["events"]["rediscovered"]) for r in transitions),
            "expired_events": sum(len(r["events"]["expired"]) for r in transitions),
            "new_confirmations": sum(len(r["events"]["newly_confirmed"]) for r in transitions),
            "material_left_only": sum(c["algorithm"] == name for c in material_cases),
            "origin_violations": sum(not r["origin_equal"] for r in valid),
            "direct_flips": sum(
                r.get("boundary", {}).get("direct_directional_flip", False) for r in valid
            ),
            "geometry_over_half_atr": sum(
                any(
                    Decimal(g["bound_delta_atr"]) > Decimal(".5")
                    for g in r.get("boundary", {}).get("geometry", [])
                )
                for r in valid
            ),
            "time_violations": sum(
                c["violation_count"]
                for r in valid
                for c in r.get("boundary", {}).get("availability_checks", {}).values()
            ),
        }
    write_new(
        output / f"{data.security}.{data.timeframe}.comparison.json",
        {"summary": summary, "rows": rows},
    )
    write_new(output / f"{data.security}.{data.timeframe}.material-causes.json", material_cases)
    return summary


def performance() -> dict[str, Any]:
    rows = []
    for tf in ("W1", "D1", "M30"):
        params = Parameters.default(tf)
        data = synthetic(tf, params.total, "oscillation")
        for name, evaluator in (("BASELINE", baseline.evaluate), ("H1", h1.evaluate)):
            timings = []
            for _ in range(7):
                start = time.perf_counter_ns()
                result = evaluator(data, data.bars[-1].completed_at)
                timings.append(time.perf_counter_ns() - start)
            tracemalloc.start()
            evaluator(data, data.bars[-1].completed_at)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            rows.append(
                {
                    "timeframe": tf,
                    "algorithm": name,
                    "window": params.total,
                    "repeats": 7,
                    "p50_ns": int(statistics.median(timings)),
                    "p95_nearest_rank_ns": max(timings),
                    "peak_traced_bytes": peak,
                    "timings_ns": timings,
                    "pivot_bar_visits": params.total,
                    "geometry_comparisons": result.document()["diagnostics"]["comparison_counts"],
                }
            )
    return {
        "hardware": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "fixture": "SYNTHETIC oscillation; default maximum normal W/A/N; no SLA",
        "rows": rows,
    }


def run(directory: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError("Use a fresh comparison output directory")
    datasets = load_original(directory)
    frozen = json.loads((EVIDENCE / "research-02/freeze.json").read_text())
    summaries = []
    with localcontext(CONTEXT):
        for tf, data in datasets.items():
            summaries.append(
                frame(data, [datetime.fromisoformat(t) for t in frozen["cutoffs"][tf]], output)
            )
    write_new(output / "summary.json", summaries)
    write_new(output / "performance.json", performance())
    print(canonical(summaries), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.data_dir, args.output_dir)
