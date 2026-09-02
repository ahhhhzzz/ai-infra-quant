from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal, getcontext
from itertools import pairwise

import pytest

from ai_infra_quant.core.domain.enums import DataAvailabilityStatus, SnapshotQualityStatus
from ai_infra_quant.core.domain.market_data import DailyBar
from ai_infra_quant.core.domain.paqs_input import (
    AdjustmentBasis,
    AdjustmentMetadata,
    CalendarMetadata,
    DerivedBar,
    DerivedCoverage,
    DerivedTimeframe,
    PaqsInputBundle,
    SourceCoverage,
)
from ai_infra_quant.core.strategy.paqs_structure import (
    AtrPoint,
    BarReference,
    BaseRegime,
    KeyLevelRole,
    KeyLevelSource,
    PaqsStructureConfig,
    Pivot,
    PivotHierarchy,
    PivotType,
    StructureBar,
    StructureTimeframe,
    SwingLabel,
    SwingLabelValue,
    Zone,
    ZoneStatus,
    ZoneTouch,
    build_key_levels,
    build_structure_snapshot,
    build_zone_geometry,
    build_zones,
    calculate_atr,
    detect_pivots,
    detect_ranges,
    determine_base_regime,
    label_swings,
    normalize_structure_bars,
)

NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)
Q = Decimal("0.000000000000000001")


def _bar(
    index: int,
    close: str,
    *,
    high: str | None = None,
    low: str | None = None,
    timeframe: StructureTimeframe = StructureTimeframe.D1,
) -> StructureBar:
    close_value = Decimal(close)
    return StructureBar(
        security="US.SYNTHETIC",
        timeframe=timeframe,
        reference=BarReference(
            index=index,
            key=f"{timeframe.value}:SYNTHETIC:{index:04d}",
            session_date=date(2026, 1, 1) + timedelta(days=index),
        ),
        open=close_value,
        high=Decimal(high) if high is not None else close_value + Decimal("1"),
        low=Decimal(low) if low is not None else close_value - Decimal("1"),
        close=close_value,
        volume=Decimal("100"),
        is_completed=True,
        source_coverage="COMPLETE",
    )


def _bars(count: int, close: str = "102") -> tuple[StructureBar, ...]:
    return tuple(_bar(index, close) for index in range(count))


def _ready_atr(bars: tuple[StructureBar, ...], value: str = "1") -> tuple[AtrPoint, ...]:
    return tuple(AtrPoint(bar.reference, Decimal("2"), Decimal(value)) for bar in bars)


def _pivot(
    index: int,
    pivot_type: PivotType,
    price: str,
    *,
    hierarchy: PivotHierarchy = PivotHierarchy.MAJOR,
    atr: str = "1",
    confirmation_index: int | None = None,
) -> Pivot:
    confirmed_at = index + 1 if confirmation_index is None else confirmation_index
    extreme = BarReference(index, f"D1:SYNTHETIC:{index:04d}")
    confirmation = BarReference(confirmed_at, f"D1:SYNTHETIC:{confirmed_at:04d}")
    return Pivot(
        pivot_id=f"{hierarchy.value}-{pivot_type.value}-{index}-{price}-{confirmed_at}",
        security="US.SYNTHETIC",
        timeframe=StructureTimeframe.D1,
        hierarchy=hierarchy,
        pivot_type=pivot_type,
        price=Decimal(price),
        extreme_source_ref=extreme,
        confirmation_source_ref=confirmation,
        atr_at_confirmation=Decimal(atr),
        lambda_used=Decimal("1.8") if hierarchy is PivotHierarchy.MAJOR else Decimal("1.0"),
        confirmed=True,
        explanation=("synthetic fixture",),
    )


def _touch(index: int, side: str, price: str = "100") -> ZoneTouch:
    pivot_type = PivotType.LOW if side == "L" else PivotType.HIGH
    pivot = _pivot(index, pivot_type, price)
    return ZoneTouch(
        pivot_id=pivot.pivot_id,
        price=pivot.price,
        atr_at_confirmation=pivot.atr_at_confirmation,
        extreme_source_ref=pivot.extreme_source_ref,
        confirmation_source_ref=pivot.confirmation_source_ref,
    )


def _zone(
    zone_id: str,
    role: KeyLevelRole,
    center: str,
    lower: str,
    upper: str,
    indices: tuple[int, ...],
) -> Zone:
    side = "L" if role is KeyLevelRole.SUPPORT else "H"
    touches = tuple(_touch(index, side, center) for index in indices)
    return Zone(
        zone_id=zone_id,
        timeframe=StructureTimeframe.D1,
        role=role,
        status=ZoneStatus.CONFIRMED if len(touches) >= 2 else ZoneStatus.CANDIDATE,
        center=Decimal(center),
        reference_atr=Decimal("1"),
        mad=Decimal("0"),
        half_width=(Decimal(upper) - Decimal(lower)) / Decimal(2),
        lower_bound=Decimal(lower),
        upper_bound=Decimal(upper),
        touches=touches,
        explanation=("synthetic fixture",),
    )


def _regime_inputs(
    high_label: SwingLabelValue,
    low_label: SwingLabelValue,
    *,
    close: str,
) -> tuple[tuple[StructureBar, ...], tuple[Pivot, ...], tuple[SwingLabel, ...]]:
    previous_high = _pivot(10, PivotType.HIGH, "105")
    previous_low = _pivot(15, PivotType.LOW, "100")
    current_high = _pivot(20, PivotType.HIGH, "108")
    current_low = _pivot(25, PivotType.LOW, "102")
    labels = (
        SwingLabel(current_high.pivot_id, previous_high.pivot_id, high_label, Decimal("0.25")),
        SwingLabel(current_low.pivot_id, previous_low.pivot_id, low_label, Decimal("0.25")),
    )
    return (_bars(60, close), (previous_high, previous_low, current_high, current_low), labels)


def _bundle(
    *,
    daily_count: int = 0,
    w1: tuple[DerivedBar, ...] = (),
    m30: tuple[DerivedBar, ...] = (),
    quality: SnapshotQualityStatus = SnapshotQualityStatus.PARTIAL,
) -> PaqsInputBundle:
    daily = tuple(
        DailyBar(
            security="US.SYNTHETIC",
            session_date=date(2026, 1, 1) + timedelta(days=index),
            provider_time=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=index),
            open=Decimal("100"),
            high=Decimal("102"),
            low=Decimal("99"),
            close=Decimal("101"),
            volume=Decimal("1000"),
            is_completed=True,
            retrieved_at=NOW,
        )
        for index in range(daily_count)
    )
    return PaqsInputBundle(
        security_id="00000000-0000-4000-8000-000000000001",
        market="US",
        symbol="SYNTHETIC",
        market_timezone="America/New_York",
        provider="synthetic_test_provider",
        as_of_timestamp=NOW,
        completed_w1_bars=w1,
        completed_d1_bars=daily,
        completed_30m_bars=m30,
        calendar=CalendarMetadata(
            status=DataAvailabilityStatus.AVAILABLE,
            provider="synthetic_test_provider",
            retrieved_at=NOW,
            trading_days=(),
        ),
        adjustment=AdjustmentMetadata(
            basis=AdjustmentBasis.PROVIDER_QFQ_CURRENT,
            adjustment_as_of=NOW,
            historical_replay_safe=False,
        ),
        data_quality=quality,
        warnings=("SYNTHETIC_FIXTURE",),
        source_coverage=SourceCoverage(
            d1_source_count=daily_count,
            w1_completed_count=sum(1 for bar in w1 if bar.is_completed),
            w1_partial_count=sum(1 for bar in w1 if not bar.is_completed),
            minute_source_count=0,
            m30_completed_count=sum(1 for bar in m30 if bar.is_completed),
            m30_partial_count=sum(1 for bar in m30 if not bar.is_completed),
        ),
    )


def test_config_hash_is_canonical_stable_and_decimal_only() -> None:
    first = PaqsStructureConfig()
    equivalent = replace(
        first,
        micro_pivot_atr_lambda=Decimal("1.00"),
        range_inside_ratio=Decimal("0.700"),
    )
    changed = replace(first, micro_pivot_atr_lambda=Decimal("1.1"))

    assert first.config_hash == equivalent.config_hash
    assert first.config_hash != changed.config_hash
    assert len(first.config_hash) == 64
    assert first.canonical_values()["micro_pivot_atr_lambda"] == "1"
    with pytest.raises(TypeError, match="Decimal"):
        replace(first, micro_pivot_atr_lambda=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fixed at 14"):
        replace(first, atr_period=13)


def test_atr_true_range_warmup_seed_recurrence_and_determinism() -> None:
    bars = (
        _bar(0, "10", high="11", low="9"),
        _bar(1, "14.5", high="15", low="14"),
        *(_bar(index, "14.5", high="15.5", low="13.5") for index in range(2, 14)),
        _bar(14, "19.5", high="20", low="19"),
    )
    global_precision = getcontext().prec
    global_rounding = getcontext().rounding
    points = calculate_atr(bars)
    repeated = calculate_atr(bars)
    seed = (Decimal("2") + Decimal("5") + Decimal("2") * 12) / Decimal(14)
    seed = seed.quantize(Q, rounding=ROUND_HALF_EVEN)
    expected_next = (
        Decimal(2) / Decimal(15) * Decimal("5.5") + Decimal(13) / Decimal(15) * seed
    ).quantize(Q, rounding=ROUND_HALF_EVEN)

    assert points == repeated
    assert points[0].true_range == Decimal("2.000000000000000000")
    assert points[1].true_range == Decimal("5.000000000000000000")
    assert all(point.value is None for point in points[:13])
    assert points[13].value == seed
    assert points[14].value == expected_next
    assert points[0].value is None
    assert all(isinstance(point.true_range, Decimal) for point in points)
    assert getcontext().prec == global_precision
    assert getcontext().rounding == global_rounding


def test_zero_atr_is_not_a_pivot_threshold_or_range_divisor() -> None:
    bars = tuple(_bar(index, "100", high="100", low="100") for index in range(60))
    atr = calculate_atr(bars)

    assert atr[-1].value == Decimal("0E-18")
    assert (
        detect_pivots(
            bars,
            atr,
            config=PaqsStructureConfig(),
            hierarchy=PivotHierarchy.MAJOR,
        )
        == ()
    )
    support = _zone("support", KeyLevelRole.SUPPORT, "100", "99.8", "100.2", (0, 10))
    resistance = _zone("resistance", KeyLevelRole.RESISTANCE, "105", "104.8", "105.2", (5, 15))
    assert detect_ranges(bars, atr, (support, resistance), PaqsStructureConfig()) == ((), None)


def test_s05_delayed_close_confirmation_preserves_extreme_and_confirmation_refs() -> None:
    bars = (
        _bar(0, "9.5", high="10", low="9"),
        _bar(1, "10.3", high="10.8", low="9.2"),
        _bar(2, "12.7", high="13", low="10"),
        _bar(3, "12.4", high="12.8", low="10.5"),
        _bar(4, "11.8", high="12.5", low="10.8"),
    )
    pivots = detect_pivots(
        bars,
        _ready_atr(bars),
        config=PaqsStructureConfig(),
        hierarchy=PivotHierarchy.MICRO,
    )

    high = next(pivot for pivot in pivots if pivot.pivot_type is PivotType.HIGH)
    assert high.price == Decimal("13")
    assert high.extreme_source_ref.index == 2
    assert high.confirmation_source_ref.index == 4
    assert high.extreme_source_ref != high.confirmation_source_ref
    assert high.confirmed is True


def test_wick_without_close_reversal_and_minimum_separation_do_not_confirm() -> None:
    config = PaqsStructureConfig()
    bars = (
        _bar(0, "9.5", high="10", low="9"),
        _bar(1, "10.4", high="10.8", low="9.5"),
        _bar(
            2,
            "10.7",
            high="12",
            low="8",
        ),
        _bar(3, "11.2", high="11.5", low="9.8"),
        _bar(4, "10.8", high="14", low="10"),
        _bar(5, "12.8", high="13", low="9"),
    )
    pivots = detect_pivots(
        bars,
        _ready_atr(bars),
        config=config,
        hierarchy=PivotHierarchy.MICRO,
    )

    assert all(pivot.confirmation_source_ref.index != 2 for pivot in pivots)
    assert all(
        pivot.extreme_source_ref.index < pivot.confirmation_source_ref.index for pivot in pivots
    )
    assert all(
        later.extreme_source_ref.index - earlier.extreme_source_ref.index >= config.pivot_min_bars
        for earlier, later in pairwise(pivots)
    )


def test_s06_same_bar_unseeded_ambiguity_confirms_neither_direction() -> None:
    bars = (
        _bar(0, "9.5", high="10", low="9"),
        _bar(1, "10", high="13", low="7"),
    )
    pivots = detect_pivots(
        bars,
        _ready_atr(bars),
        config=PaqsStructureConfig(),
        hierarchy=PivotHierarchy.MICRO,
    )
    assert pivots == ()


def test_micro_and_major_pivot_engines_are_independent() -> None:
    bars = (
        _bar(0, "9.5", high="10", low="9"),
        _bar(1, "10.3", high="10.8", low="9.2"),
        _bar(2, "10.0", high="11", low="10"),
        _bar(3, "9.9", high="10.5", low="9.8"),
    )
    atr = _ready_atr(bars)
    micro = detect_pivots(bars, atr, config=PaqsStructureConfig(), hierarchy=PivotHierarchy.MICRO)
    major = detect_pivots(bars, atr, config=PaqsStructureConfig(), hierarchy=PivotHierarchy.MAJOR)

    assert micro
    assert major == ()
    assert all(pivot.hierarchy is PivotHierarchy.MICRO for pivot in micro)


def test_pivot_minimum_extreme_separation_blocks_early_reversal() -> None:
    bars = (
        _bar(0, "9.5", high="10", low="9"),
        _bar(1, "10.2", high="10.8", low="9.5"),
        _bar(2, "9.5", high="10.7", low="9"),
        _bar(3, "12.5", high="13", low="10"),
        _bar(4, "11.5", high="12.5", low="11"),
    )
    pivots = detect_pivots(
        bars,
        _ready_atr(bars),
        config=PaqsStructureConfig(),
        hierarchy=PivotHierarchy.MICRO,
    )

    assert [pivot.pivot_type for pivot in pivots] == [PivotType.LOW, PivotType.HIGH]
    assert pivots[1].extreme_source_ref.index == 3
    assert pivots[1].confirmation_source_ref.index == 4


def test_s14_prefix_invariance_keeps_confirmed_pivot_facts_immutable() -> None:
    bars = (
        _bar(0, "9.5", high="10", low="9"),
        _bar(1, "10.3", high="10.8", low="9.2"),
        _bar(2, "12.7", high="13", low="10"),
        _bar(3, "11.8", high="12", low="10.8"),
        _bar(4, "9.5", high="11", low="9"),
        _bar(5, "10.5", high="11", low="9.5"),
        _bar(6, "13", high="14", low="10"),
    )
    config = PaqsStructureConfig()
    prefix = detect_pivots(
        bars[:5],
        _ready_atr(bars[:5]),
        config=config,
        hierarchy=PivotHierarchy.MICRO,
    )
    extended = detect_pivots(
        bars,
        _ready_atr(bars),
        config=config,
        hierarchy=PivotHierarchy.MICRO,
    )

    assert tuple(p for p in extended if p.confirmation_source_ref.index <= 4) == prefix


def test_s07_swing_labels_cover_higher_lower_and_equal_tolerance() -> None:
    pivots = (
        _pivot(0, PivotType.HIGH, "10"),
        _pivot(2, PivotType.LOW, "8"),
        _pivot(4, PivotType.HIGH, "12"),
        _pivot(6, PivotType.LOW, "9"),
        _pivot(8, PivotType.HIGH, "12.1"),
        _pivot(10, PivotType.LOW, "9.1"),
        _pivot(12, PivotType.HIGH, "11"),
        _pivot(14, PivotType.LOW, "7"),
    )
    labels = label_swings(pivots, PaqsStructureConfig())

    assert [label.label for label in labels] == [
        SwingLabelValue.HH,
        SwingLabelValue.HL,
        SwingLabelValue.EH,
        SwingLabelValue.EL,
        SwingLabelValue.LH,
        SwingLabelValue.LL,
    ]
    assert all(label.tolerance_used == Decimal("0.250000000000000000") for label in labels)


def test_major_swing_key_levels_exclude_micro_and_unconfirmed_pivots() -> None:
    major = _pivot(0, PivotType.LOW, "100")
    micro = _pivot(5, PivotType.HIGH, "105", hierarchy=PivotHierarchy.MICRO)
    unconfirmed = replace(_pivot(10, PivotType.HIGH, "106"), confirmed=False)
    levels = build_key_levels((major, micro, unconfirmed), (), (), PaqsStructureConfig())

    assert len(levels) == 1
    assert levels[0].source is KeyLevelSource.MAJOR_SWING
    assert levels[0].role is KeyLevelRole.SUPPORT
    assert levels[0].lower_bound == levels[0].upper_bound == Decimal("100")


def test_s08_one_touch_is_candidate_and_roles_never_cross_cluster() -> None:
    pivots = (
        _pivot(0, PivotType.LOW, "100"),
        _pivot(5, PivotType.HIGH, "100"),
    )
    zones = build_zones(pivots, PaqsStructureConfig())

    assert len(zones) == 2
    assert {zone.role for zone in zones} == {
        KeyLevelRole.SUPPORT,
        KeyLevelRole.RESISTANCE,
    }
    assert all(zone.status is ZoneStatus.CANDIDATE for zone in zones)

    candidate_config = replace(
        PaqsStructureConfig(),
        zone_cluster_epsilon_atr=Decimal("0.25"),
        zone_min_halfwidth_atr=Decimal("0.30"),
        zone_merge_iou=Decimal("0.30"),
    )
    overlapping_candidates = build_zones(
        (
            _pivot(0, PivotType.LOW, "100"),
            _pivot(5, PivotType.LOW, "100.26"),
        ),
        candidate_config,
    )
    assert len(overlapping_candidates) == 2
    assert all(zone.status is ZoneStatus.CANDIDATE for zone in overlapping_candidates)


def test_s09_zone_clustering_touch_separation_median_mad_and_clamps() -> None:
    config = PaqsStructureConfig()
    accepted = (
        _pivot(0, PivotType.LOW, "100"),
        _pivot(5, PivotType.LOW, "100.2"),
        _pivot(10, PivotType.LOW, "100.4"),
    )
    zone = build_zones(accepted, config)[0]
    adjacent = build_zones(
        (
            _pivot(0, PivotType.LOW, "100"),
            _pivot(2, PivotType.LOW, "100.1"),
        ),
        config,
    )[0]
    minimum = build_zone_geometry(
        (
            _pivot(0, PivotType.LOW, "100"),
            _pivot(5, PivotType.LOW, "100"),
        ),
        KeyLevelRole.SUPPORT,
        config,
    )
    maximum = build_zone_geometry(
        (
            _pivot(0, PivotType.LOW, "100", atr="2"),
            _pivot(5, PivotType.LOW, "104", atr="2"),
        ),
        KeyLevelRole.SUPPORT,
        replace(config, zone_max_halfwidth_atr=Decimal("0.50")),
    )

    assert zone.status is ZoneStatus.CONFIRMED
    assert zone.center == Decimal("100.200000000000000000")
    assert zone.mad == Decimal("0.200000000000000000")
    assert zone.half_width == Decimal("0.200000000000000000")
    assert adjacent.independent_touch_count == 1
    assert adjacent.status is ZoneStatus.CANDIDATE
    assert minimum.half_width == Decimal("0.150000000000000000")
    assert maximum.half_width == Decimal("1.000000000000000000")


def test_zone_cluster_epsilon_separates_incompatible_observations() -> None:
    zones = build_zones(
        (
            _pivot(0, PivotType.LOW, "100"),
            _pivot(5, PivotType.LOW, "100.6"),
        ),
        PaqsStructureConfig(),
    )
    assert len(zones) == 2


def test_s10_confirmed_zone_merge_tie_break_and_shuffle_are_deterministic() -> None:
    config = replace(
        PaqsStructureConfig(),
        zone_cluster_epsilon_atr=Decimal("0.25"),
        zone_min_touch_separation_bars=3,
        zone_min_halfwidth_atr=Decimal("0.30"),
        zone_merge_iou=Decimal("0.30"),
    )
    pivots = (
        _pivot(0, PivotType.LOW, "100"),
        _pivot(3, PivotType.LOW, "100"),
        _pivot(6, PivotType.LOW, "100.26"),
        _pivot(9, PivotType.LOW, "100.26"),
        _pivot(12, PivotType.LOW, "100.52"),
        _pivot(15, PivotType.LOW, "100.52"),
    )
    forward = build_zones(pivots, config)
    shuffled = build_zones(tuple(reversed(pivots)), config)

    assert forward == shuffled
    assert len(forward) == 2
    merged = min(forward, key=lambda zone: zone.center)
    assert merged.independent_touch_count == 4
    assert {touch.price for touch in merged.touches} == {Decimal("100"), Decimal("100.26")}
    assert build_zones(pivots, config) == forward


def test_range_preconditions_alternation_and_lookback_are_enforced() -> None:
    config = PaqsStructureConfig()
    support = _zone("support", KeyLevelRole.SUPPORT, "100", "99.8", "100.2", (0, 10))
    resistance = _zone("resistance", KeyLevelRole.RESISTANCE, "105", "104.8", "105.2", (5, 15))
    bars = _bars(60)
    candidate_support = _zone("candidate", KeyLevelRole.SUPPORT, "100", "99.8", "100.2", (0,))
    non_alternating_resistance = _zone(
        "non-alt", KeyLevelRole.RESISTANCE, "105", "104.8", "105.2", (20, 25)
    )

    assert detect_ranges(bars, _ready_atr(bars), (candidate_support, resistance), config) == (
        (),
        None,
    )
    assert detect_ranges(bars, _ready_atr(bars), (support, non_alternating_resistance), config) == (
        (),
        None,
    )
    short = _bars(39)
    assert detect_ranges(short, _ready_atr(short), (support, resistance), config) == (
        (),
        None,
    )
    not_ready = list(_ready_atr(bars))
    not_ready[-1] = AtrPoint(bars[-1].reference, Decimal("2"), None)
    assert detect_ranges(bars, tuple(not_ready), (support, resistance), config) == ((), None)


def test_s03_confirmed_range_is_active_and_has_base_regime_precedence() -> None:
    config = PaqsStructureConfig()
    support = _zone("support", KeyLevelRole.SUPPORT, "100", "99.8", "100.2", (0, 10))
    resistance = _zone("resistance", KeyLevelRole.RESISTANCE, "105", "104.8", "105.2", (5, 15))
    bars = _bars(60)
    ranges, active = detect_ranges(bars, _ready_atr(bars), (support, resistance), config)
    bull_bars, major, labels = _regime_inputs(SwingLabelValue.HH, SwingLabelValue.HL, close="102")
    regime = determine_base_regime(
        bars=bull_bars,
        major_pivots=major,
        major_labels=labels,
        active_range=active,
        input_valid=True,
        atr_ready=True,
    )

    assert len(ranges) == 1
    assert active is not None
    assert active.reaction_sequence == ("L", "H", "L", "H")
    assert active.inside_ratio == Decimal("1.000000000000000000")
    assert active.width_atr == Decimal("5.000000000000000000")
    assert regime.value is BaseRegime.RANGE


def test_s11_poor_inside_ratio_invalidates_range() -> None:
    support = _zone("support", KeyLevelRole.SUPPORT, "100", "99.8", "100.2", (0, 10))
    resistance = _zone("resistance", KeyLevelRole.RESISTANCE, "105", "104.8", "105.2", (5, 15))
    closes = ("102",) * 20 + ("110",) * 13 + ("102",) * 27
    bars = tuple(_bar(index, close) for index, close in enumerate(closes))
    assert detect_ranges(bars, _ready_atr(bars), (support, resistance), PaqsStructureConfig()) == (
        (),
        None,
    )


@pytest.mark.parametrize(
    ("resistance_center", "bounds"), [("101", ("100.8", "101.2")), ("113", ("112.8", "113.2"))]
)
def test_s12_range_width_bounds_are_enforced(
    resistance_center: str, bounds: tuple[str, str]
) -> None:
    support = _zone("support", KeyLevelRole.SUPPORT, "100", "99.8", "100.2", (0, 10))
    resistance = _zone(
        "resistance",
        KeyLevelRole.RESISTANCE,
        resistance_center,
        bounds[0],
        bounds[1],
        (5, 15),
    )
    bars = _bars(60, "100.5" if resistance_center == "101" else "105")
    assert detect_ranges(bars, _ready_atr(bars), (support, resistance), PaqsStructureConfig()) == (
        (),
        None,
    )


def test_latest_close_outside_keeps_valid_range_but_not_active() -> None:
    support = _zone("support", KeyLevelRole.SUPPORT, "100", "99.8", "100.2", (0, 10))
    resistance = _zone("resistance", KeyLevelRole.RESISTANCE, "105", "104.8", "105.2", (5, 15))
    bars = (*_bars(59), _bar(59, "106"))
    ranges, active = detect_ranges(
        bars, _ready_atr(bars), (support, resistance), PaqsStructureConfig()
    )
    assert len(ranges) == 1
    assert ranges[0].is_active is False
    assert active is None


def test_s13_multiple_ranges_use_deterministic_active_precedence() -> None:
    support = _zone("support", KeyLevelRole.SUPPORT, "100", "99.8", "100.2", (0, 10))
    resistance_a = _zone("resistance-a", KeyLevelRole.RESISTANCE, "105", "104.8", "105.2", (5, 15))
    resistance_b = _zone(
        "resistance-b", KeyLevelRole.RESISTANCE, "106", "105.8", "106.2", (5, 15, 25)
    )
    bars = _bars(60, "103")
    first = detect_ranges(
        bars,
        _ready_atr(bars),
        (support, resistance_a, resistance_b),
        PaqsStructureConfig(),
    )
    shuffled = detect_ranges(
        bars,
        _ready_atr(bars),
        (resistance_b, support, resistance_a),
        PaqsStructureConfig(),
    )

    assert first == shuffled
    assert len(first[0]) == 2
    assert first[1] is not None
    assert first[1].resistance_zone_id == "resistance-b"


def test_s01_clean_bull_major_structure_and_coherence_boundary() -> None:
    bars, major, labels = _regime_inputs(SwingLabelValue.HH, SwingLabelValue.HL, close="103")
    bull = determine_base_regime(
        bars=bars,
        major_pivots=major,
        major_labels=labels,
        active_range=None,
        input_valid=True,
        atr_ready=True,
    )
    broken_bars = (*bars[:-1], _bar(59, "101"))
    broken = determine_base_regime(
        bars=broken_bars,
        major_pivots=major,
        major_labels=labels,
        active_range=None,
        input_valid=True,
        atr_ready=True,
    )

    assert bull.value is BaseRegime.BULL_TREND
    assert broken.value is BaseRegime.UNCERTAIN


def test_s02_clean_bear_major_structure_and_coherence_boundary() -> None:
    bars, major, labels = _regime_inputs(SwingLabelValue.LH, SwingLabelValue.LL, close="103")
    bear = determine_base_regime(
        bars=bars,
        major_pivots=major,
        major_labels=labels,
        active_range=None,
        input_valid=True,
        atr_ready=True,
    )
    broken_bars = (*bars[:-1], _bar(59, "109"))
    broken = determine_base_regime(
        bars=broken_bars,
        major_pivots=major,
        major_labels=labels,
        active_range=None,
        input_valid=True,
        atr_ready=True,
    )

    assert bear.value is BaseRegime.BEAR_TREND
    assert broken.value is BaseRegime.UNCERTAIN


@pytest.mark.parametrize(
    ("high_label", "low_label"),
    [
        (SwingLabelValue.EH, SwingLabelValue.EL),
        (SwingLabelValue.HH, SwingLabelValue.LL),
    ],
)
def test_equal_conflicting_or_micro_only_structure_is_uncertain(
    high_label: SwingLabelValue, low_label: SwingLabelValue
) -> None:
    bars, major, labels = _regime_inputs(high_label, low_label, close="103")
    result = determine_base_regime(
        bars=bars,
        major_pivots=major,
        major_labels=labels,
        active_range=None,
        input_valid=True,
        atr_ready=True,
    )
    micro_only = determine_base_regime(
        bars=bars,
        major_pivots=(),
        major_labels=(),
        active_range=None,
        input_valid=True,
        atr_ready=True,
    )
    assert result.value is BaseRegime.UNCERTAIN
    assert micro_only.value is BaseRegime.UNCERTAIN


def test_s04_insufficient_history_is_uncertain_and_invalid_input_suppresses_structure() -> None:
    invalid = build_structure_snapshot(
        _bundle(daily_count=60, quality=SnapshotQualityStatus.INVALID),
        calculated_at=NOW,
    )
    insufficient = build_structure_snapshot(_bundle(daily_count=5), calculated_at=NOW)

    assert all(not timeframe.atr_ready for timeframe in invalid.timeframes)
    assert all(not timeframe.major_pivots for timeframe in invalid.timeframes)
    assert all(timeframe.base_regime is BaseRegime.UNCERTAIN for timeframe in invalid.timeframes)
    daily = next(
        timeframe
        for timeframe in insufficient.timeframes
        if timeframe.timeframe is StructureTimeframe.D1
    )
    assert daily.latest_atr is None
    assert daily.base_regime is BaseRegime.UNCERTAIN


def test_range_boundary_key_levels_preserve_zone_geometry() -> None:
    support = _zone("support", KeyLevelRole.SUPPORT, "100", "99.8", "100.2", (0, 10))
    resistance = _zone("resistance", KeyLevelRole.RESISTANCE, "105", "104.8", "105.2", (5, 15))
    ranges, _ = detect_ranges(
        _bars(60),
        _ready_atr(_bars(60)),
        (support, resistance),
        PaqsStructureConfig(),
    )
    levels = build_key_levels((), (support, resistance), ranges, PaqsStructureConfig())

    range_levels = [level for level in levels if level.source is KeyLevelSource.RANGE_BOUNDARY]
    assert len(range_levels) == 2
    assert {(level.lower_bound, level.upper_bound) for level in range_levels} == {
        (support.lower_bound, support.upper_bound),
        (resistance.lower_bound, resistance.upper_bound),
    }


def test_s15_m30_normalization_consumes_only_completed_complete_006a_bars() -> None:
    start = datetime(2026, 9, 1, 13, 30, tzinfo=UTC)

    def derived(index: int, *, completed: bool, coverage: DerivedCoverage) -> DerivedBar:
        return DerivedBar(
            security="US.SYNTHETIC",
            timeframe=DerivedTimeframe.M30,
            interval_start=start + timedelta(minutes=30 * index),
            interval_end=start + timedelta(minutes=30 * (index + 1)),
            open=Decimal("100"),
            high=Decimal("102"),
            low=Decimal("99"),
            close=Decimal("101"),
            volume=Decimal("1000"),
            market_timezone="America/New_York",
            session_type="REGULAR",
            source_bar_count=30 if coverage is DerivedCoverage.COMPLETE else 29,
            expected_source_bar_count=30,
            coverage=coverage,
            is_completed=completed,
        )

    complete = derived(0, completed=True, coverage=DerivedCoverage.COMPLETE)
    incomplete = derived(1, completed=False, coverage=DerivedCoverage.PARTIAL)
    bars = normalize_structure_bars(_bundle(m30=(incomplete, complete)))[StructureTimeframe.M30]

    assert len(bars) == 1
    assert bars[0].reference.index == 0
    assert bars[0].reference.interval_start == complete.interval_start
    assert bars[0].source_coverage == "COMPLETE"


def test_w1_normalization_requires_complete_coverage_and_exclusions_are_invariant() -> None:
    start = datetime(2026, 1, 5, tzinfo=UTC)

    def weekly(index: int, coverage: DerivedCoverage, close: str = "101") -> DerivedBar:
        close_value = Decimal(close)
        expected = None if coverage is DerivedCoverage.UNKNOWN else 5
        return DerivedBar(
            security="US.SYNTHETIC",
            timeframe=DerivedTimeframe.W1,
            interval_start=start + timedelta(weeks=index),
            interval_end=start + timedelta(weeks=index + 1),
            open=close_value,
            high=close_value + Decimal("1"),
            low=close_value - Decimal("1"),
            close=close_value,
            volume=Decimal("1000"),
            market_timezone="America/New_York",
            session_type=None,
            source_bar_count=5,
            expected_source_bar_count=expected,
            coverage=coverage,
            is_completed=True,
        )

    complete = tuple(weekly(index, DerivedCoverage.COMPLETE) for index in range(14))
    excluded = (
        weekly(14, DerivedCoverage.UNKNOWN, "500"),
        weekly(15, DerivedCoverage.PARTIAL, "2"),
    )
    baseline_bundle = _bundle(w1=complete)
    augmented_bundle = _bundle(w1=(*complete, *excluded))
    insufficient_bundle = _bundle(w1=(*complete[:12], *excluded))

    normalized = normalize_structure_bars(augmented_bundle)[StructureTimeframe.W1]
    baseline = build_structure_snapshot(baseline_bundle, calculated_at=NOW).timeframes[0]
    augmented = build_structure_snapshot(augmented_bundle, calculated_at=NOW).timeframes[0]
    insufficient = build_structure_snapshot(insufficient_bundle, calculated_at=NOW).timeframes[0]

    assert len(normalized) == 14
    assert all(bar.source_coverage == DerivedCoverage.COMPLETE.value for bar in normalized)
    assert baseline.bar_count == augmented.bar_count == 14
    assert baseline.atr_ready is augmented.atr_ready is True
    assert baseline == augmented
    assert insufficient.bar_count == 12
    assert insufficient.atr_ready is False
    assert insufficient.latest_atr is None


def test_structure_snapshot_rejects_impossible_calculation_provenance() -> None:
    with pytest.raises(ValueError, match="cannot precede"):
        build_structure_snapshot(
            _bundle(),
            calculated_at=NOW - timedelta(microseconds=1),
        )


def test_structure_snapshot_is_deterministic_except_explicit_calculation_time() -> None:
    bundle = _bundle(daily_count=60)
    first = build_structure_snapshot(bundle, calculated_at=NOW)
    repeated = build_structure_snapshot(bundle, calculated_at=NOW)
    later = build_structure_snapshot(bundle, calculated_at=NOW + timedelta(seconds=1))

    assert first == repeated
    assert first.config_hash == later.config_hash
    assert first.timeframes == later.timeframes
    assert first.calculated_at != later.calculated_at
    assert first.adjustment_metadata.historical_replay_safe is False


def test_active_range_fixture_has_complete_explanation_provenance() -> None:
    support = _zone("support", KeyLevelRole.SUPPORT, "100", "99.8", "100.2", (0, 10))
    resistance = _zone("resistance", KeyLevelRole.RESISTANCE, "105", "104.8", "105.2", (5, 15))
    ranges, active = detect_ranges(
        _bars(60),
        _ready_atr(_bars(60)),
        (support, resistance),
        PaqsStructureConfig(),
    )
    assert ranges
    assert active is not None
    assert active.support_zone_id == support.zone_id
    assert active.resistance_zone_id == resistance.zone_id
    assert "latest_close_inside" in active.explanation
    assert all(zone.touches for zone in (support, resistance))
