from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.config import Settings
from ai_infra_quant.database.models.accounting import (
    CashBalanceModel,
    LedgerEntryModel,
    LedgerTransactionModel,
    PortfolioSnapshotModel,
)
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork
from ai_infra_quant.database.seed import bootstrap_phase_one, opening_at


def test_opening_facts_are_exact_and_balanced_in_python(
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    settings: Settings,
) -> None:
    bootstrap_phase_one(session_factory, settings)
    with session_factory() as session:
        snapshot = session.scalar(select(PortfolioSnapshotModel))
        balance = session.scalar(select(CashBalanceModel))
        entries = session.scalars(select(LedgerEntryModel)).all()
    assert snapshot is not None and balance is not None
    assert snapshot.total_equity == Decimal("20000.000000000000000000")
    assert snapshot.units_outstanding == Decimal("200.000000000000000000")
    assert snapshot.nav_per_unit == Decimal("100.000000000000000000")
    assert snapshot.market_value == Decimal("0.000000000000000000")
    assert snapshot.unrealized_pnl == Decimal("0.000000000000000000")
    assert balance.settled_amount == Decimal("20000.000000000000000000")
    debits = sum(
        (entry.base_amount for entry in entries if entry.direction == "DEBIT"), Decimal("0")
    )
    credits = sum(
        (entry.base_amount for entry in entries if entry.direction == "CREDIT"), Decimal("0")
    )
    assert debits == credits == Decimal("20000.000000000000000000")


def test_unbalanced_transaction_is_rejected_before_any_write(
    session_factory: sessionmaker[Session], settings: Settings
) -> None:
    bootstrap_phase_one(session_factory, settings)
    with session_factory() as session:
        account_ids = session.scalars(
            select(LedgerEntryModel.ledger_account_id).order_by(LedgerEntryModel.entry_no)
        ).all()
        before = len(session.scalars(select(LedgerTransactionModel)).all())
    seed_result = bootstrap_phase_one(session_factory, settings)
    transaction = LedgerTransactionModel(
        id="00000000-0000-0000-0000-000000000101",
        sequence_no=2,
        portfolio_id=seed_result.portfolio_id,
        transaction_type="ADJUSTMENT",
        effective_at=opening_at(settings),
        recorded_at=opening_at(settings),
        source_type="TEST_SYNTHETIC",
        source_id="unbalanced",
        idempotency_key="synthetic-unbalanced",
        reverses_transaction_id=None,
        description="Synthetic imbalance test",
        created_by="pytest",
    )
    entries = [
        LedgerEntryModel(
            id=f"00000000-0000-0000-0000-00000000010{index}",
            ledger_transaction_id=transaction.id,
            ledger_account_id=account_ids[index - 1],
            entry_no=index,
            direction=direction,
            amount=amount,
            currency="HKD",
            base_currency="HKD",
            base_fx_rate=Decimal("1"),
            base_amount=amount,
            quantity=None,
            unit_price=None,
            security_id=None,
            effective_at=transaction.effective_at,
            created_at=transaction.recorded_at,
        )
        for index, direction, amount in (
            (1, "DEBIT", Decimal("10")),
            (2, "CREDIT", Decimal("9")),
        )
    ]
    with (
        SQLAlchemyUnitOfWork(session_factory) as uow,
        pytest.raises(ValueError, match="not balanced"),
    ):
        uow.add_balanced_transaction(transaction, entries)
    with session_factory() as session:
        after = len(session.scalars(select(LedgerTransactionModel)).all())
    assert after == before


@pytest.mark.parametrize(
    "table", ["ledger_transactions", "ledger_entries", "unit_transactions", "portfolio_snapshots"]
)
def test_append_only_triggers_reject_updates_and_deletes(
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    settings: Settings,
    table: str,
) -> None:
    bootstrap_phase_one(session_factory, settings)
    for statement in (f"UPDATE {table} SET id = id", f"DELETE FROM {table}"):
        with migrated_engine.connect() as connection, pytest.raises(DatabaseError):
            connection.exec_driver_sql(statement)
            connection.commit()
