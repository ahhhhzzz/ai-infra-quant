from typing import Any

from alembic import command
from sqlalchemy import inspect, text
from test_migrations import _alembic_config
from test_paqs_e_ledger import _record
from test_paqs_e_ledger import ledger as ledger_fixture
from test_paqs_e_narrative_ledger_api import record

from ai_infra_quant.database.repositories.paqs_e_narrative import SQLAlchemyNarrativeLedger
from ai_infra_quant.database.session import current_migration_revision

ledger = ledger_fixture


def test_0003_representative_ledger_watchlist_bytes_survive_0004(
    ledger: Any, session_factory: Any, migrated_engine: Any, database_url: str
) -> None:
    config = _alembic_config(database_url)
    command.downgrade(config, "0003_task007c1_narrative_ledger")
    from test_paqs_e_ledger import NOW, SECURITY_ID

    from ai_infra_quant.database.models.security import WatchlistItemModel, WatchlistModel

    with session_factory.begin() as session:
        session.add(
            WatchlistModel(
                id="00000000-0000-4000-8000-000000000011",
                name="synthetic",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.flush()
        session.add(
            WatchlistItemModel(
                id="00000000-0000-4000-8000-000000000012",
                watchlist_id="00000000-0000-4000-8000-000000000011",
                security_id=SECURITY_ID,
                added_at=NOW,
                display_order=0,
            )
        )
    legacy = _record(ledger)
    narrative_store = SQLAlchemyNarrativeLedger(session_factory)
    narrative = record(narrative_store)
    tables = set(inspect(migrated_engine).get_table_names()) - {"alembic_version"}

    def freeze() -> Any:
        with migrated_engine.connect() as connection:
            return {
                table: (
                    connection.execute(
                        text(
                            "SELECT type,name,sql FROM sqlite_master "
                            "WHERE tbl_name=:table ORDER BY type,name"
                        ),
                        {"table": table},
                    ).all(),
                    connection.execute(text(f'SELECT * FROM "{table}"')).all(),
                )
                for table in tables
            }

    before = freeze()
    assert before["watchlist_items"][1]
    assert before["paqs_e_narrative_results"][1]
    assert before["paqs_e_decisions"][1]
    command.upgrade(config, "head")
    assert current_migration_revision(migrated_engine) == "0004_task006b1_market_archive"
    assert freeze() == before
    assert ledger.get_decision(legacy.decision.id) == legacy.decision
    assert narrative_store.get_result(narrative.result.narrative_result_id) == narrative.result
    assert set(inspect(migrated_engine).get_table_names()) - tables - {"alembic_version"} == {
        "market_archive_captures",
        "market_archive_bar_versions",
        "market_archive_memberships",
    }
    command.downgrade(config, "0003_task007c1_narrative_ledger")
    assert freeze() == before
