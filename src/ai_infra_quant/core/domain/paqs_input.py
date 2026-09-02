from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.common import require_utc
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus, SnapshotQualityStatus
from ai_infra_quant.core.domain.market_data import DailyBar, MinuteBar, TradingDay


class DerivedTimeframe(StrEnum):
    W1 = "W1"
    M30 = "M30"


class DerivedCoverage(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class AdjustmentBasis(StrEnum):
    PROVIDER_QFQ_CURRENT = "PROVIDER_QFQ_CURRENT"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class DerivedBar:
    security: str
    timeframe: DerivedTimeframe
    interval_start: datetime
    interval_end: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    market_timezone: str
    session_type: str | None
    source_bar_count: int
    expected_source_bar_count: int | None
    coverage: DerivedCoverage
    is_completed: bool

    def __post_init__(self) -> None:
        start = require_utc(self.interval_start)
        end = require_utc(self.interval_end)
        if end <= start:
            raise ValueError("derived interval end must follow its start")
        if self.source_bar_count <= 0:
            raise ValueError("derived bar requires at least one source bar")
        if self.expected_source_bar_count is not None:
            if self.expected_source_bar_count <= 0:
                raise ValueError("expected source count must be positive")
            if self.source_bar_count > self.expected_source_bar_count:
                raise ValueError("source count cannot exceed expected source count")
        if any(not isinstance(value, Decimal) or not value.is_finite() for value in self.ohlcv):
            raise ValueError("derived OHLCV values must be finite Decimal values")
        if min(self.open, self.high, self.low, self.close) <= 0 or self.volume < 0:
            raise ValueError("derived OHLC must be positive and volume non-negative")
        if self.high < max(self.open, self.low, self.close):
            raise ValueError("derived high is inconsistent")
        if self.low > min(self.open, self.high, self.close):
            raise ValueError("derived low is inconsistent")
        object.__setattr__(self, "interval_start", start)
        object.__setattr__(self, "interval_end", end)

    @property
    def ohlcv(self) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
        return self.open, self.high, self.low, self.close, self.volume


@dataclass(frozen=True, slots=True)
class AdjustmentMetadata:
    basis: AdjustmentBasis
    adjustment_as_of: datetime
    historical_replay_safe: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "adjustment_as_of", require_utc(self.adjustment_as_of))


@dataclass(frozen=True, slots=True)
class CalendarMetadata:
    status: DataAvailabilityStatus
    provider: str
    retrieved_at: datetime
    trading_days: tuple[TradingDay, ...]
    reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "retrieved_at", require_utc(self.retrieved_at))


@dataclass(frozen=True, slots=True)
class SourceCoverage:
    d1_source_count: int
    w1_completed_count: int
    w1_partial_count: int
    minute_source_count: int
    m30_completed_count: int
    m30_partial_count: int


@dataclass(frozen=True, slots=True)
class PaqsInputBundle:
    security_id: str
    market: str
    symbol: str
    market_timezone: str
    provider: str
    as_of_timestamp: datetime
    completed_w1_bars: tuple[DerivedBar, ...]
    completed_d1_bars: tuple[DailyBar, ...]
    completed_30m_bars: tuple[DerivedBar, ...]
    calendar: CalendarMetadata
    adjustment: AdjustmentMetadata
    data_quality: SnapshotQualityStatus
    warnings: tuple[str, ...]
    source_coverage: SourceCoverage

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_timestamp", require_utc(self.as_of_timestamp))


def derive_weekly_bars(
    *,
    security: str,
    market_timezone: str,
    daily_bars: tuple[DailyBar, ...],
    trading_days: tuple[TradingDay, ...],
    as_of: datetime,
) -> tuple[DerivedBar, ...]:
    cutoff = require_utc(as_of)
    timezone = ZoneInfo(market_timezone)
    eligible = tuple(bar for bar in daily_bars if bar.is_completed and bar.retrieved_at <= cutoff)
    grouped: dict[tuple[int, int], list[DailyBar]] = defaultdict(list)
    for bar in eligible:
        iso = bar.session_date.isocalendar()
        grouped[(iso.year, iso.week)].append(bar)
    calendar_by_week: dict[tuple[int, int], list[TradingDay]] = defaultdict(list)
    for trading_day in trading_days:
        if trading_day.retrieved_at > cutoff:
            continue
        iso = trading_day.market_date.isocalendar()
        calendar_by_week[(iso.year, iso.week)].append(trading_day)

    output: list[DerivedBar] = []
    for key in sorted(grouped):
        source = sorted(grouped[key], key=lambda bar: bar.session_date)
        monday = date.fromisocalendar(key[0], key[1], 1)
        local_start = datetime.combine(monday, time.min, tzinfo=timezone)
        local_end = local_start + timedelta(days=7)
        later_week_known = any(candidate > key for candidate in grouped)
        week_has_ended = cutoff >= local_end.astimezone(UTC)
        calendar_rows = sorted(calendar_by_week.get(key, []), key=lambda item: item.market_date)
        calendar_final = False
        if calendar_rows:
            final_day = calendar_rows[-1]
            if final_day.session_segments:
                final_end = datetime.combine(
                    final_day.market_date,
                    final_day.session_segments[-1].end,
                    tzinfo=timezone,
                ).astimezone(UTC)
                calendar_final = cutoff >= final_end
        expected = len(calendar_rows) or None
        source_dates = {bar.session_date for bar in source}
        expected_dates = {item.market_date for item in calendar_rows}
        if expected is None:
            coverage = DerivedCoverage.UNKNOWN
        elif source_dates == expected_dates:
            coverage = DerivedCoverage.COMPLETE
        else:
            coverage = DerivedCoverage.PARTIAL
        finalized = calendar_final or later_week_known or week_has_ended
        output.append(
            _aggregate(
                security=security,
                timeframe=DerivedTimeframe.W1,
                interval_start=local_start.astimezone(UTC),
                interval_end=local_end.astimezone(UTC),
                market_timezone=market_timezone,
                session_type=None,
                source=source,
                expected=expected,
                coverage=coverage,
                is_completed=finalized and coverage is not DerivedCoverage.PARTIAL,
            )
        )
    return tuple(output)


def derive_m30_bars(
    *,
    security: str,
    market_timezone: str,
    minute_bars: tuple[MinuteBar, ...],
    trading_days: tuple[TradingDay, ...],
    as_of: datetime,
) -> tuple[DerivedBar, ...]:
    cutoff = require_utc(as_of)
    timezone = ZoneInfo(market_timezone)
    source_by_start = {
        bar.interval_start: bar
        for bar in minute_bars
        if bar.is_completed and bar.retrieved_at <= cutoff and bar.interval_end <= cutoff
    }
    output: list[DerivedBar] = []
    for trading_day in sorted(trading_days, key=lambda item: item.market_date):
        if trading_day.retrieved_at > cutoff:
            continue
        for segment in trading_day.session_segments:
            local_bucket_start = datetime.combine(
                trading_day.market_date, segment.start, tzinfo=timezone
            )
            local_segment_end = datetime.combine(
                trading_day.market_date, segment.end, tzinfo=timezone
            )
            while local_bucket_start + timedelta(minutes=30) <= local_segment_end:
                local_bucket_end = local_bucket_start + timedelta(minutes=30)
                bucket_start = local_bucket_start.astimezone(UTC)
                bucket_end = local_bucket_end.astimezone(UTC)
                if bucket_end > cutoff:
                    local_bucket_start = local_bucket_end
                    continue
                expected_starts = tuple(
                    bucket_start + timedelta(minutes=offset) for offset in range(30)
                )
                source = [
                    source_by_start[value] for value in expected_starts if value in source_by_start
                ]
                if source:
                    coverage = (
                        DerivedCoverage.COMPLETE
                        if len(source) == 30
                        and all(
                            bar.interval_end == expected_start + timedelta(minutes=1)
                            for bar, expected_start in zip(source, expected_starts, strict=True)
                        )
                        else DerivedCoverage.PARTIAL
                    )
                    output.append(
                        _aggregate(
                            security=security,
                            timeframe=DerivedTimeframe.M30,
                            interval_start=bucket_start,
                            interval_end=bucket_end,
                            market_timezone=market_timezone,
                            session_type="REGULAR",
                            source=source,
                            expected=30,
                            coverage=coverage,
                            is_completed=coverage is DerivedCoverage.COMPLETE,
                        )
                    )
                local_bucket_start = local_bucket_end
    return tuple(output)


def expected_completed_m30_bucket_count(
    trading_days: tuple[TradingDay, ...], as_of: datetime
) -> int:
    cutoff = require_utc(as_of)
    count = 0
    for trading_day in trading_days:
        if trading_day.retrieved_at > cutoff:
            continue
        timezone = ZoneInfo(trading_day.market_timezone)
        for segment in trading_day.session_segments:
            bucket_start = datetime.combine(trading_day.market_date, segment.start, tzinfo=timezone)
            segment_end = datetime.combine(trading_day.market_date, segment.end, tzinfo=timezone)
            while bucket_start + timedelta(minutes=30) <= segment_end:
                if bucket_start.astimezone(UTC) + timedelta(minutes=30) <= cutoff:
                    count += 1
                bucket_start += timedelta(minutes=30)
    return count


def _aggregate(
    *,
    security: str,
    timeframe: DerivedTimeframe,
    interval_start: datetime,
    interval_end: datetime,
    market_timezone: str,
    session_type: str | None,
    source: list[DailyBar] | list[MinuteBar],
    expected: int | None,
    coverage: DerivedCoverage,
    is_completed: bool,
) -> DerivedBar:
    return DerivedBar(
        security=security,
        timeframe=timeframe,
        interval_start=interval_start,
        interval_end=interval_end,
        open=source[0].open,
        high=max(bar.high for bar in source),
        low=min(bar.low for bar in source),
        close=source[-1].close,
        volume=sum((bar.volume for bar in source), start=Decimal(0)),
        market_timezone=market_timezone,
        session_type=session_type,
        source_bar_count=len(source),
        expected_source_bar_count=expected,
        coverage=coverage,
        is_completed=is_completed,
    )
