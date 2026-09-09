"""H1 four-arm calculations with unchanged reviewed availability-2 policy.

Adapted from d50d73e diagnostics.boundary; only calculation functions resolve to H1.
"""

from datetime import datetime
from decimal import Decimal, localcontext
from typing import Any

from ..diagnostics import classify, structural
from ..engine import prepare
from ..temporal import availability_check, information_change
from ..types import CONTEXT, Bar, Dataset, Parameters, Result, q
from .engine import calculate_window, evaluate, failure


def boundary(data: Dataset, bars: tuple[Bar, ...], params: Parameters) -> dict[str, Any]:
    if len(bars) != params.total + 1:
        raise ValueError("BOUNDARY_REQUIRES_N_PLUS_ONE")
    old_cutoff, new_cutoff = bars[-2].completed_at, bars[-1].completed_at
    # bars identifies the requested transition only; raw data retains every version.
    selected_old = prepare(data, old_cutoff)
    selected_new = prepare(data, new_cutoff)
    if bars != selected_new[-params.total - 1 :]:
        raise ValueError("BOUNDARY_TRANSITION_NOT_SELECTED_FROM_SOURCE")
    old_bars = selected_old[-params.total :]
    both_bars = selected_new[-params.total :]
    left_edge = min(old_bars[0].start, bars[0].start) if old_bars else bars[0].start
    change = information_change(selected_old, selected_new, old_cutoff, left_edge)
    right_bars = tuple(b for b in selected_new if old_bars and b.start >= old_bars[0].start)
    left_bars = old_bars[1:]
    arm_bars = {"OLD": old_bars, "RIGHT": right_bars, "LEFT": left_bars, "BOTH": both_bars}
    checks = {
        name: availability_check(items, data, old_cutoff if name in {"OLD", "LEFT"} else new_cutoff)
        for name, items in arm_bars.items()
    }
    with localcontext(CONTEXT):
        old = evaluate(data, old_cutoff, params)
        both = evaluate(data, new_cutoff, params)

        def diagnostic_arm(name: str, expected: int, cutoff: datetime) -> Result:
            items = arm_bars[name]
            if len(items) != expected or len(old_bars) != params.total:
                return failure(data, cutoff, params, "BOUNDARY_HORIZON_UNAVAILABLE")
            try:
                return calculate_window(data, items, cutoff, params, params.warm, diagnostic=True)
            except (ValueError, TypeError, ArithmeticError) as exc:
                return failure(data, cutoff, params, str(exc))

        right = diagnostic_arm("RIGHT", params.total + 1, new_cutoff)
        left = diagnostic_arm("LEFT", params.total - 1, old_cutoff)
        results = dict(zip(("OLD", "RIGHT", "LEFT", "BOTH"), (old, right, left, both), strict=True))
        projections = [structural(r) for r in results.values()]
        confounded = any(change.values())
        horizon_unavailable = len(old_bars) != params.total or len(right_bars) != params.total + 1
        invalid_arm = any(
            r.document()["decision"]["input_status"] == "INVALID" for r in results.values()
        )
        label = (
            "REVISION_CONFOUNDED"
            if confounded
            else "COMBINED_OR_UNRESOLVED"
            if horizon_unavailable or invalid_arm
            else classify(*projections)
        )
        directional = {projections[0]["regime"], projections[3]["regime"]} == {
            "BULL_TREND",
            "BEAR_TREND",
        }
        replaced = projections[0]["pivots"][-1:] != projections[3]["pivots"][-1:]
        atr = both.document()["decision"].get("atr")
        geometry = []
        for role in ("SUPPORT", "RESISTANCE"):
            a = [z for z in projections[0]["zones"] if z[0] == role]
            b = [z for z in projections[3]["zones"] if z[0] == role]
            for before, after in zip(a, b, strict=False):
                if atr and Decimal(atr) > 0:
                    delta = max(
                        abs(Decimal(before[i]) - Decimal(after[i])) for i in (1, 2)
                    ) / Decimal(atr)
                    intersection = max(
                        Decimal(0),
                        min(Decimal(before[2]), Decimal(after[2]))
                        - max(Decimal(before[1]), Decimal(after[1])),
                    )
                    union = max(Decimal(before[2]), Decimal(after[2])) - min(
                        Decimal(before[1]), Decimal(after[1])
                    )
                    geometry.append(
                        {
                            "role": role,
                            "bound_delta_atr": str(q(delta)),
                            "iou": str(q(intersection / union)) if union else "0",
                        }
                    )
        before_range, after_range = projections[0]["range"], projections[3]["range"]
        if before_range and after_range and atr and Decimal(atr) > 0:
            lower_a, upper_a = map(Decimal, before_range)
            lower_b, upper_b = map(Decimal, after_range)
            intersection = max(Decimal(0), min(upper_a, upper_b) - max(lower_a, lower_b))
            union = max(upper_a, upper_b) - min(lower_a, lower_b)
            geometry.append(
                {
                    "role": "RANGE",
                    "bound_delta_atr": str(
                        q(max(abs(lower_a - lower_b), abs(upper_a - upper_b)) / Decimal(atr))
                    ),
                    "iou": str(q(intersection / union)) if union else "0",
                }
            )
        material = (
            directional
            or replaced
            or any(Decimal(g["bound_delta_atr"]) > Decimal("0.5") for g in geometry)
            or projections[0]["range"] != projections[3]["range"]
            or len(projections[0]["zones"]) != len(projections[3]["zones"])
        )
        return {
            "classification": label,
            "diagnostic_version": "availability-2",
            "information_change": change,
            "horizon_unavailable": horizon_unavailable,
            "availability_checks": checks,
            "arm_decision_hashes": {name: r.semantic_hash for name, r in results.items()},
            "arm_input_statuses": {
                name: r.document()["decision"]["input_status"] for name, r in results.items()
            },
            "direct_directional_flip": directional,
            "latest_pivot_replaced": replaced,
            "material": material,
            "geometry": geometry,
            "arms": dict(zip(("OLD", "RIGHT", "LEFT", "BOTH"), projections, strict=True)),
            "review_required": confounded or invalid_arm or (label == "LEFT_ONLY" and material),
            "intervals": {
                "OLD": len(old_bars),
                "RIGHT": len(right_bars),
                "LEFT": len(left_bars),
                "BOTH": len(both_bars),
            },
        }
