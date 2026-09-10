"""Bounded, synthetic proof witnesses; exclusive output, no user data access."""

import argparse
import json
from dataclasses import replace
from decimal import Decimal, localcontext
from itertools import pairwise, product
from pathlib import Path
from time import perf_counter
from typing import Any

from .. import engine as baseline
from ..fixtures import synthetic
from ..r02 import engine as h1
from ..r02.phase_a import case
from ..types import CONTEXT, Dataset, Parameters, canonical, digest
from .models import History, advance, evaluate, kernel, projection, transition


def hand(center: int = 2, mirror: bool = False, count: int = 9) -> Dataset:
    source = synthetic("M30", count)
    bars = []
    for i, bar in enumerate(source.bars):
        o, h, lo, c = (109, 110, 108, 109) if i == center else (100, 101, 99, 100)
        if mirror:
            o, h, lo, c = 200 - o, 200 - lo, 200 - h, 200 - c
        bars.append(
            replace(bar, open=Decimal(o), high=Decimal(h), low=Decimal(lo), close=Decimal(c))
        )
    return replace(source, bars=tuple(bars))


def h1_rejection(root: Path) -> dict[str, Any]:
    data = synthetic("M30", 201, "path_lock")
    result = case(data, data.bars[-1].completed_at, candidate=True)
    result["label"] = "SYNTHETIC robustness rejection, not real-market evidence"
    retained = json.loads(
        (
            root / "docs/evidence/TASK_006B_Q/research-02/refined-causes/"
            "h1-rejection-counterexample.json"
        ).read_text(encoding="utf-8")
    )
    assert json.loads(canonical(result)) == retained
    old_time, new_time = data.bars[-2].completed_at, data.bars[-1].completed_at
    old = h1.evaluate(data, old_time).document()["decision"]["active_pivots"]
    new = h1.evaluate(data, new_time).document()["decision"]["active_pivots"]
    assert not old and len(new) == 13
    by_ref = {b.ref: b for b in data.bars}
    recognition = [
        {
            "kind": p["kind"],
            "price": p["price"],
            "extreme_ref": p["extreme_ref"],
            "confirmation_ref": p["confirmed_ref"],
            "extreme_time": by_ref[p["extreme_ref"]].end,
            "reversal_time": by_ref[p["confirmed_ref"]].completed_at,
            "first_observed_in_this_two_cutoff_schedule": new_time,
        }
        for p in new
    ]
    assert all(r["reversal_time"] <= old_time for r in recognition)
    return {
        "retained_diagnostic_exact_match": True,
        "diagnostic_hash": digest("r03", result),
        "old_count": 0,
        "rediscovered": 13,
        "old_cutoff": old_time,
        "new_cutoff": new_time,
        "cause": result["cause"],
        "events": recognition,
    }


def trap(mirror: bool = False) -> dict[str, Any]:
    data = synthetic("M30", 4)
    prices = [(109, 110, 108, 109), (108, 109, 90, 108), (96, 100, 95, 96), (97, 99, 96, 97)]
    bars = []
    for b, (o, h, lo, c) in zip(data.bars, prices, strict=True):
        if mirror:
            o, h, lo, c = 200 - o, 200 - lo, 200 - h, 200 - c
        bars.append(replace(b, open=Decimal(o), high=Decimal(h), low=Decimal(lo), close=Decimal(c)))
    params = Parameters.default("M30")
    a, _ = baseline.pivots(tuple(bars), (Decimal(1),) * 4, params)
    candidate, _ = h1.pivots(tuple(bars), (Decimal(1),) * 4, params)
    expected = (
        [("LOW", 0, 1, Decimal(90)), ("HIGH", 2, 3, Decimal(105))]
        if mirror
        else [("HIGH", 0, 1, Decimal(110)), ("LOW", 2, 3, Decimal(95))]
    )
    actual = [(p.kind, p.extreme, p.confirmed, p.price) for p in candidate]
    assert actual == expected and len(a) == 1
    return {
        "mirror": mirror,
        "constant_atr_unit_only": "1",
        "baseline": a,
        "h1": candidate,
        "omitted_more_extreme_price": 110 if mirror else 90,
    }


def atr_witness() -> dict[str, Any]:
    data = synthetic("M30", 15)
    bars = tuple(
        replace(
            b,
            open=Decimal(100),
            close=Decimal(100),
            high=Decimal(115 if i == 0 else 101),
            low=Decimal(85 if i == 0 else 99),
        )
        for i, b in enumerate(data.bars)
    )
    a, b = baseline.atr_series(bars), baseline.atr_series(bars[1:])
    assert a[13] == 4 and a[14] == Decimal("3.733333333333333333") and b[13] == 2
    with localcontext(CONTEXT):
        assert a[14] is not None and b[13] is not None
        old_gate, new_gate = (
            Decimal(4) >= Decimal("1.8") * a[14],
            Decimal(4) >= Decimal("1.8") * b[13],
        )
    assert not old_gate and new_gate
    return {
        "old_atr13": a[13],
        "old_atr14": a[14],
        "shifted_atr13": b[13],
        "fixed_distance": 4,
        "old_gate": old_gate,
        "new_gate": new_gate,
        "scope": "ATR-only counterfactual, not actual event or geometry equality",
    }


def local_cases() -> dict[str, Any]:
    output: dict[str, Any] = {}
    for center, warm in ((2, 0), (2, 2), (4, 0), (4, 2)):
        data = hand(center)
        old = evaluate(data, data.bars[-2].completed_at, warm)
        new = evaluate(data, data.bars[-1].completed_at, warm)
        state = advance(History(), old)
        after = advance(state, new)
        assert after.records[: len(state.records)] == state.records
        output[f"center{center}_warm{warm}"] = {
            "old": old,
            "new": new,
            "metrics": transition(old, new),
            "history": after,
            "projection": projection(after, new),
            "empty_at_new_records": len(advance(History(), new).records),
        }
    assert output["center2_warm0"]["metrics"]["lost"] == 1
    assert output["center2_warm0"]["metrics"]["coverage_removed"] == 1
    assert output["center2_warm2"]["metrics"]["expired"] == 1
    assert output["center4_warm2"]["metrics"]["full_support_opportunities"] == 1
    assert output["center4_warm2"]["metrics"]["lost"] == 0
    return output


def integer_oracle(word: tuple[int, ...]) -> tuple[tuple[int, str], ...]:
    """Independent closed form on C+-1 domain: strict local turn plus prior-turn veto."""
    turns = {
        j: "HIGH" if word[j] > max(word[j - 1], word[j + 1]) else "LOW"
        for j in range(1, len(word) - 1)
        if word[j] > max(word[j - 1], word[j + 1]) or word[j] < min(word[j - 1], word[j + 1])
    }
    return tuple((j, turns[j]) for j in sorted(turns) if j >= 2 and j - 1 not in turns)


def enumeration() -> dict[str, Any]:
    start = perf_counter()
    totals = {
        str(w): dict.fromkeys(
            (
                "endpoint_opportunities",
                "lost",
                "rediscovered",
                "expired",
                "full_support_opportunities",
                "full_support_lost",
                "full_support_rediscovered",
                "coverage_removed",
            ),
            0,
        )
        for w in (0, 2)
    }
    count = 0
    for word in product((99, 100, 101), repeat=9):
        if perf_counter() - start > 120:
            break
        old, new = word[:8], word[1:]
        results = []
        for window in (old, new):
            actual = kernel(
                tuple(Decimal(c + 1) for c in window),
                tuple(Decimal(c - 1) for c in window),
                tuple(Decimal(c) for c in window),
            )
            assert actual == integer_oracle(window)
            assert all(b[0] - a[0] >= 2 for a, b in pairwise(actual))
            results.append(actual)
        for warm in (0, 2):
            a = {(j, k) for j, k in results[0] if j >= warm}
            b = {(j + 1, k) for j, k in results[1] if j >= warm}
            # Global source positions; confirmation=center+1, never array-offset equality.
            common = {p for p in a if p[0] >= warm + 1}
            full = {p for p in common if p[0] - 2 >= 1}
            rediscovered = {p for p in b - a if warm + 1 <= p[0] and p[0] + 1 <= 7}
            full_rediscovered = {p for p in rediscovered if p[0] - 2 >= 0}
            row = totals[str(warm)]
            row["endpoint_opportunities"] += len(common)
            row["lost"] += len(common - b)
            row["rediscovered"] += len(rediscovered)
            row["expired"] += len(a - common)
            row["full_support_opportunities"] += len(full)
            row["full_support_lost"] += len(full - b)
            row["full_support_rediscovered"] += len(full_rediscovered)
            row["coverage_removed"] += len(common - full)
            assert not full - b and not full_rediscovered
        count += 1
    return {
        "status": "FINITE_DOMAIN_CHECKED" if count == 19683 else "INCOMPLETE",
        "domain": "all 3^9 close words in {99,100,101}; O=C,H=C+1,L=C-1",
        "seed": None,
        "count": count,
        "planned": 19683,
        "budget_seconds": 120,
        "elapsed_seconds": str(round(perf_counter() - start, 3)),
        "metrics": totals,
    }


def write_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(json.loads(canonical(value)), ensure_ascii=False, indent=2) + "\n")


def run(root: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    write_new(
        output / "witnesses.json",
        {
            "label": "SYNTHETIC",
            "h1": h1_rejection(root),
            "traps": [trap(), trap(True)],
            "atr": atr_witness(),
            "local": local_cases(),
        },
    )
    write_new(output / "enumeration.json", enumeration())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.output)
