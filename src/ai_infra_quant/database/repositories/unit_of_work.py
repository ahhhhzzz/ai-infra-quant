from __future__ import annotations

from decimal import Decimal
from types import TracebackType
from typing import Self

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.core.domain.money import parse_decimal
from ai_infra_quant.core.domain.security import normalize_currency
from ai_infra_quant.database.models.accounting import (
    LedgerAccountModel,
    LedgerEntryModel,
    LedgerTransactionModel,
)
from ai_infra_quant.database.models.portfolio import PortfolioModel
from ai_infra_quant.database.repositories.portfolio import SQLAlchemyPortfolioRepository
from ai_infra_quant.database.repositories.security import SQLAlchemySecurityRepository
from ai_infra_quant.database.repositories.watchlist import SQLAlchemyWatchlistRepository


class SQLAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self.session: Session
        self.securities: SQLAlchemySecurityRepository
        self.portfolios: SQLAlchemyPortfolioRepository
        self.watchlists: SQLAlchemyWatchlistRepository

    def __enter__(self) -> Self:
        self.session = self._session_factory()
        self.securities = SQLAlchemySecurityRepository(self.session)
        self.portfolios = SQLAlchemyPortfolioRepository(self.session)
        self.watchlists = SQLAlchemyWatchlistRepository(self.session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        self.session.close()

    def add_balanced_transaction(
        self, transaction: LedgerTransactionModel, entries: list[LedgerEntryModel]
    ) -> None:
        if len(entries) < 2:
            raise ValueError("a ledger transaction requires at least two entries")
        if len({entry.id for entry in entries}) != len(entries):
            raise ValueError("ledger entry IDs must be unique within a transaction")
        if len({entry.entry_no for entry in entries}) != len(entries):
            raise ValueError("ledger entry numbers must be unique within a transaction")
        if any(
            not isinstance(entry.entry_no, int)
            or isinstance(entry.entry_no, bool)
            or entry.entry_no <= 0
            for entry in entries
        ):
            raise ValueError("ledger entry numbers must be positive integers")

        portfolio = self.session.get(PortfolioModel, transaction.portfolio_id)
        if portfolio is None:
            raise ValueError("ledger transaction portfolio does not exist")
        portfolio_currency = normalize_currency(portfolio.base_currency)
        account_ids = {entry.ledger_account_id for entry in entries}
        accounts = self.session.scalars(
            select(LedgerAccountModel).where(LedgerAccountModel.id.in_(account_ids))
        ).all()
        if {account.id for account in accounts} != account_ids:
            raise ValueError("every ledger entry must reference an existing ledger account")
        if any(account.portfolio_id != transaction.portfolio_id for account in accounts):
            raise ValueError("ledger accounts must belong to the transaction portfolio")

        debit = Decimal(0)
        credit = Decimal(0)
        for entry in entries:
            if entry.ledger_transaction_id != transaction.id:
                raise ValueError("every ledger entry must belong to the supplied transaction")
            if entry.direction not in {"DEBIT", "CREDIT"}:
                raise ValueError("ledger entry direction must be DEBIT or CREDIT")
            if normalize_currency(entry.currency) != entry.currency:
                raise ValueError("ledger entry currency must be canonical uppercase ISO-4217")
            if normalize_currency(entry.base_currency) != entry.base_currency:
                raise ValueError("ledger base currency must be canonical uppercase ISO-4217")
            if entry.base_currency != portfolio_currency:
                raise ValueError("ledger base currency must match the portfolio base currency")
            if parse_decimal(entry.amount) <= 0:
                raise ValueError("ledger entry amount must be strictly positive")
            if parse_decimal(entry.base_amount) <= 0:
                raise ValueError("ledger entry base amount must be strictly positive")
            if parse_decimal(entry.base_fx_rate) <= 0:
                raise ValueError("ledger entry base FX rate must be strictly positive")
            if entry.direction == "DEBIT":
                debit += parse_decimal(entry.base_amount)
            else:
                credit += parse_decimal(entry.base_amount)
        if debit != credit:
            raise ValueError("ledger transaction is not balanced in base currency")
        if debit <= 0:
            raise ValueError("balanced ledger transaction must have a positive total")
        self.session.add(transaction)
        self.session.flush()
        self.session.add_all(entries)
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
