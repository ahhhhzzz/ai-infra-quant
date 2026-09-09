"""F02: old information sets are reconstructed from raw versions, never flattened new data."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from tools.research.paqs_q.diagnostics import audit, boundary, structural
from tools.research.paqs_q.engine import calculate_window, evaluate, prepare
from tools.research.paqs_q.fixtures import synthetic
from tools.research.paqs_q.study import boundary_case_lists
from tools.research.paqs_q.temporal import availability_check
from tools.research.paqs_q.types import Parameters

P = Parameters.default("D1")


def test_later_revision_keeps_old_identical_and_marks_confounded() -> None:
    data = synthetic(count=313, pattern="bull")
    old_cutoff, new_cutoff = data.bars[-2].completed_at, data.bars[-1].completed_at
    revision = replace(data.bars[290], high=Decimal(9999), available_at=new_cutoff)
    revised = replace(data, bars=(*data.bars, revision))
    result = boundary(revised, prepare(revised, new_cutoff), P)
    old = evaluate(revised, old_cutoff)
    assert old.decision_json == evaluate(data, old_cutoff).decision_json
    assert len(old.document()["decision"]["active_pivots"]) == 21
    assert result["arms"]["OLD"] == structural(old)
    assert result["arm_decision_hashes"]["OLD"] == old.semantic_hash
    assert result["classification"] == "REVISION_CONFOUNDED"
    assert result["information_change"]["revised_historical_count"] == 1
    assert result["review_required"]
    expected_old_check = availability_check(
        prepare(revised, old_cutoff)[-312:], revised, old_cutoff
    )
    assert result["availability_checks"]["OLD"] == expected_old_check
    for name, check in result["availability_checks"].items():
        assert check["violation_count"] == 0
        assert check["unknown_availability_count"] == 0
        assert (
            check["cutoff"] == (old_cutoff if name in ("OLD", "LEFT") else new_cutoff).isoformat()
        )
        assert check["observation_count"] == result["intervals"][name]
    audited = audit(revised, limit=1)
    assert audited["rows"][0]["boundary_class"] == "REVISION_CONFOUNDED"
    assert audited["future_references"] == 0  # all actual arm inputs checked now.
    assert set(audited["rows"][0]["boundary_availability_checks"]) == {
        "OLD",
        "RIGHT",
        "LEFT",
        "BOTH",
    }
    summary = boundary_case_lists(audited["outliers"])
    assert summary["material_left_only"] == []
    assert summary["revision_confounded_cutoffs"] == [new_cutoff.isoformat()]
    assert any(r["kind"] == "BOUNDARY_REVISION_CONFOUNDED" for r in audited["outliers"])


@pytest.mark.parametrize("missing_prior", [False, True])
def test_delayed_observation_and_missing_old_version_do_not_invent_old_data(
    missing_prior: bool,
) -> None:
    data = synthetic(count=314, pattern="bull")
    cutoff = data.bars[-1].completed_at
    delayed = replace(data.bars[290], available_at=cutoff)
    # In either case no eligible version for this key existed at OLD. Retain its absence.
    raw = tuple(b for i, b in enumerate(data.bars) if i != 290)
    if missing_prior:
        delayed = replace(delayed, high=Decimal(9999))
    changed = replace(data, bars=(*raw, delayed))
    result = boundary(changed, prepare(changed, cutoff)[-313:], P)
    old = evaluate(changed, data.bars[-2].completed_at)
    assert result["arms"]["OLD"] == structural(old)
    assert result["arm_decision_hashes"]["OLD"] == old.semantic_hash
    assert result["classification"] == "REVISION_CONFOUNDED"
    assert result["information_change"]["newly_available_historical_count"] == 1
    assert result["horizon_unavailable"]  # RIGHT would contain 314, not the declared 313.
    assert result["arm_input_statuses"]["RIGHT"] == "INVALID"
    assert all(c["violation_count"] == 0 for c in result["availability_checks"].values())


def test_flattened_input_missing_prior_history_is_explicitly_insufficient() -> None:
    data = synthetic(count=313, pattern="bull")
    revised = replace(data.bars[290], high=Decimal(9999), available_at=data.bars[-1].completed_at)
    flattened = replace(
        data, bars=tuple(revised if i == 290 else b for i, b in enumerate(data.bars))
    )
    result = boundary(flattened, prepare(flattened, data.bars[-1].completed_at), P)
    old = evaluate(flattened, data.bars[-2].completed_at)
    assert old.document()["decision"]["structure_status"] == "INSUFFICIENT_FOR_Q_HORIZON"
    assert result["arm_decision_hashes"]["OLD"] == old.semantic_hash
    assert result["classification"] == "REVISION_CONFOUNDED"


def test_no_revision_keeps_original_four_horizons_and_old_identity() -> None:
    data = synthetic(count=313, pattern="bull")
    result = boundary(data, data.bars, P)
    assert result["intervals"] == {"OLD": 312, "RIGHT": 313, "LEFT": 311, "BOTH": 312}
    assert not any(result["information_change"].values())
    assert result["classification"] != "REVISION_CONFOUNDED"
    assert (
        result["arm_decision_hashes"]["OLD"]
        == evaluate(data, data.bars[-2].completed_at).semantic_hash
    )
    assert (
        result["arm_decision_hashes"]["BOTH"]
        == evaluate(data, data.bars[-1].completed_at).semantic_hash
    )


def test_low_level_arm_rejects_future_input_even_when_pivot_is_not_future() -> None:
    data = synthetic(count=313)
    cutoff = data.bars[-2].completed_at
    revision = replace(data.bars[290], available_at=data.bars[-1].completed_at)
    raw = tuple(revision if i == 290 else b for i, b in enumerate(data.bars[:-1]))
    check = availability_check(raw, data, cutoff)
    assert check["availability_violations"] == 1 and check["completion_violations"] == 0
    with pytest.raises(ValueError, match="WINDOW_AVAILABILITY_AFTER_CUTOFF"):
        calculate_window(data, raw, cutoff, P, P.warm)


def test_observational_unknown_is_counted_without_as_of_certification() -> None:
    data = synthetic(count=313)
    data = replace(
        data, mode="OBSERVATIONAL", bars=tuple(replace(b, available_at=None) for b in data.bars)
    )
    result = boundary(data, data.bars, P)
    for name, check in result["availability_checks"].items():
        assert check["unknown_availability_count"] == result["intervals"][name]
        assert check["availability_status"] == "OBSERVATIONAL_UNKNOWN"
        assert check["violation_count"] == 0


def test_future_revision_beyond_both_cutoffs_cannot_change_any_arm() -> None:
    data = synthetic(count=313, pattern="bull")
    future = replace(
        data.bars[290],
        high=Decimal("NaN"),
        coverage="INVALID",
        available_at=data.bars[-1].completed_at + timedelta(days=1),
    )
    changed = replace(data, bars=(*data.bars, future))
    a, b = (boundary(d, prepare(d, data.bars[-1].completed_at), P) for d in (data, changed))
    assert a == b


def test_same_price_later_version_still_has_explicit_information_change() -> None:
    data = synthetic(count=313)
    later = replace(data.bars[290], available_at=data.bars[-1].completed_at)
    changed = replace(data, bars=(*data.bars, later))
    result = boundary(changed, prepare(changed, data.bars[-1].completed_at), P)
    assert result["classification"] == "REVISION_CONFOUNDED"
    assert result["information_change"]["revised_historical_count"] == 1
    assert result["arms"]["OLD"] == structural(evaluate(data, data.bars[-2].completed_at))


def test_every_warm_input_completion_and_unknown_time_is_checked() -> None:
    data = synthetic(count=312)
    cutoff = data.bars[-1].completed_at
    warm_future = replace(data.bars[0], completed_at=cutoff + timedelta(days=1))
    bars = (warm_future, *data.bars[1:])
    assert availability_check(bars, data, cutoff)["completion_violations"] == 1
    with pytest.raises(ValueError, match="WINDOW_COMPLETION_AFTER_CUTOFF"):
        calculate_window(data, bars, cutoff, P, P.warm)
    unknown = (replace(data.bars[0], available_at=None), *data.bars[1:])
    assert availability_check(unknown, data, cutoff)["as_of_unknown_violations"] == 1
    with pytest.raises(ValueError, match="WINDOW_AVAILABILITY_UNKNOWN"):
        calculate_window(data, unknown, cutoff, P, P.warm)
