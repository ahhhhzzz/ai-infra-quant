from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.config import Settings
from ai_infra_quant.database.models.accounting import (
    CashBalanceModel,
    CashFlowModel,
    LedgerAccountModel,
    LedgerEntryModel,
    LedgerTransactionModel,
    PortfolioSnapshotModel,
)
from ai_infra_quant.database.models.portfolio import BrokerAccountModel, PortfolioModel
from ai_infra_quant.database.models.security import SecurityModel
from ai_infra_quant.database.models.settings import SettingModel
from ai_infra_quant.database.seed import SeedConfigurationMismatch, bootstrap_phase_one, stable_id

COUNT_MODELS = (
    PortfolioModel,
    BrokerAccountModel,
    SecurityModel,
    LedgerAccountModel,
    LedgerTransactionModel,
    LedgerEntryModel,
    CashFlowModel,
    CashBalanceModel,
    PortfolioSnapshotModel,
    SettingModel,
)


def _opening_state(session_factory: sessionmaker[Session]) -> tuple[object, ...]:
    with session_factory() as session:
        counts = tuple(
            session.scalar(select(func.count()).select_from(model)) for model in COUNT_MODELS
        )
        return (
            counts,
            session.execute(
                select(
                    LedgerAccountModel.id,
                    LedgerAccountModel.account_code,
                    LedgerAccountModel.currency,
                ).order_by(LedgerAccountModel.id),
            ).all(),
            session.execute(
                select(
                    LedgerEntryModel.ledger_account_id,
                    LedgerEntryModel.currency,
                    LedgerEntryModel.base_currency,
                    LedgerEntryModel.amount,
                    LedgerEntryModel.base_amount,
                ).order_by(LedgerEntryModel.entry_no),
            ).all(),
            session.execute(
                select(
                    CashBalanceModel.id,
                    CashBalanceModel.currency,
                    CashBalanceModel.settled_amount,
                ),
            ).all(),
            session.execute(
                select(
                    PortfolioSnapshotModel.base_currency,
                    PortfolioSnapshotModel.total_equity,
                    PortfolioSnapshotModel.nav_per_unit,
                ),
            ).all(),
        )


def test_hkd_bootstrap_preserves_existing_currency_specific_ids_and_codes(
    session_factory: sessionmaker[Session], settings: Settings
) -> None:
    bootstrap_phase_one(session_factory, settings)

    with session_factory() as session:
        accounts = {
            account.account_code: account
            for account in session.scalars(select(LedgerAccountModel)).all()
        }
        balance = session.scalar(select(CashBalanceModel))

    assert accounts["CASH_HKD"].id == stable_id("ledger-account:cash-hkd")
    assert accounts["CONTRIBUTED_CAPITAL_HKD"].id == stable_id(
        "ledger-account:contributed-capital-hkd"
    )
    assert {account.currency for account in accounts.values()} == {"HKD"}
    assert balance is not None
    assert balance.id == stable_id("cash-balance:paper:HKD")
    assert balance.currency == "HKD"


def test_usd_bootstrap_is_consistent_idempotent_and_currency_drift_safe(
    session_factory: sessionmaker[Session], settings: Settings
) -> None:
    usd_settings = Settings.model_validate(
        {**settings.model_dump(), "initial_base_currency": " usd "}
    )
    first = bootstrap_phase_one(session_factory, usd_settings)
    second = bootstrap_phase_one(session_factory, usd_settings)
    assert first == second

    with session_factory() as session:
        accounts = {
            account.account_code: account
            for account in session.scalars(select(LedgerAccountModel)).all()
        }
        cash_balance = session.scalar(select(CashBalanceModel))
        portfolio = session.scalar(select(PortfolioModel))
        broker_account = session.scalar(select(BrokerAccountModel))
        cash_flow = session.scalar(select(CashFlowModel))
        snapshot = session.scalar(select(PortfolioSnapshotModel))
        ledger_entries = session.scalars(select(LedgerEntryModel)).all()

    assert set(accounts) == {"CASH_USD", "CONTRIBUTED_CAPITAL_USD"}
    assert all("HKD" not in account_code for account_code in accounts)
    assert accounts["CASH_USD"].id == stable_id("ledger-account:cash-usd")
    assert accounts["CASH_USD"].id != stable_id("ledger-account:cash-hkd")
    assert accounts["CONTRIBUTED_CAPITAL_USD"].id == stable_id(
        "ledger-account:contributed-capital-usd"
    )
    assert accounts["CONTRIBUTED_CAPITAL_USD"].id != stable_id(
        "ledger-account:contributed-capital-hkd"
    )
    assert {account.currency for account in accounts.values()} == {"USD"}
    assert cash_balance is not None
    assert cash_balance.id == stable_id("cash-balance:paper:USD")
    assert cash_balance.id != stable_id("cash-balance:paper:HKD")
    assert cash_balance.currency == "USD"
    assert portfolio is not None and portfolio.base_currency == "USD"
    assert broker_account is not None and broker_account.base_currency == "USD"
    assert cash_flow is not None and cash_flow.currency == "USD"
    assert snapshot is not None and snapshot.base_currency == "USD"
    assert {entry.currency for entry in ledger_entries} == {"USD"}
    assert {entry.base_currency for entry in ledger_entries} == {"USD"}

    before_drift = _opening_state(session_factory)
    changed = Settings.model_validate({**usd_settings.model_dump(), "initial_base_currency": "HKD"})
    with pytest.raises(SeedConfigurationMismatch, match="SEED_CONFIGURATION_MISMATCH"):
        bootstrap_phase_one(session_factory, changed)
    assert _opening_state(session_factory) == before_drift
