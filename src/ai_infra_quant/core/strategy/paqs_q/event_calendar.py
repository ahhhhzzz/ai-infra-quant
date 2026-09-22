"""Calendar-counted event streams. No B0 quartet/session-segment policy is reused."""

from datetime import timedelta
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.paqs_q.inputs import QInput

from .calendar import require, slot
from .qualification import validate_window


class Insufficient(ValueError):
    pass


def qualify(data: QInput) -> tuple[str, ...]:
    if problem := data.problem():
        raise ValueError(problem)
    validate_window(data.bars, data)
    if data.quality == "INVALID":
        raise ValueError("INVALID_DATA_QUALITY")
    if not data.bars:
        raise Insufficient("NO_COMPLETED_BARS")
    if any(a.completed_at > b.start for a, b in zip(data.bars, data.bars[1:], strict=False)):
        raise Insufficient("PREVIOUS_BAR_NOT_KNOWN_BEFORE_NEXT_START")
    if any(b.coverage != "COMPLETE" for b in data.bars):
        raise Insufficient("INCOMPLETE_BAR_COVERAGE")
    if any(
        b.adjustment
        not in {
            "SYNTHETIC",
            "POINT_IN_TIME_ADJUSTED",
            "PROVIDER_QFQ_CURRENT",
            "UNADJUSTED",
            "SPLIT_ADJUSTED",
            "TOTAL_RETURN_ADJUSTED",
        }
        for b in data.bars
    ):
        raise Insufficient("ADJUSTMENT_EVIDENCE_UNKNOWN")
    if data.mode == "AS_OF":
        if data.quality != "COMPLETE":
            raise Insufficient("STRICT_QUALITY_REQUIRED")
        if any(b.adjustment not in {"SYNTHETIC", "POINT_IN_TIME_ADJUSTED"} for b in data.bars):
            raise Insufficient("STRICT_ADJUSTMENT_UNPROVEN")
        if any(b.adjustment != "SYNTHETIC" for b in data.bars):
            provenance = data.provenance.document()
            evidence = (
                provenance.get("historical_evidence") if isinstance(provenance, dict) else None
            )
            if not isinstance(evidence, dict) or any(
                not isinstance(evidence.get(key), str) or not evidence[key].strip()
                for key in ("price_versions", "adjustment_as_of", "calendar_versions")
            ):
                raise Insufficient("HISTORICAL_EVIDENCE_REFERENCES_REQUIRED")
        if any(b.available_at is None for b in data.bars):
            raise Insufficient("HISTORICAL_PRICE_AVAILABILITY_UNKNOWN")
        if any(b.available_at != b.completed_at for b in data.bars):
            raise Insufficient("HISTORICAL_PRICE_NOT_KNOWN_AT_COMPLETION")
        if any(not f.complete or f.available_at is None for f in data.calendar):
            raise Insufficient("STRICT_CALENDAR_UNPROVEN")
    zone = ZoneInfo(data.market_timezone)
    first = data.bars[0].start.astimezone(zone).date()
    last = data.bars[-1].start.astimezone(zone).date()
    days = {f.day: f for f in data.calendar}
    if not days:
        raise Insufficient("CALENDAR_MISSING")
    if data.mode == "AS_OF" or data.timeframe == "W1":
        end = last + timedelta(days=6) if data.timeframe == "W1" else last
        for i in range((end - first).days + 1):
            day = first + timedelta(days=i)
            if day not in days:
                raise Insufficient("CALENDAR_DATE_MISSING")
    for bar in data.bars:
        try:
            facts, _ = slot(bar, days, data.mode)
        except ValueError as exc:
            if str(exc) in {"CALENDAR_UNKNOWN", "WEEK_INCOMPLETE", "CALENDAR_NOT_STRICT"}:
                raise Insufficient(str(exc)) from exc
            raise
        if data.mode == "AS_OF" and any(
            f.available_at is None or f.available_at > bar.completed_at for f in facts
        ):
            raise Insufficient("HISTORICAL_CALENDAR_NOT_KNOWN_AT_COMPLETION")
    if data.timeframe == "W1":
        if any(a.end != b.start for a, b in zip(data.bars, data.bars[1:], strict=False)):
            raise Insufficient("MISSING_EXPECTED_WEEK")
    else:
        expected = []
        for day in sorted(days):
            if not first <= day <= last:
                continue
            try:
                fact = require(days, day, data.bars[0], data.mode)
            except ValueError as exc:
                if str(exc) in {"CALENDAR_UNKNOWN", "CALENDAR_NOT_STRICT"}:
                    raise Insufficient(str(exc)) from exc
                raise
            if fact.kind != "OPEN":
                continue
            if data.timeframe == "D1":
                expected.append(fact.segments[0][0])
            else:
                for start, end in fact.segments:
                    if (end - start) % timedelta(minutes=30):
                        raise ValueError("INCOMPLETE_EXPECTED_M30_SEGMENT")
                    point = start
                    while point < end:
                        if data.bars[0].start <= point <= data.bars[-1].start:
                            expected.append(point)
                        point += timedelta(minutes=30)
        if expected != [b.start for b in data.bars]:
            raise Insufficient("MISSING_EXPECTED_BAR")
    return (
        ()
        if data.mode == "AS_OF"
        else (
            "OBSERVATIONAL_NOT_POINT_IN_TIME",
            "Historical versions/availability and adjustment timing are not certified.",
            "Only supplied calendar facts are checked; unlisted dates do not certify completeness.",
            "Fixed-start legacy initialization and history-origin sensitivity are retained.",
        )
    )
