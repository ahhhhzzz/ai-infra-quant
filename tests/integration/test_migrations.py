from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Column, Engine, String, Table, inspect

from ai_infra_quant.database.base import Base
from ai_infra_quant.database.session import create_database_engine

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


def _alembic_config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.cmd_opts = Namespace(x=[f"database_url={database_url}"])
    return config


def test_fresh_migration_is_at_head_and_has_phase_one_tables(migrated_engine: Engine) -> None:
    with migrated_engine.connect() as connection:
        assert MigrationContext.configure(connection).get_current_revision() == (
            "0001_phase1_foundation"
        )
    tables = set(inspect(migrated_engine).get_table_names())
    assert tables == PHASE_ONE_TABLES


def test_migration_decimal_columns_are_declared_text(migrated_engine: Engine) -> None:
    with migrated_engine.connect() as connection:
        columns = connection.exec_driver_sql("PRAGMA table_info(portfolio_snapshots)").all()
    declared = {column[1]: column[2].upper() for column in columns}
    assert declared["total_equity"] == "TEXT"
    assert declared["nav_per_unit"] == "TEXT"
    assert declared["unrealized_pnl"] == "TEXT"


def test_downgrade_upgrade_cycle(database_url: str) -> None:
    config = _alembic_config(database_url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    assert Path(database_url.removeprefix("sqlite:///")).exists()


def test_versioned_migrations_do_not_depend_on_orm_metadata() -> None:
    versions = Path("src/ai_infra_quant/database/migrations/versions")
    forbidden = ("Base.metadata", ".create_all(", ".drop_all(")
    for migration in versions.glob("*.py"):
        source = migration.read_text(encoding="utf-8")
        assert not any(token in source for token in forbidden), migration


def test_revision_0001_ignores_later_orm_tables(tmp_path: Path) -> None:
    future = Table(
        "future_phase_table",
        Base.metadata,
        Column("id", String(36), primary_key=True),
    )
    database_url = f"sqlite:///{(tmp_path / 'isolated.db').resolve().as_posix()}"
    config = _alembic_config(database_url)
    try:
        command.upgrade(config, "head")
        engine = create_database_engine(database_url)
        try:
            assert set(inspect(engine).get_table_names()) == PHASE_ONE_TABLES
        finally:
            engine.dispose()
    finally:
        Base.metadata.remove(future)
