from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON
from ai_infra_quant.core.domain.paqs_q.inputs import Bar, Fact, QInput
from ai_infra_quant.core.strategy.paqs_q.event_calendar import Insufficient, qualify
from ai_infra_quant.core.strategy.paqs_q.event_context import compute_context
from tools.research.event_engine.data import daily_input, demo_input

from .support import candle


def intraday(market="HK"):
    zone = ZoneInfo("Asia/Hong_Kong" if market == "HK" else "America/New_York")
    security = "HK.00700" if market == "HK" else "US.SYNTH"
    day = datetime(2025, 3, 7).date()  # Friday before US DST Sunday
    known = datetime(2025, 1, 1, tzinfo=UTC)
    facts, bars = [], []
    while len(bars) < 40:
        opened = day.weekday() < 5
        clocks = (
            ((time(9, 30), time(12)), (time(13), time(16)))
            if market == "HK"
            else ((time(9, 30), time(16)),)
        )
        segments = (
            tuple(
                (datetime.combine(day, a, zone), datetime.combine(day, b, zone)) for a, b in clocks
            )
            if opened
            else ()
        )
        facts.append(
            Fact(
                day,
                market,
                str(zone),
                "OPEN" if opened else "CLOSED",
                segments,
                "SYNTHETIC",
                known,
                known,
                True,
            )
        )
        for start, end in segments:
            left = start
            while left < end and len(bars) < 40:
                right = left + timedelta(minutes=30)
                bars.append(
                    Bar(
                        security,
                        "M30",
                        left,
                        right,
                        right,
                        right,
                        right,
                        Decimal(100),
                        Decimal(101),
                        Decimal(99),
                        Decimal(100),
                        Decimal(100),
                    )
                )
                left = right
        day += timedelta(days=1)
    return QInput(
        security,
        market,
        "HKD" if market == "HK" else "USD",
        str(zone),
        "M30",
        bars[-1].completed_at,
        tuple(bars),
        tuple(facts),
    )


def weekly():
    daily = daily_input([candle(str(100 + i)) for i in range(100)])
    zone = ZoneInfo(daily.market_timezone)
    facts = list(daily.calendar)
    for n in (1, 2):
        facts.append(
            replace(
                facts[-1],
                day=daily.calendar[-1].day + timedelta(days=n),
                kind="CLOSED",
                segments=(),
            )
        )
    bars = []
    for offset in range(0, len(daily.bars), 5):
        group = daily.bars[offset : offset + 5]
        start = datetime.combine(group[0].start.astimezone(zone).date(), time.min, zone)
        end = start + timedelta(days=7)
        bars.append(
            replace(
                group[0],
                timeframe="W1",
                start=start,
                end=end,
                completed_at=group[-1].completed_at,
                available_at=group[-1].completed_at,
                retrieved_at=group[-1].completed_at,
                open=group[0].open,
                close=group[-1].close,
                high=max(b.high for b in group),
                low=min(b.low for b in group),
            )
        )
    return replace(daily, timeframe="W1", bars=tuple(bars), calendar=tuple(facts))


@pytest.mark.parametrize("market", ["HK", "US"])
def test_m30_crosses_lunch_overnight_weekend_dst(market):
    data = intraday(market)
    context = compute_context(data)
    assert context.frames[-1].readiness.atr
    assert len(context.frames) == 40
    if market == "US":
        assert data.bars[0].start.hour == 14 and data.bars[13].start.hour == 13
    else:
        assert data.bars[4].end.hour == 4 and data.bars[5].start.hour == 5
    with pytest.raises(Insufficient, match="MISSING_EXPECTED_BAR"):
        compute_context(replace(data, bars=data.bars[:5] + data.bars[6:]))
    with pytest.raises(ValueError):
        compute_context(
            replace(
                data,
                bars=(
                    replace(data.bars[0], start=data.bars[0].start + timedelta(minutes=1)),
                    *data.bars[1:],
                ),
            )
        )


def test_w1_factual_completion_before_nominal_week_end_and_holiday():
    data = weekly()
    assert data.bars[-1].end > data.as_of
    assert compute_context(data).frames[-1].readiness.atr
    # Last Friday closed; factual completion becomes Thursday, nominal geometry stays Monday.
    friday = data.calendar[-3]
    thursday = data.calendar[-4]
    last = replace(
        data.bars[-1], completed_at=thursday.segments[-1][1], available_at=thursday.segments[-1][1]
    )
    changed = replace(
        data,
        bars=(*data.bars[:-1], last),
        as_of=last.completed_at,
        calendar=(
            *data.calendar[:-3],
            replace(friday, kind="CLOSED", segments=()),
            *data.calendar[-2:],
        ),
    )
    assert qualify(changed) == ()
    with pytest.raises(Insufficient, match="CALENDAR_DATE_MISSING"):
        qualify(replace(data, calendar=data.calendar[:-1]))
    with pytest.raises(Insufficient, match="MISSING_EXPECTED_WEEK"):
        qualify(replace(data, bars=data.bars[:5] + data.bars[6:]))
    with pytest.raises(ValueError, match="WEEK_FACTUAL_COMPLETION"):
        qualify(
            replace(
                data,
                bars=(
                    *data.bars[:-1],
                    replace(
                        data.bars[-1],
                        completed_at=data.as_of - timedelta(hours=1),
                        available_at=data.as_of - timedelta(hours=1),
                    ),
                ),
            )
        )


def test_d1_missing_session_is_not_window_expiry_but_closed_day_is_allowed():
    data = demo_input()
    missing = data.bars[90]
    changed = replace(data, bars=data.bars[:90] + data.bars[91:])
    with pytest.raises(Insufficient, match="MISSING_EXPECTED_BAR"):
        qualify(changed)
    holiday = tuple(
        replace(f, kind="CLOSED", segments=()) if f.day == missing.start.date() else f
        for f in data.calendar
    )
    assert qualify(replace(changed, calendar=holiday)) == ()


def test_modes_do_not_downgrade_or_bypass_f1_validation():
    data = demo_input()
    bars = tuple(
        replace(b, available_at=None, adjustment="PROVIDER_QFQ_CURRENT") for b in data.bars
    )
    unknown = replace(data, bars=bars, quality="PARTIAL")
    with pytest.raises(Insufficient, match="STRICT_QUALITY_REQUIRED"):
        compute_context(unknown)
    observed = compute_context(replace(unknown, mode="OBSERVATIONAL"))
    assert not observed.strict_confirmation
    assert "OBSERVATIONAL_NOT_POINT_IN_TIME" in observed.limitations
    future = replace(bars[-1], completed_at=data.as_of + timedelta(days=1))
    for mode in ("AS_OF", "OBSERVATIONAL"):
        with pytest.raises(ValueError, match="FUTURE_PRICE_EVIDENCE"):
            qualify(replace(unknown, mode=mode, bars=(*bars[:-1], future)))
        with pytest.raises(ValueError, match="UNFINISHED"):
            qualify(
                replace(
                    data, mode=mode, bars=(replace(data.bars[0], completed=False), *data.bars[1:])
                )
            )


def test_strict_historical_evidence_and_late_availability():
    data = demo_input()
    changed = replace(
        data, bars=tuple(replace(b, adjustment="POINT_IN_TIME_ADJUSTED") for b in data.bars)
    )
    with pytest.raises(Insufficient, match="HISTORICAL_EVIDENCE_REFERENCES_REQUIRED"):
        qualify(changed)
    evidence = FrozenJSON.of(
        {
            "historical_evidence": {
                "price_versions": "fixture-price-archive",
                "adjustment_as_of": "fixture-adjustment-history",
                "calendar_versions": "fixture-calendar-history",
            }
        }
    )
    assert qualify(replace(changed, provenance=evidence)) == ()
    with pytest.raises(Insufficient, match="HISTORICAL_PRICE_NOT_KNOWN_AT_COMPLETION"):
        qualify(
            replace(
                data,
                bars=(
                    replace(
                        data.bars[0], available_at=data.bars[0].completed_at + timedelta(seconds=1)
                    ),
                    *data.bars[1:],
                ),
            )
        )
    with pytest.raises(Insufficient, match="HISTORICAL_CALENDAR_NOT_KNOWN_AT_COMPLETION"):
        qualify(
            replace(
                data,
                calendar=(replace(data.calendar[0], available_at=data.as_of), *data.calendar[1:]),
            )
        )


def test_invalid_data_and_incomplete_evidence_distinguished():
    data = demo_input()
    with pytest.raises(ValueError, match="OHLC_INVALID"):
        qualify(replace(data, bars=(replace(data.bars[0], high=Decimal(1)), *data.bars[1:])))
    with pytest.raises(ValueError, match="ADJUSTMENT_BASIS_MISMATCH"):
        qualify(
            replace(data, bars=(replace(data.bars[0], adjustment="UNADJUSTED"), *data.bars[1:]))
        )
    with pytest.raises(Insufficient, match="NO_COMPLETED_BARS"):
        qualify(replace(data, bars=()))
    with pytest.raises(Insufficient, match="INCOMPLETE_BAR_COVERAGE"):
        qualify(
            replace(
                data,
                quality="PARTIAL",
                bars=(replace(data.bars[0], coverage="PARTIAL"), *data.bars[1:]),
            )
        )
    missing = replace(data, calendar=data.calendar[1:])
    with pytest.raises(Insufficient, match="CALENDAR_DATE_MISSING"):
        qualify(missing)
