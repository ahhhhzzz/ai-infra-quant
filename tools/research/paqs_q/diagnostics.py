"""Offline experiments, never production outputs or performance optimization."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal, localcontext
from typing import Any

from .engine import calculate_window, evaluate, failure, prepare
from .temporal import availability_check, information_change
from .types import CONTEXT, Bar, Dataset, Parameters, Result, digest, q


def structural(result: Result) -> dict[str, Any]:
    d = result.document()["decision"]
    return {
        "regime": d["regime"],
        "pivots": [
            (p["kind"], p["price"], p["extreme_ref"], p["confirmed_ref"])
            for p in d["active_pivots"]
        ],
        "zones": [
            (
                z["role"],
                z["lower"],
                z["upper"],
                tuple((p["extreme_ref"], p["confirmed_ref"]) for p in z["touches"]),
            )
            for z in d["zones"]
        ],
        "range": (d["range"]["lower"], d["range"]["upper"]) if d["range"] else None,
    }


def classify(old: Any, right: Any, left: Any, both: Any) -> str:
    if old == right == left == both:
        return "UNCHANGED"
    if both != old and both == right and left == old:
        return "RIGHT_ONLY"
    if both != old and both == left and right == old:
        return "LEFT_ONLY"
    return "COMBINED_OR_UNRESOLVED"


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


def old_engine(data: Dataset, bars: tuple[Bar, ...]) -> dict[str, Any]:
    # Comparison only. The independent engine never imports or invokes this module's baseline.
    from ai_infra_quant.core.strategy import paqs_structure as old

    with localcontext(CONTEXT):
        normalized = tuple(
            old.StructureBar(
                data.security,
                old.StructureTimeframe(data.timeframe),
                old.BarReference(i, b.ref, interval_start=b.start, interval_end=b.end),
                b.open,
                b.high,
                b.low,
                b.close,
                b.volume,
                True,
                b.coverage,
            )
            for i, b in enumerate(bars)
        )
        config = old.PaqsStructureConfig()
        atr = old.calculate_atr(normalized)
        piv = old.detect_pivots(normalized, atr, config=config, hierarchy=old.PivotHierarchy.MAJOR)
        labels = old.label_swings(piv, config)
        zones = old.build_zones(piv, config)
        _, box = old.detect_ranges(normalized, atr, zones, config)
        regime = old.determine_base_regime(
            bars=normalized,
            major_pivots=piv,
            major_labels=labels,
            active_range=box,
            input_valid=True,
            atr_ready=bool(atr and atr[-1].value is not None),
        )
        return {
            "regime": regime.value.value,
            "major_pivot_count": len(piv),
            "latest_refs": [
                (p.extreme_source_ref.key, p.confirmation_source_ref.key) for p in piv[-2:]
            ],
            "confirmed_zones": sum(z.status == old.ZoneStatus.CONFIRMED for z in zones),
            "confirmed_zones_older_than_126": sum(
                z.status == old.ZoneStatus.CONFIRMED
                and len(bars) - 1 - max(t.extreme_source_ref.index for t in z.touches) > 126
                for z in zones
            ),
        }


def variants(params: Parameters) -> tuple[tuple[str, Parameters], ...]:
    lambdas = ("0.9", "1.1") if params.timeframe == "M30" else ("1.7", "1.9")
    result = [("lambda=" + v, replace(params, pivot_lambda=Decimal(v))) for v in lambdas]
    if params.timeframe == "D1":
        result.extend(
            ("epsilon=" + v, replace(params, zone_epsilon=Decimal(v))) for v in ("0.45", "0.55")
        )
        result.extend(("age=" + str(v), replace(params, zone_age=v)) for v in (100, 160))
        result.extend(("range=" + str(v), replace(params, range_length=v)) for v in (30, 60))
    return tuple(result)


def run_lengths(values: list[str | None]) -> list[int]:
    lengths: list[int] = []
    previous = None
    for value in values:
        if value is None:
            previous = None
        elif value == previous:
            lengths[-1] += 1
        else:
            lengths.append(1)
            previous = value
    return lengths


def audit(data: Dataset, limit: int = 100, *, ceiling: datetime | None = None) -> dict[str, Any]:
    params = Parameters.default(data.timeframe)
    if not data.bars:
        return {"status": "UNAVAILABLE", "eligible_bars": 0, "cutoffs": 0, "target": limit}
    ceiling = ceiling or max(b.completed_at for b in data.bars)
    available = prepare(data, ceiling)
    terminals = available[-limit:]
    rows: list[dict[str, Any]] = []
    issues = []
    comparisons: dict[str, dict[str, Any]] = {
        name: {
            "pairs": 0,
            "regime_disagreements": 0,
            "structure_disagreements": 0,
            "range_cutoffs": 0,
            "range_states": [],
            "range_ids": [],
        }
        for name, _ in variants(params)
    }
    previous_index: int | None = None
    previous_regime: str | None = None
    transitions = changes = origin_violations = future_refs = 0
    for terminal in terminals:
        cutoff = terminal.completed_at
        legitimate = prepare(data, cutoff)
        index = len(legitimate) - 1
        if len(legitimate) < params.total:
            rows.append(
                {
                    "cutoff": cutoff.isoformat(),
                    "status": "INSUFFICIENT",
                    "available": len(legitimate),
                }
            )
            previous_index = previous_regime = None
            for stats in comparisons.values():
                stats["range_states"].append(None)
                stats["range_ids"].append(None)
            continue
        current = evaluate(data, cutoff, params)
        d = current.document()["decision"]
        if d["input_status"] == "INVALID":
            rows.append(
                {"cutoff": cutoff.isoformat(), "status": "INVALID", "reasons": d["reasons"]}
            )
            previous_index = previous_regime = None
            for stats in comparisons.values():
                stats["range_states"].append(None)
                stats["range_ids"].append(None)
            continue
        trimmed = evaluate(replace(data, bars=legitimate[-params.total :]), cutoff, params)
        origin_violations += current.semantic_hash != trimmed.semantic_hash
        current_check = availability_check(legitimate[-params.total :], data, cutoff)
        future_refs += current_check["violation_count"]
        if previous_index is not None and index == previous_index + 1:
            transitions += 1
            changes += d["regime"] != previous_regime
        previous_index, previous_regime = index, d["regime"]
        baseline = old_engine(data, legitimate[-params.total :])
        compact: dict[str, Any] = {
            "availability_check": current_check,
            "old_bounded_regime": baseline["regime"],
            "old_bounded_pivots": baseline["major_pivot_count"],
            "cutoff": cutoff.isoformat(),
            "status": "VALID_OBSERVATION",
            "regime": d["regime"],
            "input_status": d["input_status"],
            "structure_status": d["structure_status"],
            "hash": current.semantic_hash,
            "pivots": len(d["active_pivots"]),
            "latest_pivot_age": len(legitimate[-params.total :])
            - 1
            - d["active_pivots"][-1]["extreme"]
            if d["active_pivots"]
            else None,
            "zones": len(d["zones"]),
            "expired_zones": current.document()["diagnostics"]["expired_zone_count"],
            "range_id": d["range"]["identity"] if d["range"] else None,
            "cap_suppressed_ranges": current.document()["diagnostics"][
                "cap_suppressed_range_count"
            ],
        }
        for name, variant in variants(params):
            # OFAT uses the same already-selected observations; full-vs-bounded is checked above.
            other = evaluate(replace(data, bars=legitimate[-params.total :]), cutoff, variant)
            od = other.document()["decision"]
            count = comparisons[name]
            count["pairs"] += 1
            count["regime_disagreements"] += od["regime"] != d["regime"]
            different = structural(other) != structural(current)
            count["structure_disagreements"] += different
            count["range_cutoffs"] += od["regime"] == "RANGE"
            count["range_states"].append("RANGE" if od["regime"] == "RANGE" else None)
            count["range_ids"].append(od["range"]["identity"] if od["range"] else None)
            if different:
                issues.append(
                    {
                        "kind": "PARAMETER_DISAGREEMENT",
                        "cutoff": cutoff.isoformat(),
                        "variant": name,
                        "base_projection_hash": digest("structure", structural(current)),
                        "variant_projection_hash": digest("structure", structural(other)),
                        "base_regime": d["regime"],
                        "variant_regime": od["regime"],
                        "base_pivot_count": len(d["active_pivots"]),
                        "variant_pivot_count": len(od["active_pivots"]),
                        "base_zones": [(z["lower"], z["upper"]) for z in d["zones"]],
                        "variant_zones": [(z["lower"], z["upper"]) for z in od["zones"]],
                    }
                )
        if len(legitimate) >= params.total + 1:
            ablation = boundary(data, legitimate[-params.total - 1 :], params)
            compact["boundary_class"] = ablation["classification"]
            compact["boundary_availability_checks"] = ablation["availability_checks"]
            compact["boundary_information_change"] = ablation["information_change"]
            future_refs += sum(
                check["violation_count"] for check in ablation["availability_checks"].values()
            )
            if ablation["material"] or ablation["review_required"]:
                issues.append(
                    {"kind": "BOUNDARY_MATERIAL", "cutoff": cutoff.isoformat(), **ablation}
                )
        if compact["cap_suppressed_ranges"]:
            issues.append(
                {
                    "kind": "ZONE_CAP_SUPPRESSION",
                    "cutoff": cutoff.isoformat(),
                    "count": compact["cap_suppressed_ranges"],
                }
            )
        rows.append(compact)
    valid = [r for r in rows if r["status"] == "VALID_OBSERVATION"]
    regime_counts = {
        state: sum(r["regime"] == state for r in valid)
        for state in ("BULL_TREND", "BEAR_TREND", "RANGE", "UNCERTAIN")
    }
    for stats in comparisons.values():
        stats["range_state_runs"] = run_lengths(stats.pop("range_states"))
        stats["range_id_runs"] = run_lengths(stats.pop("range_ids"))
    with localcontext(CONTEXT):
        churn = str(q(Decimal(100) * changes / transitions)) if transitions else None
    return {
        "security": data.security,
        "timeframe": data.timeframe,
        "eligible_bars": len(available),
        "supplied_bars": len(data.bars),
        "excluded_or_unavailable_bars": len(data.bars) - len(available),
        "target": limit,
        "status": "COMPLETE_OBSERVATIONAL_SAMPLE" if len(valid) >= limit else "INSUFFICIENT",
        "cutoffs": len(valid),
        "rows": rows,
        "regime_counts": regime_counts,
        "adjacent_transitions": transitions,
        "state_changes": changes,
        "churn_per_100": churn,
        "d1_churn_review": data.timeframe == "D1" and churn is not None and Decimal(churn) > 20,
        "origin_violations": origin_violations,
        "future_references": future_refs,
        "future_reference_scope": (
            "all CURRENT/OLD/RIGHT/LEFT/BOTH input completion and availability; "
            "unknown observational time is not certified"
        ),
        "sensitivity": comparisons,
        "range_state_runs": run_lengths(
            ["RANGE" if r.get("regime") == "RANGE" else None for r in rows]
        ),
        "range_id_runs": run_lengths([r.get("range_id") for r in rows]),
        "outliers": issues,
        "old_new_terminal": {
            "old_full": old_engine(data, available),
            "old_bounded": old_engine(data, available[-params.total :]),
            "new": structural(evaluate(data, ceiling)),
        },
        "provenance": dict(data.provenance),
    }
