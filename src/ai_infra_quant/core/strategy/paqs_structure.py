from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from enum import StrEnum

from ai_infra_quant.core.domain.common import require_utc
from ai_infra_quant.core.domain.enums import SnapshotQualityStatus
from ai_infra_quant.core.domain.money import canonical_decimal_string, parse_decimal
from ai_infra_quant.core.domain.paqs_input import (
    AdjustmentMetadata,
    DerivedBar,
    DerivedCoverage,
    PaqsInputBundle,
)

_CALCULATION_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
_FINANCIAL_QUANTUM = Decimal("0.000000000000000001")
STRATEGY_VERSION = "PAQS-v0.3.1"
STRUCTURE_VERSION = "TASK-006B-v1"


class StructureTimeframe(StrEnum):
    W1 = "W1"
    D1 = "D1"
    M30 = "M30"


class TimeframeRole(StrEnum):
    CONTEXT = "CONTEXT"
    SETUP = "SETUP"
    TRIGGER = "TRIGGER"


class PivotHierarchy(StrEnum):
    MICRO = "MICRO"
    MAJOR = "MAJOR"


class PivotType(StrEnum):
    HIGH = "HIGH"
    LOW = "LOW"


class SwingLabelValue(StrEnum):
    HH = "HH"
    LH = "LH"
    EH = "EH"
    HL = "HL"
    LL = "LL"
    EL = "EL"


class KeyLevelRole(StrEnum):
    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"
    REFERENCE = "REFERENCE"


class KeyLevelSource(StrEnum):
    MAJOR_SWING = "MAJOR_SWING"
    PIVOT_CLUSTER = "PIVOT_CLUSTER"
    RANGE_BOUNDARY = "RANGE_BOUNDARY"


class ZoneStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    CONFIRMED = "CONFIRMED"


class BaseRegime(StrEnum):
    BULL_TREND = "BULL_TREND"
    BEAR_TREND = "BEAR_TREND"
    RANGE = "RANGE"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True, slots=True)
class PaqsStructureConfig:
    atr_period: int = 14
    micro_pivot_atr_lambda: Decimal = Decimal("1.0")
    major_pivot_atr_lambda: Decimal = Decimal("1.8")
    pivot_min_bars: int = 2
    structure_equal_tolerance_atr: Decimal = Decimal("0.25")
    zone_cluster_epsilon_atr: Decimal = Decimal("0.50")
    zone_min_touch_separation_bars: int = 5
    zone_min_halfwidth_atr: Decimal = Decimal("0.15")
    zone_max_halfwidth_atr: Decimal = Decimal("0.75")
    zone_merge_iou: Decimal = Decimal("0.50")
    range_lookback_bars: int = 40
    range_inside_ratio: Decimal = Decimal("0.70")
    min_range_width_atr: Decimal = Decimal("2.0")
    max_range_width_atr: Decimal = Decimal("12.0")

    def __post_init__(self) -> None:
        if isinstance(self.atr_period, bool) or self.atr_period != 14:
            raise ValueError("atr_period is fixed at 14 for TASK-006B")
        _require_decimal_range(
            self.micro_pivot_atr_lambda, Decimal("1.0"), Decimal("2.5"), "micro lambda"
        )
        _require_decimal_range(
            self.major_pivot_atr_lambda, Decimal("1.0"), Decimal("2.5"), "major lambda"
        )
        _require_int_range(self.pivot_min_bars, 1, 5, "pivot_min_bars")
        _require_decimal_range(
            self.structure_equal_tolerance_atr,
            Decimal("0.10"),
            Decimal("0.50"),
            "structure equal tolerance",
        )
        _require_decimal_range(
            self.zone_cluster_epsilon_atr,
            Decimal("0.25"),
            Decimal("0.90"),
            "zone cluster epsilon",
        )
        _require_int_range(self.zone_min_touch_separation_bars, 3, 20, "zone touch separation")
        _require_decimal_range(
            self.zone_min_halfwidth_atr,
            Decimal("0.10"),
            Decimal("0.30"),
            "zone minimum halfwidth",
        )
        _require_decimal_range(
            self.zone_max_halfwidth_atr,
            Decimal("0.50"),
            Decimal("1.00"),
            "zone maximum halfwidth",
        )
        if self.zone_min_halfwidth_atr > self.zone_max_halfwidth_atr:
            raise ValueError("zone minimum halfwidth cannot exceed maximum halfwidth")
        _require_decimal_range(
            self.zone_merge_iou, Decimal("0.30"), Decimal("0.70"), "zone merge IoU"
        )
        _require_int_range(self.range_lookback_bars, 20, 80, "range lookback")
        _require_decimal_range(
            self.range_inside_ratio, Decimal("0.60"), Decimal("0.85"), "range inside ratio"
        )
        _require_decimal_range(
            self.min_range_width_atr,
            Decimal("1.5"),
            Decimal("4.0"),
            "minimum range width",
        )
        _require_decimal_range(
            self.max_range_width_atr,
            Decimal("8.0"),
            Decimal("20.0"),
            "maximum range width",
        )
        if self.min_range_width_atr > self.max_range_width_atr:
            raise ValueError("minimum range width cannot exceed maximum range width")

    @property
    def config_hash(self) -> str:
        encoded = json.dumps(
            self.canonical_values(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
        return hashlib.sha256(encoded).hexdigest()

    def canonical_values(self) -> dict[str, int | str]:
        return {
            "atr_period": self.atr_period,
            "micro_pivot_atr_lambda": _canonical(self.micro_pivot_atr_lambda),
            "major_pivot_atr_lambda": _canonical(self.major_pivot_atr_lambda),
            "pivot_min_bars": self.pivot_min_bars,
            "structure_equal_tolerance_atr": _canonical(self.structure_equal_tolerance_atr),
            "zone_cluster_epsilon_atr": _canonical(self.zone_cluster_epsilon_atr),
            "zone_min_touch_separation_bars": self.zone_min_touch_separation_bars,
            "zone_min_halfwidth_atr": _canonical(self.zone_min_halfwidth_atr),
            "zone_max_halfwidth_atr": _canonical(self.zone_max_halfwidth_atr),
            "zone_merge_iou": _canonical(self.zone_merge_iou),
            "range_lookback_bars": self.range_lookback_bars,
            "range_inside_ratio": _canonical(self.range_inside_ratio),
            "min_range_width_atr": _canonical(self.min_range_width_atr),
            "max_range_width_atr": _canonical(self.max_range_width_atr),
        }


@dataclass(frozen=True, slots=True)
class BarReference:
    index: int
    key: str
    session_date: date | None = None
    interval_start: datetime | None = None
    interval_end: datetime | None = None

    def __post_init__(self) -> None:
        if self.index < 0 or not self.key:
            raise ValueError("bar reference requires a non-negative index and key")
        if self.interval_start is not None:
            object.__setattr__(self, "interval_start", require_utc(self.interval_start))
        if self.interval_end is not None:
            object.__setattr__(self, "interval_end", require_utc(self.interval_end))


@dataclass(frozen=True, slots=True)
class StructureBar:
    security: str
    timeframe: StructureTimeframe
    reference: BarReference
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    is_completed: bool
    source_coverage: str

    def __post_init__(self) -> None:
        values = tuple(parse_decimal(value) for value in self.ohlcv)
        if min(values[:4]) <= 0 or values[4] < 0:
            raise ValueError("structure OHLC must be positive and volume non-negative")
        if self.high < max(self.open, self.low, self.close) or self.low > min(
            self.open, self.high, self.close
        ):
            raise ValueError("structure OHLC is inconsistent")
        if not self.is_completed:
            raise ValueError("structure engine accepts completed bars only")

    @property
    def ohlcv(self) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
        return self.open, self.high, self.low, self.close, self.volume


@dataclass(frozen=True, slots=True)
class AtrPoint:
    source_ref: BarReference
    true_range: Decimal
    value: Decimal | None


@dataclass(frozen=True, slots=True)
class Pivot:
    pivot_id: str
    security: str
    timeframe: StructureTimeframe
    hierarchy: PivotHierarchy
    pivot_type: PivotType
    price: Decimal
    extreme_source_ref: BarReference
    confirmation_source_ref: BarReference
    atr_at_confirmation: Decimal
    lambda_used: Decimal
    confirmed: bool
    explanation: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SwingLabel:
    pivot_id: str
    previous_comparable_pivot_id: str
    label: SwingLabelValue
    tolerance_used: Decimal


@dataclass(frozen=True, slots=True)
class ZoneTouch:
    pivot_id: str
    price: Decimal
    atr_at_confirmation: Decimal
    extreme_source_ref: BarReference
    confirmation_source_ref: BarReference


@dataclass(frozen=True, slots=True)
class Zone:
    zone_id: str
    timeframe: StructureTimeframe
    role: KeyLevelRole
    status: ZoneStatus
    center: Decimal
    reference_atr: Decimal
    mad: Decimal
    half_width: Decimal
    lower_bound: Decimal
    upper_bound: Decimal
    touches: tuple[ZoneTouch, ...]
    explanation: tuple[str, ...]

    @property
    def independent_touch_count(self) -> int:
        return len(self.touches)


@dataclass(frozen=True, slots=True)
class KeyLevel:
    level_id: str
    timeframe: StructureTimeframe
    role: KeyLevelRole
    source: KeyLevelSource
    lower_bound: Decimal
    upper_bound: Decimal
    source_object_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StructureRange:
    range_id: str
    timeframe: StructureTimeframe
    support_zone_id: str
    resistance_zone_id: str
    lower_bound: Decimal
    upper_bound: Decimal
    inside_ratio: Decimal
    width_atr: Decimal
    total_independent_touch_count: int
    reaction_sequence: tuple[str, ...]
    is_active: bool
    explanation: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RegimeResult:
    value: BaseRegime
    explanation: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TimeframeStructure:
    role: TimeframeRole
    timeframe: StructureTimeframe
    latest_completed_bar_ref: BarReference | None
    bar_count: int
    atr_ready: bool
    latest_atr: Decimal | None
    micro_pivots: tuple[Pivot, ...]
    major_pivots: tuple[Pivot, ...]
    micro_swing_labels: tuple[SwingLabel, ...]
    major_swing_labels: tuple[SwingLabel, ...]
    key_levels: tuple[KeyLevel, ...]
    zones: tuple[Zone, ...]
    valid_ranges: tuple[StructureRange, ...]
    active_range: StructureRange | None
    base_regime: BaseRegime
    regime_explanation: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PaqsStructureSnapshot:
    strategy_version: str
    structure_version: str
    config_hash: str
    config: PaqsStructureConfig
    security_id: str
    market: str
    symbol: str
    market_timezone: str
    provider: str
    as_of_timestamp: datetime
    calculated_at: datetime
    input_quality: SnapshotQualityStatus
    input_warnings: tuple[str, ...]
    adjustment_metadata: AdjustmentMetadata
    timeframes: tuple[TimeframeStructure, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_timestamp", require_utc(self.as_of_timestamp))
        object.__setattr__(self, "calculated_at", require_utc(self.calculated_at))


def normalize_structure_bars(
    bundle: PaqsInputBundle,
) -> dict[StructureTimeframe, tuple[StructureBar, ...]]:
    display_symbol = f"{bundle.market}.{bundle.symbol}"
    eligible_weekly = sorted(
        (
            bar
            for bar in bundle.completed_w1_bars
            if bar.is_completed and bar.coverage is not DerivedCoverage.PARTIAL
        ),
        key=lambda item: item.interval_start,
    )
    weekly = tuple(
        _derived_structure_bar(bar, StructureTimeframe.W1, index)
        for index, bar in enumerate(eligible_weekly)
    )
    daily = tuple(
        StructureBar(
            security=display_symbol,
            timeframe=StructureTimeframe.D1,
            reference=BarReference(
                index=index,
                key=f"D1:{bar.session_date.isoformat()}",
                session_date=bar.session_date,
            ),
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
            is_completed=bar.is_completed,
            source_coverage="COMPLETE",
        )
        for index, bar in enumerate(
            sorted(bundle.completed_d1_bars, key=lambda item: item.session_date)
        )
        if bar.is_completed
    )
    eligible_m30 = sorted(
        (
            bar
            for bar in bundle.completed_30m_bars
            if bar.is_completed and bar.coverage is DerivedCoverage.COMPLETE
        ),
        key=lambda item: item.interval_start,
    )
    m30 = tuple(
        _derived_structure_bar(bar, StructureTimeframe.M30, index)
        for index, bar in enumerate(eligible_m30)
    )
    return {
        StructureTimeframe.W1: weekly,
        StructureTimeframe.D1: daily,
        StructureTimeframe.M30: m30,
    }


def calculate_atr(bars: tuple[StructureBar, ...], period: int = 14) -> tuple[AtrPoint, ...]:
    _require_int_range(period, 1, 1000, "ATR period")
    true_ranges: list[Decimal] = []
    output: list[AtrPoint] = []
    previous_close: Decimal | None = None
    previous_atr: Decimal | None = None
    with localcontext(_CALCULATION_CONTEXT):
        alpha = Decimal(2) / Decimal(period + 1)
        for bar in bars:
            if previous_close is None:
                true_range = _quantize(bar.high - bar.low)
            else:
                true_range = _quantize(
                    max(
                        bar.high - bar.low,
                        abs(bar.high - previous_close),
                        abs(bar.low - previous_close),
                    )
                )
            true_ranges.append(true_range)
            value: Decimal | None = None
            if len(true_ranges) == period:
                value = _quantize(sum(true_ranges, Decimal(0)) / Decimal(period))
            elif len(true_ranges) > period:
                if previous_atr is None:
                    raise AssertionError("ATR recurrence requires its seed")
                value = _quantize(alpha * true_range + (Decimal(1) - alpha) * previous_atr)
            output.append(AtrPoint(bar.reference, true_range, value))
            previous_atr = value if value is not None else previous_atr
            previous_close = bar.close
    return tuple(output)


def detect_pivots(
    bars: tuple[StructureBar, ...],
    atr_points: tuple[AtrPoint, ...],
    *,
    config: PaqsStructureConfig,
    hierarchy: PivotHierarchy,
) -> tuple[Pivot, ...]:
    if len(bars) != len(atr_points):
        raise ValueError("bars and ATR points must be aligned")
    threshold_lambda = (
        config.micro_pivot_atr_lambda
        if hierarchy is PivotHierarchy.MICRO
        else config.major_pivot_atr_lambda
    )
    state = "UNSEEDED"
    candidate_high: tuple[Decimal, BarReference] | None = None
    candidate_low: tuple[Decimal, BarReference] | None = None
    pivots: list[Pivot] = []
    for bar, atr_point in zip(bars, atr_points, strict=True):
        atr = atr_point.value
        if atr is None or atr <= 0:
            continue
        if state == "UNSEEDED":
            candidate_high = _higher_candidate(candidate_high, bar.high, bar.reference)
            candidate_low = _lower_candidate(candidate_low, bar.low, bar.reference)
            down_ready = _reversal_ready(
                candidate_high[0] - bar.close,
                atr,
                threshold_lambda,
                candidate_high[1],
                bar.reference,
            )
            up_ready = _reversal_ready(
                bar.close - candidate_low[0],
                atr,
                threshold_lambda,
                candidate_low[1],
                bar.reference,
            )
            if down_ready == up_ready:
                continue
            if down_ready:
                pivots.append(
                    _pivot(
                        bars[0].security,
                        bar.timeframe,
                        hierarchy,
                        PivotType.HIGH,
                        candidate_high,
                        bar.reference,
                        atr,
                        threshold_lambda,
                        config.config_hash,
                    )
                )
                state = "SEEK_LOW"
                candidate_low = (bar.low, bar.reference)
            else:
                pivots.append(
                    _pivot(
                        bars[0].security,
                        bar.timeframe,
                        hierarchy,
                        PivotType.LOW,
                        candidate_low,
                        bar.reference,
                        atr,
                        threshold_lambda,
                        config.config_hash,
                    )
                )
                state = "SEEK_HIGH"
                candidate_high = (bar.high, bar.reference)
            continue

        previous = pivots[-1]
        if state == "SEEK_HIGH":
            candidate_high = _higher_candidate(candidate_high, bar.high, bar.reference)
            if candidate_high is not None and _can_confirm(
                candidate_high,
                bar.reference,
                candidate_high[0] - bar.close,
                atr,
                threshold_lambda,
                previous,
                config.pivot_min_bars,
            ):
                pivots.append(
                    _pivot(
                        bars[0].security,
                        bar.timeframe,
                        hierarchy,
                        PivotType.HIGH,
                        candidate_high,
                        bar.reference,
                        atr,
                        threshold_lambda,
                        config.config_hash,
                    )
                )
                state = "SEEK_LOW"
                candidate_low = (bar.low, bar.reference)
        else:
            candidate_low = _lower_candidate(candidate_low, bar.low, bar.reference)
            if candidate_low is not None and _can_confirm(
                candidate_low,
                bar.reference,
                bar.close - candidate_low[0],
                atr,
                threshold_lambda,
                previous,
                config.pivot_min_bars,
            ):
                pivots.append(
                    _pivot(
                        bars[0].security,
                        bar.timeframe,
                        hierarchy,
                        PivotType.LOW,
                        candidate_low,
                        bar.reference,
                        atr,
                        threshold_lambda,
                        config.config_hash,
                    )
                )
                state = "SEEK_HIGH"
                candidate_high = (bar.high, bar.reference)
    return tuple(pivots)


def label_swings(pivots: tuple[Pivot, ...], config: PaqsStructureConfig) -> tuple[SwingLabel, ...]:
    previous_by_type: dict[PivotType, Pivot] = {}
    output: list[SwingLabel] = []
    for pivot in pivots:
        if not pivot.confirmed:
            continue
        previous = previous_by_type.get(pivot.pivot_type)
        if previous is not None:
            tolerance = _quantize(config.structure_equal_tolerance_atr * pivot.atr_at_confirmation)
            if pivot.pivot_type is PivotType.HIGH:
                label = (
                    SwingLabelValue.HH
                    if pivot.price > previous.price + tolerance
                    else SwingLabelValue.LH
                    if pivot.price < previous.price - tolerance
                    else SwingLabelValue.EH
                )
            else:
                label = (
                    SwingLabelValue.HL
                    if pivot.price > previous.price + tolerance
                    else SwingLabelValue.LL
                    if pivot.price < previous.price - tolerance
                    else SwingLabelValue.EL
                )
            output.append(
                SwingLabel(
                    pivot_id=pivot.pivot_id,
                    previous_comparable_pivot_id=previous.pivot_id,
                    label=label,
                    tolerance_used=tolerance,
                )
            )
        previous_by_type[pivot.pivot_type] = pivot
    return tuple(output)


def build_zones(pivots: tuple[Pivot, ...], config: PaqsStructureConfig) -> tuple[Zone, ...]:
    output: list[_ZoneBuild] = []
    for pivot_type, role in (
        (PivotType.LOW, KeyLevelRole.SUPPORT),
        (PivotType.HIGH, KeyLevelRole.RESISTANCE),
    ):
        observations = sorted(
            (
                pivot
                for pivot in pivots
                if pivot.confirmed
                and pivot.hierarchy is PivotHierarchy.MAJOR
                and pivot.pivot_type is pivot_type
            ),
            key=_pivot_cluster_sort_key,
        )
        clusters: list[list[Pivot]] = []
        for observation in observations:
            eligible = [
                cluster
                for cluster in clusters
                if all(
                    _pair_distance(observation, member) <= config.zone_cluster_epsilon_atr
                    for member in cluster
                )
            ]
            if not eligible:
                clusters.append([observation])
                continue
            selected = min(
                eligible,
                key=lambda cluster: (
                    _center_distance(observation, cluster),
                    _stable_id("cluster", *(pivot.pivot_id for pivot in cluster)),
                ),
            )
            selected.append(observation)
        for cluster in clusters:
            accepted = _independent_pivots(cluster, config.zone_min_touch_separation_bars)
            output.append(_ZoneBuild(build_zone_geometry(accepted, role, config), accepted))
    return tuple(item.zone for item in _merge_confirmed_zones(output, config))


def detect_ranges(
    bars: tuple[StructureBar, ...],
    atr_points: tuple[AtrPoint, ...],
    zones: tuple[Zone, ...],
    config: PaqsStructureConfig,
) -> tuple[tuple[StructureRange, ...], StructureRange | None]:
    if not bars:
        return (), None
    supports = tuple(
        zone
        for zone in zones
        if zone.role is KeyLevelRole.SUPPORT and zone.status is ZoneStatus.CONFIRMED
    )
    resistances = tuple(
        zone
        for zone in zones
        if zone.role is KeyLevelRole.RESISTANCE and zone.status is ZoneStatus.CONFIRMED
    )
    if len(bars) < config.range_lookback_bars:
        return (), None
    lookback_bars = bars[-config.range_lookback_bars :]
    atr_by_key = {point.source_ref.key: point.value for point in atr_points}
    lookback_atrs = tuple(atr_by_key[bar.reference.key] for bar in lookback_bars)
    if any(value is None for value in lookback_atrs):
        return (), None
    ready_atrs = tuple(value for value in lookback_atrs if value is not None)
    median_atr = _median(ready_atrs)
    if median_atr <= 0:
        return (), None
    valid: list[StructureRange] = []
    for support in supports:
        for resistance in resistances:
            if resistance.lower_bound <= support.upper_bound:
                continue
            reaction_sequence = _alternating_reactions(support, resistance)
            if len(reaction_sequence) < 4:
                continue
            inside_count = sum(
                1
                for bar in lookback_bars
                if support.lower_bound <= bar.close <= resistance.upper_bound
            )
            inside_ratio = _quantize(Decimal(inside_count) / Decimal(config.range_lookback_bars))
            if inside_ratio < config.range_inside_ratio:
                continue
            width_atr = _quantize((resistance.center - support.center) / median_atr)
            if not config.min_range_width_atr <= width_atr <= config.max_range_width_atr:
                continue
            latest_close = bars[-1].close
            is_active = support.lower_bound <= latest_close <= resistance.upper_bound
            range_id = _stable_id(
                "range",
                bars[0].timeframe.value,
                config.config_hash,
                support.zone_id,
                resistance.zone_id,
            )
            valid.append(
                StructureRange(
                    range_id=range_id,
                    timeframe=bars[0].timeframe,
                    support_zone_id=support.zone_id,
                    resistance_zone_id=resistance.zone_id,
                    lower_bound=support.lower_bound,
                    upper_bound=resistance.upper_bound,
                    inside_ratio=inside_ratio,
                    width_atr=width_atr,
                    total_independent_touch_count=(
                        support.independent_touch_count + resistance.independent_touch_count
                    ),
                    reaction_sequence=reaction_sequence,
                    is_active=is_active,
                    explanation=(
                        f"alternating_reactions={len(reaction_sequence)}",
                        f"inside_ratio={_canonical(inside_ratio)}",
                        f"width_atr={_canonical(width_atr)}",
                        "latest_close_inside" if is_active else "latest_close_outside",
                    ),
                )
            )
    valid.sort(key=lambda item: item.range_id)
    active = [item for item in valid if item.is_active]
    selected = (
        min(
            active,
            key=lambda item: (
                -item.total_independent_touch_count,
                -item.inside_ratio,
                item.width_atr,
                item.range_id,
            ),
        )
        if active
        else None
    )
    return tuple(valid), selected


def determine_base_regime(
    *,
    bars: tuple[StructureBar, ...],
    major_pivots: tuple[Pivot, ...],
    major_labels: tuple[SwingLabel, ...],
    active_range: StructureRange | None,
    input_valid: bool,
    atr_ready: bool,
) -> RegimeResult:
    if not input_valid or not bars or not atr_ready:
        return RegimeResult(
            BaseRegime.UNCERTAIN,
            ("input_invalid_or_insufficient",),
        )
    if active_range is not None:
        return RegimeResult(
            BaseRegime.RANGE,
            (f"active_range={active_range.range_id}", "active_range_precedence"),
        )
    pivot_by_id = {pivot.pivot_id: pivot for pivot in major_pivots}
    latest_high = next(
        (
            label
            for label in reversed(major_labels)
            if pivot_by_id[label.pivot_id].pivot_type is PivotType.HIGH
        ),
        None,
    )
    latest_low = next(
        (
            label
            for label in reversed(major_labels)
            if pivot_by_id[label.pivot_id].pivot_type is PivotType.LOW
        ),
        None,
    )
    if latest_high is None or latest_low is None:
        return RegimeResult(BaseRegime.UNCERTAIN, ("major_swing_history_incomplete",))
    latest_close = bars[-1].close
    high_pivot = pivot_by_id[latest_high.pivot_id]
    low_pivot = pivot_by_id[latest_low.pivot_id]
    if latest_high.label is SwingLabelValue.HH and latest_low.label is SwingLabelValue.HL:
        if latest_close >= low_pivot.price:
            return RegimeResult(
                BaseRegime.BULL_TREND,
                (
                    f"latest_major_high={latest_high.label.value}",
                    f"latest_major_low={latest_low.label.value}",
                    f"close_not_below_hl={low_pivot.pivot_id}",
                ),
            )
        return RegimeResult(
            BaseRegime.UNCERTAIN,
            ("bull_labels_present", f"close_below_hl={low_pivot.pivot_id}"),
        )
    if latest_high.label is SwingLabelValue.LH and latest_low.label is SwingLabelValue.LL:
        if latest_close <= high_pivot.price:
            return RegimeResult(
                BaseRegime.BEAR_TREND,
                (
                    f"latest_major_high={latest_high.label.value}",
                    f"latest_major_low={latest_low.label.value}",
                    f"close_not_above_lh={high_pivot.pivot_id}",
                ),
            )
        return RegimeResult(
            BaseRegime.UNCERTAIN,
            ("bear_labels_present", f"close_above_lh={high_pivot.pivot_id}"),
        )
    return RegimeResult(
        BaseRegime.UNCERTAIN,
        (
            f"latest_major_high={latest_high.label.value}",
            f"latest_major_low={latest_low.label.value}",
            "major_labels_equal_conflicting_or_incomplete",
        ),
    )


def build_structure_snapshot(
    bundle: PaqsInputBundle,
    *,
    config: PaqsStructureConfig | None = None,
    calculated_at: datetime,
) -> PaqsStructureSnapshot:
    selected_config = config or PaqsStructureConfig()
    normalized = normalize_structure_bars(bundle)
    input_valid = bundle.data_quality is not SnapshotQualityStatus.INVALID
    timeframes = tuple(
        _timeframe_structure(
            normalized[timeframe],
            role,
            selected_config,
            input_valid=input_valid,
        )
        for timeframe, role in (
            (StructureTimeframe.W1, TimeframeRole.CONTEXT),
            (StructureTimeframe.D1, TimeframeRole.SETUP),
            (StructureTimeframe.M30, TimeframeRole.TRIGGER),
        )
    )
    return PaqsStructureSnapshot(
        strategy_version=STRATEGY_VERSION,
        structure_version=STRUCTURE_VERSION,
        config_hash=selected_config.config_hash,
        config=selected_config,
        security_id=bundle.security_id,
        market=bundle.market,
        symbol=bundle.symbol,
        market_timezone=bundle.market_timezone,
        provider=bundle.provider,
        as_of_timestamp=bundle.as_of_timestamp,
        calculated_at=calculated_at,
        input_quality=bundle.data_quality,
        input_warnings=bundle.warnings,
        adjustment_metadata=bundle.adjustment,
        timeframes=timeframes,
    )


def _timeframe_structure(
    bars: tuple[StructureBar, ...],
    role: TimeframeRole,
    config: PaqsStructureConfig,
    *,
    input_valid: bool,
) -> TimeframeStructure:
    timeframe = {
        TimeframeRole.CONTEXT: StructureTimeframe.W1,
        TimeframeRole.SETUP: StructureTimeframe.D1,
        TimeframeRole.TRIGGER: StructureTimeframe.M30,
    }[role]
    if not input_valid:
        return TimeframeStructure(
            role=role,
            timeframe=timeframe,
            latest_completed_bar_ref=bars[-1].reference if bars else None,
            bar_count=len(bars),
            atr_ready=False,
            latest_atr=None,
            micro_pivots=(),
            major_pivots=(),
            micro_swing_labels=(),
            major_swing_labels=(),
            key_levels=(),
            zones=(),
            valid_ranges=(),
            active_range=None,
            base_regime=BaseRegime.UNCERTAIN,
            regime_explanation=("input_quality_invalid",),
            warnings=("Structure calculation suppressed because PAQS input quality is INVALID",),
        )
    atr_points = calculate_atr(bars, config.atr_period)
    latest_atr = atr_points[-1].value if atr_points else None
    micro = detect_pivots(bars, atr_points, config=config, hierarchy=PivotHierarchy.MICRO)
    major = detect_pivots(bars, atr_points, config=config, hierarchy=PivotHierarchy.MAJOR)
    micro_labels = label_swings(micro, config)
    major_labels = label_swings(major, config)
    zones = build_zones(major, config)
    ranges, active_range = detect_ranges(bars, atr_points, zones, config)
    levels = build_key_levels(major, zones, ranges, config)
    regime = determine_base_regime(
        bars=bars,
        major_pivots=major,
        major_labels=major_labels,
        active_range=active_range,
        input_valid=input_valid,
        atr_ready=latest_atr is not None,
    )
    warnings: list[str] = []
    if not bars:
        warnings.append("No legitimate completed bars are available")
    elif latest_atr is None:
        warnings.append(
            f"ATR requires {config.atr_period} legitimate completed bars; {len(bars)} available"
        )
    if not major:
        warnings.append("No confirmed Major Pivots are available")
    return TimeframeStructure(
        role=role,
        timeframe=timeframe,
        latest_completed_bar_ref=bars[-1].reference if bars else None,
        bar_count=len(bars),
        atr_ready=latest_atr is not None,
        latest_atr=latest_atr,
        micro_pivots=micro,
        major_pivots=major,
        micro_swing_labels=micro_labels,
        major_swing_labels=major_labels,
        key_levels=levels,
        zones=zones,
        valid_ranges=ranges,
        active_range=active_range,
        base_regime=regime.value,
        regime_explanation=regime.explanation,
        warnings=tuple(warnings),
    )


def _derived_structure_bar(
    bar: DerivedBar, timeframe: StructureTimeframe, index: int
) -> StructureBar:
    return StructureBar(
        security=bar.security,
        timeframe=timeframe,
        reference=BarReference(
            index=index,
            key=f"{timeframe.value}:{bar.interval_start.isoformat()}",
            interval_start=bar.interval_start,
            interval_end=bar.interval_end,
        ),
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=bar.volume,
        is_completed=bar.is_completed,
        source_coverage=bar.coverage.value,
    )


def _higher_candidate(
    current: tuple[Decimal, BarReference] | None,
    price: Decimal,
    reference: BarReference,
) -> tuple[Decimal, BarReference]:
    return (price, reference) if current is None or price > current[0] else current


def _lower_candidate(
    current: tuple[Decimal, BarReference] | None,
    price: Decimal,
    reference: BarReference,
) -> tuple[Decimal, BarReference]:
    return (price, reference) if current is None or price < current[0] else current


def _reversal_ready(
    distance: Decimal,
    atr: Decimal,
    threshold_lambda: Decimal,
    extreme_ref: BarReference,
    confirmation_ref: BarReference,
) -> bool:
    return extreme_ref.index < confirmation_ref.index and distance >= threshold_lambda * atr


def _can_confirm(
    candidate: tuple[Decimal, BarReference],
    confirmation_ref: BarReference,
    distance: Decimal,
    atr: Decimal,
    threshold_lambda: Decimal,
    previous: Pivot,
    minimum_separation: int,
) -> bool:
    return (
        _reversal_ready(
            distance,
            atr,
            threshold_lambda,
            candidate[1],
            confirmation_ref,
        )
        and candidate[1].index - previous.extreme_source_ref.index >= minimum_separation
    )


def _pivot(
    security: str,
    timeframe: StructureTimeframe,
    hierarchy: PivotHierarchy,
    pivot_type: PivotType,
    candidate: tuple[Decimal, BarReference],
    confirmation_ref: BarReference,
    atr: Decimal,
    threshold_lambda: Decimal,
    config_hash: str,
) -> Pivot:
    pivot_id = _stable_id(
        "pivot",
        security,
        timeframe.value,
        hierarchy.value,
        pivot_type.value,
        config_hash,
        candidate[1].key,
        confirmation_ref.key,
    )
    return Pivot(
        pivot_id=pivot_id,
        security=security,
        timeframe=timeframe,
        hierarchy=hierarchy,
        pivot_type=pivot_type,
        price=candidate[0],
        extreme_source_ref=candidate[1],
        confirmation_source_ref=confirmation_ref,
        atr_at_confirmation=atr,
        lambda_used=threshold_lambda,
        confirmed=True,
        explanation=(
            f"extreme={candidate[1].key}",
            f"confirmed_by_close={confirmation_ref.key}",
            f"threshold={_canonical(_quantize(threshold_lambda * atr))}",
            "extreme_precedes_confirmation",
        ),
    )


def _pivot_cluster_sort_key(pivot: Pivot) -> tuple[Decimal, str, str, str]:
    return (
        pivot.price,
        pivot.extreme_source_ref.key,
        pivot.confirmation_source_ref.key,
        pivot.pivot_id,
    )


def _pair_distance(left: Pivot, right: Pivot) -> Decimal:
    denominator = _median((left.atr_at_confirmation, right.atr_at_confirmation))
    if denominator <= 0:
        return Decimal(0) if left.price == right.price else Decimal("Infinity")
    return _quantize(abs(left.price - right.price) / denominator)


def _center_distance(pivot: Pivot, cluster: list[Pivot]) -> Decimal:
    center = _median(tuple(item.price for item in cluster))
    cluster_atr = _median(tuple(item.atr_at_confirmation for item in cluster))
    denominator = _median((pivot.atr_at_confirmation, cluster_atr))
    if denominator <= 0:
        return Decimal(0) if pivot.price == center else Decimal("Infinity")
    return _quantize(abs(pivot.price - center) / denominator)


def _independent_pivots(
    pivots: list[Pivot] | tuple[Pivot, ...], separation: int
) -> tuple[Pivot, ...]:
    ordered = sorted(
        pivots,
        key=lambda item: (
            item.extreme_source_ref.index,
            item.extreme_source_ref.key,
            item.confirmation_source_ref.key,
            item.pivot_id,
        ),
    )
    accepted: list[Pivot] = []
    for pivot in ordered:
        if (
            not accepted
            or pivot.extreme_source_ref.index - accepted[-1].extreme_source_ref.index >= separation
        ):
            accepted.append(pivot)
    return tuple(accepted)


@dataclass(frozen=True, slots=True)
class _ZoneBuild:
    zone: Zone
    pivots: tuple[Pivot, ...]


def build_zone_geometry(
    pivots: tuple[Pivot, ...], role: KeyLevelRole, config: PaqsStructureConfig
) -> Zone:
    if not pivots:
        raise ValueError("zone requires at least one independent Pivot")
    center = _median(tuple(pivot.price for pivot in pivots))
    reference_atr = _median(tuple(pivot.atr_at_confirmation for pivot in pivots))
    mad = _median(tuple(abs(pivot.price - center) for pivot in pivots))
    minimum = _quantize(config.zone_min_halfwidth_atr * reference_atr)
    maximum = _quantize(config.zone_max_halfwidth_atr * reference_atr)
    half_width = min(max(mad, minimum), maximum)
    status = ZoneStatus.CONFIRMED if len(pivots) >= 2 else ZoneStatus.CANDIDATE
    timeframe = pivots[0].timeframe
    zone_id = _stable_id(
        "zone",
        role.value,
        timeframe.value,
        config.config_hash,
        *(sorted(pivot.pivot_id for pivot in pivots)),
    )
    touches = tuple(
        ZoneTouch(
            pivot_id=pivot.pivot_id,
            price=pivot.price,
            atr_at_confirmation=pivot.atr_at_confirmation,
            extreme_source_ref=pivot.extreme_source_ref,
            confirmation_source_ref=pivot.confirmation_source_ref,
        )
        for pivot in pivots
    )
    return Zone(
        zone_id=zone_id,
        timeframe=timeframe,
        role=role,
        status=status,
        center=center,
        reference_atr=reference_atr,
        mad=mad,
        half_width=half_width,
        lower_bound=_quantize(center - half_width),
        upper_bound=_quantize(center + half_width),
        touches=touches,
        explanation=(
            f"independent_touches={len(touches)}",
            f"median_center={_canonical(center)}",
            f"mad={_canonical(mad)}",
            f"reference_atr={_canonical(reference_atr)}",
            f"half_width={_canonical(half_width)}",
        ),
    )


def _merge_confirmed_zones(
    builds: list[_ZoneBuild], config: PaqsStructureConfig
) -> list[_ZoneBuild]:
    working = list(builds)
    while True:
        eligible: list[tuple[Decimal, int, int]] = []
        for left_index, left in enumerate(working):
            if left.zone.status is not ZoneStatus.CONFIRMED:
                continue
            for right_index in range(left_index + 1, len(working)):
                right = working[right_index]
                if (
                    right.zone.status is not ZoneStatus.CONFIRMED
                    or left.zone.role is not right.zone.role
                    or left.zone.timeframe is not right.zone.timeframe
                ):
                    continue
                iou = _interval_iou(left.zone, right.zone)
                if iou >= config.zone_merge_iou:
                    eligible.append((iou, left_index, right_index))
        if not eligible:
            break
        _, left_index, right_index = min(
            eligible,
            key=lambda item: (
                -item[0],
                min(
                    working[item[1]].zone.lower_bound,
                    working[item[2]].zone.lower_bound,
                ),
                min(working[item[1]].zone.zone_id, working[item[2]].zone.zone_id),
                max(working[item[1]].zone.zone_id, working[item[2]].zone.zone_id),
            ),
        )
        left = working[left_index]
        right = working[right_index]
        union = {pivot.pivot_id: pivot for pivot in (*left.pivots, *right.pivots)}
        accepted = _independent_pivots(tuple(union.values()), config.zone_min_touch_separation_bars)
        merged = _ZoneBuild(
            build_zone_geometry(accepted, left.zone.role, config),
            accepted,
        )
        working = [
            item for index, item in enumerate(working) if index not in {left_index, right_index}
        ]
        working.append(merged)
    working.sort(
        key=lambda item: (
            item.zone.role.value,
            item.zone.lower_bound,
            item.zone.zone_id,
        )
    )
    return working


def _interval_iou(left: Zone, right: Zone) -> Decimal:
    intersection = max(
        Decimal(0),
        min(left.upper_bound, right.upper_bound) - max(left.lower_bound, right.lower_bound),
    )
    union = max(left.upper_bound, right.upper_bound) - min(left.lower_bound, right.lower_bound)
    return Decimal(0) if union == 0 else _quantize(intersection / union)


def _alternating_reactions(support: Zone, resistance: Zone) -> tuple[str, ...]:
    by_index: dict[int, set[str]] = {}
    for touch in support.touches:
        by_index.setdefault(touch.extreme_source_ref.index, set()).add("L")
    for touch in resistance.touches:
        by_index.setdefault(touch.extreme_source_ref.index, set()).add("H")
    if any(len(sides) != 1 for sides in by_index.values()):
        return ()
    chronological = [next(iter(by_index[index])) for index in sorted(by_index)]
    compressed: list[str] = []
    for side in chronological:
        if not compressed or compressed[-1] != side:
            compressed.append(side)
    return tuple(compressed)


def build_key_levels(
    major_pivots: tuple[Pivot, ...],
    zones: tuple[Zone, ...],
    ranges: tuple[StructureRange, ...],
    config: PaqsStructureConfig,
) -> tuple[KeyLevel, ...]:
    levels = [
        KeyLevel(
            level_id=_stable_id("level", KeyLevelSource.MAJOR_SWING.value, pivot.pivot_id),
            timeframe=pivot.timeframe,
            role=(
                KeyLevelRole.SUPPORT
                if pivot.pivot_type is PivotType.LOW
                else KeyLevelRole.RESISTANCE
            ),
            source=KeyLevelSource.MAJOR_SWING,
            lower_bound=pivot.price,
            upper_bound=pivot.price,
            source_object_ids=(pivot.pivot_id,),
        )
        for pivot in major_pivots
        if pivot.confirmed and pivot.hierarchy is PivotHierarchy.MAJOR
    ]
    zones_by_id = {zone.zone_id: zone for zone in zones}
    for zone in zones:
        if zone.status is ZoneStatus.CONFIRMED:
            levels.append(
                KeyLevel(
                    level_id=_stable_id("level", KeyLevelSource.PIVOT_CLUSTER.value, zone.zone_id),
                    timeframe=zone.timeframe,
                    role=zone.role,
                    source=KeyLevelSource.PIVOT_CLUSTER,
                    lower_bound=zone.lower_bound,
                    upper_bound=zone.upper_bound,
                    source_object_ids=(zone.zone_id,),
                )
            )
    for structure_range in ranges:
        for zone_id in (
            structure_range.support_zone_id,
            structure_range.resistance_zone_id,
        ):
            zone = zones_by_id[zone_id]
            levels.append(
                KeyLevel(
                    level_id=_stable_id(
                        "level",
                        KeyLevelSource.RANGE_BOUNDARY.value,
                        config.config_hash,
                        structure_range.range_id,
                        zone_id,
                    ),
                    timeframe=zone.timeframe,
                    role=zone.role,
                    source=KeyLevelSource.RANGE_BOUNDARY,
                    lower_bound=zone.lower_bound,
                    upper_bound=zone.upper_bound,
                    source_object_ids=(structure_range.range_id, zone_id),
                )
            )
    levels.sort(
        key=lambda item: (
            item.source.value,
            item.role.value,
            item.lower_bound,
            item.level_id,
        )
    )
    return tuple(levels)


def _median(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("median requires at least one value")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return _quantize(ordered[middle])
    return _quantize((ordered[middle - 1] + ordered[middle]) / Decimal(2))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_CALCULATION_CONTEXT):
        result = value.quantize(_FINANCIAL_QUANTUM, rounding=ROUND_HALF_EVEN)
    return result.copy_abs() if result == 0 else result


def _canonical(value: Decimal) -> str:
    return canonical_decimal_string(_quantize(value))


def _stable_id(kind: str, *parts: str) -> str:
    payload = "\x1f".join((kind, *parts)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require_decimal_range(
    value: Decimal, minimum: Decimal, maximum: Decimal, field_name: str
) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal")
    parsed = parse_decimal(value)
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{field_name} is outside its approved research range")


def _require_int_range(value: int, minimum: int, maximum: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{field_name} must be an integer in [{minimum}, {maximum}]")
