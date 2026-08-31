from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from ai_infra_quant.core.domain.execution import (
    CancelOrderRequest,
    FillResult,
    ModifyOrderRequest,
    OrderResult,
    StandardOrder,
)
from ai_infra_quant.core.domain.providers import (
    BrokerAccount,
    BrokerCapabilities,
    BrokerPosition,
    CashBalance,
    ConnectionResult,
    MarketStatus,
    ProviderRecord,
)


class BrokerAdapter(ABC):
    broker_name: str

    @abstractmethod
    def connect(self) -> ConnectionResult: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def connection_status(self) -> ConnectionResult: ...

    @abstractmethod
    def capabilities(self) -> BrokerCapabilities: ...

    @abstractmethod
    def get_accounts(self) -> list[BrokerAccount]: ...

    @abstractmethod
    def get_account_info(self, account_id: str) -> ProviderRecord: ...

    @abstractmethod
    def get_cash_balances(self, account_id: str) -> list[CashBalance]: ...

    @abstractmethod
    def get_positions(self, account_id: str) -> list[BrokerPosition]: ...

    @abstractmethod
    def get_orders(self, account_id: str) -> list[OrderResult]: ...

    @abstractmethod
    def get_fills(self, account_id: str) -> list[FillResult]: ...

    @abstractmethod
    def get_buying_power(self, account_id: str, currency: str) -> Decimal: ...

    @abstractmethod
    def place_order(self, order: StandardOrder) -> OrderResult: ...

    @abstractmethod
    def cancel_order(self, request: CancelOrderRequest) -> OrderResult: ...

    @abstractmethod
    def modify_order(self, request: ModifyOrderRequest) -> OrderResult: ...

    @abstractmethod
    def get_market_status(self, market: str) -> MarketStatus: ...
