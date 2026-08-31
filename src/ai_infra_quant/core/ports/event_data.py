from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from ai_infra_quant.core.domain.providers import EventDataCapabilities, ProviderRecord


class EventDataProvider(ABC):
    @abstractmethod
    def capabilities(self) -> EventDataCapabilities: ...

    @abstractmethod
    def get_earnings_calendar(
        self, security_id: str, start: datetime, end: datetime
    ) -> list[ProviderRecord]: ...

    @abstractmethod
    def get_corporate_actions(
        self, security_id: str, start: datetime, end: datetime
    ) -> list[ProviderRecord]: ...

    @abstractmethod
    def get_regulatory_events(
        self, security_id: str, start: datetime, end: datetime
    ) -> list[ProviderRecord]: ...

    @abstractmethod
    def get_manual_risk_flags(
        self, security_id: str, start: datetime, end: datetime
    ) -> list[ProviderRecord]: ...
