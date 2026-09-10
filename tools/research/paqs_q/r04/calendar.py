"""Explicit versioned calendar facts, slots and negative adjacency evidence."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from itertools import pairwise
from zoneinfo import ZoneInfo

from ..types import Bar, digest, utc


@dataclass(frozen=True)
class Fact:
    day: date
    market: str
    timezone: str
    kind: str
    segments: tuple[tuple[datetime, datetime], ...]
    source: str
    retrieved_at: datetime
    available_at: datetime | None
    complete: bool

    @property
    def ref(self) -> str:
        return digest(
            "r04-calendar",
            (
                self.day.isoformat(),
                self.market,
                self.timezone,
                self.kind,
                self.segments,
                self.source,
                self.retrieved_at,
                self.available_at,
                self.complete,
            ),
        )


def select(facts: tuple[Fact, ...], cutoff: datetime, mode: str) -> dict[date, Fact]:
    if len(facts) > 10000:
        raise ValueError("CALENDAR_BOUND")
    groups: dict[date, list[Fact]] = {}
    for fact in facts:
        if fact.available_at is not None and utc(fact.available_at) > cutoff:
            continue
        if fact.available_at is None and mode == "AS_OF":
            continue
        groups.setdefault(fact.day, []).append(fact)
    result = {}
    for day, group in groups.items():
        latest = max(f.available_at or datetime.min.replace(tzinfo=UTC) for f in group)
        chosen = [
            f for f in group if (f.available_at or datetime.min.replace(tzinfo=UTC)) == latest
        ]
        if len({f.ref for f in chosen}) != 1:
            raise ValueError("CALENDAR_CONFLICT")
        if (
            any(f.available_at is None for f in group)
            and any(f.available_at for f in group)
            and len({(f.kind, f.segments, f.complete) for f in group}) != 1
        ):
            raise ValueError("CALENDAR_UNKNOWN_VERSION_ORDER")
        result[day] = chosen[0]
    return result


def require(days: dict[date, Fact], day: date, bar: Bar, mode: str) -> Fact:
    fact = days.get(day)
    if fact is None or fact.kind == "UNKNOWN":
        raise ValueError("CALENDAR_UNKNOWN")
    expected = {"US": "America/New_York", "HK": "Asia/Hong_Kong"}
    market = bar.security.split(".")[0]
    if fact.market != market or fact.timezone != expected[market]:
        raise ValueError("CALENDAR_IDENTITY")
    utc(fact.retrieved_at)
    if fact.available_at is not None:
        utc(fact.available_at)
    if type(fact.complete) is not bool or fact.kind not in {"OPEN", "CLOSED"}:
        raise ValueError("CALENDAR_SHAPE")
    if mode == "AS_OF" and (not fact.complete or fact.available_at is None):
        raise ValueError("CALENDAR_NOT_STRICT")
    if (fact.kind == "OPEN") != bool(fact.segments):
        raise ValueError("CALENDAR_SHAPE")
    for start, end in fact.segments:
        if utc(start) >= utc(end) or any(
            t.astimezone(ZoneInfo(fact.timezone)).date() != day for t in (start, end)
        ):
            raise ValueError("CALENDAR_SEGMENT_SHAPE")
    if any(a[1] > b[0] for a, b in pairwise(fact.segments)):
        raise ValueError("CALENDAR_SEGMENT_OVERLAP")
    return fact


def dates(first: date, last: date) -> tuple[date, ...]:
    delta = (last - first).days
    if not 0 <= delta <= 40:
        raise ValueError("CALENDAR_INTERVAL_BOUND")
    return tuple(first + timedelta(days=i) for i in range(delta + 1))


def slot(bar: Bar, days: dict[date, Fact], mode: str) -> tuple[tuple[Fact, ...], str]:
    zone = ZoneInfo("America/New_York" if bar.security.startswith("US.") else "Asia/Hong_Kong")
    day = bar.start.astimezone(zone).date()
    if bar.timeframe == "W1":
        if (
            day.weekday() != 0
            or bar.end.astimezone(zone).date() != day + timedelta(days=7)
            or bar.start.astimezone(zone).time() != time.min
            or bar.end.astimezone(zone).time() != time.min
        ):
            raise ValueError("WEEK_INTERVAL")
        facts = tuple(require(days, d, bar, mode) for d in dates(day, day + timedelta(days=6)))
        opened = [f for f in facts if f.kind == "OPEN"]
        if not opened or bar.coverage != "COMPLETE":
            raise ValueError("WEEK_INCOMPLETE")
        if bar.completed_at != opened[-1].segments[-1][1]:
            raise ValueError("WEEK_FACTUAL_COMPLETION")
        return facts, day.isoformat()
    fact = require(days, day, bar, mode)
    if fact.kind != "OPEN":
        raise ValueError("BAR_ON_CLOSED_DAY")
    if bar.timeframe == "D1":
        if (bar.start, bar.end) != (fact.segments[0][0], fact.segments[-1][1]):
            raise ValueError("DAILY_SLOT_MISMATCH")
        return (fact,), day.isoformat()
    for index, (start, end) in enumerate(fact.segments):
        if start <= bar.start < bar.end <= end:
            if (bar.start - start) % timedelta(minutes=30) or bar.end - bar.start != timedelta(
                minutes=30
            ):
                raise ValueError("BUCKET_ALIGNMENT")
            if bar.session != "REGULAR" or bar.coverage != "COMPLETE":
                raise ValueError("BUCKET_NOT_COMPLETE_REGULAR")
            return (fact,), f"{day}:{index}"
    raise ValueError("OUTSIDE_REGULAR_SEGMENT")


def support(bars: tuple[Bar, ...], days: dict[date, Fact], mode: str) -> tuple[Fact, ...]:
    facts: dict[date, Fact] = {}
    slots = []
    for bar in bars:
        used, segment = slot(bar, days, mode)
        facts.update((f.day, f) for f in used)
        slots.append(segment)
    for index, (a, b) in enumerate(pairwise(bars)):
        if a.timeframe == "M30":
            if slots[index] != slots[index + 1]:
                raise ValueError("PROHIBITED_SEGMENT_BOUNDARY")
            if a.end != b.start:
                raise ValueError("MISSING_EXPECTED_BUCKET")
        elif a.timeframe == "W1":
            if a.end != b.start:
                raise ValueError("MISSING_EXPECTED_WEEK")
        else:
            zone = ZoneInfo(slot(a, days, mode)[0][0].timezone)
            start, end = a.start.astimezone(zone).date(), b.start.astimezone(zone).date()
            for day in dates(start, end)[1:-1]:
                fact = require(days, day, a, mode)
                facts[day] = fact
                if fact.kind == "OPEN":
                    raise ValueError("MISSING_EXPECTED_SESSION")
    return tuple(facts[k] for k in sorted(facts))
