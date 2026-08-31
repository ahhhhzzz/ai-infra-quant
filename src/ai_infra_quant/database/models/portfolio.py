from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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


class BrokerProfileModel(Base):
    __tablename__ = "broker_profiles"
    __table_args__ = (
        UniqueConstraint("name", name="name"),
        CheckConstraint(
            "environment IN ('PAPER','SIMULATED','LIVE','READ_ONLY')", name="environment"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    adapter_key: Mapped[str] = mapped_column(String(64), nullable=False)
    environment: Mapped[str] = mapped_column(String(24), nullable=False)
    implementation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    configuration_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class BrokerAccountModel(Base):
    __tablename__ = "broker_accounts"
    __table_args__ = (
        UniqueConstraint("broker_profile_id", "external_account_id_hash", name="external_identity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    broker_profile_id: Mapped[str] = mapped_column(
        ForeignKey("broker_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    external_account_id: Mapped[str | None] = mapped_column(String(255))
    external_account_id_hash: Mapped[str | None] = mapped_column(String(128))
    display_label: Mapped[str] = mapped_column(String(120), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    base_currency: Mapped[str | None] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    is_read_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_reconciled_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class PortfolioModel(Base):
    __tablename__ = "portfolios"
    __table_args__ = (UniqueConstraint("name", name="name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    inception_date: Mapped[date] = mapped_column(Date, nullable=False)
    valuation_timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    daily_cutoff_policy: Mapped[str | None] = mapped_column(String(120))
    initial_nav: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class PortfolioAccountModel(Base):
    __tablename__ = "portfolio_accounts"
    __table_args__ = (
        Index(
            "uq_portfolio_accounts_active_broker_account",
            "broker_account_id",
            unique=True,
            sqlite_where=text("effective_to IS NULL"),
            postgresql_where=text("effective_to IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("portfolios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    broker_account_id: Mapped[str] = mapped_column(
        ForeignKey("broker_accounts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    effective_from: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(UTCDateTime())
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
