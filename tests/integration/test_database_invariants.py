from __future__ import annotations

import pytest
from sqlalchemy import Engine, inspect
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.config import Settings
from ai_infra_quant.database.seed import bootstrap_phase_one


def _assert_rejected(engine: Engine, statement: str, parameters: tuple[object, ...] = ()) -> None:
    with engine.begin() as connection, pytest.raises(DatabaseError):
        connection.exec_driver_sql(statement, parameters)


def test_active_portfolio_membership_is_unique(
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    settings: Settings,
) -> None:
    bootstrap_phase_one(session_factory, settings)
    _assert_rejected(
        migrated_engine,
        """
        INSERT INTO portfolio_accounts
            (id, portfolio_id, broker_account_id, effective_from, effective_to, is_primary)
        SELECT '00000000-0000-0000-0000-000000000201', portfolio_id, broker_account_id,
               effective_from, NULL, is_primary
        FROM portfolio_accounts LIMIT 1
        """,
    )


def test_active_provider_mapping_forward_and_reverse_keys_are_unique(
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    settings: Settings,
) -> None:
    seed = bootstrap_phase_one(session_factory, settings)
    with migrated_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            INSERT INTO provider_symbol_mappings
                (id, security_id, provider_type, provider_name, provider_symbol,
                 valid_from, valid_to, mapping_status, source, retrieved_at)
            VALUES (?, ?, 'MARKET_DATA', 'test-provider', 'TEST.SYMBOL',
                    NULL, NULL, 'UNVERIFIED', 'TEST_SYNTHETIC', NULL)
            """,
            ("00000000-0000-0000-0000-000000000202", seed.security_ids[0]),
        )
    _assert_rejected(
        migrated_engine,
        """
        INSERT INTO provider_symbol_mappings
            (id, security_id, provider_type, provider_name, provider_symbol,
             valid_from, valid_to, mapping_status, source, retrieved_at)
        VALUES (?, ?, 'MARKET_DATA', 'test-provider', 'OTHER.SYMBOL',
                NULL, NULL, 'UNVERIFIED', 'TEST_SYNTHETIC', NULL)
        """,
        ("00000000-0000-0000-0000-000000000203", seed.security_ids[0]),
    )
    _assert_rejected(
        migrated_engine,
        """
        INSERT INTO provider_symbol_mappings
            (id, security_id, provider_type, provider_name, provider_symbol,
             valid_from, valid_to, mapping_status, source, retrieved_at)
        VALUES (?, ?, 'MARKET_DATA', 'test-provider', 'TEST.SYMBOL',
                NULL, NULL, 'UNVERIFIED', 'TEST_SYNTHETIC', NULL)
        """,
        ("00000000-0000-0000-0000-000000000204", seed.security_ids[1]),
    )


def test_active_strategy_assignment_scopes_are_unique(
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    settings: Settings,
) -> None:
    seed = bootstrap_phase_one(session_factory, settings)
    with migrated_engine.connect() as connection:
        strategy_id = connection.exec_driver_sql("SELECT id FROM strategy_definitions").scalar_one()
    with migrated_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            INSERT INTO strategy_assignments
                (id, security_id, strategy_definition_id, portfolio_id, parameters_json,
                 parameters_hash, effective_from, effective_to, created_at)
            VALUES (?, ?, ?, NULL, '{}', 'hash-1', ?, NULL, ?)
            """,
            (
                "00000000-0000-0000-0000-000000000205",
                seed.security_ids[0],
                strategy_id,
                "2026-08-31T00:00:00.000000Z",
                "2026-08-31T00:00:00.000000Z",
            ),
        )
        connection.exec_driver_sql(
            """
            INSERT INTO strategy_assignments
                (id, security_id, strategy_definition_id, portfolio_id, parameters_json,
                 parameters_hash, effective_from, effective_to, created_at)
            VALUES (?, ?, ?, ?, '{}', 'hash-2', ?, NULL, ?)
            """,
            (
                "00000000-0000-0000-0000-000000000206",
                seed.security_ids[1],
                strategy_id,
                seed.portfolio_id,
                "2026-08-31T00:00:00.000000Z",
                "2026-08-31T00:00:00.000000Z",
            ),
        )
    _assert_rejected(
        migrated_engine,
        """
        INSERT INTO strategy_assignments
            (id, security_id, strategy_definition_id, portfolio_id, parameters_json,
             parameters_hash, effective_from, effective_to, created_at)
        VALUES (?, ?, ?, NULL, '{}', 'hash-3', ?, NULL, ?)
        """,
        (
            "00000000-0000-0000-0000-000000000207",
            seed.security_ids[0],
            strategy_id,
            "2026-08-31T00:00:00.000000Z",
            "2026-08-31T00:00:00.000000Z",
        ),
    )
    _assert_rejected(
        migrated_engine,
        """
        INSERT INTO strategy_assignments
            (id, security_id, strategy_definition_id, portfolio_id, parameters_json,
             parameters_hash, effective_from, effective_to, created_at)
        VALUES (?, ?, ?, ?, '{}', 'hash-4', ?, NULL, ?)
        """,
        (
            "00000000-0000-0000-0000-000000000208",
            seed.security_ids[1],
            strategy_id,
            seed.portfolio_id,
            "2026-08-31T00:00:00.000000Z",
            "2026-08-31T00:00:00.000000Z",
        ),
    )


def test_nullable_logical_ledger_and_setting_keys_are_unique(
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    settings: Settings,
) -> None:
    bootstrap_phase_one(session_factory, settings)
    _assert_rejected(
        migrated_engine,
        """
        INSERT INTO ledger_accounts
            (id, portfolio_id, broker_account_id, security_id, account_code, account_type,
             currency, normal_balance, active, created_at, updated_at)
        SELECT '00000000-0000-0000-0000-000000000209', portfolio_id, broker_account_id,
               security_id, account_code, account_type, currency, normal_balance, active,
               created_at, updated_at
        FROM ledger_accounts
        WHERE broker_account_id IS NULL AND security_id IS NULL AND currency IS NOT NULL
        LIMIT 1
        """,
    )
    _assert_rejected(
        migrated_engine,
        """
        INSERT INTO settings
            (id, scope_type, scope_id, key, value_json, value_type, schema_version,
             is_secret, updated_at, version)
        SELECT '00000000-0000-0000-0000-000000000210', scope_type, NULL, key,
               value_json, value_type, schema_version, is_secret, updated_at, version
        FROM settings WHERE scope_id IS NULL AND key = 'phase' LIMIT 1
        """,
    )


def test_cash_flow_pre_snapshot_is_a_restricting_foreign_key(
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    settings: Settings,
) -> None:
    bootstrap_phase_one(session_factory, settings)
    foreign_keys = inspect(migrated_engine).get_foreign_keys("cash_flows")
    assert any(
        foreign_key["constrained_columns"] == ["pre_flow_snapshot_id"]
        and foreign_key["referred_table"] == "portfolio_snapshots"
        and foreign_key["options"].get("ondelete") == "RESTRICT"
        for foreign_key in foreign_keys
    )
    with migrated_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            INSERT INTO ledger_transactions
                (id, sequence_no, portfolio_id, transaction_type, effective_at, recorded_at,
                 source_type, source_id, idempotency_key, reverses_transaction_id,
                 description, created_by)
            SELECT '00000000-0000-0000-0000-000000000211', 2, portfolio_id,
                   'TEST_SYNTHETIC', effective_at, recorded_at, 'TEST_SYNTHETIC',
                   'snapshot-fk', 'snapshot-fk', NULL, 'snapshot fk test', 'pytest'
            FROM ledger_transactions LIMIT 1
            """
        )
    _assert_rejected(
        migrated_engine,
        """
        INSERT INTO cash_flows
            (id, portfolio_id, broker_account_id, currency, flow_type, amount, effective_at,
             requested_at, posted_at, idempotency_key, status, base_fx_rate, base_amount,
             pre_flow_nav, units_issued, units_redeemed, pre_flow_snapshot_id,
             ledger_transaction_id, reverses_cash_flow_id)
        SELECT '00000000-0000-0000-0000-000000000212', portfolio_id, broker_account_id,
               currency, 'TEST_SYNTHETIC', amount, effective_at, requested_at, posted_at,
               'snapshot-fk', status, base_fx_rate, base_amount, pre_flow_nav,
               units_issued, units_redeemed,
               '00000000-0000-0000-0000-000000009999',
               '00000000-0000-0000-0000-000000000211', NULL
        FROM cash_flows LIMIT 1
        """,
    )


def test_snapshot_quality_check_is_enforced(
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    settings: Settings,
) -> None:
    bootstrap_phase_one(session_factory, settings)
    _assert_rejected(
        migrated_engine,
        """
        INSERT INTO portfolio_snapshots
        SELECT '00000000-0000-0000-0000-000000000213', portfolio_id,
               '2026-09-01T00:00:00.000000Z', valuation_kind, base_currency, cash_value,
               market_value, receivables, payables, total_equity, units_outstanding,
               nav_per_unit, cost_basis, realized_pnl, unrealized_pnl, fees, taxes,
               equity_pnl, fx_pnl, cash_ratio, invested_ratio, price_manifest_hash,
               fx_manifest_hash, ledger_sequence, is_official, 'AVAILABLE', missing_data_json
        FROM portfolio_snapshots LIMIT 1
        """,
    )
