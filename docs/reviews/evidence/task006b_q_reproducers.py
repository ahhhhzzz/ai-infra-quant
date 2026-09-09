"""Independent synthetic reproducers for exact implementation a29d2d6.

Run from repository root with PYTHONPATH=src:. (Windows: src;.).
No network, archive, database mutation or production wiring.
Assertions pin observed defects, not the corrected behavior.
"""

import json
from dataclasses import replace
from decimal import Decimal

from tools.research.paqs_q.diagnostics import audit, boundary, structural
from tools.research.paqs_q.engine import evaluate, prepare
from tools.research.paqs_q.fixtures import synthetic
from tools.research.paqs_q.types import Parameters


def main() -> None:
    data = synthetic(count=440, pattern="bull")
    invalid = replace(data, bars=tuple(replace(bar, coverage="INVALID") for bar in data.bars))
    decision = evaluate(invalid, invalid.bars[-1].completed_at).document()["decision"]
    first = {
        "id": "006B-Q-F01",
        "source_bar_coverage": "INVALID for every D1 bar",
        "input_status": decision["input_status"],
        "structure_status": decision["structure_status"],
        "regime": decision["regime"],
        "warnings": decision["warnings"],
    }
    assert first["input_status"] == "COMPLETE"
    assert first["regime"] == "BULL_TREND"
    assert first["warnings"] == []

    data = synthetic(count=313, pattern="bull")
    old_cutoff = data.bars[-2].completed_at
    new_cutoff = data.bars[-1].completed_at
    revision = replace(data.bars[290], high=Decimal("9999"), available_at=new_cutoff)
    revised = replace(data, bars=(*data.bars, revision))
    actual_old = structural(evaluate(revised, old_cutoff))
    clean_old = structural(evaluate(data, old_cutoff))
    selected_at_new = prepare(revised, new_cutoff)
    arms = boundary(revised, selected_at_new, Parameters.default("D1"))
    diagnostics = audit(revised, limit=1)
    second = {
        "id": "006B-Q-F02",
        "old_cutoff": old_cutoff.isoformat(),
        "revision_available_at": revision.available_at.isoformat(),
        "normal_old_evaluation_unchanged": actual_old == clean_old,
        "boundary_old_matches_normal_old": arms["arms"]["OLD"] == actual_old,
        "actual_old_pivot_count": len(actual_old["pivots"]),
        "boundary_old_pivot_count": len(arms["arms"]["OLD"]["pivots"]),
        "audit_future_references": diagnostics["future_references"],
        "classification": arms["classification"],
    }
    assert second["normal_old_evaluation_unchanged"] is True
    assert second["boundary_old_matches_normal_old"] is False
    assert second["actual_old_pivot_count"] == 21
    assert second["boundary_old_pivot_count"] == 19
    assert second["audit_future_references"] == 0
    print(json.dumps([first, second], indent=2))


if __name__ == "__main__":
    main()
