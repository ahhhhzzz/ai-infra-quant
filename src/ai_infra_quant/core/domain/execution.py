from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ai_infra_quant.core.domain.common import canonical_uuid, require_utc
from ai_infra_quant.core.domain.enums import OrderSide, OrderState, OrderType, TimeInForce
from ai_infra_quant.core.domain.money import parse_decimal
from ai_infra_quant.core.domain.security import normalize_currency


@dataclass(frozen=True, slots=True)
class StandardOrder:
    internal_order_id: str
    client_order_id: str
    idempotency_key: str
    portfolio_id: str
    account_id: str
    broker_profile_id: str
    security_id: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    currency: str
    time_in_force: TimeInForce
    created_at: datetime
    limit_price: Decimal | None = None
    expires_at: datetime | None = None
    strategy_run_id: str | None = None
    recommendation_id: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "internal_order_id",
            "portfolio_id",
            "account_id",
            "broker_profile_id",
            "security_id",
        ):
            object.__setattr__(self, field_name, canonical_uuid(getattr(self, field_name)))
        object.__setattr__(self, "quantity", parse_decimal(self.quantity))
        object.__setattr__(self, "currency", normalize_currency(self.currency))
        object.__setattr__(self, "created_at", require_utc(self.created_at))
        if self.quantity <= 0:
            raise ValueError("order quantity must be positive")
        if self.order_type is OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit orders require a limit price")
        if self.order_type is OrderType.MARKET and self.limit_price is not None:
            raise ValueError("market orders cannot have a limit price")


@dataclass(frozen=True, slots=True)
class OrderResult:
    order_id: str
    state: OrderState
    message: str | None = None


@dataclass(frozen=True, slots=True)
class FillResult:
    fill_id: str
    order_id: str
    quantity: Decimal
    price: Decimal
    executed_at: datetime


@dataclass(frozen=True, slots=True)
class CancelOrderRequest:
    order_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class ModifyOrderRequest:
    order_id: str
    quantity: Decimal
    limit_price: Decimal | None
