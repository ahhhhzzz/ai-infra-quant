"""Reproduce retained cases and census before selecting candidate algorithms."""

import argparse
import json
from collections import Counter
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from ..diagnostics import boundary
from ..engine import atr_series, evaluate, pivots, prepare
from ..io import read_dataset
from ..types import Dataset, Parameters, canonical, digest
from .trace import events, trace

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "docs/evidence/TASK_006B_Q"


def write_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as file:
        file.write(json.dumps(json.loads(canonical(value)), ensure_ascii=False, indent=2) + "\n")


def load_original(directory: Path) -> dict[str, Dataset]:
    expected = json.loads((EVIDENCE / "coverage.json").read_text())["observation_file_hashes"]
    datasets = {}
    for tf in ("W1", "D1", "M30"):
        name = f"US.AVGO.{tf}.json"
        path = directory / name
        assert sha256(path.read_bytes()).hexdigest() == expected[name], name
        datasets[tf] = read_dataset(path)
    return datasets


def census(data: Dataset, cutoffs: list[datetime]) -> dict[str, Any]:
    rows = []
    for cutoff in cutoffs:
        params = Parameters.default(data.timeframe)
        bars = prepare(data, cutoff)[-params.total :]
        result = evaluate(data, cutoff).document()
        d, diagnostic = result["decision"], result["diagnostics"]
        trace_rows = trace(bars, atr_series(bars), params)
        rows.append(
            {
                "cutoff": cutoff,
                "regime": d["regime"],
                "reason": d["structure_status"],
                "input_status": d["input_status"],
                "evidence": d.get("evidence"),
                "active_pivots": d["active_pivots"],
                "labels": d.get("labels", []),
                "dual_count": sum(r["dual"] for r in trace_rows),
                "unseeded_at_terminal": bool(
                    trace_rows and trace_rows[-1]["state_after"] == "UNSEEDED"
                ),
                "first_seed": next((r["emitted"] for r in trace_rows if r["emitted"]), None),
                "stale": "ACTIVE_PIVOT_STALE" in d.get("warnings", []),
                "range_available": d["range"] is not None,
                "zone_count": len(d["zones"]),
                "cap_suppressed_ranges": diagnostic.get("cap_suppressed_range_count", 0),
                "available_bars": len(bars),
            }
        )
    return {
        "rows": rows,
        "reason_counts": dict(Counter(r["reason"] for r in rows)),
        "dual_at_any_point": sum(r["dual_count"] > 0 for r in rows),
        "terminal_unseeded": sum(r["unseeded_at_terminal"] for r in rows),
        "stale_count": sum(r["stale"] for r in rows),
        "range_unavailable": sum(not r["range_available"] for r in rows),
    }


def case(data: Dataset, cutoff: datetime) -> dict[str, Any]:
    params = Parameters.default(data.timeframe)
    seq = prepare(data, cutoff)[-params.total - 1 :]
    ablation = boundary(data, seq, params)
    old, left = seq[:-1], seq[1:-1]
    a, b = atr_series(old), atr_series(left)
    ta, tb = trace(old, a, params), trace(left, b, params)
    # Independently assert instrumentation reproduces the retained baseline events.
    for bars, atrs, traced in ((old, a, ta), (left, b, tb)):
        expected, _ = pivots(bars, atrs, params)
        assert events(traced, {bar.ref for bar in bars}) == [
            (p.kind, p.extreme_ref, p.confirmed_ref) for p in expected
        ]
    old_rows = {r["ref"]: r for r in ta}
    fields = ("state_before", "high_ref", "low_ref", "down", "up", "emitted")
    first = next(
        (
            {"old": old_rows[r["ref"]], "left": r}
            for r in tb
            if r["ref"] in old_rows and any(old_rows[r["ref"]][f] != r[f] for f in fields)
        ),
        None,
    )
    first_predicate = next(
        (
            {"old": old_rows[r["ref"]], "left": r}
            for r in tb
            if r["ref"] in old_rows
            and any(old_rows[r["ref"]][f] != r[f] for f in ("down", "up", "emitted"))
        ),
        None,
    )
    common = {bar.ref for bar in left[params.warm :]}
    old_events, left_events = events(ta, common), events(tb, common)
    # Diagnostic 2x2: keep old bar geometry and common active evidence. First positive
    # seed at old local 13 vs 14; common ATR sequence from OLD vs LEFT. The unmatched
    # old index 13 retains old ATR for the ATR-only intervention. Never a normal output.
    aligned = tuple(a[i] if i < 14 else b[i - 1] for i in range(len(old)))
    controls = {
        "old_seed_old_atr": events(trace(old, a, params), common),
        "new_seed_old_atr": events(trace(old, a, params, seed_start=14), common),
        "old_seed_new_common_atr": events(trace(old, aligned, params), common),
        "new_seed_new_common_atr": events(trace(old, aligned, params, seed_start=14), common),
    }
    assert controls["old_seed_old_atr"] == old_events
    assert controls["new_seed_new_common_atr"] == left_events
    seed_changes = controls["new_seed_old_atr"] != old_events
    atr_changes = controls["old_seed_new_common_atr"] != old_events
    cause = (
        "LEGITIMATE_ACTIVE_EXPIRY"
        if old_events == left_events
        else "SEED_PATH"
        if seed_changes and not atr_changes and controls["new_seed_old_atr"] == left_events
        else "ATR_RECURRENCE"
        if atr_changes and not seed_changes and controls["old_seed_new_common_atr"] == left_events
        else "INTERACTING_OR_UNRESOLVED"
    )
    refs = {bar.ref: (i, bar) for i, bar in enumerate(seq)}
    lost = [ev for ev in old_events if ev not in left_events]
    gained = [ev for ev in left_events if ev not in old_events]

    def item(index: int) -> dict[str, Any]:
        bar = seq[index]
        return {
            "transition_index": index,
            "ref": bar.ref,
            "start": bar.start,
            "end": bar.end,
            "completed_at": bar.completed_at,
            "session": bar.session,
            "market_local_start": bar.start.astimezone(ZoneInfo(data.market_timezone)).isoformat(),
            "market_local_completed": bar.completed_at.astimezone(
                ZoneInfo(data.market_timezone)
            ).isoformat(),
        }

    return {
        "timeframe": data.timeframe,
        "cutoff": cutoff,
        "source": dict(data.provenance),
        "arm_evidence": ablation,
        "cause": cause,
        "old_window_hash": digest("qstr-window", tuple(x.observation() for x in old)),
        "left_window_hash": digest("qstr-window", tuple(x.observation() for x in left)),
        "exiting_warm": item(0),
        "exiting_active": item(params.warm),
        "old_initial_positive_atr": ta[0],
        "left_initial_positive_atr": tb[0],
        "first_state_divergence": first,
        "first_predicate_divergence": first_predicate,
        "interventions_diagnostic_only": controls,
        "seed_changes_common_events": seed_changes,
        "atr_changes_common_events": atr_changes,
        "lost_still_eligible": lost,
        "rediscovered_still_eligible": gained,
        "changed_event_times": [
            {"event": ev, "extreme": item(refs[ev[1]][0]), "confirmation": item(refs[ev[2]][0])}
            for ev in lost + gained
        ],
        "trace_sequences": {
            "OLD": [{k: r[k] for k in ("index", "state_after", "dual", "emitted")} for r in ta],
            "LEFT": [{k: r[k] for k in ("index", "state_after", "dual", "emitted")} for r in tb],
        },
        "old_consequences": evaluate(data, seq[-2].completed_at).document()["decision"]["evidence"],
        "both_consequences": evaluate(data, cutoff).document()["decision"]["evidence"],
    }


def run(directory: Path, output: Path) -> None:
    datasets = load_original(directory)
    cases = json.loads((EVIDENCE / "boundary-case-review.json").read_text())["cases"]
    rows = [case(datasets[c["timeframe"]], datetime.fromisoformat(c["cutoff"])) for c in cases]
    write_new(output / "phase-a-cases.json", rows)
    ceiling = datetime.fromisoformat(
        json.loads((EVIDENCE / "universe.json").read_text())["cutoffs"]["not_after"]
    )
    d1 = datasets["D1"]
    counts = census(d1, [b.completed_at for b in prepare(d1, ceiling)[-100:]])
    write_new(output / "phase-a-d1-census.json", counts)
    print(
        canonical(
            {
                "cases": len(rows),
                "causes": dict(Counter(r["cause"] for r in rows)),
                "d1": {k: v for k, v in counts.items() if k != "rows"},
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.data_dir, args.output_dir)
