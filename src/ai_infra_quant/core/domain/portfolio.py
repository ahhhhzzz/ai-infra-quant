from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from ai_infra_quant.core.domain.common import canonical_uuid, require_utc
from ai_infra_quant.core.domain.enums import SnapshotQualityStatus
from ai_infra_quant.core.domain.money import parse_decimal
from ai_infra_quant.core.domain.security import normalize_currency


@dataclass(frozen=True, slots=True)
class Portfolio:
    id: str
    name: str
    base_currency: str
    inception_date: date
    valuation_timezone: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", canonical_uuid(self.id))
        object.__setattr__(self, "base_currency", normalize_currency(self.base_currency))


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    portfolio_id: str
    valuation_at: datetime
    total_equity: Decimal
    cash_value: Decimal
    market_value: Decimal
    units_outstanding: Decimal
    nav: Decimal
    cost_basis: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    fees: Decimal
    taxes: Decimal
    equity_pnl: Decimal
    fx_pnl: Decimal
    cash_ratio: Decimal
    invested_ratio: Decimal
    quality_status: SnapshotQualityStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "portfolio_id", canonical_uuid(self.portfolio_id))
        object.__setattr__(self, "valuation_at", require_utc(self.valuation_at))
        for field_name in (
            "total_equity",
            "cash_value",
            "market_value",
            "units_outstanding",
            "nav",
            "cost_basis",
            "realized_pnl",
            "unrealized_pnl",
            "fees",
            "taxes",
            "equity_pnl",
            "fx_pnl",
            "cash_ratio",
            "invested_ratio",
        ):
            object.__setattr__(self, field_name, parse_decimal(getattr(self, field_name)))
