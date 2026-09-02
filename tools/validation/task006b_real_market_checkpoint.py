"""Run the approved TASK-006B real-market structure validation checkpoint.

This harness is validation-only. It retrieves quote/history data through the
accepted Futu OpenD adapter and executes the accepted TASK-006A input and
TASK-006B structure services. It does not contain a second structure algorithm.
"""

from __future__ import annotations

import json
import socket
from argparse import Namespace
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, replace
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from itertools import pairwise
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from typing import Any, cast

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from ai_infra_quant.backend.main import create_app
from ai_infra_quant.config import Settings
from ai_infra_quant.core.domain.market_data import DailyBar
from ai_infra_quant.core.domain.paqs_input import DerivedBar, DerivedCoverage, PaqsInputBundle
from ai_infra_quant.core.strategy.paqs_structure import (
    BaseRegime,
    PaqsStructureConfig,
    PaqsStructureSnapshot,
    Pivot,
    PivotType,
    StructureTimeframe,
    SwingLabel,
    TimeframeStructure,
    Zone,
    ZoneStatus,
    build_structure_snapshot,
)
from ai_infra_quant.database.session import create_database_engine

ACCEPTED_TASK006B_SHA = "96747041ef0ff8c00937c5dd5e80cb4c5c28c17c"
PROVIDER_BASIS = "PROVIDER_QFQ_CURRENT"
SECURITIES = (
    ("US", "AVGO"),
    ("US", "VRT"),
    ("HK", "09698"),
    ("US", "NVDA"),
    ("HK", "00700"),
)
REPLAY_D1_TARGET = 500
NO_LOOKAHEAD_SAMPLE_TARGET = 50
SENSITIVITY_D1_TARGET = 250
FUTU_HOST = "127.0.0.1"
FUTU_PORT = 11111


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _decimal(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def _ratio(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.0000"
    return str(
        (Decimal(numerator) / Decimal(denominator)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_EVEN
        )
    )


def _per_100(count: int, bars: int) -> str:
    if bars == 0:
        return "0.00"
    return str(
        (Decimal(count) * Decimal(100) / Decimal(bars)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
    )


def _median_number(values: Sequence[int]) -> str | None:
    if not values:
        return None
    return str(Decimal(str(median(values))).quantize(Decimal("0.01")))


def _reference(reference: Any) -> dict[str, object]:
    return {
        "index": reference.index,
        "key": reference.key,
        "session_date": (
            None if reference.session_date is None else reference.session_date.isoformat()
        ),
        "interval_start": (
            None if reference.interval_start is None else reference.interval_start.isoformat()
        ),
        "interval_end": (
            None if reference.interval_end is None else reference.interval_end.isoformat()
        ),
    }


def _pivot(pivot: Pivot | None) -> dict[str, object] | None:
    if pivot is None:
        return None
    return {
        "id": pivot.pivot_id,
        "hierarchy": pivot.hierarchy.value,
        "type": pivot.pivot_type.value,
        "price": _decimal(pivot.price),
        "extreme": _reference(pivot.extreme_source_ref),
        "confirmation": _reference(pivot.confirmation_source_ref),
        "atr_at_confirmation": _decimal(pivot.atr_at_confirmation),
    }


def _swing(label: SwingLabel) -> dict[str, object]:
    return {
        "pivot_id": label.pivot_id,
        "previous_pivot_id": label.previous_comparable_pivot_id,
        "label": label.label.value,
        "tolerance": _decimal(label.tolerance_used),
    }


def _zone(zone: Zone) -> dict[str, object]:
    return {
        "id": zone.zone_id,
        "role": zone.role.value,
        "status": zone.status.value,
        "center": _decimal(zone.center),
        "lower": _decimal(zone.lower_bound),
        "upper": _decimal(zone.upper_bound),
        "touch_count": zone.independent_touch_count,
        "touch_refs": [touch.extreme_source_ref.key for touch in zone.touches],
    }


def _structure_summary(structure: TimeframeStructure) -> dict[str, object]:
    latest_high = next(
        (pivot for pivot in reversed(structure.major_pivots) if pivot.pivot_type.value == "HIGH"),
        None,
    )
    latest_low = next(
        (pivot for pivot in reversed(structure.major_pivots) if pivot.pivot_type.value == "LOW"),
        None,
    )
    confirmed_zones = [zone for zone in structure.zones if zone.status is ZoneStatus.CONFIRMED]
    active = structure.active_range
    return {
        "timeframe": structure.timeframe.value,
        "role": structure.role.value,
        "bar_count": structure.bar_count,
        "latest_completed_bar_ref": (
            None
            if structure.latest_completed_bar_ref is None
            else _reference(structure.latest_completed_bar_ref)
        ),
        "atr_ready": structure.atr_ready,
        "latest_atr": _decimal(structure.latest_atr),
        "micro_pivot_count": len(structure.micro_pivots),
        "major_pivot_count": len(structure.major_pivots),
        "latest_major_high": _pivot(latest_high),
        "latest_major_low": _pivot(latest_low),
        "latest_major_swing_labels": [_swing(label) for label in structure.major_swing_labels[-4:]],
        "confirmed_zones": [_zone(zone) for zone in confirmed_zones],
        "active_range": (
            None
            if active is None
            else {
                "id": active.range_id,
                "lower": _decimal(active.lower_bound),
                "upper": _decimal(active.upper_bound),
                "inside_ratio": _decimal(active.inside_ratio),
                "width_atr": _decimal(active.width_atr),
                "reaction_sequence": list(active.reaction_sequence),
            }
        ),
        "base_regime": structure.base_regime.value,
        "regime_explanation": list(structure.regime_explanation),
        "warnings": list(structure.warnings),
    }


def _timeframe(
    snapshot: PaqsStructureSnapshot, timeframe: StructureTimeframe
) -> TimeframeStructure:
    return next(item for item in snapshot.timeframes if item.timeframe is timeframe)


def _prefix_bundle(
    bundle: PaqsInputBundle,
    timeframe: StructureTimeframe,
    bars: Sequence[DailyBar] | Sequence[DerivedBar],
) -> PaqsInputBundle:
    if timeframe is StructureTimeframe.D1:
        daily_bars = cast(Sequence[DailyBar], bars)
        return replace(
            bundle,
            completed_w1_bars=(),
            completed_d1_bars=tuple(daily_bars),
            completed_30m_bars=(),
        )
    if timeframe is StructureTimeframe.M30:
        derived_bars = cast(Sequence[DerivedBar], bars)
        return replace(
            bundle,
            completed_w1_bars=(),
            completed_d1_bars=(),
            completed_30m_bars=tuple(derived_bars),
        )
    raise ValueError("prefix replay is limited to D1 and M30")


def _build_prefix(
    bundle: PaqsInputBundle,
    timeframe: StructureTimeframe,
    bars: Sequence[DailyBar] | Sequence[DerivedBar],
    count: int,
    config: PaqsStructureConfig,
) -> TimeframeStructure:
    prefix = _prefix_bundle(bundle, timeframe, bars[:count])
    snapshot = build_structure_snapshot(
        prefix,
        config=config,
        calculated_at=max(_utc_now(), prefix.as_of_timestamp),
    )
    return _timeframe(snapshot, timeframe)


def _replay(
    bundle: PaqsInputBundle,
    timeframe: StructureTimeframe,
    bars: Sequence[DailyBar] | Sequence[DerivedBar],
    config: PaqsStructureConfig,
) -> list[tuple[int, TimeframeStructure]]:
    return [
        (count, _build_prefix(bundle, timeframe, bars, count, config))
        for count in range(config.atr_period, len(bars) + 1)
    ]


def _pivot_signature(pivot: Pivot) -> tuple[object, ...]:
    return (
        pivot.pivot_id,
        pivot.hierarchy.value,
        pivot.pivot_type.value,
        pivot.price,
        pivot.extreme_source_ref,
        pivot.confirmation_source_ref,
        pivot.atr_at_confirmation,
        pivot.lambda_used,
        pivot.confirmed,
    )


def _swing_signature(label: SwingLabel) -> tuple[object, ...]:
    return (
        label.pivot_id,
        label.previous_comparable_pivot_id,
        label.label.value,
        label.tolerance_used,
    )


def _sample_counts(start: int, end: int, target: int) -> tuple[int, ...]:
    if end < start:
        return ()
    available = end - start + 1
    if available <= target:
        return tuple(range(start, end + 1))
    return tuple(
        sorted({start + (offset * (available - 1)) // (target - 1) for offset in range(target)})
    )


def _no_lookahead_audit(
    timeline: Sequence[tuple[int, TimeframeStructure]],
    total_bars: int,
    atr_period: int,
) -> dict[str, object]:
    by_count = dict(timeline)
    cutoffs = _sample_counts(atr_period, total_bars - 1, NO_LOOKAHEAD_SAMPLE_TARGET)
    violations: list[dict[str, object]] = []
    for cutoff in cutoffs:
        later_count = min(total_bars, cutoff + 5)
        prior = by_count[cutoff]
        later = by_count[later_count]
        for hierarchy, prior_pivots, later_pivots, prior_labels, later_labels in (
            (
                "MICRO",
                prior.micro_pivots,
                later.micro_pivots,
                prior.micro_swing_labels,
                later.micro_swing_labels,
            ),
            (
                "MAJOR",
                prior.major_pivots,
                later.major_pivots,
                prior.major_swing_labels,
                later.major_swing_labels,
            ),
        ):
            retained = tuple(
                pivot for pivot in later_pivots if pivot.confirmation_source_ref.index < cutoff
            )
            pivot_match = tuple(map(_pivot_signature, prior_pivots)) == tuple(
                map(_pivot_signature, retained)
            )
            retained_ids = {pivot.pivot_id for pivot in retained}
            retained_labels = tuple(
                label for label in later_labels if label.pivot_id in retained_ids
            )
            label_match = tuple(map(_swing_signature, prior_labels)) == tuple(
                map(_swing_signature, retained_labels)
            )
            if not pivot_match or not label_match:
                violations.append(
                    {
                        "cutoff_bar_count": cutoff,
                        "later_bar_count": later_count,
                        "hierarchy": hierarchy,
                        "pivot_match": pivot_match,
                        "swing_label_match": label_match,
                    }
                )
    return {
        "sampled_cutoff_count": len(cutoffs),
        "cutoffs": list(cutoffs),
        "future_prefix_step_bars": 5,
        "violation_count": len(violations),
        "violations": violations[:10],
    }


def _active_lifetimes(timeline: Sequence[tuple[int, TimeframeStructure]]) -> list[int]:
    lifetimes: list[int] = []
    current_id: str | None = None
    length = 0
    for _, structure in timeline:
        active_id = None if structure.active_range is None else structure.active_range.range_id
        if active_id is not None and active_id == current_id:
            length += 1
        else:
            if current_id is not None:
                lifetimes.append(length)
            current_id = active_id
            length = 1 if active_id is not None else 0
    if current_id is not None:
        lifetimes.append(length)
    return lifetimes


def _stability_metrics(
    timeline: Sequence[tuple[int, TimeframeStructure]], total_bars: int
) -> dict[str, object]:
    if not timeline:
        return {"replay_cutoff_count": 0, "reason": "fewer than 14 legitimate bars"}
    final = timeline[-1][1]
    major_gaps = [
        later.extreme_source_ref.index - earlier.extreme_source_ref.index
        for earlier, later in zip(final.major_pivots, final.major_pivots[1:], strict=False)
    ]
    confirmed_zones = [zone for zone in final.zones if zone.status is ZoneStatus.CONFIRMED]
    regime_counts = Counter(structure.base_regime.value for _, structure in timeline)
    regime_changes = sum(
        left.base_regime is not right.base_regime for (_, left), (_, right) in pairwise(timeline)
    )
    active_count = sum(structure.active_range is not None for _, structure in timeline)
    lifetimes = _active_lifetimes(timeline)
    return {
        "replay_cutoff_count": len(timeline),
        "micro_pivots_per_100_bars": _per_100(len(final.micro_pivots), total_bars),
        "major_pivots_per_100_bars": _per_100(len(final.major_pivots), total_bars),
        "median_bars_between_major_pivots": _median_number(major_gaps),
        "confirmed_zone_count": len(confirmed_zones),
        "median_confirmed_zone_touch_count": _median_number(
            [zone.independent_touch_count for zone in confirmed_zones]
        ),
        "regime_fractions": {
            regime.value: _ratio(regime_counts[regime.value], len(timeline))
            for regime in BaseRegime
        },
        "regime_state_changes": regime_changes,
        "regime_state_changes_per_100_bars": _per_100(regime_changes, len(timeline)),
        "active_range_fraction": _ratio(active_count, len(timeline)),
        "median_active_range_lifetime_bars": _median_number(lifetimes),
    }


def _bar_key(bar: DailyBar | DerivedBar) -> str:
    if isinstance(bar, DailyBar):
        return f"D1:{bar.session_date.isoformat()}"
    return f"{bar.timeframe.value}:{bar.interval_start.isoformat()}"


def _bar_prices(bar: DailyBar | DerivedBar) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    return bar.open, bar.high, bar.low, bar.close


def _edge_cases(
    timeline: Sequence[tuple[int, TimeframeStructure]],
    bars: Sequence[DailyBar] | Sequence[DerivedBar],
) -> dict[str, object]:
    if not timeline:
        return {"reason": "insufficient replay history"}
    by_count = dict(timeline)
    moves: list[tuple[Decimal, int]] = []
    gaps: list[tuple[Decimal, int]] = []
    for index in range(1, len(bars)):
        current_open, _, _, current_close = _bar_prices(bars[index])
        _, _, _, previous_close = _bar_prices(bars[index - 1])
        moves.append((current_close - previous_close, index))
        gaps.append((current_open - previous_close, index))
    atr_observations = [
        (structure.latest_atr, count)
        for count, structure in timeline
        if structure.latest_atr is not None
    ]
    positive_move = max(moves, default=(Decimal(0), 0), key=lambda item: item[0])
    negative_move = min(moves, default=(Decimal(0), 0), key=lambda item: item[0])
    largest_gap = max(gaps, default=(Decimal(0), 0), key=lambda item: abs(item[0]))
    high_atr = max(atr_observations, key=lambda item: item[0] or Decimal(0))
    low_atr = min(atr_observations, key=lambda item: item[0] or Decimal(0))
    dense = max(
        timeline,
        key=lambda item: len(item[1].micro_pivots)
        - len(by_count.get(max(14, item[0] - 20), item[1]).micro_pivots),
    )
    equal_label = next(
        (
            (count, label)
            for count, structure in timeline
            for label in structure.major_swing_labels
            if label.label.value in {"EH", "EL"}
        ),
        None,
    )
    candidate = next(
        (
            (count, zone)
            for count, structure in timeline
            for zone in structure.zones
            if zone.status is ZoneStatus.CANDIDATE
        ),
        None,
    )
    confirmed = next(
        (
            (count, zone)
            for count, structure in timeline
            for zone in structure.zones
            if zone.status is ZoneStatus.CONFIRMED
        ),
        None,
    )
    active = next(
        (
            (count, structure.active_range)
            for count, structure in timeline
            if structure.active_range is not None
        ),
        None,
    )

    def movement(value: tuple[Decimal, int]) -> dict[str, object]:
        return {
            "amount": _decimal(value[0]),
            "bar": _bar_key(bars[value[1]]),
            "previous_bar": _bar_key(bars[max(0, value[1] - 1)]),
        }

    return {
        "largest_positive_close_move": movement(positive_move),
        "largest_negative_close_move": movement(negative_move),
        "largest_absolute_opening_gap": movement(largest_gap),
        "highest_atr": {
            "value": _decimal(high_atr[0]),
            "bar": _bar_key(bars[high_atr[1] - 1]),
        },
        "lowest_ready_atr": {
            "value": _decimal(low_atr[0]),
            "bar": _bar_key(bars[low_atr[1] - 1]),
        },
        "dense_micro_window_end": _bar_key(bars[dense[0] - 1]),
        "dense_micro_total_at_cutoff": len(dense[1].micro_pivots),
        "first_near_equal_major_swing": (
            None
            if equal_label is None
            else {
                "cutoff": _bar_key(bars[equal_label[0] - 1]),
                "label": _swing(equal_label[1]),
            }
        ),
        "first_candidate_zone": (
            None
            if candidate is None
            else {"cutoff": _bar_key(bars[candidate[0] - 1]), "zone": _zone(candidate[1])}
        ),
        "first_confirmed_zone": (
            None
            if confirmed is None
            else {"cutoff": _bar_key(bars[confirmed[0] - 1]), "zone": _zone(confirmed[1])}
        ),
        "first_active_range": (
            None
            if active is None
            else {
                "cutoff": _bar_key(bars[active[0] - 1]),
                "range_id": active[1].range_id,
            }
        ),
        "cutoffs_without_active_range": sum(
            structure.active_range is None for _, structure in timeline
        ),
    }


def _semantic_pivot_identity(structure: TimeframeStructure) -> tuple[object, ...] | None:
    if not structure.major_pivots:
        return None
    pivot = structure.major_pivots[-1]
    return (
        pivot.pivot_type.value,
        _decimal(pivot.price),
        pivot.extreme_source_ref.key,
        pivot.confirmation_source_ref.key,
    )


def _latest_major_type_identity(
    structure: TimeframeStructure, pivot_type: PivotType
) -> tuple[object, ...] | None:
    pivot = next(
        (item for item in reversed(structure.major_pivots) if item.pivot_type is pivot_type),
        None,
    )
    if pivot is None:
        return None
    return (
        pivot.pivot_type.value,
        _decimal(pivot.price),
        pivot.extreme_source_ref.key,
        pivot.confirmation_source_ref.key,
    )


def _semantic_zone_signature(structure: TimeframeStructure) -> tuple[object, ...]:
    return tuple(
        (
            zone.role.value,
            zone.status.value,
            zone.center,
            zone.lower_bound,
            zone.upper_bound,
            tuple(touch.extreme_source_ref.key for touch in zone.touches),
        )
        for zone in structure.zones
    )


def _semantic_active_range(structure: TimeframeStructure) -> tuple[object, ...] | None:
    active = structure.active_range
    if active is None:
        return None
    return (
        active.lower_bound,
        active.upper_bound,
        active.inside_ratio,
        active.width_atr,
        active.reaction_sequence,
    )


def _sensitivity(
    bundle: PaqsInputBundle,
    bars: Sequence[DailyBar],
) -> dict[str, object]:
    subset = bars[-SENSITIVITY_D1_TARGET:]
    default = PaqsStructureConfig()
    counts = range(default.atr_period, len(subset) + 1)
    baseline = {
        count: _build_prefix(bundle, StructureTimeframe.D1, subset, count, default)
        for count in counts
    }
    variants = (
        ("major_pivot_atr_lambda", "1.7", Decimal("1.7")),
        ("major_pivot_atr_lambda", "1.8", Decimal("1.8")),
        ("major_pivot_atr_lambda", "1.9", Decimal("1.9")),
        ("zone_cluster_epsilon_atr", "0.45", Decimal("0.45")),
        ("zone_cluster_epsilon_atr", "0.50", Decimal("0.50")),
        ("zone_cluster_epsilon_atr", "0.55", Decimal("0.55")),
        ("range_inside_ratio", "0.65", Decimal("0.65")),
        ("range_inside_ratio", "0.70", Decimal("0.70")),
        ("range_inside_ratio", "0.75", Decimal("0.75")),
    )
    results: list[dict[str, object]] = []
    for field, value_text, value in variants:
        if field == "major_pivot_atr_lambda":
            config = replace(default, major_pivot_atr_lambda=value)
        elif field == "zone_cluster_epsilon_atr":
            config = replace(default, zone_cluster_epsilon_atr=value)
        else:
            config = replace(default, range_inside_ratio=value)
        changed: Counter[str] = Counter()
        for count in counts:
            comparison = (
                baseline[count]
                if config == default
                else _build_prefix(bundle, StructureTimeframe.D1, subset, count, config)
            )
            reference = baseline[count]
            changed["latest_major_pivot"] += _semantic_pivot_identity(
                reference
            ) != _semantic_pivot_identity(comparison)
            changed["zone_set_or_geometry"] += _semantic_zone_signature(
                reference
            ) != _semantic_zone_signature(comparison)
            changed["active_range"] += _semantic_active_range(reference) != _semantic_active_range(
                comparison
            )
            changed["base_regime"] += reference.base_regime is not comparison.base_regime
        results.append(
            {
                "parameter": field,
                "value": value_text,
                "cutoffs": len(baseline),
                "changed_cutoffs": dict(changed),
            }
        )
    return {
        "d1_subset_bar_count": len(subset),
        "d1_subset_start": None if not subset else _bar_key(subset[0]),
        "d1_subset_end": None if not subset else _bar_key(subset[-1]),
        "cutoff_count": len(baseline),
        "comparisons": results,
    }


def _longest_run(
    timeline: Sequence[tuple[int, TimeframeStructure]], regimes: set[BaseRegime]
) -> tuple[int, TimeframeStructure] | None:
    best: tuple[int, TimeframeStructure] | None = None
    best_length = 0
    current_length = 0
    for item in timeline:
        if item[1].base_regime in regimes:
            current_length += 1
            if current_length > best_length:
                best = item
                best_length = current_length
        else:
            current_length = 0
    return best


def _human_sample(
    category: str,
    selected: tuple[int, TimeframeStructure] | None,
    bars: Sequence[DailyBar],
    criterion: str,
    question: str,
) -> dict[str, object]:
    if selected is None:
        return {
            "category": category,
            "available": False,
            "selection_criterion": criterion,
            "reason": "no qualifying cutoff observed",
            "reviewer_question": question,
        }
    count, structure = selected
    close = bars[count - 1].close
    nearest_zones = sorted(structure.zones, key=lambda zone: abs(zone.center - close))[:4]
    return {
        "category": category,
        "available": True,
        "selection_criterion": criterion,
        "cutoff": _bar_key(bars[count - 1]),
        "preceding_window": {
            "start": _bar_key(bars[max(0, count - 10)]),
            "end": _bar_key(bars[count - 1]),
            "bar_count": min(10, count),
        },
        "latest_close": _decimal(close),
        "atr": _decimal(structure.latest_atr),
        "recent_micro_pivots": [_pivot(pivot) for pivot in structure.micro_pivots[-3:]],
        "recent_major_pivots": [_pivot(pivot) for pivot in structure.major_pivots[-3:]],
        "recent_major_swing_labels": [_swing(label) for label in structure.major_swing_labels[-4:]],
        "nearest_zones": [_zone(zone) for zone in nearest_zones],
        "total_zone_count": len(structure.zones),
        "active_range": (
            None
            if structure.active_range is None
            else {
                "lower": _decimal(structure.active_range.lower_bound),
                "upper": _decimal(structure.active_range.upper_bound),
                "inside_ratio": _decimal(structure.active_range.inside_ratio),
            }
        ),
        "base_regime": structure.base_regime.value,
        "regime_explanation": list(structure.regime_explanation),
        "reviewer_question": question,
    }


def _human_samples(
    timeline: Sequence[tuple[int, TimeframeStructure]], bars: Sequence[DailyBar]
) -> list[dict[str, object]]:
    if not timeline:
        return [
            _human_sample(
                "insufficient_history",
                None,
                bars,
                "D1 replay requires at least 14 completed bars",
                "Is additional real history required?",
            )
        ]
    by_count = dict(timeline)
    trend = _longest_run(timeline, {BaseRegime.BULL_TREND, BaseRegime.BEAR_TREND})
    range_state = _longest_run(timeline, {BaseRegime.RANGE})
    if range_state is None:
        range_state = max(timeline, key=lambda item: len(item[1].micro_pivots))
        range_criterion = "No active Range observed; highest cumulative Micro Pivot count proxy"
    else:
        range_criterion = "End of the longest observed active-Range run"
    shock_index = max(
        range(1, len(bars)),
        key=lambda index: max(
            abs(bars[index].close - bars[index - 1].close),
            abs(bars[index].open - bars[index - 1].close),
        ),
    )
    shock_count = max(PaqsStructureConfig().atr_period, shock_index + 1)
    shock = (shock_count, by_count[shock_count])
    uncertain = _longest_run(timeline, {BaseRegime.UNCERTAIN})
    return [
        _human_sample(
            "trend",
            trend,
            bars,
            "End of the longest BULL_TREND or BEAR_TREND run",
            "Does the Major Pivot sequence support this trend classification?",
        ),
        _human_sample(
            "range_or_choppy",
            range_state,
            bars,
            range_criterion,
            "Do the Zones and reaction sequence represent repeated visible reactions?",
        ),
        _human_sample(
            "volatility_shock_or_gap",
            shock,
            bars,
            "Largest absolute D1 close move or opening gap in the replay window",
            "Did Pivot confirmation remain plausible around this volatility shock?",
        ),
        _human_sample(
            "ambiguous_uncertain",
            uncertain,
            bars,
            "End of the longest UNCERTAIN run",
            "Is UNCERTAIN appropriately conservative here, or is structure missing?",
        ),
    ]


def _legitimate_m30(bundle: PaqsInputBundle) -> tuple[DerivedBar, ...]:
    return tuple(
        bar
        for bar in bundle.completed_30m_bars
        if bar.is_completed and bar.coverage is DerivedCoverage.COMPLETE
    )


def _span(bars: Sequence[DailyBar] | Sequence[DerivedBar]) -> dict[str, object]:
    if not bars:
        return {"bar_count": 0, "start": None, "end": None}
    return {
        "bar_count": len(bars),
        "start": _bar_key(bars[0]),
        "end": _bar_key(bars[-1]),
    }


def _validate_security(container: Any, security_id: str, symbol: str) -> dict[str, Any]:
    state = container.market_data_queries.state(security_id)
    bundle = container.paqs_input_queries.current_bundle(security_id)
    calculated_at = max(_utc_now(), bundle.as_of_timestamp)
    current = build_structure_snapshot(bundle, calculated_at=calculated_at)
    d1_bars = bundle.completed_d1_bars[-REPLAY_D1_TARGET:]
    m30_bars = _legitimate_m30(bundle)
    default = PaqsStructureConfig()
    d1_timeline = _replay(bundle, StructureTimeframe.D1, d1_bars, default)
    m30_timeline = _replay(bundle, StructureTimeframe.M30, m30_bars, default)
    d1_no_lookahead = _no_lookahead_audit(d1_timeline, len(d1_bars), default.atr_period)
    m30_no_lookahead = _no_lookahead_audit(m30_timeline, len(m30_bars), default.atr_period)
    current_by_timeframe = {item.timeframe: item for item in current.timeframes}
    diagnostic_concerns: list[dict[str, object]] = []
    for timeframe, timeline in (
        (StructureTimeframe.D1, d1_timeline),
        (StructureTimeframe.M30, m30_timeline),
    ):
        if timeline and len(timeline[-1][1].major_pivots) > len(timeline[-1][1].micro_pivots):
            diagnostic_concerns.append(
                {
                    "kind": "major_pivot_density_exceeds_micro",
                    "timeframe": timeframe.value,
                    "micro_pivot_count": len(timeline[-1][1].micro_pivots),
                    "major_pivot_count": len(timeline[-1][1].major_pivots),
                    "bar_count": timeline[-1][0],
                }
            )
    if d1_timeline:
        full_d1 = current_by_timeframe[StructureTimeframe.D1]
        replay_d1 = d1_timeline[-1][1]
        full_signature = (
            _latest_major_type_identity(full_d1, PivotType.HIGH),
            _latest_major_type_identity(full_d1, PivotType.LOW),
            full_d1.base_regime.value,
        )
        replay_signature = (
            _latest_major_type_identity(replay_d1, PivotType.HIGH),
            _latest_major_type_identity(replay_d1, PivotType.LOW),
            replay_d1.base_regime.value,
        )
        if full_signature != replay_signature:
            diagnostic_concerns.append(
                {
                    "kind": "d1_history_origin_semantic_divergence",
                    "full_history_bar_count": len(bundle.completed_d1_bars),
                    "replay_bar_count": len(d1_bars),
                    "full_history_signature": full_signature,
                    "latest_500_signature": replay_signature,
                }
            )
    quote = state.quote
    return {
        "security": symbol,
        "quote": {
            "status": quote.status.value,
            "reason": quote.reason,
            "price": None if quote.data is None else _decimal(quote.data.price),
            "is_equity": None if quote.data is None else quote.data.is_equity,
            "retrieved_at": quote.retrieved_at.isoformat(),
        },
        "input": {
            "as_of_timestamp": bundle.as_of_timestamp.isoformat(),
            "calculated_at": calculated_at.isoformat(),
            "quality": bundle.data_quality.value,
            "warnings": list(bundle.warnings),
            "adjustment_basis": bundle.adjustment.basis.value,
            "historical_replay_safe": bundle.adjustment.historical_replay_safe,
            "source_coverage": asdict(bundle.source_coverage),
        },
        "current_structure": {
            item.timeframe.value: _structure_summary(item) for item in current.timeframes
        },
        "replay": {
            "D1": {
                "coverage": _span(d1_bars),
                "terminal_structure": (
                    None if not d1_timeline else _structure_summary(d1_timeline[-1][1])
                ),
                "stability": _stability_metrics(d1_timeline, len(d1_bars)),
                "no_lookahead": d1_no_lookahead,
                "edge_cases": _edge_cases(d1_timeline, d1_bars),
            },
            "M30": {
                "coverage": _span(m30_bars),
                "terminal_structure": (
                    None if not m30_timeline else _structure_summary(m30_timeline[-1][1])
                ),
                "stability": _stability_metrics(m30_timeline, len(m30_bars)),
                "no_lookahead": m30_no_lookahead,
                "edge_cases": _edge_cases(m30_timeline, m30_bars),
            },
        },
        "sensitivity": _sensitivity(bundle, d1_bars),
        "human_review_samples": _human_samples(d1_timeline, d1_bars),
        "diagnostic_concerns": diagnostic_concerns,
    }


def _opend_reachable() -> tuple[bool, str | None]:
    try:
        with socket.create_connection((FUTU_HOST, FUTU_PORT), timeout=3):
            return True, None
    except OSError as exc:
        return False, str(exc)


def run_checkpoint() -> dict[str, object]:
    started_at = _utc_now()
    reachable, reason = _opend_reachable()
    report: dict[str, Any] = {
        "checkpoint": "TASK-006B_REAL_MARKET_STRUCTURE_CHECKPOINT",
        "accepted_task006b_sha": ACCEPTED_TASK006B_SHA,
        "started_at": started_at.isoformat(),
        "provider": "futu_opend_quote",
        "provider_endpoint": f"{FUTU_HOST}:{FUTU_PORT}",
        "adjustment_basis": PROVIDER_BASIS,
        "historical_replay_safe": False,
        "opend_reachable": reachable,
        "opend_reason": reason,
        "securities": {},
        "errors": {},
    }
    if not reachable:
        report["status"] = "BLOCKED_REAL_DATA"
        report["completed_at"] = _utc_now().isoformat()
        return report

    concern_count = 0
    with TemporaryDirectory(prefix="task006b-real-market-") as temporary:
        database_path = Path(temporary) / "validation.db"
        database_url = f"sqlite:///{database_path.resolve().as_posix()}"
        migration = Config("alembic.ini")
        migration.cmd_opts = Namespace(x=[f"database_url={database_url}"])
        command.upgrade(migration, "head")
        engine = create_database_engine(database_url)
        settings = Settings(database_url=database_url, market_data_provider="futu")
        application = create_app(settings, engine)
        with TestClient(application):
            container = application.state.container
            for market, symbol in SECURITIES[3:]:
                try:
                    container.supported_security_service.add(market=market, symbol=symbol)
                except Exception as exc:
                    report["errors"][f"{market}.{symbol}:supported_add"] = str(exc)[:500]
            watchlist = {
                item.security.display_symbol: item.security.id
                for item in container.watchlist_service.get().items
            }
            for market, symbol in SECURITIES:
                display_symbol = f"{market}.{symbol}"
                security_id = watchlist.get(display_symbol)
                if security_id is None:
                    report["errors"][display_symbol] = "Security unavailable in temporary watchlist"
                    continue
                try:
                    result = _validate_security(container, security_id, display_symbol)
                    report["securities"][display_symbol] = result
                    concern_count += len(result["diagnostic_concerns"])
                except Exception as exc:
                    report["errors"][display_symbol] = f"{type(exc).__name__}: {str(exc)[:500]}"
        engine.dispose()

    sufficient = len(report["securities"]) == len(SECURITIES)
    if not sufficient:
        report["status"] = "BLOCKED_REAL_DATA"
    elif concern_count:
        report["status"] = "STRUCTURE_CONCERNS_FOUND"
    else:
        report["status"] = "READY_FOR_HUMAN_REVIEW"
    report["completed_at"] = _utc_now().isoformat()
    return report


def main() -> int:
    report = run_checkpoint()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] != "BLOCKED_REAL_DATA" else 2


if __name__ == "__main__":
    raise SystemExit(main())
