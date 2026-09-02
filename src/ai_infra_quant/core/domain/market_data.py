from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import StrEnum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ai_infra_quant.core.domain.common import require_utc
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.security import (
    canonicalize_security_identity,
    normalize_currency,
)

PROVIDER_FUTU_QUOTE = "futu_opend_quote"


class PriceKind(StrEnum):
    LATEST = "LATEST"


class CanonicalMarketState(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PRE_MARKET = "PRE_MARKET"
    AFTER_HOURS = "AFTER_HOURS"
    BREAK = "BREAK"
    UNKNOWN = "UNKNOWN"


class TradingDayType(StrEnum):
    FULL = "FULL"
    MORNING_ONLY = "MORNING_ONLY"
    AFTERNOON_ONLY = "AFTERNOON_ONLY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class TradingSessionSegment:
    start: time
    end: time

    def __post_init__(self) -> None:
        if self.start.tzinfo is not None or self.end.tzinfo is not None:
            raise ValueError("trading-session wall times must be timezone-naive")
        if self.end <= self.start:
            raise ValueError("trading-session segment end must follow its start")


@dataclass(frozen=True, slots=True)
class TradingDay:
    market: str
    market_date: date
    market_timezone: str
    day_type: TradingDayType
    provider_day_type: str
    session_segments: tuple[TradingSessionSegment, ...]
    provider: str
    retrieved_at: datetime

    def __post_init__(self) -> None:
        market = self.market.strip().upper()
        if market not in {"US", "HK"}:
            raise ValueError("trading-day market must be US or HK")
        object.__setattr__(self, "market", market)
        try:
            timezone = ZoneInfo(self.market_timezone).key
        except ZoneInfoNotFoundError as exc:
            raise ValueError("market_timezone must be a valid IANA timezone") from exc
        object.__setattr__(self, "market_timezone", timezone)
        object.__setattr__(self, "retrieved_at", require_utc(self.retrieved_at))
        if any(
            current.end > following.start
            for current, following in zip(
                self.session_segments, self.session_segments[1:], strict=False
            )
        ):
            raise ValueError("trading-session segments must not overlap")


@dataclass(frozen=True, slots=True)
class MarketDataSecurity:
    market: str
    symbol: str
    currency: str
    market_timezone: str

    def __post_init__(self) -> None:
        market, symbol = canonicalize_security_identity(self.market, self.symbol)
        object.__setattr__(self, "market", market)
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "currency", normalize_currency(self.currency))
        try:
            timezone = ZoneInfo(self.market_timezone).key
        except ZoneInfoNotFoundError as exc:
            raise ValueError("market_timezone must be a valid IANA timezone") from exc
        object.__setattr__(self, "market_timezone", timezone)

    @property
    def display_symbol(self) -> str:
        return f"{self.market}.{self.symbol}"


@dataclass(frozen=True, slots=True)
class QuoteSnapshot:
    security: str
    price: Decimal
    currency: str
    latest_quote_at: datetime
    retrieved_at: datetime
    price_kind: PriceKind = PriceKind.LATEST
    is_equity: bool | None = None

    def __post_init__(self) -> None:
        _require_positive_decimal(self.price, "price")
        if self.is_equity is not None and not isinstance(self.is_equity, bool):
            raise ValueError("is_equity must be an explicit bool or None")
        object.__setattr__(self, "latest_quote_at", require_utc(self.latest_quote_at))
        object.__setattr__(self, "retrieved_at", require_utc(self.retrieved_at))


@dataclass(frozen=True, slots=True)
class MarketStatusSnapshot:
    security: str
    state: CanonicalMarketState
    provider_state: str
    retrieved_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "retrieved_at", require_utc(self.retrieved_at))


@dataclass(frozen=True, slots=True)
class DailyBar:
    security: str
    session_date: date
    provider_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    is_completed: bool
    retrieved_at: datetime

    def __post_init__(self) -> None:
        _validate_ohlcv(self.open, self.high, self.low, self.close, self.volume)
        if not self.is_completed:
            raise ValueError("canonical daily output must be completed")
        object.__setattr__(self, "provider_time", require_utc(self.provider_time))
        object.__setattr__(self, "retrieved_at", require_utc(self.retrieved_at))


@dataclass(frozen=True, slots=True)
class MinuteBar:
    security: str
    interval_start: datetime
    interval_end: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    is_completed: bool
    retrieved_at: datetime

    def __post_init__(self) -> None:
        _validate_ohlcv(self.open, self.high, self.low, self.close, self.volume)
        interval_start = require_utc(self.interval_start)
        interval_end = require_utc(self.interval_end)
        if interval_end <= interval_start:
            raise ValueError("minute interval end must follow its start")
        if not self.is_completed:
            raise ValueError("canonical minute output must be completed")
        object.__setattr__(self, "interval_start", interval_start)
        object.__setattr__(self, "interval_end", interval_end)
        object.__setattr__(self, "retrieved_at", require_utc(self.retrieved_at))


@dataclass(frozen=True, slots=True)
class ProviderStatus:
    quote_context_open: bool
    sdk_version: str | None


@dataclass(frozen=True, slots=True)
class ProviderResult[ResultT]:
    status: DataAvailabilityStatus
    retrieved_at: datetime
    provider: str = PROVIDER_FUTU_QUOTE
    data: ResultT | None = None
    reason: str | None = None
    provider_delay_seconds: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "retrieved_at", require_utc(self.retrieved_at))
        if self.status is DataAvailabilityStatus.AVAILABLE and self.data is None:
            raise ValueError("available provider result requires data")
        if self.provider_delay_seconds is not None and self.provider_delay_seconds < 0:
            raise ValueError("provider delay cannot be negative")


def _require_positive_decimal(value: Decimal, field_name: str) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
        raise ValueError(f"{field_name} must be a positive finite Decimal")


def _validate_ohlcv(
    open_value: Decimal,
    high_value: Decimal,
    low_value: Decimal,
    close_value: Decimal,
    volume: Decimal,
) -> None:
    for field_name, value in (
        ("open", open_value),
        ("high", high_value),
        ("low", low_value),
        ("close", close_value),
    ):
        _require_positive_decimal(value, field_name)
    if not isinstance(volume, Decimal) or not volume.is_finite() or volume < 0:
        raise ValueError("volume must be a non-negative finite Decimal")
    if high_value < max(open_value, close_value, low_value):
        raise ValueError("high must not be below OHLC values")
    if low_value > min(open_value, close_value, high_value):
        raise ValueError("low must not be above OHLC values")
