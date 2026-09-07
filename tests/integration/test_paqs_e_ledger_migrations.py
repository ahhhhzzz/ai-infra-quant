from __future__ import annotations

from typing import Any

from alembic import command
from sqlalchemy import Engine, inspect, text
from test_migrations import PHASE_ONE_TABLES, _alembic_config

from ai_infra_quant.config import Settings
from ai_infra_quant.database.seed import bootstrap_phase_one
from ai_infra_quant.database.session import (
    create_database_engine,
    create_session_factory,
    current_migration_revision,
)

LEDGER_TABLES = {"paqs_e_runtime_artifacts", "paqs_e_analysis_runs", "paqs_e_decisions"}


def test_fresh_sqlite_head_has_only_task007b_objects(migrated_engine: Engine) -> None:
    assert current_migration_revision(migrated_engine) == "0002_task007b_paqs_e_ledger"
    assert set(inspect(migrated_engine).get_table_names()) == PHASE_ONE_TABLES | LEDGER_TABLES
    with migrated_engine.connect() as connection:
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            ).scalars()
        )
        declared = dict(
            (row[1], row[2])
            for row in connection.execute(text("PRAGMA table_info(paqs_e_decisions)"))
        )
    assert triggers >= {
        f"{table}_immutable_{operation}"
        for table in LEDGER_TABLES
        for operation in ("update", "delete")
    }
    assert "paqs_e_decisions_series_insert" in triggers
    assert declared["rr_t1"] == "TEXT"
    assert {
        index["name"]
        for table in LEDGER_TABLES
        for index in inspect(migrated_engine).get_indexes(table)
    } >= {
        "ix_paqs_e_runs_security_created",
        "ix_paqs_e_decisions_security_created",
    }


def _phase_one_shape(engine: Any) -> Any:
    with engine.connect() as connection:
        schema = connection.execute(
            text(
                "SELECT type, name, tbl_name, sql FROM sqlite_master "
                "WHERE name NOT LIKE 'paqs_e_%' AND name NOT LIKE 'ix_paqs_e_%' "
                "AND tbl_name NOT LIKE 'paqs_e_%' ORDER BY type, name"
            )
        ).all()
        data = {
            table: connection.execute(text(f"SELECT * FROM {table}")).all()
            for table in PHASE_ONE_TABLES - {"alembic_version"}
        }
    return schema, data


def test_existing_0001_upgrade_downgrade_preserves_all_phase_one_objects_and_data(
    database_url: str,
) -> None:
    config = _alembic_config(database_url)
    command.upgrade(config, "0001_phase1_foundation")
    engine = create_database_engine(database_url)
    try:
        bootstrap_phase_one(create_session_factory(engine), Settings(database_url=database_url))
        original = _phase_one_shape(engine)
        command.upgrade(config, "head")
        assert current_migration_revision(engine) == "0002_task007b_paqs_e_ledger"
        assert _phase_one_shape(engine) == original
        command.downgrade(config, "0001_phase1_foundation")
        assert current_migration_revision(engine) == "0001_phase1_foundation"
        assert set(inspect(engine).get_table_names()) == PHASE_ONE_TABLES
        assert _phase_one_shape(engine) == original
    finally:
        engine.dispose()
