from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

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
