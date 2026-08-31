from __future__ import annotations

from pydantic import Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from ai_infra_quant.backend.schemas.common import StrictSchema
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.money import decimal_string
from ai_infra_quant.core.domain.security import (
    Security,
    SecurityIdentityError,
    canonicalize_security_identity,
)


class TradingRulesRead(StrictSchema):
    lot_size: str | None = None
    min_order_quantity: str | None = None
    quantity_step: str | None = None
    tick_size: str | None = None
    min_notional: str | None = None
    fractional_supported: bool = False
    status: DataAvailabilityStatus


class SecuritySummaryRead(StrictSchema):
    id: str
    market: str
    symbol: str
    display_symbol: str
    display_name: str
    exchange: str | None
    currency: str
    instrument_type: str
    metadata_status: DataAvailabilityStatus


class SecurityReadV1(SecuritySummaryRead):
    enabled: bool
    record_source: str
    verification_status: str
    tradability_status: str
    trading_rules: TradingRulesRead
    market_timezone: str | None
    trading_calendar: str | None
    provider_mappings: list[dict[str, str]]


class SecurityCreateV1(StrictSchema):
    market: str
    symbol: str
    currency: str = Field(min_length=3, max_length=3)
    instrument_type: str
    display_name: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def canonicalize_identity(self) -> SecurityCreateV1:
        try:
            market, symbol = canonicalize_security_identity(self.market, self.symbol)
        except SecurityIdentityError as exc:
            raise PydanticCustomError(exc.code, str(exc)) from exc
        self.market = market
        self.symbol = symbol
        return self

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized.isascii() or not normalized.isalpha():
            raise ValueError("currency must be three ASCII letters")
        return normalized

    @field_validator("instrument_type")
    @classmethod
    def validate_instrument_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"EQUITY", "ETF", "UNKNOWN"}:
            raise ValueError("instrument_type must be EQUITY, ETF, or UNKNOWN")
        return normalized

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("display_name cannot be blank")
        return normalized


def security_summary_from_domain(security: Security) -> SecuritySummaryRead:
    return SecuritySummaryRead(
        id=security.id,
        market=security.market,
        symbol=security.symbol,
        display_symbol=security.display_symbol,
        display_name=security.display_name,
        exchange=security.exchange,
        currency=security.currency,
        instrument_type=security.instrument_type.value,
        metadata_status=security.metadata_status,
    )


def _optional_decimal(value: object) -> str | None:
    from decimal import Decimal

    return decimal_string(value) if isinstance(value, Decimal) else None


def security_read_from_domain(security: Security) -> SecurityReadV1:
    rules = security.trading_rules
    return SecurityReadV1(
        **security_summary_from_domain(security).model_dump(),
        enabled=security.enabled,
        record_source=security.record_source.value,
        verification_status=security.verification_status.value,
        tradability_status=security.tradability_status.value,
        trading_rules=TradingRulesRead(
            lot_size=_optional_decimal(rules.lot_size),
            min_order_quantity=_optional_decimal(rules.min_order_quantity),
            quantity_step=_optional_decimal(rules.quantity_step),
            tick_size=_optional_decimal(rules.tick_size),
            min_notional=_optional_decimal(rules.min_notional),
            fractional_supported=rules.fractional_supported,
            status=rules.status,
        ),
        market_timezone=security.market_timezone,
        trading_calendar=security.trading_calendar,
        provider_mappings=[],
    )
