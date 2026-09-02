from __future__ import annotations

from ai_infra_quant.backend.schemas.common import StrictSchema
from ai_infra_quant.core.domain.enums import SnapshotQualityStatus
from ai_infra_quant.core.domain.money import decimal_string
from ai_infra_quant.core.strategy.paqs_structure import (
    BarReference,
    BaseRegime,
    KeyLevel,
    KeyLevelRole,
    KeyLevelSource,
    PaqsStructureConfig,
    PaqsStructureSnapshot,
    Pivot,
    PivotHierarchy,
    PivotType,
    StructureRange,
    StructureTimeframe,
    SwingLabel,
    SwingLabelValue,
    TimeframeRole,
    TimeframeStructure,
    Zone,
    ZoneStatus,
    ZoneTouch,
)


class StructureConfigRead(StrictSchema):
    atr_period: int
    micro_pivot_atr_lambda: str
    major_pivot_atr_lambda: str
    pivot_min_bars: int
    structure_equal_tolerance_atr: str
    zone_cluster_epsilon_atr: str
    zone_min_touch_separation_bars: int
    zone_min_halfwidth_atr: str
    zone_max_halfwidth_atr: str
    zone_merge_iou: str
    range_lookback_bars: int
    range_inside_ratio: str
    min_range_width_atr: str
    max_range_width_atr: str


class BarReferenceRead(StrictSchema):
    index: int
    key: str
    session_date: str | None
    interval_start: str | None
    interval_end: str | None


class PivotRead(StrictSchema):
    pivot_id: str
    security: str
    timeframe: StructureTimeframe
    hierarchy: PivotHierarchy
    pivot_type: PivotType
    price: str
    extreme_source_ref: BarReferenceRead
    confirmation_source_ref: BarReferenceRead
    atr_at_confirmation: str
    lambda_used: str
    confirmed: bool
    explanation: list[str]


class SwingLabelRead(StrictSchema):
    pivot_id: str
    previous_comparable_pivot_id: str
    label: SwingLabelValue
    tolerance_used: str


class ZoneTouchRead(StrictSchema):
    pivot_id: str
    price: str
    atr_at_confirmation: str
    extreme_source_ref: BarReferenceRead
    confirmation_source_ref: BarReferenceRead


class ZoneRead(StrictSchema):
    zone_id: str
    timeframe: StructureTimeframe
    role: KeyLevelRole
    status: ZoneStatus
    center: str
    reference_atr: str
    mad: str
    half_width: str
    lower_bound: str
    upper_bound: str
    independent_touch_count: int
    touches: list[ZoneTouchRead]
    explanation: list[str]


class KeyLevelRead(StrictSchema):
    level_id: str
    timeframe: StructureTimeframe
    role: KeyLevelRole
    source: KeyLevelSource
    lower_bound: str
    upper_bound: str
    source_object_ids: list[str]


class StructureRangeRead(StrictSchema):
    range_id: str
    timeframe: StructureTimeframe
    support_zone_id: str
    resistance_zone_id: str
    lower_bound: str
    upper_bound: str
    inside_ratio: str
    width_atr: str
    total_independent_touch_count: int
    reaction_sequence: list[str]
    is_active: bool
    explanation: list[str]


class TimeframeStructureRead(StrictSchema):
    role: TimeframeRole
    timeframe: StructureTimeframe
    latest_completed_bar_ref: BarReferenceRead | None
    bar_count: int
    atr_ready: bool
    latest_atr: str | None
    micro_pivots: list[PivotRead]
    major_pivots: list[PivotRead]
    micro_swing_labels: list[SwingLabelRead]
    major_swing_labels: list[SwingLabelRead]
    key_levels: list[KeyLevelRead]
    zones: list[ZoneRead]
    valid_ranges: list[StructureRangeRead]
    active_range: StructureRangeRead | None
    base_regime: BaseRegime
    regime_explanation: list[str]
    warnings: list[str]


class AdjustmentMetadataRead(StrictSchema):
    basis: str
    adjustment_as_of: str
    historical_replay_safe: bool


class PaqsStructureSnapshotRead(StrictSchema):
    strategy_version: str
    structure_version: str
    config_hash: str
    config: StructureConfigRead
    security_id: str
    market: str
    symbol: str
    display_symbol: str
    market_timezone: str
    provider: str
    as_of_timestamp: str
    calculated_at: str
    input_quality: SnapshotQualityStatus
    input_warnings: list[str]
    adjustment_metadata: AdjustmentMetadataRead
    timeframes: list[TimeframeStructureRead]


def paqs_structure_snapshot_read(
    snapshot: PaqsStructureSnapshot,
) -> PaqsStructureSnapshotRead:
    adjustment = snapshot.adjustment_metadata
    return PaqsStructureSnapshotRead(
        strategy_version=snapshot.strategy_version,
        structure_version=snapshot.structure_version,
        config_hash=snapshot.config_hash,
        config=_config_read(snapshot.config),
        security_id=snapshot.security_id,
        market=snapshot.market,
        symbol=snapshot.symbol,
        display_symbol=f"{snapshot.market}.{snapshot.symbol}",
        market_timezone=snapshot.market_timezone,
        provider=snapshot.provider,
        as_of_timestamp=_utc(snapshot.as_of_timestamp),
        calculated_at=_utc(snapshot.calculated_at),
        input_quality=snapshot.input_quality,
        input_warnings=list(snapshot.input_warnings),
        adjustment_metadata=AdjustmentMetadataRead(
            basis=adjustment.basis.value,
            adjustment_as_of=_utc(adjustment.adjustment_as_of),
            historical_replay_safe=adjustment.historical_replay_safe,
        ),
        timeframes=[_timeframe_read(item) for item in snapshot.timeframes],
    )


def _config_read(config: PaqsStructureConfig) -> StructureConfigRead:
    return StructureConfigRead.model_validate(config.canonical_values())


def _reference_read(reference: BarReference) -> BarReferenceRead:
    return BarReferenceRead(
        index=reference.index,
        key=reference.key,
        session_date=None if reference.session_date is None else reference.session_date.isoformat(),
        interval_start=(
            None if reference.interval_start is None else _utc(reference.interval_start)
        ),
        interval_end=None if reference.interval_end is None else _utc(reference.interval_end),
    )


def _pivot_read(pivot: Pivot) -> PivotRead:
    return PivotRead(
        pivot_id=pivot.pivot_id,
        security=pivot.security,
        timeframe=pivot.timeframe,
        hierarchy=pivot.hierarchy,
        pivot_type=pivot.pivot_type,
        price=decimal_string(pivot.price),
        extreme_source_ref=_reference_read(pivot.extreme_source_ref),
        confirmation_source_ref=_reference_read(pivot.confirmation_source_ref),
        atr_at_confirmation=decimal_string(pivot.atr_at_confirmation),
        lambda_used=decimal_string(pivot.lambda_used),
        confirmed=pivot.confirmed,
        explanation=list(pivot.explanation),
    )


def _swing_read(label: SwingLabel) -> SwingLabelRead:
    return SwingLabelRead(
        pivot_id=label.pivot_id,
        previous_comparable_pivot_id=label.previous_comparable_pivot_id,
        label=label.label,
        tolerance_used=decimal_string(label.tolerance_used),
    )


def _touch_read(touch: ZoneTouch) -> ZoneTouchRead:
    return ZoneTouchRead(
        pivot_id=touch.pivot_id,
        price=decimal_string(touch.price),
        atr_at_confirmation=decimal_string(touch.atr_at_confirmation),
        extreme_source_ref=_reference_read(touch.extreme_source_ref),
        confirmation_source_ref=_reference_read(touch.confirmation_source_ref),
    )


def _zone_read(zone: Zone) -> ZoneRead:
    return ZoneRead(
        zone_id=zone.zone_id,
        timeframe=zone.timeframe,
        role=zone.role,
        status=zone.status,
        center=decimal_string(zone.center),
        reference_atr=decimal_string(zone.reference_atr),
        mad=decimal_string(zone.mad),
        half_width=decimal_string(zone.half_width),
        lower_bound=decimal_string(zone.lower_bound),
        upper_bound=decimal_string(zone.upper_bound),
        independent_touch_count=zone.independent_touch_count,
        touches=[_touch_read(touch) for touch in zone.touches],
        explanation=list(zone.explanation),
    )


def _level_read(level: KeyLevel) -> KeyLevelRead:
    return KeyLevelRead(
        level_id=level.level_id,
        timeframe=level.timeframe,
        role=level.role,
        source=level.source,
        lower_bound=decimal_string(level.lower_bound),
        upper_bound=decimal_string(level.upper_bound),
        source_object_ids=list(level.source_object_ids),
    )


def _range_read(structure_range: StructureRange) -> StructureRangeRead:
    return StructureRangeRead(
        range_id=structure_range.range_id,
        timeframe=structure_range.timeframe,
        support_zone_id=structure_range.support_zone_id,
        resistance_zone_id=structure_range.resistance_zone_id,
        lower_bound=decimal_string(structure_range.lower_bound),
        upper_bound=decimal_string(structure_range.upper_bound),
        inside_ratio=decimal_string(structure_range.inside_ratio),
        width_atr=decimal_string(structure_range.width_atr),
        total_independent_touch_count=structure_range.total_independent_touch_count,
        reaction_sequence=list(structure_range.reaction_sequence),
        is_active=structure_range.is_active,
        explanation=list(structure_range.explanation),
    )


def _timeframe_read(item: TimeframeStructure) -> TimeframeStructureRead:
    active_range = None if item.active_range is None else _range_read(item.active_range)
    return TimeframeStructureRead(
        role=item.role,
        timeframe=item.timeframe,
        latest_completed_bar_ref=(
            None
            if item.latest_completed_bar_ref is None
            else _reference_read(item.latest_completed_bar_ref)
        ),
        bar_count=item.bar_count,
        atr_ready=item.atr_ready,
        latest_atr=None if item.latest_atr is None else decimal_string(item.latest_atr),
        micro_pivots=[_pivot_read(pivot) for pivot in item.micro_pivots],
        major_pivots=[_pivot_read(pivot) for pivot in item.major_pivots],
        micro_swing_labels=[_swing_read(label) for label in item.micro_swing_labels],
        major_swing_labels=[_swing_read(label) for label in item.major_swing_labels],
        key_levels=[_level_read(level) for level in item.key_levels],
        zones=[_zone_read(zone) for zone in item.zones],
        valid_ranges=[_range_read(value) for value in item.valid_ranges],
        active_range=active_range,
        base_regime=item.base_regime,
        regime_explanation=list(item.regime_explanation),
        warnings=list(item.warnings),
    )


def _utc(value: object) -> str:
    from datetime import datetime

    if not isinstance(value, datetime):
        raise TypeError("expected datetime")
    return value.isoformat().replace("+00:00", "Z")
