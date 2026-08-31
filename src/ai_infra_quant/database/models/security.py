from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ai_infra_quant.database.base import Base
from ai_infra_quant.database.types import ExactDecimal, UTCDateTime


class SecurityModel(Base):
    __tablename__ = "securities"
    __table_args__ = (
        UniqueConstraint("market", "symbol", name="uq_securities_market_symbol"),
        CheckConstraint("length(currency) = 3", name="currency_length"),
        CheckConstraint("instrument_type IN ('EQUITY','ETF','UNKNOWN')", name="instrument_type"),
        CheckConstraint("record_source IN ('SYSTEM_SEED','USER_SUPPLIED')", name="record_source"),
        CheckConstraint(
            "verification_status IN "
            "('VERIFIED','SYSTEM_SEED_UNVERIFIED','USER_SUPPLIED_UNVERIFIED')",
            name="verification_status",
        ),
        CheckConstraint(
            "tradability_status IN ('VERIFIED','UNVERIFIED','NOT_SUPPORTED','DISABLED')",
            name="tradability_status",
        ),
        CheckConstraint(
            "metadata_status IN ('AVAILABLE','MISSING','UNAVAILABLE','NOT_SUPPORTED','INVALID')",
            name="metadata_status",
        ),
        CheckConstraint(
            "record_source != 'USER_SUPPLIED' OR "
            "(verification_status = 'USER_SUPPLIED_UNVERIFIED' "
            "AND tradability_status = 'UNVERIFIED' AND metadata_status = 'UNAVAILABLE' "
            "AND exchange IS NULL "
            "AND lot_size IS NULL AND min_order_quantity IS NULL "
            "AND quantity_step IS NULL AND fractional_quantity_step IS NULL "
            "AND fractional_supported = false "
            "AND tick_size IS NULL AND min_notional IS NULL "
            "AND market_timezone IS NULL AND trading_calendar IS NULL)",
            name="user_supplied_fail_closed",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    exchange: Mapped[str | None] = mapped_column(String(64))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(16), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    lot_size: Mapped[Decimal | None] = mapped_column(ExactDecimal())
    min_order_quantity: Mapped[Decimal | None] = mapped_column(ExactDecimal())
    quantity_step: Mapped[Decimal | None] = mapped_column(ExactDecimal())
    fractional_quantity_step: Mapped[Decimal | None] = mapped_column(ExactDecimal())
    tick_size: Mapped[Decimal | None] = mapped_column(ExactDecimal())
    min_notional: Mapped[Decimal | None] = mapped_column(ExactDecimal())
    fractional_supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    market_timezone: Mapped[str | None] = mapped_column(String(64))
    trading_calendar: Mapped[str | None] = mapped_column(String(120))
    metadata_status: Mapped[str] = mapped_column(String(24), nullable=False)
    record_source: Mapped[str] = mapped_column(String(24), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False)
    tradability_status: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class ProviderSymbolMappingModel(Base):
    __tablename__ = "provider_symbol_mappings"
    __table_args__ = (
        Index(
            "uq_provider_mappings_active_security",
            "security_id",
            "provider_type",
            "provider_name",
            unique=True,
            sqlite_where=text("valid_to IS NULL"),
            postgresql_where=text("valid_to IS NULL"),
        ),
        Index(
            "uq_provider_mappings_active_reverse",
            "provider_type",
            "provider_name",
            "provider_symbol",
            unique=True,
            sqlite_where=text("valid_to IS NULL"),
            postgresql_where=text("valid_to IS NULL"),
        ),
        CheckConstraint(
            "provider_type IN ('BROKER','MARKET_DATA','FUNDAMENTAL','EVENT')",
            name="provider_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    security_id: Mapped[str] = mapped_column(
        ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    provider_type: Mapped[str] = mapped_column(String(24), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_symbol: Mapped[str] = mapped_column(String(120), nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(UTCDateTime())
    valid_to: Mapped[datetime | None] = mapped_column(UTCDateTime())
    mapping_status: Mapped[str] = mapped_column(String(24), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    retrieved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class WatchlistModel(Base):
    __tablename__ = "watchlists"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "name", name="uq_watchlists_portfolio_name"),
        Index(
            "uq_watchlists_default_portfolio",
            "portfolio_id",
            unique=True,
            sqlite_where=text("is_default = 1"),
            postgresql_where=text("is_default IS TRUE"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    portfolio_id: Mapped[str | None] = mapped_column(
        ForeignKey("portfolios.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class WatchlistItemModel(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        Index(
            "uq_watchlist_items_active_membership",
            "watchlist_id",
            "security_id",
            unique=True,
            sqlite_where=text("removed_at IS NULL"),
            postgresql_where=text("removed_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    watchlist_id: Mapped[str] = mapped_column(
        ForeignKey("watchlists.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    security_id: Mapped[str] = mapped_column(
        ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    removed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
