from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.config import Settings
from ai_infra_quant.database.models.accounting import (
    LedgerAccountModel,
    LedgerEntryModel,
    LedgerTransactionModel,
)
from ai_infra_quant.database.models.portfolio import PortfolioModel
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork
from ai_infra_quant.database.seed import bootstrap_phase_one, opening_at


def _valid_transaction(
    session_factory: sessionmaker[Session], settings: Settings
) -> tuple[LedgerTransactionModel, list[LedgerEntryModel]]:
    seed = bootstrap_phase_one(session_factory, settings)
    with session_factory() as session:
        account_ids = session.scalars(
            select(LedgerAccountModel.id).order_by(LedgerAccountModel.account_code)
        ).all()
    at = opening_at(settings)
    transaction = LedgerTransactionModel(
        id="00000000-0000-0000-0000-000000000301",
        sequence_no=2,
        portfolio_id=seed.portfolio_id,
        transaction_type="TEST_SYNTHETIC",
        effective_at=at,
        recorded_at=at,
        source_type="TEST_SYNTHETIC",
        source_id="ledger-validation",
        idempotency_key="ledger-validation",
        reverses_transaction_id=None,
        description="Ledger invariant test",
        created_by="pytest",
    )
    entries = [
        LedgerEntryModel(
            id=f"00000000-0000-0000-0000-00000000030{index + 1}",
            ledger_transaction_id=transaction.id,
            ledger_account_id=account_ids[index],
            entry_no=index + 1,
            direction=("DEBIT", "CREDIT")[index],
            amount=Decimal("10"),
            currency="HKD",
            base_currency="HKD",
            base_fx_rate=Decimal("1"),
            base_amount=Decimal("10"),
            quantity=None,
            unit_price=None,
            security_id=None,
            effective_at=at,
            created_at=at,
        )
        for index in range(2)
    ]
    return transaction, entries


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("too_few", "at least two"),
        ("wrong_transaction", "supplied transaction"),
        ("duplicate_id", "IDs must be unique"),
        ("duplicate_number", "numbers must be unique"),
        ("invalid_direction", "DEBIT or CREDIT"),
        ("negative_amount", "amount must be strictly positive"),
        ("negative_base_amount", "base amount must be strictly positive"),
        ("zero_fx", "FX rate must be strictly positive"),
        ("lowercase_currency", "currency must be canonical"),
        ("lowercase_base_currency", "base currency must be canonical"),
        ("wrong_base_currency", "match the portfolio"),
    ],
)
def test_unit_of_work_rejects_invalid_ledger_entries_before_writing(
    session_factory: sessionmaker[Session],
    settings: Settings,
    case: str,
    message: str,
) -> None:
    transaction, entries = _valid_transaction(session_factory, settings)
    if case == "too_few":
        entries = entries[:1]
    elif case == "wrong_transaction":
        entries[0].ledger_transaction_id = "00000000-0000-0000-0000-000000009999"
    elif case == "duplicate_id":
        entries[1].id = entries[0].id
    elif case == "duplicate_number":
        entries[1].entry_no = entries[0].entry_no
    elif case == "invalid_direction":
        entries[0].direction = "IGNORED"
    elif case == "negative_amount":
        entries[0].amount = Decimal("-10")
    elif case == "negative_base_amount":
        entries[0].base_amount = Decimal("-10")
    elif case == "zero_fx":
        entries[0].base_fx_rate = Decimal("0")
    elif case == "lowercase_currency":
        entries[0].currency = "hkd"
    elif case == "lowercase_base_currency":
        entries[0].base_currency = "hkd"
    elif case == "wrong_base_currency":
        entries[0].base_currency = "USD"

    with (
        SQLAlchemyUnitOfWork(session_factory) as uow,
        pytest.raises(ValueError, match=message),
    ):
        uow.add_balanced_transaction(transaction, entries)
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(LedgerTransactionModel)) == 1


def test_unit_of_work_rejects_cross_portfolio_ledger_account(
    session_factory: sessionmaker[Session], settings: Settings
) -> None:
    transaction, entries = _valid_transaction(session_factory, settings)
    at = opening_at(settings)
    other_portfolio_id = "00000000-0000-0000-0000-000000000304"
    other_account_id = "00000000-0000-0000-0000-000000000305"
    with session_factory() as session:
        session.add(
            PortfolioModel(
                id=other_portfolio_id,
                name="Other test portfolio",
                base_currency="HKD",
                inception_date=date(2026, 8, 31),
                valuation_timezone="Asia/Hong_Kong",
                daily_cutoff_policy=None,
                initial_nav=Decimal("100"),
                status="ACTIVE",
                created_at=at,
                updated_at=at,
                version=1,
            )
        )
        session.flush()
        session.add(
            LedgerAccountModel(
                id=other_account_id,
                portfolio_id=other_portfolio_id,
                broker_account_id=None,
                security_id=None,
                account_code="OTHER_CASH",
                account_type="CASH_ASSET",
                currency="HKD",
                normal_balance="DEBIT",
                active=True,
                created_at=at,
                updated_at=at,
            )
        )
        session.commit()
    entries[0].ledger_account_id = other_account_id
    with (
        SQLAlchemyUnitOfWork(session_factory) as uow,
        pytest.raises(ValueError, match="transaction portfolio"),
    ):
        uow.add_balanced_transaction(transaction, entries)
