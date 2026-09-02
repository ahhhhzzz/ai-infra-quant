from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.market_data import (
    DailyBar,
    MinuteBar,
    TradingDay,
    TradingDayType,
    TradingSessionSegment,
)
from ai_infra_quant.core.domain.paqs_input import (
    DerivedCoverage,
    derive_m30_bars,
    derive_weekly_bars,
)

RETRIEVED = datetime(2026, 1, 1, tzinfo=UTC)


def _daily(session_date: date, close: str, *, retrieved_at: datetime = RETRIEVED) -> DailyBar:
    value = Decimal(close)
    return DailyBar(
        security="US.TEST",
        session_date=session_date,
        provider_time=datetime.combine(session_date, time.min, tzinfo=UTC),
        open=value - Decimal("1"),
        high=value + Decimal("2"),
        low=value - Decimal("2"),
        close=value,
        volume=Decimal("100"),
        is_completed=True,
        retrieved_at=retrieved_at,
    )


def _trading_day(
    market_date: date,
    *,
    market: str = "US",
    segments: tuple[TradingSessionSegment, ...] | None = None,
) -> TradingDay:
    timezone = "America/New_York" if market == "US" else "Asia/Hong_Kong"
    if segments is None:
        segments = (
            (TradingSessionSegment(time(9, 30), time(16, 0)),)
            if market == "US"
            else (
                TradingSessionSegment(time(9, 30), time(12, 0)),
                TradingSessionSegment(time(13, 0), time(16, 0)),
            )
        )
    return TradingDay(
        market=market,
        market_date=market_date,
        market_timezone=timezone,
        day_type=TradingDayType.FULL,
        provider_day_type="WHOLE",
        session_segments=segments,
        provider="test",
        retrieved_at=RETRIEVED,
    )


def _minutes(
    market_date: date,
    start: time,
    count: int,
    *,
    market: str = "US",
    skip: set[int] | None = None,
) -> tuple[MinuteBar, ...]:
    timezone = ZoneInfo("America/New_York" if market == "US" else "Asia/Hong_Kong")
    first = datetime.combine(market_date, start, tzinfo=timezone).astimezone(UTC)
    skipped = skip or set()
    bars = []
    for offset in range(count):
        if offset in skipped:
            continue
        value = Decimal("100") + Decimal(offset) / Decimal("100")
        interval_start = first + timedelta(minutes=offset)
        bars.append(
            MinuteBar(
                security=f"{market}.TEST",
                interval_start=interval_start,
                interval_end=interval_start + timedelta(minutes=1),
                open=value,
                high=value + Decimal("1"),
                low=value - Decimal("1"),
                close=value + Decimal("0.5"),
                volume=Decimal(offset + 1),
                is_completed=True,
                retrieved_at=RETRIEVED,
            )
        )
    return tuple(bars)


def test_completed_week_aggregates_decimal_ohlcv() -> None:
    dates = [date(2026, 7, 6) + timedelta(days=offset) for offset in range(5)]
    daily = tuple(_daily(value, str(100 + offset)) for offset, value in enumerate(dates))
    calendar = tuple(_trading_day(value) for value in dates)
    bars = derive_weekly_bars(
        security="US.TEST",
        market_timezone="America/New_York",
        daily_bars=daily,
        trading_days=calendar,
        as_of=datetime(2026, 7, 10, 21, tzinfo=UTC),
    )
    assert len(bars) == 1
    bar = bars[0]
    assert bar.is_completed is True
    assert bar.coverage is DerivedCoverage.COMPLETE
    assert bar.source_bar_count == bar.expected_source_bar_count == 5
    assert bar.open == Decimal("99")
    assert bar.high == Decimal("106")
    assert bar.low == Decimal("98")
    assert bar.close == Decimal("104")
    assert bar.volume == Decimal("500")


def test_current_partial_week_is_excluded_until_legitimate_finalization() -> None:
    dates = (date(2026, 7, 6), date(2026, 7, 7), date(2026, 7, 8))
    scheduled_dates = tuple(date(2026, 7, 6) + timedelta(days=offset) for offset in range(5))
    bars = derive_weekly_bars(
        security="US.TEST",
        market_timezone="America/New_York",
        daily_bars=tuple(_daily(value, "100") for value in dates),
        trading_days=tuple(_trading_day(value) for value in scheduled_dates),
        as_of=datetime(2026, 7, 8, 22, tzinfo=UTC),
    )
    assert len(bars) == 1
    assert bars[0].is_completed is False


def test_later_week_daily_finalizes_prior_week_only_when_available() -> None:
    friday = _daily(date(2026, 7, 10), "100")
    later_retrieved = datetime(2026, 7, 13, 21, tzinfo=UTC)
    monday = _daily(date(2026, 7, 13), "101", retrieved_at=later_retrieved)
    early = derive_weekly_bars(
        security="US.TEST",
        market_timezone="America/New_York",
        daily_bars=(friday, monday),
        trading_days=(),
        as_of=datetime(2026, 7, 10, 21, tzinfo=UTC),
    )
    assert len(early) == 1
    assert early[0].is_completed is False
    later = derive_weekly_bars(
        security="US.TEST",
        market_timezone="America/New_York",
        daily_bars=(friday, monday),
        trading_days=(),
        as_of=later_retrieved,
    )
    assert later[0].is_completed is True
    assert later[0].source_bar_count == 1
    assert later[0].close == Decimal("100")


def test_holiday_shortened_week_finalizes_without_friday() -> None:
    dates = [date(2026, 7, 6) + timedelta(days=offset) for offset in range(4)]
    bars = derive_weekly_bars(
        security="US.TEST",
        market_timezone="America/New_York",
        daily_bars=tuple(_daily(value, "100") for value in dates),
        trading_days=tuple(_trading_day(value) for value in dates),
        as_of=datetime(2026, 7, 9, 21, tzinfo=UTC),
    )
    assert bars[0].is_completed is True
    assert bars[0].expected_source_bar_count == 4


def test_us_m30_uses_regular_boundaries_and_excludes_extended_session() -> None:
    market_date = date(2026, 7, 6)
    source = (
        *_minutes(market_date, time(9, 0), 30),
        *_minutes(market_date, time(9, 30), 390),
        *_minutes(market_date, time(16, 0), 30),
    )
    bars = derive_m30_bars(
        security="US.TEST",
        market_timezone="America/New_York",
        minute_bars=source,
        trading_days=(_trading_day(market_date),),
        as_of=datetime(2026, 7, 6, 22, tzinfo=UTC),
    )
    assert len(bars) == 13
    local = ZoneInfo("America/New_York")
    assert bars[0].interval_start.astimezone(local).time() == time(9, 30)
    assert bars[-1].interval_end.astimezone(local).time() == time(16, 0)
    assert all(bar.is_completed for bar in bars)


def test_us_dst_uses_iana_timezone_offsets() -> None:
    winter = date(2026, 3, 6)
    summer = date(2026, 3, 9)
    bars = derive_m30_bars(
        security="US.TEST",
        market_timezone="America/New_York",
        minute_bars=(
            *_minutes(winter, time(9, 30), 30),
            *_minutes(summer, time(9, 30), 30),
        ),
        trading_days=(_trading_day(winter), _trading_day(summer)),
        as_of=datetime(2026, 3, 10, tzinfo=UTC),
    )
    assert bars[0].interval_start.hour == 14
    assert bars[1].interval_start.hour == 13


def test_hk_morning_and_afternoon_are_independently_anchored() -> None:
    market_date = date(2026, 7, 6)
    bars = derive_m30_bars(
        security="HK.TEST",
        market_timezone="Asia/Hong_Kong",
        minute_bars=(
            *_minutes(market_date, time(9, 30), 150, market="HK"),
            *_minutes(market_date, time(13, 0), 180, market="HK"),
        ),
        trading_days=(_trading_day(market_date, market="HK"),),
        as_of=datetime(2026, 7, 6, 9, tzinfo=UTC),
    )
    local_times = [bar.interval_start.astimezone(ZoneInfo("Asia/Hong_Kong")).time() for bar in bars]
    assert len(bars) == 11
    assert time(11, 30) in local_times
    assert time(13, 0) in local_times
    assert time(12, 0) not in local_times


def test_m30_ohlcv_and_missing_source_are_truthful_without_fill() -> None:
    market_date = date(2026, 7, 6)
    complete = derive_m30_bars(
        security="US.TEST",
        market_timezone="America/New_York",
        minute_bars=_minutes(market_date, time(9, 30), 30),
        trading_days=(_trading_day(market_date),),
        as_of=datetime(2026, 7, 6, 15, tzinfo=UTC),
    )[0]
    assert complete.open == Decimal("100")
    assert complete.high == Decimal("101.29")
    assert complete.low == Decimal("99")
    assert complete.close == Decimal("100.79")
    assert complete.volume == sum((Decimal(value) for value in range(1, 31)), Decimal(0))

    partial = derive_m30_bars(
        security="US.TEST",
        market_timezone="America/New_York",
        minute_bars=_minutes(market_date, time(9, 30), 30, skip={12}),
        trading_days=(_trading_day(market_date),),
        as_of=datetime(2026, 7, 6, 15, tzinfo=UTC),
    )[0]
    assert partial.source_bar_count == 29
    assert partial.coverage is DerivedCoverage.PARTIAL
    assert partial.is_completed is False


def test_unfinished_current_bucket_and_unknown_session_schedule_are_excluded() -> None:
    market_date = date(2026, 7, 6)
    cutoff = datetime(2026, 7, 6, 13, 45, tzinfo=UTC)
    unfinished = derive_m30_bars(
        security="US.TEST",
        market_timezone="America/New_York",
        minute_bars=_minutes(market_date, time(9, 30), 15),
        trading_days=(_trading_day(market_date),),
        as_of=cutoff,
    )
    unknown = _trading_day(market_date, segments=())
    unavailable = derive_m30_bars(
        security="US.TEST",
        market_timezone="America/New_York",
        minute_bars=_minutes(market_date, time(9, 30), 30),
        trading_days=(unknown,),
        as_of=datetime(2026, 7, 6, 15, tzinfo=UTC),
    )
    assert unfinished == ()
    assert unavailable == ()
