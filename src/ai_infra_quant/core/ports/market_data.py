from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from types import TracebackType
from typing import Protocol, Self

from ai_infra_quant.core.domain.market_data import (
    DailyBar,
    MarketDataSecurity,
    MarketStatusSnapshot,
    MinuteBar,
    ProviderResult,
    ProviderStatus,
    QuoteSnapshot,
    TradingDay,
)
from ai_infra_quant.core.domain.providers import (
    ConnectionResult,
    MarketDataCapabilities,
    ProviderRecord,
    Quote,
)


@dataclass(frozen=True, slots=True)
class HistoryRequest:
    security_id: str
    start: datetime
    end: datetime
    interval: str


@dataclass(frozen=True, slots=True)
class SubscriptionRequest:
    security_ids: tuple[str, ...]
    channel: str


class MarketDataProvider(ABC):
    @abstractmethod
    def connect(self) -> ConnectionResult: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def capabilities(self) -> MarketDataCapabilities: ...

    @abstractmethod
    def get_quote(self, security_id: str) -> Quote: ...

    @abstractmethod
    def get_snapshot(self, security_ids: list[str]) -> list[Quote]: ...

    @abstractmethod
    def get_history(self, request: HistoryRequest) -> list[ProviderRecord]: ...

    @abstractmethod
    def subscribe(self, request: SubscriptionRequest) -> ConnectionResult: ...

    @abstractmethod
    def unsubscribe(self, request: SubscriptionRequest) -> ConnectionResult: ...

    @abstractmethod
    def get_order_book(self, security_id: str) -> ProviderRecord: ...


class ReadOnlyMarketDataProvider(Protocol):
    """Minimal request-scoped canonical market-data boundary for Phase 2."""

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def provider_status(self) -> ProviderResult[ProviderStatus]: ...

    def get_latest_quote(self, security: MarketDataSecurity) -> ProviderResult[QuoteSnapshot]: ...

    def get_market_status(
        self, security: MarketDataSecurity
    ) -> ProviderResult[MarketStatusSnapshot]: ...

    def get_daily_bars(
        self, security: MarketDataSecurity, limit: int
    ) -> ProviderResult[tuple[DailyBar, ...]]: ...

    def get_recent_minute_bars(
        self, security: MarketDataSecurity, lookback_days: int
    ) -> ProviderResult[tuple[MinuteBar, ...]]: ...

    def get_trading_days(
        self, market: str, start_date: date, end_date: date
    ) -> ProviderResult[tuple[TradingDay, ...]]: ...
