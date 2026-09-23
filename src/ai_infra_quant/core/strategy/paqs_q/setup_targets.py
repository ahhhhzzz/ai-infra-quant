"""Causal, deterministic structural obstacles and regular-open gap adaptation."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.paqs_q.canonical import decimal_text, digest
from ai_infra_quant.core.domain.paqs_q.event_reference import ContextEvidence
from ai_infra_quant.core.domain.paqs_q.inputs import QInput
from ai_infra_quant.core.domain.paqs_q.setup_reference import TargetEvidence

D = Decimal


@dataclass(frozen=True, slots=True)
class Obstacle:
    kind: str
    key: str
    lower: Decimal
    upper: Decimal
    known_at: datetime
    gap_original_lower: Decimal | None = None
    gap_original_upper: Decimal | None = None
    gap_status: Literal["OPEN", "PARTIALLY_FILLED"] | None = None


def latest_index(data: QInput, cutoff: datetime) -> int | None:
    answer = None
    for i, bar in enumerate(data.bars):
        if bar.completed_at <= cutoff and (bar.available_at is None or bar.available_at <= cutoff):
            answer = i
        elif bar.completed_at > cutoff:
            break
    return answer


def trading_days(data: QInput, start_day: date, end_day: date) -> int:
    return sum(f.kind == "OPEN" and start_day < f.day <= end_day for f in data.calendar)


def next_regular_open(data: QInput, after: datetime) -> datetime | None:
    """First calendar-certified M30 slot at/after a completed candle's end."""
    from datetime import timedelta

    for fact in data.calendar:
        if fact.kind != "OPEN" or (
            data.mode == "AS_OF" and (not fact.complete or fact.available_at is None)
        ):
            continue
        for start, end in fact.segments:
            point = start
            while point < end:
                if point >= after:
                    if fact.available_at is not None and fact.available_at > point:
                        return None
                    return point
                point += timedelta(minutes=30)
    return None


def regular_open_gaps(
    d1: QInput,
    d1_context: ContextEvidence,
    m30: QInput,
    cutoff: datetime,
) -> tuple[tuple[Obstacle, ...], tuple[str, ...]]:
    """Use completed M30 evidence only; never infer an opening fact from D1 OHLC."""
    zone = ZoneInfo(m30.market_timezone)
    days = {f.day: f for f in m30.calendar}
    completed = [
        b
        for b in m30.bars
        if b.session == "REGULAR"
        and b.completed_at <= cutoff
        and (b.available_at is None or b.available_at <= cutoff)
    ]
    found: list[Obstacle] = []
    rejected: list[str] = []
    for i in range(1, len(completed)):
        previous, current = completed[i - 1], completed[i]
        prev_day = previous.start.astimezone(zone).date()
        day = current.start.astimezone(zone).date()
        if day == prev_day:
            continue  # HK lunch or any same-day continuation is never a new daily gap.
        prev_fact, current_fact = days.get(prev_day), days.get(day)
        if (
            prev_fact is None
            or current_fact is None
            or prev_fact.kind != "OPEN"
            or current_fact.kind != "OPEN"
            or previous.end != prev_fact.segments[-1][1]
            or current.start != current_fact.segments[0][0]
        ):
            rejected.append(f"GAP_SESSION_COVERAGE_UNPROVEN:{day}")
            continue
        prior_d1 = latest_index(d1, current.start)
        if prior_d1 is None or d1.bars[prior_d1].completed_at >= current.start:
            rejected.append(f"GAP_PRIOR_D1_ATR_UNAVAILABLE:{day}")
            continue
        atr_text = d1_context.frames[prior_d1].atr
        if atr_text is None or D(atr_text) <= 0:
            rejected.append(f"GAP_PRIOR_D1_ATR_UNAVAILABLE:{day}")
            continue
        if abs(current.open - previous.close) < D("0.25") * D(atr_text):
            continue
        key = digest("paqs-q/regular-gap/v1", (previous.version_ref, current.version_ref))
        low, high = sorted((current.open, previous.close))
        if current.open >= previous.close:
            rejected.append(f"GAP_UP_SUPPORT_NOT_LONG_TARGET:{key}")
            continue
        after = [b for b in completed[i:] if b.completed_at <= cutoff]
        filled_to = max((b.high for b in after), default=low)
        if filled_to >= high:
            rejected.append(f"GAP_FILLED:{key}")
            continue
        cutoff_day = cutoff.astimezone(zone).date()
        if trading_days(m30, day, cutoff_day) > 15:
            rejected.append(f"GAP_EXPIRED:{key}")
            continue
        remaining = max(low, filled_to)
        found.append(
            Obstacle(
                "REGULAR_SESSION_OPEN_GAP",
                key,
                remaining,
                high,
                current.completed_at,
                low,
                high,
                "PARTIALLY_FILLED" if remaining > low else "OPEN",
            )
        )
    return tuple(found), tuple(rejected)


def structural_obstacles(
    d1: QInput,
    context: ContextEvidence,
    m30: QInput,
    cutoff: datetime,
) -> tuple[tuple[Obstacle, ...], tuple[str, ...], bool]:
    index = latest_index(d1, cutoff)
    if index is None:
        return (), ("D1_CONTEXT_UNAVAILABLE",), False
    frame = context.frames[index]
    zones = {z.key: z for z in context.zones}
    ranges = {r.version_key: r for r in context.ranges}
    found: list[Obstacle] = []
    if frame.active_range is not None:
        active = ranges[frame.active_range]
        found.append(
            Obstacle(
                "OPPOSITE_RANGE_BOUNDARY",
                active.version_key,
                D(active.upper),
                D(active.upper),
                d1.bars[active.calculation_index].completed_at,
            )
        )
    for pivot in context.pivots:
        if pivot.hierarchy != "MAJOR" or pivot.confirmation_index > index:
            continue
        key = pivot.key
        if pivot.kind == "HIGH" and pivot.label is not None:
            found.append(
                Obstacle(
                    "PREVIOUS_MAJOR_SWING_HIGH",
                    key,
                    D(pivot.price),
                    D(pivot.price),
                    d1.bars[pivot.confirmation_index].completed_at,
                )
            )
    for key in frame.zones:
        item = zones[key]
        if item.role == "RESISTANCE" and item.status == "CONFIRMED":
            found.append(
                Obstacle(
                    "CONFIRMED_MAJOR_RESISTANCE",
                    key,
                    D(item.lower),
                    D(item.upper),
                    d1.bars[item.confirmation_index].completed_at,
                )
            )
    gaps, gap_reasons = regular_open_gaps(d1, context, m30, cutoff)
    found.extend(gaps)
    coverage = d1.quality == m30.quality == "COMPLETE"
    return tuple(found), gap_reasons, coverage


def targets(
    obstacles: tuple[Obstacle, ...],
    entry: Decimal,
    atr: Decimal,
) -> tuple[TargetEvidence | None, TargetEvidence | None, tuple[str, ...], bool]:
    accepted: list[Obstacle] = []
    rejected: list[str] = []
    inside = False
    for item in sorted(obstacles, key=lambda o: (o.lower, o.upper, o.key)):
        if item.lower <= entry <= item.upper:
            rejected.append(f"ENTRY_INSIDE_RESISTANCE:{item.key}")
            inside = True
        elif item.upper < entry:
            rejected.append(f"BEHIND_ENTRY:{item.key}")
        elif item.lower > entry:
            accepted.append(item)
    clusters: list[list[Obstacle]] = []
    tolerance = D("0.25") * atr
    for item in accepted:
        if clusters and item.lower - clusters[-1][0].lower <= tolerance:
            clusters[-1].append(item)
        else:
            clusters.append([item])

    def evidence(cluster: list[Obstacle]) -> TargetEvidence:
        first = min(cluster, key=lambda o: (o.lower, o.key))
        gap = next((o for o in cluster if o.gap_status is not None), None)
        return TargetEvidence(
            effective_price=decimal_text(first.lower),
            lower=decimal_text(first.lower),
            upper=decimal_text(max(o.upper for o in cluster)),
            sources=tuple(o.kind for o in cluster),
            source_keys=tuple(o.key for o in cluster),
            known_at=max(o.known_at for o in cluster),
            gap_original_lower=(
                decimal_text(gap.gap_original_lower)
                if gap and gap.gap_original_lower is not None
                else None
            ),
            gap_original_upper=(
                decimal_text(gap.gap_original_upper)
                if gap and gap.gap_original_upper is not None
                else None
            ),
            gap_status=gap.gap_status if gap else None,
        )

    result = [evidence(group) for group in clusters]
    return (
        result[0] if result else None,
        result[1] if len(result) > 1 else None,
        tuple(rejected),
        inside,
    )
