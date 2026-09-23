"""Clearly synthetic, internally price-consistent W1/D1/M30 candles."""

from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, digest
from ai_infra_quant.core.domain.paqs_q.inputs import Bar, Fact, QInput
from ai_infra_quant.core.domain.paqs_q.setup_reference import EntryReference, MultiInput
from tools.research.event_engine.data import demo_input

D = Decimal
ZONE = ZoneInfo("America/New_York")
KNOWN = datetime(2020, 1, 1, tzinfo=UTC)
PROVENANCE = FrozenJSON.of({"source": "SYNTHETIC_SETUP_DEMO_V1"})
DEFAULT_SCALE = D("0.1")
DEFAULT_OFFSET = D("-2.7")
ZERO = D("0")


def _calendar(start: date, end: date) -> tuple[Fact, ...]:
    result: list[Fact] = []
    day = start
    while day <= end:
        opened = day.weekday() < 5
        segments = (
            (
                (
                    datetime.combine(day, time(9, 30), ZONE),
                    datetime.combine(day, time(16), ZONE),
                ),
            )
            if opened
            else ()
        )
        result.append(
            Fact(
                day,
                "US",
                str(ZONE),
                "OPEN" if opened else "CLOSED",
                segments,
                "SYNTHETIC",
                KNOWN,
                KNOWN,
                True,
            )
        )
        day += timedelta(days=1)
    return tuple(result)


def _daily_bars(base: QInput, count: int) -> tuple[Bar, ...]:
    return base.bars[:count]


def _m30_after(last: Bar, count: int, scale: Decimal, offset: Decimal) -> tuple[Bar, ...]:
    profile = demo_input().bars
    # A labelled synthetic pullback after the D1 breakout/retest, not market data.
    anchor = last.close + offset
    result: list[Bar] = []
    day = last.start.astimezone(ZONE).date() + timedelta(days=1)
    while len(result) < count:
        if day.weekday() < 5:
            session = datetime.combine(day, time(9, 30), ZONE)
            for n in range(13):
                if len(result) >= count:
                    break
                source = profile[len(result) % len(profile)]
                start = session + timedelta(minutes=30 * n)
                end = start + timedelta(minutes=30)

                def convert(value: Decimal) -> Decimal:
                    return anchor + (value - D(100)) * scale

                result.append(
                    Bar(
                        "US.SYNTH",
                        "M30",
                        start,
                        end,
                        end,
                        end,
                        end,
                        convert(source.open),
                        convert(source.high),
                        convert(source.low),
                        convert(source.close),
                        D(100),
                    )
                )
        day += timedelta(days=1)
    return tuple(result)


def _aggregate_daily(m30: tuple[Bar, ...]) -> tuple[Bar, ...]:
    output = []
    for offset in range(0, len(m30), 13):
        group = m30[offset : offset + 13]
        output.append(
            Bar(
                "US.SYNTH",
                "D1",
                group[0].start,
                group[-1].end,
                group[-1].end,
                group[-1].end,
                group[-1].end,
                group[0].open,
                max(x.high for x in group),
                min(x.low for x in group),
                group[-1].close,
                D(1300),
            )
        )
    return tuple(output)


def _weekly(daily: tuple[Bar, ...], history: int, calendar: tuple[Fact, ...]) -> QInput:
    first_day = daily[0].start.astimezone(ZONE).date()
    history_start = first_day - timedelta(weeks=history)
    profile = demo_input().bars
    values = []
    for n in range(history):
        source = profile[n % len(profile)]
        monday = history_start + timedelta(weeks=n)
        start = datetime.combine(monday, time.min, ZONE)
        end = start + timedelta(days=7)
        completed = datetime.combine(monday + timedelta(days=4), time(16), ZONE)
        values.append(
            Bar(
                "US.SYNTH",
                "W1",
                start,
                end,
                completed,
                completed,
                completed,
                source.open,
                source.high,
                source.low,
                source.close,
                D(500),
            )
        )
    grouped: dict[date, list[Bar]] = {}
    for bar in daily:
        day = bar.start.astimezone(ZONE).date()
        grouped.setdefault(day - timedelta(days=day.weekday()), []).append(bar)
    last_day = daily[-1].start.astimezone(ZONE).date()
    for monday, group in sorted(grouped.items()):
        friday = monday + timedelta(days=4)
        if friday > last_day or len(group) != 5:
            continue
        start = datetime.combine(monday, time.min, ZONE)
        end = start + timedelta(days=7)
        completed = group[-1].completed_at
        values.append(
            Bar(
                "US.SYNTH",
                "W1",
                start,
                end,
                completed,
                completed,
                completed,
                group[0].open,
                max(x.high for x in group),
                min(x.low for x in group),
                group[-1].close,
                D(500),
            )
        )
    end_day = values[-1].start.astimezone(ZONE).date() + timedelta(days=6)
    facts = tuple(f for f in calendar if f.day <= end_day)
    return QInput(
        "US.SYNTH",
        "US",
        "USD",
        str(ZONE),
        "W1",
        values[-1].completed_at,
        tuple(values),
        facts,
        provenance=PROVENANCE,
    )


def demo_bundle(
    *,
    daily_count: int = 90,
    weekly_history: int = 80,
    m30_count: int = 130,
    scale: Decimal = DEFAULT_SCALE,
    offset: Decimal = DEFAULT_OFFSET,
    references: bool = True,
    range_failure: bool = False,
    daily_offset: Decimal = ZERO,
    daily_slope: Decimal = ZERO,
    trend_pullback: bool = False,
) -> MultiInput:
    source = demo_input()
    if trend_pullback:
        bars = []
        for i, bar in enumerate(source.bars):
            shift = D("20") + D("0.1") * i
            updated = replace(
                bar,
                open=bar.open + shift,
                high=bar.high + shift,
                low=bar.low + shift,
                close=bar.close + shift,
            )
            if i in {50, 55, 60}:
                updated = replace(updated, low=D("125.9"))
            manual = {
                56: ("130.6", "131.2", "129.4", "131"),
                61: ("126", "130.2", "125.8", "130"),
                62: ("130", "135.2", "129.8", "135"),
                63: ("135", "135.2", "131.8", "132"),
                64: ("132", "132.2", "125.9", "128"),
                65: ("128", "130.2", "127.8", "130"),
                66: ("130", "133.2", "129.8", "133"),
                67: ("133", "133.2", "125.9", "132"),
            }
            if i in manual:
                o, h, lo, c = (D(v) for v in manual[i])
                updated = replace(updated, open=o, high=h, low=lo, close=c)
            bars.append(updated)
        source = replace(source, bars=tuple(bars))
    if daily_offset or daily_slope:
        source = replace(
            source,
            bars=tuple(
                replace(
                    b,
                    open=b.open + daily_offset + daily_slope * i,
                    high=b.high + daily_offset + daily_slope * i,
                    low=b.low + daily_offset + daily_slope * i,
                    close=b.close + daily_offset + daily_slope * i,
                )
                for i, b in enumerate(source.bars)
            ),
        )
    if range_failure:
        bars = list(source.bars)
        bars[80] = replace(bars[80], low=D("98.8"))
        source = replace(source, bars=tuple(bars))
    base = _daily_bars(source, daily_count)
    m30_bars = _m30_after(base[-1], m30_count, scale, offset)
    daily = (*base, *_aggregate_daily(m30_bars))
    first = daily[0].start.astimezone(ZONE).date() - timedelta(weeks=weekly_history)
    last = daily[-1].start.astimezone(ZONE).date()
    calendar = _calendar(first, last + timedelta(days=6))
    w1 = _weekly(daily, weekly_history, calendar)
    d1 = replace(
        source,
        bars=daily,
        calendar=tuple(f for f in calendar if f.day >= daily[0].start.astimezone(ZONE).date()),
        as_of=daily[-1].completed_at,
        provenance=PROVENANCE,
    )
    m30 = QInput(
        "US.SYNTH",
        "US",
        "USD",
        str(ZONE),
        "M30",
        m30_bars[-1].completed_at,
        m30_bars,
        tuple(f for f in calendar if f.day >= m30_bars[0].start.astimezone(ZONE).date()),
        provenance=PROVENANCE,
    )
    refs = (
        tuple(
            EntryReference(
                bar.open,
                bar.start,
                bar.start,
                "SYNTHETIC_OPEN",
                digest("synthetic-open-event/v1", (bar.start, bar.open)),
                "SYNTHETIC",
                "US.SYNTH",
            )
            for bar in m30_bars
        )
        if references
        else ()
    )
    return MultiInput(w1, d1, m30, refs)
