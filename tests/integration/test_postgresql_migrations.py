from __future__ import annotations

import os
from argparse import Namespace
from datetime import datetime

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.config import Settings
from ai_infra_quant.database.models.security import WatchlistItemModel, WatchlistModel
from ai_infra_quant.database.seed import bootstrap_phase_one, opening_at

POSTGRESQL_TEST_URL_ENV = "PHASE1_POSTGRESQL_TEST_URL"
PHASE_ONE_TABLES = {
    "alembic_version",
    "broker_accounts",
    "broker_profiles",
    "cash_balances",
    "cash_flows",
    "ledger_accounts",
    "ledger_entries",
    "ledger_transactions",
    "portfolio_accounts",
    "portfolio_snapshots",
    "portfolios",
    "provider_symbol_mappings",
    "securities",
    "settings",
    "strategy_assignments",
    "strategy_definitions",
    "unit_transactions",
    "watchlist_items",
    "watchlists",
}
TASK007B_TABLES = {"paqs_e_runtime_artifacts", "paqs_e_analysis_runs", "paqs_e_decisions"}
PARTIAL_UNIQUE_INDEXES = {
    "uq_provider_mappings_active_security",
    "uq_provider_mappings_active_reverse",
    "uq_watchlists_default_portfolio",
    "uq_watchlist_items_active_membership",
    "uq_portfolio_accounts_active_broker_account",
    "uq_strategy_assignments_active_portfolio_security",
    "uq_strategy_assignments_active_global_security",
    "uq_settings_system_scope_key",
    "uq_settings_named_scope_key",
    "uq_ledger_accounts_none",
    "uq_ledger_accounts_broker",
    "uq_ledger_accounts_security",
    "uq_ledger_accounts_currency",
    "uq_ledger_accounts_broker_security",
    "uq_ledger_accounts_broker_currency",
    "uq_ledger_accounts_security_currency",
    "uq_ledger_accounts_all_dimensions",
}


def _postgresql_test_url() -> str:
    database_url = os.environ.get(POSTGRESQL_TEST_URL_ENV)
    if database_url is None:
        pytest.skip(f"{POSTGRESQL_TEST_URL_ENV} is not configured")
    if make_url(database_url).get_backend_name() != "postgresql":
        pytest.fail(f"{POSTGRESQL_TEST_URL_ENV} must be a PostgreSQL URL")
    pytest.importorskip("psycopg")
    return database_url


def _alembic_config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.cmd_opts = Namespace(x=[f"database_url={database_url}"])
    return config


def _prepare_empty_database(engine: Engine, config: Config) -> None:
    tables = set(inspect(engine).get_table_names())
    if tables:
        if "alembic_version" not in tables or not tables.issubset(
            PHASE_ONE_TABLES | TASK007B_TABLES
        ):
            pytest.fail("dedicated PostgreSQL test database contains unrelated tables")
        command.downgrade(config, "base")
        with engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE IF EXISTS alembic_version")
    assert not inspect(engine).get_table_names()


def _assert_duplicate_default_watchlist_rejected(
    session_factory: sessionmaker[Session], portfolio_id: str, created_at: datetime
) -> None:
    with session_factory() as session:
        session.add(
            WatchlistModel(
                id="00000000-0000-0000-0000-000000000201",
                portfolio_id=portfolio_id,
                name="Duplicate default",
                is_default=True,
                created_at=created_at,
                updated_at=created_at,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def _assert_duplicate_active_watchlist_item_rejected(
    session_factory: sessionmaker[Session],
    watchlist_id: str,
    security_id: str,
    added_at: datetime,
) -> None:
    with session_factory() as session:
        session.add(
            WatchlistItemModel(
                id="00000000-0000-0000-0000-000000000202",
                watchlist_id=watchlist_id,
                security_id=security_id,
                added_at=added_at,
                removed_at=None,
                display_order=99,
                note="Synthetic duplicate",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_postgresql_16_fresh_upgrade_downgrade_reupgrade_and_invariants() -> None:
    database_url = _postgresql_test_url()
    config = _alembic_config(database_url)
    engine = create_engine(database_url, future=True)
    try:
        _prepare_empty_database(engine, config)

        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert MigrationContext.configure(connection).get_current_revision() == (
                "0003_task007c1_narrative_ledger"
            )

        command.downgrade(config, "base")
        with engine.connect() as connection:
            assert MigrationContext.configure(connection).get_current_revision() is None
        assert set(inspect(engine).get_table_names()) == {"alembic_version"}
        command.upgrade(config, "head")

        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == PHASE_ONE_TABLES | TASK007B_TABLES | {
            "paqs_e_narrative_runs",
            "paqs_e_narrative_results",
        }
        rr_column = next(
            column
            for column in inspector.get_columns("paqs_e_decisions")
            if column["name"] == "rr_t1"
        )
        assert str(rr_column["type"]) == "NUMERIC(38, 18)"
        index_names = {
            index["name"]
            for table in PHASE_ONE_TABLES - {"alembic_version"}
            for index in inspector.get_indexes(table)
        }
        assert PARTIAL_UNIQUE_INDEXES.issubset(index_names)

        settings = Settings(database_url="sqlite:///:memory:")
        session_factory = sessionmaker(
            bind=engine,
            class_=Session,
            expire_on_commit=False,
            future=True,
        )
        seed_result = bootstrap_phase_one(session_factory, settings)
        created_at = opening_at(settings)
        _assert_duplicate_default_watchlist_rejected(
            session_factory, seed_result.portfolio_id, created_at
        )
        _assert_duplicate_active_watchlist_item_rejected(
            session_factory,
            seed_result.watchlist_id,
            seed_result.security_ids[0],
            created_at,
        )

        command.check(config)
    finally:
        engine.dispose()
