"""Hand oracles and adversarial invariants for the independent candidate."""

import json
import os
import subprocess
import sys
from dataclasses import replace
from datetime import timedelta
from decimal import ROUND_DOWN, Decimal, localcontext
from itertools import pairwise

import pytest

from tools.research.paqs_q.engine import atr_series, evaluate, labels, pivots, prepare, regime
from tools.research.paqs_q.fixtures import synthetic
from tools.research.paqs_q.types import Evidence, Parameters, Pivot, canonical

D = Decimal


def pivot(kind: str, price: str, index: int, atr: str = "2", confirmed: int | None = None) -> Pivot:
    return Pivot(
        kind,
        D(price),
        index,
        index + 1 if confirmed is None else confirmed,
        f"bar-{index}",
        f"bar-{index + 1}",
        D(atr),
        Evidence("QSTR-005", (), "synthetic hand oracle", None),
        f"{kind}-{index}",
    )


def test_atr_hand_oracle_first_tr_seed_and_ema():
    data = synthetic(count=15)
    bars = tuple(replace(b, open=D(10), high=D(11), low=D(9), close=D(10)) for b in data.bars)
    bars = (*bars[:-1], replace(bars[-1], high=D(13), low=D(8)))
    atr = atr_series(bars)
    assert atr[:13] == (None,) * 13
    assert atr[13] == D(2)
    assert atr[14] == D("2.4")  # (2/15)*5+(13/15)*2, not Wilder.


@pytest.mark.parametrize(
    "difference,expected",
    [("1.799999999999999999", False), ("1.8", True), ("1.800000000000000001", True)],
)
def test_pivot_threshold_exact(difference, expected):
    bars = synthetic(count=2).bars
    bars = (
        replace(bars[0], high=D(10), low=D(8), close=D(9)),
        replace(bars[1], high=D(10), low=D(8), close=D(10) - D(difference)),
    )
    found, ambiguous = pivots(bars, (D(1), D(1)), Parameters.default("D1"))
    assert bool(found) is expected
    assert not ambiguous
    if expected:
        assert (found[0].kind, found[0].extreme, found[0].confirmed) == ("HIGH", 0, 1)
        assert found[0].evidence.threshold == D("1.8")


def test_pivot_tie_update_first_same_bar_gap_and_reverse_sequence():
    # Equal high retains earliest 0. The same-bar new low at 2 cannot be confirmed at 2.
    triples = [(10, 8, 9), (10, 8, 8), (9, 6, 7), (9, 6, 8), (11, 8, 10), (11, 8, 9)]
    bars = tuple(
        replace(b, high=D(h), low=D(low), close=D(c))
        for b, (h, low, c) in zip(synthetic(count=6).bars, triples, strict=True)
    )
    result, _ = pivots(bars, (D(1),) * 6, Parameters.default("D1"))
    assert [(p.kind, p.extreme, p.confirmed) for p in result] == [
        ("HIGH", 0, 1),
        ("LOW", 2, 3),
        ("HIGH", 4, 5),
    ]
    assert all(p.extreme < p.confirmed for p in result)
    assert all(b.extreme - a.extreme >= 2 for a, b in pairwise(result))
    same = replace(bars[0], high=D(20), low=D(1), close=D(10))
    assert not pivots((same,), (D(1),), Parameters.default("D1"))[0]


def test_unseeded_both_thresholds_ambiguous_never_forces_pivot():
    bars = tuple(replace(b, high=D(20), low=D(1), close=D(10)) for b in synthetic(count=4).bars)
    result, ambiguous = pivots(bars, (D(1),) * 4, Parameters.default("D1"))
    assert result == ()
    assert ambiguous == (1, 2, 3)


@pytest.mark.parametrize("tf", ["W1", "D1", "M30"])
def test_origin_invariance_three_prefixes_and_adversarial_extremes(tf):
    data = synthetic(tf, 700, "bull")
    params = Parameters.default(tf)
    cutoff = data.bars[-1].completed_at
    expected = evaluate(replace(data, bars=data.bars[-params.total :]), cutoff)
    for extra in (1, 31, 200):
        prefix = data.bars[-params.total - extra : -params.total]
        prefix = tuple(replace(b, high=D(999999), low=D("0.01")) for b in prefix)
        actual = evaluate(replace(data, bars=prefix + data.bars[-params.total :]), cutoff)
        assert actual.decision_json == expected.decision_json
        assert actual.semantic_hash == expected.semantic_hash
        assert actual.source_hash != expected.source_hash


def test_repeated_cross_process_and_decimal_context_bytes():
    data = synthetic(pattern="bull")
    cutoff = data.bars[-1].completed_at
    expected = evaluate(data, cutoff)
    for precision in (7, 28, 80):
        with localcontext() as ctx:
            ctx.prec, ctx.rounding = precision, ROUND_DOWN
            assert evaluate(data, cutoff).decision_json == expected.decision_json
    script = (
        "from tools.research.paqs_q.fixtures import synthetic; "
        "from tools.research.paqs_q.engine import evaluate; "
        "d=synthetic(pattern='bull'); print(evaluate(d,d.bars[-1].completed_at).semantic_hash)"
    )
    for seed in ("1", "987"):
        output = subprocess.check_output(
            [sys.executable, "-c", script], env={**os.environ, "PYTHONHASHSEED": seed}, text=True
        )
        assert output.strip() == expected.semantic_hash
    document = expected.document()
    document["decision"]["regime"] = "TAMPERED"
    assert expected.document()["decision"]["regime"] != "TAMPERED"


def test_future_versions_incomplete_and_invalid_future_isolation():
    data = synthetic(count=441)
    cutoff = data.bars[-2].completed_at
    original = replace(data, bars=data.bars[:-1])
    expected = evaluate(original, cutoff)
    future = replace(data.bars[-1], high=D("NaN"))
    revision = replace(data.bars[-5], available_at=cutoff + timedelta(days=1), high=D(9999))
    incomplete = replace(data.bars[-4], completed=False, high=D(9999))
    actual = evaluate(replace(data, bars=(*original.bars, future, revision, incomplete)), cutoff)
    assert actual.decision_json == expected.decision_json
    assert actual.source_hash == "NONCANONICAL_SOURCE_ENVELOPE"
    assert all(p["confirmed"] < 312 for p in actual.document()["decision"]["active_pivots"])


def test_availability_order_conflict_and_unknown_are_explicit():
    data = synthetic()
    bar = data.bars[-2]
    revision = replace(bar, high=bar.high + 1, available_at=data.bars[-1].completed_at)
    selected = prepare(replace(data, bars=(*data.bars, revision)), data.bars[-1].completed_at)
    assert selected[-2].high == revision.high
    conflicting = replace(data.bars[-1], high=D(999))
    bad = evaluate(replace(data, bars=(*data.bars, conflicting)), data.bars[-1].completed_at)
    assert bad.document()["decision"]["reasons"] == ["CONFLICTING_TIME_VERSION"]
    unknown = replace(data, bars=tuple(replace(b, available_at=None) for b in data.bars))
    assert (
        evaluate(unknown, bar.completed_at).document()["decision"]["structure_status"]
        == "INSUFFICIENT_FOR_Q_HORIZON"
    )
    observed = evaluate(replace(unknown, mode="OBSERVATIONAL"), data.bars[-1].completed_at)
    assert "HISTORICAL_AVAILABILITY_UNKNOWN" in observed.document()["decision"]["warnings"]


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"high": D(1)}, "OHLC_INVALID"),
        ({"volume": D(-1)}, "NONPOSITIVE_PRICE_OR_NEGATIVE_VOLUME"),
        ({"close": D("Infinity")}, "NONFINITE_OR_NONDECIMAL"),
        ({"adjustment": "OTHER"}, "ADJUSTMENT_BASIS_MISMATCH"),
        ({"security": "HK.00700"}, "BAR_IDENTITY_CONFLICT"),
    ],
)
def test_invalid_data_conservative(change, reason):
    data = synthetic()
    bad = replace(data, bars=(*data.bars[:-1], replace(data.bars[-1], **change)))
    doc = evaluate(bad, data.bars[-1].completed_at).document()["decision"]
    assert doc["regime"] == "UNCERTAIN" and doc["input_status"] == "INVALID"
    assert reason in doc["reasons"] or doc["reasons"] == ["NONFINITE_NUMBER"]
    assert not doc["active_pivots"] and not doc["zones"] and doc["range"] is None


def test_flat_partial_insufficient_and_warm_only_are_honest():
    for data, reason in [
        (synthetic(pattern="flat"), "NONPOSITIVE_ATR"),
        (synthetic(count=311), "INSUFFICIENT_FOR_Q_HORIZON"),
    ]:
        doc = evaluate(data, data.bars[-1].completed_at).document()["decision"]
        assert doc["regime"] == "UNCERTAIN" and doc["structure_status"] == reason
        assert not doc["active_pivots"] and not doc["zones"]
    data = synthetic()
    doc = evaluate(replace(data, quality="PARTIAL"), data.bars[-1].completed_at).document()[
        "decision"
    ]
    assert doc["input_status"] == "PARTIAL"
    assert all(p["extreme"] >= 60 and p["confirmed"] >= 60 for p in doc["active_pivots"])
    # One earlier comparator cannot supply the missing active high/low history.
    ps = (
        pivot("HIGH", "110", 10),
        pivot("LOW", "90", 20),
        pivot("HIGH", "115", 70),
        pivot("LOW", "95", 80),
    )
    ls = labels(ps, 60)
    assert [label.value for label in ls] == ["HH", "HL"]
    assert not any(label.directional_eligible for label in ls)
    assert regime(ps[2:], ls, D(100))[0] == "UNCERTAIN"


def test_direction_requires_latest_two_sided_active_evidence_and_close():
    ps = (
        pivot("HIGH", "110", 60),
        pivot("LOW", "90", 70),
        pivot("HIGH", "115", 80),
        pivot("LOW", "95", 90),
    )
    ls = labels(ps, 60)
    assert regime(ps, ls, D(95))[0] == "BULL_TREND"
    assert regime(ps, ls, D("94.999"))[:2] == ("UNCERTAIN", "CLOSE_BELOW_HL")
    equal = (*ps, pivot("HIGH", "115.5", 100))
    assert labels(equal, 60)[-1].value == "EH"  # tolerance equality is not HH.
    assert regime(equal, labels(equal, 60), D(100))[0] == "UNCERTAIN"
    bearish = tuple(replace(p, price=D(220) - p.price) for p in ps)
    assert regime(bearish, labels(bearish, 60), D(100))[0] == "BEAR_TREND"


def test_canonical_decimal_and_provenance_separation():
    assert canonical((D("1.00"), D("-0.000"))) == '["1","0"]'
    with pytest.raises(TypeError):
        canonical(1.5)
    data = synthetic()
    changed = replace(
        data,
        provenance=(("clock", "different"),),
        bars=tuple(
            replace(b, retrieved_at=b.retrieved_at + timedelta(days=20), source_ref="DIFFERENT")
            for b in data.bars
        ),
    )
    a, b = (evaluate(d, data.bars[-1].completed_at) for d in (data, changed))
    assert a.semantic_hash == b.semantic_hash and a.source_hash != b.source_hash
    decision = json.loads(a.decision_json)
    assert isinstance(decision["atr"], str)
