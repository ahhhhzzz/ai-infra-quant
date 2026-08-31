from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from ai_infra_quant.core.domain.providers import FundamentalDataCapabilities, ProviderRecord


class FundamentalDataProvider(ABC):
    @abstractmethod
    def capabilities(self) -> FundamentalDataCapabilities: ...

    @abstractmethod
    def get_financials(self, security_id: str, as_of: datetime) -> list[ProviderRecord]: ...

    @abstractmethod
    def get_estimates(self, security_id: str, as_of: datetime) -> list[ProviderRecord]: ...

    @abstractmethod
    def get_valuation_metrics(self, security_id: str, as_of: datetime) -> ProviderRecord: ...

    @abstractmethod
    def get_valuation_history(
        self, security_id: str, end: datetime, lookback: str
    ) -> list[ProviderRecord]: ...

    @abstractmethod
    def get_balance_sheet_metrics(self, security_id: str, as_of: datetime) -> ProviderRecord: ...
