"""Prefix-frozen reference context using the retained pure structure algorithms."""

from datetime import timedelta
from decimal import Decimal, localcontext
from typing import Any, cast
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, digest, primitive
from ai_infra_quant.core.domain.paqs_q.event_reference import (
    ContextEvidence,
    Frame,
    PivotEvidence,
    RangeEvidence,
    Source,
    ZoneEvidence,
)
from ai_infra_quant.core.domain.paqs_q.inputs import CONTEXT, QInput
from ai_infra_quant.core.domain.paqs_q.results import Config
from ai_infra_quant.core.strategy.paqs_structure import (
    BarReference,
    PaqsStructureConfig,
    Pivot,
    PivotHierarchy,
    StructureBar,
    StructureTimeframe,
    SwingLabel,
    Zone,
    build_zones,
    calculate_atr,
    detect_pivots,
    detect_ranges,
    determine_base_regime,
    label_swings,
)

from .event_calendar import qualify

CONTEXT_ID = "paqs-q-event-context-reference"
EVENT_ID = "paqs-q-event-reference"
VERSION = "1.0.1"
CAPABILITY = "PREFIX_EVENT_CONTEXT_V1"


def context_config() -> Config:
    return Config(
        "paqs-q-event-context-config-v1",
        FrozenJSON.of(
            {
                **PaqsStructureConfig().canonical_values(),
                "zone_max_age_bars": 250,
                "history": "FIXED_START",
                "source_use": "AFTER_CONFIRMATION_BAR",
            }
        ),
    )


def structure_bars(data: QInput) -> tuple[StructureBar, ...]:
    return tuple(
        StructureBar(
            data.security,
            StructureTimeframe(data.timeframe),
            BarReference(i, b.version_ref, interval_start=b.start, interval_end=b.completed_at),
            b.open,
            b.high,
            b.low,
            b.close,
            b.volume,
            b.completed,
            b.coverage,
        )
        for i, b in enumerate(data.bars)
    )


def pivot_evidence(p: Pivot, labels: dict[str, SwingLabel], data: QInput) -> PivotEvidence:
    e, c = p.extreme_source_ref.index, p.confirmation_source_ref.index
    label = labels.get(p.pivot_id)
    return PivotEvidence.model_validate_json(
        FrozenJSON.of(
            {
                "key": p.pivot_id,
                "hierarchy": p.hierarchy.value,
                "kind": p.pivot_type.value,
                "price": p.price,
                "extreme_index": e,
                "confirmation_index": c,
                "extreme_time": data.bars[e].completed_at,
                "confirmation_time": data.bars[c].completed_at,
                "support_refs": (data.bars[e].version_ref, data.bars[c].version_ref),
                "label": label.label.value if label else None,
                "previous_key": label.previous_comparable_pivot_id if label else None,
                "tolerance": label.tolerance_used if label else None,
            }
        ).data
    )


def zone_evidence(z: Zone, index: int) -> ZoneEvidence:
    return ZoneEvidence.model_validate_json(
        FrozenJSON.of(
            {
                "key": z.zone_id,
                "role": z.role.value,
                "status": z.status.value,
                "lower": z.lower_bound,
                "upper": z.upper_bound,
                "center": z.center,
                "reference_atr": z.reference_atr,
                "mad": z.mad,
                "half_width": z.half_width,
                "touches": tuple(t.pivot_id for t in z.touches),
                "confirmation_index": index,
                "last_touch_index": max(t.confirmation_source_ref.index for t in z.touches),
            }
        ).data
    )


def series_prefixes(data: QInput) -> tuple[str, tuple[str, ...]]:
    series = digest(
        "paqs-q/event-series/v1",
        {
            "security": data.security,
            "market": data.market,
            "currency": data.currency,
            "timezone": data.market_timezone,
            "timeframe": data.timeframe,
            "mode": data.mode,
            "start": data.bars[0].start,
            "context_config": context_config().config_hash,
            "reference_version": VERSION,
        },
    )
    zone = ZoneInfo(data.market_timezone)
    prior_day = data.bars[0].start.astimezone(zone).date() - timedelta(days=1)
    prefix, result = series, []
    for bar in data.bars:
        end_day = (
            bar.end.astimezone(zone).date() - timedelta(days=1)
            if data.timeframe == "W1"
            else bar.completed_at.astimezone(zone).date()
        )
        # Include intervening closed days, not later sessions merely present in the snapshot.
        used = [f.payload() for f in data.calendar if prior_day < f.day <= end_day]
        prefix = digest("paqs-q/event-prefix/v1", (prefix, bar.payload(), used))
        result.append(prefix)
        prior_day = end_day
    return series, tuple(result)


def compute_context(data: QInput) -> ContextEvidence:
    limitations = qualify(data)
    config = PaqsStructureConfig()
    bars = structure_bars(data)
    with localcontext(CONTEXT):
        atr = calculate_atr(bars)
        micro = detect_pivots(bars, atr, config=config, hierarchy=PivotHierarchy.MICRO)
        major = detect_pivots(bars, atr, config=config, hierarchy=PivotHierarchy.MAJOR)
        micro_labels, major_labels = label_swings(micro, config), label_swings(major, config)
        labels = {p.pivot_id: p for p in (*micro_labels, *major_labels)}
        pivots = tuple(pivot_evidence(p, labels, data) for p in (*micro, *major))
        zones: dict[str, ZoneEvidence] = {}
        ranges: dict[str, RangeEvidence] = {}
        frames: list[Frame] = []
        geometry: tuple[Zone, ...] = ()
        previous_count = 0
        series, prefixes = series_prefixes(data)
        for i, bar in enumerate(data.bars):
            known_micro = tuple(p for p in micro if p.confirmation_source_ref.index <= i)
            known_major = tuple(p for p in major if p.confirmation_source_ref.index <= i)
            if len(known_major) != previous_count:
                geometry = build_zones(known_major, config)
                previous_count = len(known_major)
                for z in geometry:
                    if z.zone_id not in zones:
                        zones[z.zone_id] = zone_evidence(z, i)
            usable = tuple(z for z in geometry if i - zones[z.zone_id].last_touch_index <= 250)
            valid, active = detect_ranges(bars[: i + 1], atr[: i + 1], usable, config)
            frame_ranges = []
            active_version = None
            for r in valid:
                raw = {
                    "key": r.range_id,
                    "support_key": r.support_zone_id,
                    "resistance_key": r.resistance_zone_id,
                    "lower": r.lower_bound,
                    "upper": r.upper_bound,
                    "inside_ratio": r.inside_ratio,
                    "width_atr": r.width_atr,
                    "touches": r.total_independent_touch_count,
                    "reactions": r.reaction_sequence,
                    "active": r.is_active,
                    "calculation_index": i,
                }
                key = digest("paqs-q/range-version/v1", raw)
                ranges[key] = RangeEvidence.model_validate_json(
                    FrozenJSON.of({**raw, "version_key": key}).data
                )
                frame_ranges.append(key)
                if active is not None and r.range_id == active.range_id:
                    active_version = key
            atr_value = atr[i].value
            ready = atr_value is not None and atr_value > 0
            base = determine_base_regime(
                bars=bars[: i + 1],
                major_pivots=known_major,
                major_labels=tuple(
                    x for x in major_labels if x.pivot_id in {p.pivot_id for p in known_major}
                ),
                active_range=active,
                input_valid=True,
                atr_ready=ready,
            ).value.value
            frame = {
                "index": i,
                "bar_ref": bar.version_ref,
                "atr": atr[i].value,
                "micro": tuple(p.pivot_id for p in known_micro[-4:]),
                "major": tuple(p.pivot_id for p in known_major[-4:]),
                "zones": tuple(z.zone_id for z in usable),
                "ranges": frame_ranges,
                "active_range": active_version,
                "base_regime": base,
                "readiness": {
                    "atr": ready,
                    "micro": len(known_micro) >= 2,
                    "major": len(known_major) >= 2,
                    "zone": any(z.status.value == "CONFIRMED" for z in usable),
                    "range": bool(valid),
                },
            }
            frames.append(Frame.model_validate_json(FrozenJSON.of(frame).data))
        result = ContextEvidence(
            schema_version="paqs-q-event-context-evidence-v1",
            series_key=series,
            prefix_hashes=tuple(prefixes),
            strict_confirmation=data.mode == "AS_OF",
            limitations=limitations,
            calendar_refs=tuple(f.ref for f in data.calendar),
            pivots=pivots,
            zones=tuple(zones.values()),
            ranges=tuple(ranges.values()),
            frames=tuple(frames),
        )
        validate_context(result, data)
        return result


def validate_context(context: ContextEvidence, data: QInput) -> None:
    if len(context.frames) != len(data.bars) or len(context.prefix_hashes) != len(data.bars):
        raise ValueError("CONTEXT_BAR_COUNT_MISMATCH")
    if context.strict_confirmation != (data.mode == "AS_OF"):
        raise ValueError("CONTEXT_MODE_MISMATCH")
    if context.calendar_refs != tuple(f.ref for f in data.calendar):
        raise ValueError("CONTEXT_CALENDAR_MISMATCH")
    if (context.series_key, context.prefix_hashes) != series_prefixes(data):
        raise ValueError("CONTEXT_PREFIX_IDENTITY")
    if context.limitations != qualify(data):
        raise ValueError("CONTEXT_LIMITATIONS_MISMATCH")
    pivots = {p.key: p for p in context.pivots}
    zones = {z.key: z for z in context.zones}
    ranges = {r.version_key: r for r in context.ranges}
    if (
        len(pivots) != len(context.pivots)
        or len(zones) != len(context.zones)
        or len(ranges) != len(context.ranges)
    ):
        raise ValueError("CONTEXT_DUPLICATE_OBJECT")
    for p in context.pivots:
        if p.confirmation_index >= len(data.bars):
            raise ValueError("CONTEXT_FUTURE_PIVOT")
        e, c = data.bars[p.extreme_index], data.bars[p.confirmation_index]
        if (
            p.support_refs != (e.version_ref, c.version_ref)
            or p.extreme_time != primitive(e.completed_at)
            or p.confirmation_time != primitive(c.completed_at)
            or Decimal(p.price) != (e.high if p.kind == "HIGH" else e.low)
        ):
            raise ValueError("CONTEXT_PIVOT_SUPPORT_MISMATCH")
        if p.previous_key is not None and (
            p.previous_key not in pivots
            or pivots[p.previous_key].confirmation_index >= p.confirmation_index
            or pivots[p.previous_key].hierarchy != p.hierarchy
            or pivots[p.previous_key].kind != p.kind
        ):
            raise ValueError("CONTEXT_PREVIOUS_PIVOT_MISMATCH")
    for z in context.zones:
        if (
            not z.touches
            or any(k not in pivots for k in z.touches)
            or z.status != ("CONFIRMED" if len(z.touches) >= 2 else "CANDIDATE")
            or Decimal(z.lower) > Decimal(z.upper)
        ):
            raise ValueError("CONTEXT_ZONE_INVALID")
        if z.last_touch_index != max(pivots[k].confirmation_index for k in z.touches):
            raise ValueError("CONTEXT_ZONE_CLOCK")
        if z.confirmation_index < z.last_touch_index:
            raise ValueError("CONTEXT_ZONE_FUTURE_SUPPORT")
        if any(
            pivots[k].hierarchy != "MAJOR"
            or pivots[k].kind != ("LOW" if z.role == "SUPPORT" else "HIGH")
            for k in z.touches
        ):
            raise ValueError("CONTEXT_ZONE_ROLE")
    for r in context.ranges:
        if r.support_key not in zones or r.resistance_key not in zones:
            raise ValueError("CONTEXT_RANGE_SUPPORT")
        if any(
            zones[k].status != "CONFIRMED" or zones[k].confirmation_index > r.calculation_index
            for k in (r.support_key, r.resistance_key)
        ):
            raise ValueError("CONTEXT_RANGE_FUTURE_SUPPORT")
        if zones[r.support_key].role != "SUPPORT" or zones[r.resistance_key].role != "RESISTANCE":
            raise ValueError("CONTEXT_RANGE_ROLES")
        raw = r.model_dump(exclude={"version_key"})
        if r.version_key != digest("paqs-q/range-version/v1", raw):
            raise ValueError("CONTEXT_RANGE_VERSION")
    atr = calculate_atr(structure_bars(data))
    for i, f in enumerate(context.frames):
        if f.index != i or f.bar_ref != data.bars[i].version_ref:
            raise ValueError("CONTEXT_FRAME_IDENTITY")
        value = atr[i].value
        if f.atr != primitive(value) or f.readiness.atr != (value is not None and value > 0):
            raise ValueError("CONTEXT_ATR_MISMATCH")
        for hierarchy, keys in (("MICRO", f.micro), ("MAJOR", f.major)):
            known = tuple(
                p.key
                for p in context.pivots
                if p.hierarchy == hierarchy and p.confirmation_index <= i
            )
            if keys != known[-4:]:
                raise ValueError("CONTEXT_FRAME_LATEST_PIVOTS")
            if any(
                k not in pivots
                or pivots[k].hierarchy != hierarchy
                or pivots[k].confirmation_index > i
                for k in keys
            ):
                raise ValueError("CONTEXT_FRAME_FUTURE_PIVOT")
        if any(k not in zones or zones[k].confirmation_index > i for k in f.zones):
            raise ValueError("CONTEXT_FRAME_FUTURE_ZONE")
        if any(i - zones[k].last_touch_index > 250 for k in f.zones):
            raise ValueError("CONTEXT_FRAME_STALE_ZONE")
        if any(k not in ranges or ranges[k].calculation_index != i for k in f.ranges):
            raise ValueError("CONTEXT_FRAME_RANGE")
        if f.active_range is not None and (
            f.active_range not in f.ranges or not ranges[f.active_range].active
        ):
            raise ValueError("CONTEXT_ACTIVE_RANGE")


def sources(context: ContextEvidence, frame: Frame) -> tuple[Source, ...]:
    pivots = {p.key: p for p in context.pivots}
    zones = {z.key: z for z in context.zones}
    ranges = {r.version_key: r for r in context.ranges}
    active = ranges[frame.active_range] if frame.active_range else None
    rows: list[dict[str, Any]] = []
    for kind, role in (("HIGH", "RESISTANCE"), ("LOW", "SUPPORT")):
        latest = next((pivots[k] for k in reversed(frame.major) if pivots[k].kind == kind), None)
        if latest:
            rows.append(
                {
                    "source_key": latest.key,
                    "source_type": "MAJOR_SWING",
                    "role": role,
                    "lower": latest.price,
                    "upper": latest.price,
                    "confirmation_index": latest.confirmation_index,
                    "support_refs": latest.support_refs,
                    "range_key": None,
                    "range_version": None,
                }
            )
    for key in frame.zones:
        z = zones[key]
        if z.status != "CONFIRMED" or frame.index + 1 - z.last_touch_index > 250:
            continue
        in_range = active is not None and key in (active.support_key, active.resistance_key)
        rows.append(
            {
                "source_key": key,
                "source_type": "RANGE_BOUNDARY" if in_range else "ZONE",
                "role": z.role,
                "lower": z.lower,
                "upper": z.upper,
                "confirmation_index": frame.index if in_range else z.confirmation_index,
                "support_refs": tuple(
                    dict.fromkeys(ref for k in z.touches for ref in pivots[k].support_refs)
                ),
                "range_key": active.key if in_range and active else None,
                "range_version": active.version_key if in_range and active else None,
            }
        )
    return tuple(
        Source.model_validate_json(
            FrozenJSON.of(
                {
                    **row,
                    "version_key": digest("paqs-q/event-source/v1", row),
                }
            ).data
        )
        for row in sorted(rows, key=lambda r: cast(str, r["source_key"]))
    )
