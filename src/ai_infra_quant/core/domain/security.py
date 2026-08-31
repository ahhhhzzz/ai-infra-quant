from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ai_infra_quant.core.domain.common import canonical_uuid, require_utc
from ai_infra_quant.core.domain.enums import (
    DataAvailabilityStatus,
    InstrumentType,
    RecordSource,
    TradabilityStatus,
    VerificationStatus,
)

_US_SYMBOL = re.compile(r"^[A-Z0-9]+(?:[.-][A-Z0-9]+)*$")
_HK_SYMBOL = re.compile(r"^[0-9]{1,5}$")


class SecurityIdentityError(ValueError):
    code: str


class InvalidMarketError(SecurityIdentityError):
    code = "INVALID_MARKET"


class InvalidSymbolError(SecurityIdentityError):
    code = "INVALID_SYMBOL"


class SecurityIdentityConflict(RuntimeError):
    def __init__(self, security_id: str) -> None:
        super().__init__("canonical security identity already exists")
        self.security_id = security_id


def canonicalize_market(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in {"US", "HK"}:
        raise InvalidMarketError("market has no configured Phase 1 canonicalizer")
    return normalized


def canonicalize_security_identity(market: str, symbol: str) -> tuple[str, str]:
    normalized_market = canonicalize_market(market)
    normalized_symbol = symbol.strip().upper()
    if normalized_market == "US":
        if len(normalized_symbol) > 32 or _US_SYMBOL.fullmatch(normalized_symbol) is None:
            raise InvalidSymbolError(
                "US symbol must contain ASCII letters/digits separated by periods or hyphens"
            )
        return normalized_market, normalized_symbol
    if _HK_SYMBOL.fullmatch(normalized_symbol) is None:
        raise InvalidSymbolError("HK symbol must contain one to five ASCII digits")
    return normalized_market, normalized_symbol.zfill(5)


def normalize_currency(value: str) -> str:
    normalized = value.strip().upper()
    if len(normalized) != 3 or not normalized.isascii() or not normalized.isalpha():
        raise ValueError("currency must be three ASCII letters")
    return normalized


@dataclass(frozen=True, slots=True)
class TradingRules:
    lot_size: Decimal | None = None
    min_order_quantity: Decimal | None = None
    quantity_step: Decimal | None = None
    tick_size: Decimal | None = None
    min_notional: Decimal | None = None
    fractional_supported: bool = False
    status: DataAvailabilityStatus = DataAvailabilityStatus.UNAVAILABLE


@dataclass(frozen=True, slots=True)
class Security:
    id: str
    market: str
    symbol: str
    currency: str
    display_name: str
    instrument_type: InstrumentType
    enabled: bool
    record_source: RecordSource
    verification_status: VerificationStatus
    tradability_status: TradabilityStatus
    metadata_status: DataAvailabilityStatus
    created_at: datetime
    updated_at: datetime
    exchange: str | None = None
    market_timezone: str | None = None
    trading_calendar: str | None = None
    trading_rules: TradingRules = TradingRules()

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", canonical_uuid(self.id))
        market, symbol = canonicalize_security_identity(self.market, self.symbol)
        object.__setattr__(self, "market", market)
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "currency", normalize_currency(self.currency))
        object.__setattr__(self, "created_at", require_utc(self.created_at))
        object.__setattr__(self, "updated_at", require_utc(self.updated_at))
        if self.record_source is RecordSource.USER_SUPPLIED:
            if self.verification_status is not VerificationStatus.USER_SUPPLIED_UNVERIFIED:
                raise ValueError("user-supplied securities must remain unverified")
            if self.tradability_status is not TradabilityStatus.UNVERIFIED:
                raise ValueError("user-supplied securities must remain non-tradable")
            if self.metadata_status is not DataAvailabilityStatus.UNAVAILABLE:
                raise ValueError("user-supplied securities must keep metadata unavailable")
            if any((self.exchange, self.market_timezone, self.trading_calendar)):
                raise ValueError("user-supplied securities cannot infer market metadata")
            if self.trading_rules != TradingRules():
                raise ValueError("user-supplied securities cannot infer trading rules")

    @property
    def display_symbol(self) -> str:
        return f"{self.market}.{self.symbol}"

    @property
    def strategy_and_orders_allowed(self) -> bool:
        return (
            self.enabled
            and self.verification_status is VerificationStatus.VERIFIED
            and self.tradability_status is TradabilityStatus.VERIFIED
            and self.trading_rules.status is DataAvailabilityStatus.AVAILABLE
        )
