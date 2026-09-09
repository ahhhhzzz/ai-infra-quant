"""Experiments distinguish observational support from missing market acceptance."""

from dataclasses import fields

import pytest

from tools.research.paqs_q.diagnostics import (
    audit,
    boundary,
    classify,
    old_engine,
    run_lengths,
    variants,
)
from tools.research.paqs_q.engine import evaluate
from tools.research.paqs_q.fixtures import synthetic
from tools.research.paqs_q.types import Parameters


@pytest.mark.parametrize(
    "arms,expected",
    [
        ((0, 0, 0, 0), "UNCHANGED"),
        ((0, 1, 0, 1), "RIGHT_ONLY"),
        ((0, 0, 1, 1), "LEFT_ONLY"),
        ((0, 1, 2, 3), "COMBINED_OR_UNRESOLVED"),
        ((0, 1, 1, 1), "COMBINED_OR_UNRESOLVED"),
        ((0, 1, 1, 0), "COMBINED_OR_UNRESOLVED"),
    ],
)
def test_boundary_counterfactual_classification(arms, expected):
    assert classify(*arms) == expected


def test_boundary_real_calculation_uses_four_distinct_windows():
    data = synthetic(count=313, pattern="bull")
    result = boundary(data, data.bars, Parameters.default("D1"))
    assert result["intervals"] == {"OLD": 312, "RIGHT": 313, "LEFT": 311, "BOTH": 312}
    assert set(result["arms"]) == {"OLD", "RIGHT", "LEFT", "BOTH"}
    assert result["classification"] in {
        "UNCHANGED",
        "RIGHT_ONLY",
        "LEFT_ONLY",
        "COMBINED_OR_UNRESOLVED",
    }
    with pytest.raises(ValueError, match="N_PLUS_ONE"):
        boundary(data, data.bars[:-1], Parameters.default("D1"))


def test_one_parameter_at_a_time_and_separate_state_version_runs():
    params = Parameters.default("D1")
    assert len(variants(params)) == 8
    for _, variant in variants(params):
        assert sum(getattr(params, f.name) != getattr(variant, f.name) for f in fields(params)) == 1
    assert run_lengths(["RANGE", "RANGE", None, "RANGE"]) == [2, 1]
    assert run_lengths(["id1", "id2", None, "id2"]) == [1, 1, 1]


def test_old_path_lock_comparison_and_new_origin_bound():
    locked = synthetic(count=440, pattern="path_lock")
    old = old_engine(locked, locked.bars)
    new = evaluate(locked, locked.bars[-1].completed_at).document()["decision"]
    assert len(new["active_pivots"]) >= 10
    assert old["major_pivot_count"] < len(new["active_pivots"])


def test_audit_keeps_shortfall_and_does_not_promote_synthetic_to_market_pass():
    data = synthetic("M30", count=201)
    result = audit(data, limit=3)
    assert result["cutoffs"] == 2 and result["target"] == 3
    assert result["status"] == "INSUFFICIENT"
    assert len(result["rows"]) == 3
    assert result["origin_violations"] == result["future_references"] == 0
    assert result["adjacent_transitions"] == 1
