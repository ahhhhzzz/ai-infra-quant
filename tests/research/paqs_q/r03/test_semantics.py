"""Independent oracles for proposed semantics; preserved baseline tests remain unchanged."""

import json
import os
import subprocess
import sys
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal, Inexact, localcontext
from pathlib import Path

import pytest

from tools.research.paqs_q.engine import prepare
from tools.research.paqs_q.io import read_dataset, write_dataset
from tools.research.paqs_q.r03.models import (
    History,
    advance,
    evaluate,
    kernel,
    projection,
    transition,
)
from tools.research.paqs_q.r03.witnesses import (
    atr_witness,
    enumeration,
    h1_rejection,
    hand,
    integer_oracle,
    local_cases,
    trap,
    write_new,
)
from tools.research.paqs_q.temporal import availability_check, information_change
from tools.research.paqs_q.types import canonical

ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize("mirror", [False, True])
def test_independent_useful_hand_oracle(mirror: bool) -> None:
    data = hand(mirror=mirror)
    result = evaluate(data, data.bars[7].completed_at)
    assert result.status == "VALID" and len(result.events) == 1
    event = result.events[0]
    assert event.kind == ("LOW" if mirror else "HIGH")
    assert event.price == (Decimal(90) if mirror else Decimal(110))
    assert event.extreme_ref == data.bars[2].ref
    assert event.confirmation_ref == data.bars[3].ref
    assert event.support == tuple(b.ref for b in data.bars[:4])
    assert event.available_at == event.reversal_time == data.bars[3].completed_at
    state = advance(History(), result)
    assert state.records[0].recognized_at == data.bars[7].completed_at > event.reversal_time


def test_exact_h1_retained_13_reappearance() -> None:
    result = h1_rejection(ROOT)
    assert result["retained_diagnostic_exact_match"] and result["rediscovered"] == 13


@pytest.mark.parametrize("mirror", [False, True])
def test_original_trap_cost_is_retained(mirror: bool) -> None:
    assert trap(mirror)["omitted_more_extreme_price"] == (110 if mirror else 90)


def test_atr_seed_mechanism_is_not_geometry_tolerance() -> None:
    assert atr_witness()["new_gate"] is True


@pytest.mark.parametrize("shape", ["flat", "up", "down", "dual", "tie", "zero_scale"])
def test_legitimate_uncertainty_no_forced_intrabar_order(shape: str) -> None:
    data = hand()
    bars = []
    for i, b in enumerate(data.bars):
        c = Decimal(100 + i if shape == "up" else 100 - i if shape == "down" else 100)
        bars.append(replace(b, open=c, close=c, high=c + 1, low=c - 1))
    if shape in {"dual", "tie", "zero_scale"}:
        bars[2] = data.bars[2]
    if shape == "dual":
        bars[2] = replace(bars[2], open=Decimal(100), close=Decimal(100), low=Decimal(90))
    if shape == "tie":
        bars[3] = replace(bars[3], high=Decimal(110))
    if shape == "zero_scale":
        bars[1] = replace(bars[1], high=Decimal(100), low=Decimal(100))
    result = evaluate(replace(data, bars=tuple(bars)), bars[7].completed_at)
    assert result.status == "VALID" and not result.events
    assert not advance(History(), result).records


def test_equality_at_threshold_is_accepted_but_extreme_tie_is_not() -> None:
    data = hand()
    bars = list(data.bars)
    bars[2] = replace(
        bars[2], open=Decimal(102), high=Decimal(102), low=Decimal(100), close=Decimal(102)
    )
    assert len(evaluate(replace(data, bars=tuple(bars)), bars[7].completed_at).events) == 1
    bars[3] = replace(bars[3], close=Decimal("100.000000000000000001"))
    assert not evaluate(replace(data, bars=tuple(bars)), bars[7].completed_at).events


def test_raw_prior_veto_includes_unemitted_raw_turn() -> None:
    # Raw centers 1,2,3 alternate. Even vetoed raw2 blocks3; no recursive re-seeding.
    word = (100, 101, 99, 101, 100, 100, 100, 100)
    assert integer_oracle(word) == ()
    assert (
        kernel(
            tuple(Decimal(c + 1) for c in word),
            tuple(Decimal(c - 1) for c in word),
            tuple(Decimal(c) for c in word),
        )
        == ()
    )


def test_endpoint_loss_and_support_cost_never_relabelled_expiry() -> None:
    cases = local_cases()
    lost = cases["center2_warm0"]["metrics"]
    assert (
        lost["lost"],
        lost["expired"],
        lost["endpoint_opportunities"],
        lost["full_support_opportunities"],
    ) == (1, 0, 1, 0)
    expired = cases["center2_warm2"]["metrics"]
    assert (expired["lost"], expired["expired"]) == (0, 1)


def test_history_origin_counterexample_and_saved_immutability() -> None:
    data = hand()
    old, new = [evaluate(data, data.bars[i].completed_at) for i in (7, 8)]
    state = advance(History(), old)
    saved = canonical(state)
    after = advance(state, new)
    empty = advance(History(), new)
    assert canonical(state) == saved and after.records == state.records
    assert len(after.records) == 1 and not empty.records
    assert projection(after, new)[0][1] == "CURRENT_UNSUPPORTED"
    with pytest.raises(ValueError, match="SCHEDULE"):
        advance(after, old)


@pytest.mark.parametrize(
    "coverage,quality,status",
    [
        ("BAD", "COMPLETE", "INVALID"),
        ("PARTIAL", "COMPLETE", "INVALID"),
        ("UNKNOWN", "PARTIAL", "INVALID"),
        ("PARTIAL", "PARTIAL", "UNCERTAIN"),
        ("UNKNOWN", "UNKNOWN", "UNCERTAIN"),
        ("COMPLETE", "INVALID", "INVALID"),
    ],
)
def test_quality_public_and_json_no_upgrade(
    tmp_path: Path,
    coverage: str,
    quality: str,
    status: str,
) -> None:
    data = hand()
    bars = list(data.bars)
    bars[4] = replace(bars[4], coverage=coverage)
    data = replace(data, quality=quality, bars=tuple(bars))
    path = tmp_path / "input.json"
    write_dataset(path, data)
    result = evaluate(read_dataset(path), bars[7].completed_at)
    assert result.status == status and not result.events
    assert not advance(History(), result).records


@pytest.mark.parametrize("kind", ["missing", "incomplete", "unknown", "delayed", "gap"])
def test_missing_unavailable_evidence_is_not_reconstructed(kind: str) -> None:
    data = hand(count=8)
    bars = list(data.bars)
    if kind == "missing":
        del bars[0]
    elif kind == "incomplete":
        bars[0] = replace(bars[0], completed=False, high=Decimal("NaN"), coverage="BAD")
    elif kind == "unknown":
        bars[0] = replace(bars[0], available_at=None)
    elif kind == "delayed":
        bars[0] = replace(bars[0], available_at=bars[-1].end + timedelta(hours=1))
    else:
        bars[0] = replace(
            bars[0],
            start=bars[0].start - timedelta(minutes=30),
            end=bars[0].end - timedelta(minutes=30),
        )
    result = evaluate(replace(data, bars=tuple(bars)), data.bars[-1].end)
    assert result.status == "UNCERTAIN" and not result.events


def test_every_support_time_revision_isolation_and_separate_attribution() -> None:
    data = hand(center=4)
    old, new = data.bars[7].completed_at, data.bars[8].completed_at
    revision = replace(data.bars[2], high=Decimal(150), available_at=new)
    raw = replace(data, bars=(*data.bars, revision))
    assert evaluate(raw, old) == evaluate(data, old)
    selected_old, selected_new = prepare(raw, old)[-8:], prepare(raw, new)[-8:]
    assert (
        information_change(selected_old, selected_new, old, selected_new[0].start)[
            "revised_historical_count"
        ]
        == 1
    )
    for cutoff, selected in ((old, selected_old), (new, selected_new)):
        assert availability_check(selected, raw, cutoff)["violation_count"] == 0
        for event in evaluate(raw, cutoff).events:
            assert event.available_at <= cutoff and event.reversal_time <= cutoff
    before, after = evaluate(raw, old), evaluate(raw, new)
    # Revised negative-veto dependency may remove center4 without revising its endpoint.
    assert before.events and before.events != after.events
    history = advance(advance(History(), before), after)
    assert history.records[0].event == before.events[0]


def test_future_malformed_payload_and_missing_old_version() -> None:
    data = hand(count=8)
    old, new = data.bars[-1].end, data.bars[-1].end + timedelta(hours=1)
    bad = replace(data.bars[0], high=Decimal("NaN"), coverage="BAD", available_at=new)
    raw = replace(data, bars=(*data.bars, bad))
    assert evaluate(raw, old) == evaluate(data, old)
    assert evaluate(raw, new).status == "INVALID"
    delayed = replace(data.bars[0], available_at=new)
    missing = replace(data, bars=(*data.bars[1:], delayed))
    assert evaluate(missing, old).status == "UNCERTAIN"
    assert evaluate(missing, new).status == "VALID"
    event = advance(History(), evaluate(missing, new)).records[0]
    assert event.recognized_at == new and event.event.available_at == new


def test_observational_unknown_is_not_as_of_confirmation() -> None:
    data = hand()
    data = replace(
        data, mode="OBSERVATIONAL", bars=tuple(replace(b, available_at=None) for b in data.bars)
    )
    assert evaluate(data, data.bars[7].end).status == "UNCERTAIN"


def test_prefix_decimal_and_fresh_processes(tmp_path: Path) -> None:
    data = hand(center=4, count=10)
    cutoff = data.bars[8].end
    expected = evaluate(data, cutoff)
    assert expected == evaluate(replace(data, bars=data.bars[1:]), cutoff)
    with localcontext() as context:
        context.prec = 6
        context.traps[Inexact] = True
        assert evaluate(data, cutoff) == expected
    path = tmp_path / "input.json"
    write_dataset(path, data)
    script = (
        "from pathlib import Path; from datetime import datetime; import sys; "
        "from tools.research.paqs_q.io import read_dataset; "
        "from tools.research.paqs_q.r03.models import evaluate; "
        "from tools.research.paqs_q.types import canonical; "
        "print(canonical(evaluate(read_dataset(Path(sys.argv[1])),datetime.fromisoformat(sys.argv[2]))))"
    )
    cmd = [sys.executable, "-c", script, str(path), cutoff.isoformat()]
    outputs = [
        subprocess.check_output(
            cmd, cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT)}, text=True
        ).strip()
        for _ in range(2)
    ]
    assert outputs == [canonical(expected)] * 2


def test_no_duplicate_recognition_of_unchanged_old_event() -> None:
    data = hand(center=4)
    old, new = [evaluate(data, data.bars[i].end, 2) for i in (7, 8)]
    state = advance(advance(History(), old), new)
    assert len(state.records) == 1
    assert transition(old, new)["lost"] == 0
    assert state.records[0].recognized_at == old.cutoff


def test_exclusive_evidence_output(tmp_path: Path) -> None:
    path = tmp_path / "new.json"
    write_new(path, {"label": "SYNTHETIC"})
    with pytest.raises(FileExistsError):
        write_new(path, {})
    assert json.loads(path.read_text())["label"] == "SYNTHETIC"


def test_full_declared_small_domain_and_original_loss_metric() -> None:
    result = enumeration()
    assert result["status"] == "FINITE_DOMAIN_CHECKED" and result["count"] == 19683
    assert result["metrics"]["0"]["lost"] == 3402
    assert result["metrics"]["0"]["endpoint_opportunities"] == 17010
    assert result["metrics"]["0"]["coverage_removed"] == 3402
    assert result["metrics"]["2"]["lost"] == 0
    assert result["metrics"]["2"]["expired"] == 3402


def test_revision_of_support_is_not_endpoint_rewrite_or_pure_expiry() -> None:
    data = hand(center=4)
    old, new = data.bars[7].end, data.bars[8].end
    # A later available same-price version still changes the certificate's information lineage.
    revision = replace(data.bars[2], available_at=new)
    raw = replace(data, bars=(*data.bars, revision))
    a, b = evaluate(raw, old), evaluate(raw, new)
    metrics = transition(a, b)
    assert (metrics["lost"], metrics["expired"], metrics["rediscovered"]) == (0, 0, 0)
    assert metrics["common_endpoint_witness_changed"] == 1
    assert metrics["coverage_removed"] == 1
    state = advance(advance(History(), a), b)
    assert len(state.records) == 2
    assert state.records[0].recognized_at == old and state.records[1].recognized_at == new
    assert state.records[0].event.extreme_ref == state.records[1].event.extreme_ref


def test_strict_model_identity_time_and_numeric_boundaries() -> None:
    data = hand()
    end = data.bars[7].end
    for bad in (
        replace(data.bars[1], security="US.OTHER"),
        replace(data.bars[1], available_at=data.bars[1].start),
        replace(data.bars[1], high=Decimal("1e20")),
        replace(data.bars[1], low=Decimal(0)),
    ):
        bars = list(data.bars)
        bars[1] = bad
        result = evaluate(replace(data, bars=tuple(bars)), end)
        assert result.status == "INVALID" and not result.events
