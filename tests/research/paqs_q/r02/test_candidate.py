"""Independent event oracles and hard boundaries for frozen H1, not trend-rate targets."""

import json
import os
import subprocess
import sys
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal, Inexact, localcontext
from pathlib import Path

import pytest

from tools.research.paqs_q import engine as baseline
from tools.research.paqs_q.diagnostics import structural
from tools.research.paqs_q.fixtures import synthetic
from tools.research.paqs_q.io import read_dataset, write_dataset
from tools.research.paqs_q.r02 import engine
from tools.research.paqs_q.r02.boundary import boundary
from tools.research.paqs_q.r02.phase_a import write_new
from tools.research.paqs_q.r02.trace import events, trace
from tools.research.paqs_q.types import Bar, Parameters, Timeframe


def oracle_bars(mirror: bool = False) -> tuple[Bar, ...]:
    source = synthetic("M30", 4)
    # H0 confirms at1; ineligible low1=90 must not trap admissible low2=95.
    values = [(109, 110, 108, 109), (108, 109, 90, 108), (96, 100, 95, 96), (97, 99, 96, 97)]
    out = []
    for bar, (o, h, lo, c) in zip(source.bars, values, strict=True):
        if mirror:
            o, h, lo, c = 200 - o, 200 - lo, 200 - h, 200 - c
        out.append(
            replace(bar, open=Decimal(o), high=Decimal(h), low=Decimal(lo), close=Decimal(c))
        )
    return tuple(out)


@pytest.mark.parametrize("mirror", [False, True])
def test_hand_computed_admissible_extreme_and_confirmation(mirror: bool) -> None:
    bars = oracle_bars(mirror)
    params = Parameters.default("M30")
    actual, _ = engine.pivots(bars, (Decimal(1),) * 4, params)
    assert [(p.kind, p.extreme, p.confirmed, p.price) for p in actual] == (
        [("LOW", 0, 1, Decimal(90)), ("HIGH", 2, 3, Decimal(105))]
        if mirror
        else [("HIGH", 0, 1, Decimal(110)), ("LOW", 2, 3, Decimal(95))]
    )
    original, _ = baseline.pivots(bars, (Decimal(1),) * 4, params)
    assert len(original) == 1
    assert actual[1].evidence.threshold == Decimal(1)
    assert actual[1].confirmed > actual[1].extreme


def test_dual_ambiguity_does_not_force_seed() -> None:
    data = synthetic("M30", 20)
    bars = tuple(
        replace(
            b,
            open=Decimal(100),
            high=Decimal(200) if i == 0 else Decimal(101),
            low=Decimal(1) if i == 0 else Decimal(99),
            close=Decimal(100),
        )
        for i, b in enumerate(data.bars)
    )
    result, dual = engine.pivots(bars, (Decimal(1),) * 20, Parameters.default("M30"))
    assert result == ()
    assert dual == tuple(range(1, 20))


def test_exact_threshold_tie_and_no_same_bar() -> None:
    bars = oracle_bars()
    bars = (
        replace(bars[0], low=Decimal(109)),
        replace(bars[1], close=Decimal(109), low=Decimal(108)),
        replace(bars[2], high=Decimal(110)),
    )
    result, _ = engine.pivots(bars, (Decimal(1),) * 3, Parameters.default("M30"))
    assert (result[0].extreme, result[0].confirmed) == (0, 1)
    barely = (bars[0], replace(bars[1], close=Decimal("109.000000000000000001")))
    assert engine.pivots(barely, (Decimal(1),) * 2, Parameters.default("M30"))[0] == ()


@pytest.mark.parametrize("tf", ["W1", "D1", "M30"])
@pytest.mark.parametrize("pattern", ["flat", "bull", "bear", "oscillation", "path_lock"])
def test_origin_context_active_and_deterministic_invariants(tf: Timeframe, pattern: str) -> None:
    params = Parameters.default(tf)
    data = synthetic(tf, params.total + 80, pattern)
    cutoff = data.bars[-1].completed_at
    expected = engine.evaluate(data, cutoff)
    for extra in (0, 17, 53):
        shortened = replace(data, bars=data.bars[-params.total - extra :])
        with localcontext() as ctx:
            ctx.prec = 7
            ctx.traps[Inexact] = True
            assert engine.evaluate(shortened, cutoff).decision_json == expected.decision_json
    d = expected.document()["decision"]
    assert d["rule"] == engine.RULE
    assert d["input_status"] == "COMPLETE"
    if pattern == "flat":
        assert d["regime"] == "UNCERTAIN" and d["active_pivots"] == []
    if tf != "D1":
        assert d["zones"] == [] and d["range"] is None
    for p in d["active_pivots"]:
        assert params.warm <= p["extreme"] < p["confirmed"] < params.total
    for z in d["zones"]:
        assert params.total - 1 - max(p["extreme"] for p in z["touches"]) <= params.zone_age
        assert all(p["extreme"] >= params.warm for p in z["touches"])
    by_id = {p["identity"]: p for p in d["active_pivots"]}
    for label in d.get("labels", []):
        if label["directional_eligible"]:
            assert label["previous"] in by_id


@pytest.mark.parametrize(
    "coverage,quality,expected",
    [
        ("INVALID", "COMPLETE", "INVALID"),
        ("PARTIAL", "COMPLETE", "INVALID"),
        ("UNKNOWN", "PARTIAL", "INVALID"),
        ("PARTIAL", "PARTIAL", "PARTIAL"),
        ("UNKNOWN", "UNKNOWN", "UNKNOWN"),
    ],
)
def test_f01_public_wire_quality(
    tmp_path: Path, coverage: str, quality: str, expected: str
) -> None:
    data = synthetic(pattern="bull")
    data = replace(
        data, quality=quality, bars=(*data.bars[:-1], replace(data.bars[-1], coverage=coverage))
    )
    path = tmp_path / "input.json"
    write_dataset(path, data)
    d = engine.evaluate(read_dataset(path), data.bars[-1].completed_at).document()["decision"]
    assert d["input_status"] == expected
    if expected == "INVALID":
        assert d["regime"] == "UNCERTAIN"


@pytest.mark.parametrize("missing", [False, True])
def test_f02_revisions_missing_versions_and_all_arm_times(missing: bool) -> None:
    data = synthetic(count=313, pattern="bull")
    old, new = data.bars[-2].completed_at, data.bars[-1].completed_at
    changed = replace(data.bars[290], high=Decimal(9999), available_at=new)
    raw = tuple(b for i, b in enumerate(data.bars) if not missing or i != 290)
    revised = replace(data, bars=(*raw, changed))
    a = boundary(revised, baseline.prepare(revised, new)[-313:], Parameters.default("D1"))
    assert a["classification"] == "REVISION_CONFOUNDED"
    assert a["arm_decision_hashes"]["OLD"] == engine.evaluate(revised, old).semantic_hash
    if not missing:
        assert (
            engine.evaluate(data, old).decision_json == engine.evaluate(revised, old).decision_json
        )
    else:
        assert engine.evaluate(revised, old).document()["decision"]["regime"] == "UNCERTAIN"
    assert all(c["violation_count"] == 0 for c in a["availability_checks"].values())


def test_future_bad_payload_and_low_level_warm_guard() -> None:
    data = synthetic(count=313)
    old = data.bars[-2].completed_at
    future = replace(
        data.bars[40], high=Decimal("NaN"), coverage="BAD", available_at=old + timedelta(days=1)
    )
    revised = replace(data, bars=(*data.bars, future))
    assert engine.evaluate(data, old).decision_json == engine.evaluate(revised, old).decision_json
    raw = list(data.bars[-312:])
    raw[0] = replace(raw[0], available_at=data.bars[-1].completed_at + timedelta(days=1))
    with pytest.raises(ValueError, match="WINDOW_AVAILABILITY_AFTER_CUTOFF"):
        engine.calculate_window(
            data, tuple(raw), data.bars[-1].completed_at, Parameters.default("D1"), 60
        )


def test_cross_process_cli_identity(tmp_path: Path) -> None:
    data = synthetic("M30", 240, "bull")
    path = tmp_path / "input.json"
    write_dataset(path, data)
    cmd = [
        sys.executable,
        "-m",
        "tools.research.paqs_q.r02",
        "evaluate",
        "--input",
        str(path),
        "--cutoff",
        data.bars[-1].completed_at.isoformat(),
    ]
    results = [
        json.loads(
            subprocess.check_output(cmd, env={**os.environ, "PYTHONHASHSEED": seed}, text=True)
        )
        for seed in ("13", "57")
    ]
    assert results[0]["decision"] == results[1]["decision"]
    assert (
        results[0]["semantic_hash"]
        == engine.evaluate(data, data.bars[-1].completed_at).semantic_hash
    )


def test_trace_matches_baseline_independent_oracle_and_evidence_no_overwrite(
    tmp_path: Path,
) -> None:
    bars = oracle_bars()
    params = Parameters.default("M30")
    atr = (Decimal(1),) * 4
    assert events(trace(bars, atr, params), {b.ref for b in bars}) == [
        ("HIGH", bars[0].ref, bars[1].ref)
    ]
    path = tmp_path / "evidence.json"
    write_new(path, {"original": True})
    with pytest.raises(FileExistsError):
        write_new(path, {"original": False})
    assert json.loads(path.read_text()) == {"original": True}


def test_seed_trap_far_from_expiry_reduction() -> None:
    data = synthetic("M30", 201, "path_lock")
    params = Parameters.default("M30")
    a = baseline.evaluate(data, data.bars[-2].completed_at)
    b = baseline.evaluate(data, data.bars[-1].completed_at)
    # Wide bar13 leaves both seed predicates true, then exits the positive-ATR seed domain.
    assert a.document()["decision"]["active_pivots"] == []
    assert len(b.document()["decision"]["active_pivots"]) > 4
    assert any(p["extreme"] > 100 for p in b.document()["decision"]["active_pivots"])
    assert structural(a) != structural(b)
    assert params.total == 200
    # H1 deliberately preserves UNSEEDED ambiguity; this is a robustness rejection
    # oracle, not a failing engineering expectation or a reason to force a seed.
    ca = engine.evaluate(data, data.bars[-2].completed_at)
    cb = engine.evaluate(data, data.bars[-1].completed_at)
    assert ca.document()["decision"]["active_pivots"] == []
    assert len(cb.document()["decision"]["active_pivots"]) > 4
    assert all(p["confirmed"] < 199 for p in cb.document()["decision"]["active_pivots"])


def test_adversarial_extra_older_history_is_irrelevant() -> None:
    data = synthetic("M30", 300, "bull")
    expected = engine.evaluate(data, data.bars[-1].completed_at)
    for count in (1, 31, 100):
        prefix = tuple(
            replace(b, high=Decimal(999999), low=Decimal(".0001"))
            for b in data.bars[100 - count : 100]
        )
        other = replace(data, bars=(*prefix, *data.bars[-200:]))
        assert (
            engine.evaluate(other, data.bars[-1].completed_at).decision_json
            == expected.decision_json
        )


def test_monotone_does_not_invent_two_sided_direction() -> None:
    data = synthetic("M30", 200)
    bars = tuple(
        replace(
            b,
            open=Decimal(100 + i),
            high=Decimal(101 + i),
            low=Decimal(99 + i),
            close=Decimal(100 + i),
        )
        for i, b in enumerate(data.bars)
    )
    d = engine.evaluate(replace(data, bars=bars), bars[-1].completed_at).document()["decision"]
    assert d["regime"] == "UNCERTAIN"
    assert d["structure_status"] == "ACTIVE_TWO_SIDED_HISTORY_INSUFFICIENT"


def test_legitimate_active_expiry_is_not_recent_pivot_loss() -> None:
    from tools.research.paqs_q.r02.compare import event_changes

    data = synthetic("M30", 224, "oscillation")
    found = False
    for i in range(199, 223):
        old = engine.evaluate(data, data.bars[i].completed_at).document()["decision"]
        if not any(p["extreme"] == 40 for p in old["active_pivots"]):
            continue
        new = engine.evaluate(data, data.bars[i + 1].completed_at).document()["decision"]
        items = data.bars[i - 198 : i + 2]
        change = event_changes(
            old,
            new,
            {b.ref for b in items[40:]},
            data.bars[i].completed_at,
            {b.ref: b.completed_at for b in data.bars},
        )
        assert len(change["expired"]) >= 1
        assert all(p[2] not in {b.ref for b in items[40:]} for p in change["expired"])
        assert not set(map(tuple, change["expired"])) & set(map(tuple, change["lost"]))
        found = True
    assert found, "fixture must exercise actual normal-window expiry"


def test_warm_comparators_and_unfinished_extremes_never_supply_direction() -> None:
    data = synthetic("D1", 312, "bull")
    normal = engine.evaluate(data, data.bars[-1].completed_at)
    unfinished = replace(data.bars[-1], high=Decimal(999999), completed=False)
    other = replace(data, bars=(*data.bars, unfinished))
    assert engine.evaluate(other, data.bars[-1].completed_at).decision_json == normal.decision_json
    # Deliberately narrow active evidence is a diagnostic-only gate oracle, not a candidate horizon.
    d = engine.calculate_window(
        data, data.bars, data.bars[-1].completed_at, Parameters.default("D1"), 309, diagnostic=True
    ).document()["decision"]
    assert d["regime"] == "UNCERTAIN" and d["zones"] == [] and d["range"] is None


def test_atr_exit_hand_oracle_with_fixed_candidate_distance() -> None:
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
    old = baseline.atr_series(bars)
    shifted = baseline.atr_series(bars[1:])
    assert old[13] == Decimal(4)  # (30 + 13*2) /14
    assert old[14] == Decimal("3.733333333333333333")
    assert shifted[13] == Decimal(2)
    assert old[14] is not None and shifted[13] is not None
    # Diagnostic-only held-candidate distance 4; identical lambda, opposite gate outcomes.
    assert not Decimal(4) >= Decimal("1.8") * old[14]
    assert Decimal(4) >= Decimal("1.8") * shifted[13]
