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


class LedgerAccountModel(Base):
    __tablename__ = "ledger_accounts"
    __table_args__ = (
        CheckConstraint("normal_balance IN ('DEBIT','CREDIT')", name="normal_balance"),
        Index(
            "uq_ledger_accounts_none",
            "portfolio_id",
            "account_code",
            unique=True,
            sqlite_where=text(
                "broker_account_id IS NULL AND security_id IS NULL AND currency IS NULL"
            ),
            postgresql_where=text(
                "broker_account_id IS NULL AND security_id IS NULL AND currency IS NULL"
            ),
        ),
        Index(
            "uq_ledger_accounts_broker",
            "portfolio_id",
            "broker_account_id",
            "account_code",
            unique=True,
            sqlite_where=text(
                "broker_account_id IS NOT NULL AND security_id IS NULL AND currency IS NULL"
            ),
            postgresql_where=text(
                "broker_account_id IS NOT NULL AND security_id IS NULL AND currency IS NULL"
            ),
        ),
        Index(
            "uq_ledger_accounts_security",
            "portfolio_id",
            "security_id",
            "account_code",
            unique=True,
            sqlite_where=text(
                "broker_account_id IS NULL AND security_id IS NOT NULL AND currency IS NULL"
            ),
            postgresql_where=text(
                "broker_account_id IS NULL AND security_id IS NOT NULL AND currency IS NULL"
            ),
        ),
        Index(
            "uq_ledger_accounts_currency",
            "portfolio_id",
            "account_code",
            "currency",
            unique=True,
            sqlite_where=text(
                "broker_account_id IS NULL AND security_id IS NULL AND currency IS NOT NULL"
            ),
            postgresql_where=text(
                "broker_account_id IS NULL AND security_id IS NULL AND currency IS NOT NULL"
            ),
        ),
        Index(
            "uq_ledger_accounts_broker_security",
            "portfolio_id",
            "broker_account_id",
            "security_id",
            "account_code",
            unique=True,
            sqlite_where=text(
                "broker_account_id IS NOT NULL AND security_id IS NOT NULL AND currency IS NULL"
            ),
            postgresql_where=text(
                "broker_account_id IS NOT NULL AND security_id IS NOT NULL AND currency IS NULL"
            ),
        ),
        Index(
            "uq_ledger_accounts_broker_currency",
            "portfolio_id",
            "broker_account_id",
            "account_code",
            "currency",
            unique=True,
            sqlite_where=text(
                "broker_account_id IS NOT NULL AND security_id IS NULL AND currency IS NOT NULL"
            ),
            postgresql_where=text(
                "broker_account_id IS NOT NULL AND security_id IS NULL AND currency IS NOT NULL"
            ),
        ),
        Index(
            "uq_ledger_accounts_security_currency",
            "portfolio_id",
            "security_id",
            "account_code",
            "currency",
            unique=True,
            sqlite_where=text(
                "broker_account_id IS NULL AND security_id IS NOT NULL AND currency IS NOT NULL"
            ),
            postgresql_where=text(
                "broker_account_id IS NULL AND security_id IS NOT NULL AND currency IS NOT NULL"
            ),
        ),
        Index(
            "uq_ledger_accounts_all_dimensions",
            "portfolio_id",
            "broker_account_id",
            "security_id",
            "account_code",
            "currency",
            unique=True,
            sqlite_where=text(
                "broker_account_id IS NOT NULL AND security_id IS NOT NULL AND currency IS NOT NULL"
            ),
            postgresql_where=text(
                "broker_account_id IS NOT NULL AND security_id IS NOT NULL AND currency IS NOT NULL"
            ),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("portfolios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    broker_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("broker_accounts.id", ondelete="RESTRICT"), index=True
    )
    security_id: Mapped[str | None] = mapped_column(
        ForeignKey("securities.id", ondelete="RESTRICT"), index=True
    )
    account_code: Mapped[str] = mapped_column(String(64), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    normal_balance: Mapped[str] = mapped_column(String(8), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class LedgerTransactionModel(Base):
    __tablename__ = "ledger_transactions"
    __table_args__ = (
        UniqueConstraint("sequence_no", name="uq_ledger_transactions_sequence_no"),
        UniqueConstraint(
            "portfolio_id",
            "idempotency_key",
            name="uq_ledger_transactions_portfolio_idempotency_key",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("portfolios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(120), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    reverses_transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT")
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)


class LedgerEntryModel(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        UniqueConstraint(
            "ledger_transaction_id", "entry_no", name="uq_ledger_entries_transaction_entry_no"
        ),
        CheckConstraint("direction IN ('DEBIT','CREDIT')", name="direction"),
        CheckConstraint("entry_no > 0", name="entry_no_positive"),
        CheckConstraint("length(currency) = 3", name="currency_length"),
        CheckConstraint("length(base_currency) = 3", name="base_currency_length"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    ledger_transaction_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    ledger_account_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_accounts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    entry_no: Mapped[int] = mapped_column(Integer, nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    amount: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    base_fx_rate: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(ExactDecimal())
    unit_price: Mapped[Decimal | None] = mapped_column(ExactDecimal())
    security_id: Mapped[str | None] = mapped_column(
        ForeignKey("securities.id", ondelete="RESTRICT"), index=True
    )
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class CashFlowModel(Base):
    __tablename__ = "cash_flows"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id",
            "idempotency_key",
            name="uq_cash_flows_portfolio_idempotency_key",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("portfolios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    broker_account_id: Mapped[str] = mapped_column(
        ForeignKey("broker_accounts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    flow_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    posted_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    base_fx_rate: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    pre_flow_nav: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    units_issued: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    units_redeemed: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    pre_flow_snapshot_id: Mapped[str | None] = mapped_column(
        ForeignKey("portfolio_snapshots.id", ondelete="RESTRICT")
    )
    ledger_transaction_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    reverses_cash_flow_id: Mapped[str | None] = mapped_column(
        ForeignKey("cash_flows.id", ondelete="RESTRICT")
    )


class UnitTransactionModel(Base):
    __tablename__ = "unit_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("portfolios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cash_flow_id: Mapped[str] = mapped_column(
        ForeignKey("cash_flows.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    unit_event_type: Mapped[str] = mapped_column(String(24), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    nav_per_unit: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    unit_quantity: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    reverses_unit_transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("unit_transactions.id", ondelete="RESTRICT")
    )


class CashBalanceModel(Base):
    __tablename__ = "cash_balances"
    __table_args__ = (
        UniqueConstraint(
            "broker_account_id", "currency", name="uq_cash_balances_broker_account_currency"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    broker_account_id: Mapped[str] = mapped_column(
        ForeignKey("broker_accounts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    settled_amount: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    unsettled_receivable: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    unsettled_payable: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    reserved_amount: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    reported_buying_power: Mapped[Decimal | None] = mapped_column(ExactDecimal())
    reported_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    as_of_ledger_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class PortfolioSnapshotModel(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id",
            "valuation_at",
            "valuation_kind",
            "is_official",
            name="uq_portfolio_snapshots_official_point",
        ),
        CheckConstraint(
            "quality_status IN ('COMPLETE','PARTIAL','INVALID')", name="quality_status"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("portfolios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    valuation_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    valuation_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    cash_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    market_value: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    receivables: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    payables: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    total_equity: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    units_outstanding: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    nav_per_unit: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    fees: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    taxes: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    equity_pnl: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    fx_pnl: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    cash_ratio: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    invested_ratio: Mapped[Decimal] = mapped_column(ExactDecimal(), nullable=False)
    price_manifest_hash: Mapped[str | None] = mapped_column(String(128))
    fx_manifest_hash: Mapped[str | None] = mapped_column(String(128))
    ledger_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_official: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    quality_status: Mapped[str] = mapped_column(String(24), nullable=False)
    missing_data_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")


class ExactDecimalProbeModel(Base):
    """Not migrated; tests define a local table directly with ExactDecimal."""

    __abstract__ = True
