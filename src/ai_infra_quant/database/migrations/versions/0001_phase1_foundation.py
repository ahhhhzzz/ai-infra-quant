"""Create the explicit Phase 1 foundation schema.

Revision ID: 0001_phase1_foundation
Revises:
"""

from collections.abc import Iterable

import sqlalchemy as sa
from alembic import op

revision = "0001_phase1_foundation"
down_revision = None
branch_labels = None
depends_on = None


def _decimal() -> sa.types.TypeEngine[object]:
    return sa.Numeric(38, 18).with_variant(sa.Text(), "sqlite")


def _utc_datetime() -> sa.types.TypeEngine[object]:
    return sa.DateTime(timezone=True).with_variant(sa.Text(), "sqlite")


def _id(name: str) -> sa.Column[str]:
    return sa.Column(name, sa.String(36), nullable=False)


def _fk(name: str, target: str, *, nullable: bool = False) -> sa.Column[str]:
    return sa.Column(
        name,
        sa.String(36),
        sa.ForeignKey(target, ondelete="RESTRICT"),
        nullable=nullable,
    )


def _create_indexes(indexes: Iterable[tuple[str, str, list[str], bool, str | None]]) -> None:
    for name, table, columns, unique, predicate in indexes:
        kwargs: dict[str, object] = {}
        if predicate is not None:
            kwargs["sqlite_where"] = sa.text(predicate)
            kwargs["postgresql_where"] = sa.text(predicate)
        op.create_index(name, table, columns, unique=unique, **kwargs)


INDEXES = (
    (
        "ix_provider_symbol_mappings_security_id",
        "provider_symbol_mappings",
        ["security_id"],
        False,
        None,
    ),
    (
        "uq_provider_mappings_active_security",
        "provider_symbol_mappings",
        ["security_id", "provider_type", "provider_name"],
        True,
        "valid_to IS NULL",
    ),
    (
        "uq_provider_mappings_active_reverse",
        "provider_symbol_mappings",
        ["provider_type", "provider_name", "provider_symbol"],
        True,
        "valid_to IS NULL",
    ),
    ("ix_watchlists_portfolio_id", "watchlists", ["portfolio_id"], False, None),
    ("uq_watchlists_default_portfolio", "watchlists", ["portfolio_id"], True, "is_default = 1"),
    ("ix_watchlist_items_watchlist_id", "watchlist_items", ["watchlist_id"], False, None),
    ("ix_watchlist_items_security_id", "watchlist_items", ["security_id"], False, None),
    (
        "uq_watchlist_items_active_membership",
        "watchlist_items",
        ["watchlist_id", "security_id"],
        True,
        "removed_at IS NULL",
    ),
    ("ix_broker_accounts_broker_profile_id", "broker_accounts", ["broker_profile_id"], False, None),
    ("ix_portfolio_accounts_portfolio_id", "portfolio_accounts", ["portfolio_id"], False, None),
    (
        "ix_portfolio_accounts_broker_account_id",
        "portfolio_accounts",
        ["broker_account_id"],
        False,
        None,
    ),
    (
        "uq_portfolio_accounts_active_broker_account",
        "portfolio_accounts",
        ["broker_account_id"],
        True,
        "effective_to IS NULL",
    ),
    ("ix_strategy_assignments_security_id", "strategy_assignments", ["security_id"], False, None),
    (
        "ix_strategy_assignments_strategy_definition_id",
        "strategy_assignments",
        ["strategy_definition_id"],
        False,
        None,
    ),
    ("ix_strategy_assignments_portfolio_id", "strategy_assignments", ["portfolio_id"], False, None),
    (
        "uq_strategy_assignments_active_portfolio_security",
        "strategy_assignments",
        ["portfolio_id", "security_id"],
        True,
        "effective_to IS NULL AND portfolio_id IS NOT NULL",
    ),
    (
        "uq_strategy_assignments_active_global_security",
        "strategy_assignments",
        ["security_id"],
        True,
        "effective_to IS NULL AND portfolio_id IS NULL",
    ),
    ("uq_settings_system_scope_key", "settings", ["scope_type", "key"], True, "scope_id IS NULL"),
    (
        "uq_settings_named_scope_key",
        "settings",
        ["scope_type", "scope_id", "key"],
        True,
        "scope_id IS NOT NULL",
    ),
    ("ix_ledger_accounts_portfolio_id", "ledger_accounts", ["portfolio_id"], False, None),
    ("ix_ledger_accounts_broker_account_id", "ledger_accounts", ["broker_account_id"], False, None),
    ("ix_ledger_accounts_security_id", "ledger_accounts", ["security_id"], False, None),
    (
        "uq_ledger_accounts_none",
        "ledger_accounts",
        ["portfolio_id", "account_code"],
        True,
        "broker_account_id IS NULL AND security_id IS NULL AND currency IS NULL",
    ),
    (
        "uq_ledger_accounts_broker",
        "ledger_accounts",
        ["portfolio_id", "broker_account_id", "account_code"],
        True,
        "broker_account_id IS NOT NULL AND security_id IS NULL AND currency IS NULL",
    ),
    (
        "uq_ledger_accounts_security",
        "ledger_accounts",
        ["portfolio_id", "security_id", "account_code"],
        True,
        "broker_account_id IS NULL AND security_id IS NOT NULL AND currency IS NULL",
    ),
    (
        "uq_ledger_accounts_currency",
        "ledger_accounts",
        ["portfolio_id", "account_code", "currency"],
        True,
        "broker_account_id IS NULL AND security_id IS NULL AND currency IS NOT NULL",
    ),
    (
        "uq_ledger_accounts_broker_security",
        "ledger_accounts",
        ["portfolio_id", "broker_account_id", "security_id", "account_code"],
        True,
        "broker_account_id IS NOT NULL AND security_id IS NOT NULL AND currency IS NULL",
    ),
    (
        "uq_ledger_accounts_broker_currency",
        "ledger_accounts",
        ["portfolio_id", "broker_account_id", "account_code", "currency"],
        True,
        "broker_account_id IS NOT NULL AND security_id IS NULL AND currency IS NOT NULL",
    ),
    (
        "uq_ledger_accounts_security_currency",
        "ledger_accounts",
        ["portfolio_id", "security_id", "account_code", "currency"],
        True,
        "broker_account_id IS NULL AND security_id IS NOT NULL AND currency IS NOT NULL",
    ),
    (
        "uq_ledger_accounts_all_dimensions",
        "ledger_accounts",
        ["portfolio_id", "broker_account_id", "security_id", "account_code", "currency"],
        True,
        "broker_account_id IS NOT NULL AND security_id IS NOT NULL AND currency IS NOT NULL",
    ),
    ("ix_ledger_transactions_portfolio_id", "ledger_transactions", ["portfolio_id"], False, None),
    (
        "ix_ledger_entries_ledger_transaction_id",
        "ledger_entries",
        ["ledger_transaction_id"],
        False,
        None,
    ),
    ("ix_ledger_entries_ledger_account_id", "ledger_entries", ["ledger_account_id"], False, None),
    ("ix_ledger_entries_security_id", "ledger_entries", ["security_id"], False, None),
    ("ix_portfolio_snapshots_portfolio_id", "portfolio_snapshots", ["portfolio_id"], False, None),
    ("ix_cash_flows_portfolio_id", "cash_flows", ["portfolio_id"], False, None),
    ("ix_cash_flows_broker_account_id", "cash_flows", ["broker_account_id"], False, None),
    ("ix_unit_transactions_portfolio_id", "unit_transactions", ["portfolio_id"], False, None),
    ("ix_cash_balances_broker_account_id", "cash_balances", ["broker_account_id"], False, None),
)


IMMUTABLE_TABLES = (
    "ledger_transactions",
    "ledger_entries",
    "cash_flows",
    "unit_transactions",
    "portfolio_snapshots",
)


def upgrade() -> None:
    op.create_table(
        "securities",
        _id("id"),
        sa.Column("market", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("exchange", sa.String(64)),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("instrument_type", sa.String(16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("lot_size", _decimal()),
        sa.Column("min_order_quantity", _decimal()),
        sa.Column("quantity_step", _decimal()),
        sa.Column("fractional_quantity_step", _decimal()),
        sa.Column("tick_size", _decimal()),
        sa.Column("min_notional", _decimal()),
        sa.Column("fractional_supported", sa.Boolean(), nullable=False),
        sa.Column("market_timezone", sa.String(64)),
        sa.Column("trading_calendar", sa.String(120)),
        sa.Column("metadata_status", sa.String(24), nullable=False),
        sa.Column("record_source", sa.String(24), nullable=False),
        sa.Column("verification_status", sa.String(32), nullable=False),
        sa.Column("tradability_status", sa.String(24), nullable=False),
        sa.Column("created_at", _utc_datetime(), nullable=False),
        sa.Column("updated_at", _utc_datetime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_securities"),
        sa.UniqueConstraint("market", "symbol", name="identity"),
        sa.CheckConstraint("length(currency) = 3", name="ck_securities_currency_length"),
        sa.CheckConstraint(
            "instrument_type IN ('EQUITY','ETF','UNKNOWN')", name="ck_securities_instrument_type"
        ),
        sa.CheckConstraint(
            "record_source IN ('SYSTEM_SEED','USER_SUPPLIED')", name="ck_securities_record_source"
        ),
        sa.CheckConstraint(
            "verification_status IN ('VERIFIED','SYSTEM_SEED_UNVERIFIED',"
            "'USER_SUPPLIED_UNVERIFIED')",
            name="ck_securities_verification_status",
        ),
        sa.CheckConstraint(
            "tradability_status IN ('VERIFIED','UNVERIFIED','NOT_SUPPORTED','DISABLED')",
            name="ck_securities_tradability_status",
        ),
        sa.CheckConstraint(
            "metadata_status IN ('AVAILABLE','MISSING','UNAVAILABLE','NOT_SUPPORTED','INVALID')",
            name="ck_securities_metadata_status",
        ),
        sa.CheckConstraint(
            "record_source != 'USER_SUPPLIED' OR "
            "(verification_status = 'USER_SUPPLIED_UNVERIFIED' "
            "AND tradability_status = 'UNVERIFIED' "
            "AND metadata_status = 'UNAVAILABLE' "
            "AND exchange IS NULL AND lot_size IS NULL "
            "AND min_order_quantity IS NULL AND quantity_step IS NULL "
            "AND fractional_quantity_step IS NULL "
            "AND fractional_supported = false AND tick_size IS NULL "
            "AND min_notional IS NULL AND market_timezone IS NULL "
            "AND trading_calendar IS NULL)",
            name="ck_securities_user_supplied_fail_closed",
        ),
    )
    op.create_table(
        "strategy_definitions",
        _id("id"),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("implementation_key", sa.String(120), nullable=False),
        sa.Column("parameter_schema_json", sa.Text(), nullable=False),
        sa.Column("default_parameters_json", sa.Text(), nullable=False),
        sa.Column("definition_hash", sa.String(128), nullable=False),
        sa.Column("research_status", sa.String(32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", _utc_datetime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_strategy_definitions"),
        sa.UniqueConstraint("name", "version", name="identity"),
    )
    op.create_table(
        "broker_profiles",
        _id("id"),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("adapter_key", sa.String(64), nullable=False),
        sa.Column("environment", sa.String(24), nullable=False),
        sa.Column("implementation_status", sa.String(32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("configuration_json", sa.Text(), nullable=False),
        sa.Column("created_at", _utc_datetime(), nullable=False),
        sa.Column("updated_at", _utc_datetime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_broker_profiles"),
        sa.UniqueConstraint("name", name="name"),
        sa.CheckConstraint(
            "environment IN ('PAPER','SIMULATED','LIVE','READ_ONLY')",
            name="ck_broker_profiles_environment",
        ),
    )
    op.create_table(
        "portfolios",
        _id("id"),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("inception_date", sa.Date(), nullable=False),
        sa.Column("valuation_timezone", sa.String(64), nullable=False),
        sa.Column("daily_cutoff_policy", sa.String(120)),
        sa.Column("initial_nav", _decimal(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", _utc_datetime(), nullable=False),
        sa.Column("updated_at", _utc_datetime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_portfolios"),
        sa.UniqueConstraint("name", name="name"),
    )
    op.create_table(
        "settings",
        _id("id"),
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("scope_id", sa.String(36)),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("value_type", sa.String(32), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("is_secret", sa.Boolean(), nullable=False),
        sa.Column("updated_at", _utc_datetime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_settings"),
        sa.CheckConstraint("is_secret = false", name="ck_settings_never_secret"),
    )
    op.create_table(
        "broker_accounts",
        _id("id"),
        _fk("broker_profile_id", "broker_profiles.id"),
        sa.Column("external_account_id", sa.String(255)),
        sa.Column("external_account_id_hash", sa.String(128)),
        sa.Column("display_label", sa.String(120), nullable=False),
        sa.Column("account_type", sa.String(32), nullable=False),
        sa.Column("base_currency", sa.String(3)),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("is_read_only", sa.Boolean(), nullable=False),
        sa.Column("last_reconciled_at", _utc_datetime()),
        sa.Column("created_at", _utc_datetime(), nullable=False),
        sa.Column("updated_at", _utc_datetime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_broker_accounts"),
        sa.UniqueConstraint(
            "broker_profile_id",
            "external_account_id_hash",
            name="external_identity",
        ),
    )
    op.create_table(
        "portfolio_accounts",
        _id("id"),
        _fk("portfolio_id", "portfolios.id"),
        _fk("broker_account_id", "broker_accounts.id"),
        sa.Column("effective_from", _utc_datetime(), nullable=False),
        sa.Column("effective_to", _utc_datetime()),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_accounts"),
    )
    op.create_table(
        "watchlists",
        _id("id"),
        _fk("portfolio_id", "portfolios.id", nullable=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", _utc_datetime(), nullable=False),
        sa.Column("updated_at", _utc_datetime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_watchlists"),
        sa.UniqueConstraint("portfolio_id", "name", name="portfolio_name"),
    )
    op.create_table(
        "watchlist_items",
        _id("id"),
        _fk("watchlist_id", "watchlists.id"),
        _fk("security_id", "securities.id"),
        sa.Column("added_at", _utc_datetime(), nullable=False),
        sa.Column("removed_at", _utc_datetime()),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text()),
        sa.PrimaryKeyConstraint("id", name="pk_watchlist_items"),
    )
    op.create_table(
        "provider_symbol_mappings",
        _id("id"),
        _fk("security_id", "securities.id"),
        sa.Column("provider_type", sa.String(24), nullable=False),
        sa.Column("provider_name", sa.String(64), nullable=False),
        sa.Column("provider_symbol", sa.String(120), nullable=False),
        sa.Column("valid_from", _utc_datetime()),
        sa.Column("valid_to", _utc_datetime()),
        sa.Column("mapping_status", sa.String(24), nullable=False),
        sa.Column("source", sa.String(120), nullable=False),
        sa.Column("retrieved_at", _utc_datetime()),
        sa.PrimaryKeyConstraint("id", name="pk_provider_symbol_mappings"),
        sa.CheckConstraint(
            "provider_type IN ('BROKER','MARKET_DATA','FUNDAMENTAL','EVENT')",
            name="ck_provider_symbol_mappings_provider_type",
        ),
    )
    op.create_table(
        "strategy_assignments",
        _id("id"),
        _fk("security_id", "securities.id"),
        _fk("strategy_definition_id", "strategy_definitions.id"),
        _fk("portfolio_id", "portfolios.id", nullable=True),
        sa.Column("parameters_json", sa.Text(), nullable=False),
        sa.Column("parameters_hash", sa.String(128), nullable=False),
        sa.Column("effective_from", _utc_datetime(), nullable=False),
        sa.Column("effective_to", _utc_datetime()),
        sa.Column("created_at", _utc_datetime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_strategy_assignments"),
    )
    op.create_table(
        "ledger_accounts",
        _id("id"),
        _fk("portfolio_id", "portfolios.id"),
        _fk("broker_account_id", "broker_accounts.id", nullable=True),
        _fk("security_id", "securities.id", nullable=True),
        sa.Column("account_code", sa.String(64), nullable=False),
        sa.Column("account_type", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(3)),
        sa.Column("normal_balance", sa.String(8), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", _utc_datetime(), nullable=False),
        sa.Column("updated_at", _utc_datetime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_ledger_accounts"),
        sa.CheckConstraint(
            "normal_balance IN ('DEBIT','CREDIT')", name="ck_ledger_accounts_normal_balance"
        ),
    )
    op.create_table(
        "ledger_transactions",
        _id("id"),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        _fk("portfolio_id", "portfolios.id"),
        sa.Column("transaction_type", sa.String(32), nullable=False),
        sa.Column("effective_at", _utc_datetime(), nullable=False),
        sa.Column("recorded_at", _utc_datetime(), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(120), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        _fk("reverses_transaction_id", "ledger_transactions.id", nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_ledger_transactions"),
        sa.UniqueConstraint("sequence_no", name="sequence"),
        sa.UniqueConstraint("portfolio_id", "idempotency_key", name="idempotency"),
    )
    op.create_table(
        "ledger_entries",
        _id("id"),
        _fk("ledger_transaction_id", "ledger_transactions.id"),
        _fk("ledger_account_id", "ledger_accounts.id"),
        sa.Column("entry_no", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("amount", _decimal(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("base_fx_rate", _decimal(), nullable=False),
        sa.Column("base_amount", _decimal(), nullable=False),
        sa.Column("quantity", _decimal()),
        sa.Column("unit_price", _decimal()),
        _fk("security_id", "securities.id", nullable=True),
        sa.Column("effective_at", _utc_datetime(), nullable=False),
        sa.Column("created_at", _utc_datetime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_ledger_entries"),
        sa.UniqueConstraint("ledger_transaction_id", "entry_no", name="transaction_entry"),
        sa.CheckConstraint("direction IN ('DEBIT','CREDIT')", name="ck_ledger_entries_direction"),
        sa.CheckConstraint("entry_no > 0", name="ck_ledger_entries_entry_no_positive"),
        sa.CheckConstraint("length(currency) = 3", name="ck_ledger_entries_currency_length"),
        sa.CheckConstraint(
            "length(base_currency) = 3", name="ck_ledger_entries_base_currency_length"
        ),
    )
    op.create_table(
        "portfolio_snapshots",
        _id("id"),
        _fk("portfolio_id", "portfolios.id"),
        sa.Column("valuation_at", _utc_datetime(), nullable=False),
        sa.Column("valuation_kind", sa.String(24), nullable=False),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("cash_value", _decimal(), nullable=False),
        sa.Column("market_value", _decimal(), nullable=False),
        sa.Column("receivables", _decimal(), nullable=False),
        sa.Column("payables", _decimal(), nullable=False),
        sa.Column("total_equity", _decimal(), nullable=False),
        sa.Column("units_outstanding", _decimal(), nullable=False),
        sa.Column("nav_per_unit", _decimal(), nullable=False),
        sa.Column("cost_basis", _decimal(), nullable=False),
        sa.Column("realized_pnl", _decimal(), nullable=False),
        sa.Column("unrealized_pnl", _decimal(), nullable=False),
        sa.Column("fees", _decimal(), nullable=False),
        sa.Column("taxes", _decimal(), nullable=False),
        sa.Column("equity_pnl", _decimal(), nullable=False),
        sa.Column("fx_pnl", _decimal(), nullable=False),
        sa.Column("cash_ratio", _decimal(), nullable=False),
        sa.Column("invested_ratio", _decimal(), nullable=False),
        sa.Column("price_manifest_hash", sa.String(128)),
        sa.Column("fx_manifest_hash", sa.String(128)),
        sa.Column("ledger_sequence", sa.Integer(), nullable=False),
        sa.Column("is_official", sa.Boolean(), nullable=False),
        sa.Column("quality_status", sa.String(24), nullable=False),
        sa.Column("missing_data_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_snapshots"),
        sa.UniqueConstraint(
            "portfolio_id",
            "valuation_at",
            "valuation_kind",
            "is_official",
            name="official_point",
        ),
        sa.CheckConstraint(
            "quality_status IN ('COMPLETE','PARTIAL','INVALID')",
            name="ck_portfolio_snapshots_quality_status",
        ),
    )
    op.create_table(
        "cash_flows",
        _id("id"),
        _fk("portfolio_id", "portfolios.id"),
        _fk("broker_account_id", "broker_accounts.id"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("flow_type", sa.String(32), nullable=False),
        sa.Column("amount", _decimal(), nullable=False),
        sa.Column("effective_at", _utc_datetime(), nullable=False),
        sa.Column("requested_at", _utc_datetime(), nullable=False),
        sa.Column("posted_at", _utc_datetime(), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("base_fx_rate", _decimal(), nullable=False),
        sa.Column("base_amount", _decimal(), nullable=False),
        sa.Column("pre_flow_nav", _decimal(), nullable=False),
        sa.Column("units_issued", _decimal(), nullable=False),
        sa.Column("units_redeemed", _decimal(), nullable=False),
        _fk("pre_flow_snapshot_id", "portfolio_snapshots.id", nullable=True),
        _fk("ledger_transaction_id", "ledger_transactions.id"),
        _fk("reverses_cash_flow_id", "cash_flows.id", nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_cash_flows"),
        sa.UniqueConstraint("portfolio_id", "idempotency_key", name="idempotency"),
        sa.UniqueConstraint("ledger_transaction_id", name="uq_cash_flows_ledger_transaction_id"),
    )
    op.create_table(
        "unit_transactions",
        _id("id"),
        _fk("portfolio_id", "portfolios.id"),
        _fk("cash_flow_id", "cash_flows.id"),
        sa.Column("unit_event_type", sa.String(24), nullable=False),
        sa.Column("effective_at", _utc_datetime(), nullable=False),
        sa.Column("nav_per_unit", _decimal(), nullable=False),
        sa.Column("unit_quantity", _decimal(), nullable=False),
        sa.Column("base_amount", _decimal(), nullable=False),
        _fk("reverses_unit_transaction_id", "unit_transactions.id", nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_unit_transactions"),
        sa.UniqueConstraint("cash_flow_id", name="uq_unit_transactions_cash_flow_id"),
    )
    op.create_table(
        "cash_balances",
        _id("id"),
        _fk("broker_account_id", "broker_accounts.id"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("settled_amount", _decimal(), nullable=False),
        sa.Column("unsettled_receivable", _decimal(), nullable=False),
        sa.Column("unsettled_payable", _decimal(), nullable=False),
        sa.Column("reserved_amount", _decimal(), nullable=False),
        sa.Column("reported_buying_power", _decimal()),
        sa.Column("reported_at", _utc_datetime()),
        sa.Column("as_of_ledger_sequence", sa.Integer(), nullable=False),
        sa.Column("updated_at", _utc_datetime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_cash_balances"),
        sa.UniqueConstraint("broker_account_id", "currency", name="account_currency"),
    )

    _create_indexes(INDEXES)

    if op.get_context().dialect.name == "sqlite":
        for table in IMMUTABLE_TABLES:
            op.execute(
                sa.text(
                    f"CREATE TRIGGER {table}_immutable_update "
                    f"BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT, "
                    f"'{table} is immutable'); END"
                )
            )
            op.execute(
                sa.text(
                    f"CREATE TRIGGER {table}_immutable_delete "
                    f"BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT, "
                    f"'{table} is immutable'); END"
                )
            )

        user_mapping_guard = (
            "EXISTS (SELECT 1 FROM securities WHERE id = NEW.security_id "
            "AND record_source = 'USER_SUPPLIED')"
        )
        op.execute(
            sa.text(
                "CREATE TRIGGER provider_symbol_mappings_user_guard_insert "
                "BEFORE INSERT ON provider_symbol_mappings WHEN "
                f"{user_mapping_guard} BEGIN SELECT RAISE(ABORT, "
                "'user-supplied securities cannot have provider mappings'); END"
            )
        )
        op.execute(
            sa.text(
                "CREATE TRIGGER provider_symbol_mappings_user_guard_update "
                "BEFORE UPDATE ON provider_symbol_mappings WHEN "
                f"{user_mapping_guard} BEGIN SELECT RAISE(ABORT, "
                "'user-supplied securities cannot have provider mappings'); END"
            )
        )


def downgrade() -> None:
    if op.get_context().dialect.name == "sqlite":
        op.execute(sa.text("DROP TRIGGER IF EXISTS provider_symbol_mappings_user_guard_update"))
        op.execute(sa.text("DROP TRIGGER IF EXISTS provider_symbol_mappings_user_guard_insert"))
        for table in reversed(IMMUTABLE_TABLES):
            op.execute(sa.text(f"DROP TRIGGER IF EXISTS {table}_immutable_delete"))
            op.execute(sa.text(f"DROP TRIGGER IF EXISTS {table}_immutable_update"))
    for name, table, _columns, _unique, _predicate in reversed(INDEXES):
        op.drop_index(name, table_name=table)
    for table in (
        "cash_balances",
        "unit_transactions",
        "cash_flows",
        "portfolio_snapshots",
        "ledger_entries",
        "ledger_transactions",
        "ledger_accounts",
        "strategy_assignments",
        "provider_symbol_mappings",
        "watchlist_items",
        "watchlists",
        "portfolio_accounts",
        "broker_accounts",
        "settings",
        "portfolios",
        "broker_profiles",
        "strategy_definitions",
        "securities",
    ):
        op.drop_table(table)
