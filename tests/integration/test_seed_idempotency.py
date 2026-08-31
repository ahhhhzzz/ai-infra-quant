from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.application.watchlist_service import WatchlistService
from ai_infra_quant.config import Settings
from ai_infra_quant.database.models.accounting import LedgerTransactionModel
from ai_infra_quant.database.models.portfolio import PortfolioModel
from ai_infra_quant.database.models.security import SecurityModel, WatchlistItemModel
from ai_infra_quant.database.models.settings import SettingModel
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork
from ai_infra_quant.database.seed import (
    SeedConfigurationMismatch,
    bootstrap_phase_one,
    opening_at,
    seed_configuration_fingerprint,
)


def test_seed_is_idempotent_and_preserves_watchlist_removal(
    session_factory: sessionmaker[Session], settings: Settings
) -> None:
    first = bootstrap_phase_one(session_factory, settings)
    service = WatchlistService(lambda: SQLAlchemyUnitOfWork(session_factory))
    service.remove(first.security_ids[0])
    second = bootstrap_phase_one(session_factory, settings)
    assert first == second
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(SecurityModel)) == 3
        assert session.scalar(select(func.count()).select_from(LedgerTransactionModel)) == 1
        active = session.scalar(
            select(func.count())
            .select_from(WatchlistItemModel)
            .where(WatchlistItemModel.removed_at.is_(None))
        )
        history = session.scalar(select(func.count()).select_from(WatchlistItemModel))
    assert active == 2
    assert history == 3


@pytest.mark.parametrize(
    "overrides",
    [
        {"initial_portfolio_name": "Renamed opening portfolio"},
        {"initial_capital": Decimal("30000"), "initial_units": Decimal("300")},
        {"initial_base_currency": "USD"},
        {"inception_date": date(2026, 9, 1)},
        {"valuation_timezone": "UTC"},
    ],
)
def test_seed_configuration_drift_fails_atomically(
    session_factory: sessionmaker[Session], settings: Settings, overrides: dict[str, object]
) -> None:
    first = bootstrap_phase_one(session_factory, settings)
    with session_factory() as session:
        before = (
            session.scalar(select(func.count()).select_from(PortfolioModel)),
            session.scalar(select(func.count()).select_from(SecurityModel)),
            session.scalar(select(func.count()).select_from(LedgerTransactionModel)),
            session.scalar(select(func.count()).select_from(SettingModel)),
        )
    changed = Settings.model_validate({**settings.model_dump(), **overrides})
    with pytest.raises(SeedConfigurationMismatch) as caught:
        bootstrap_phase_one(session_factory, changed)
    assert caught.value.code == "SEED_CONFIGURATION_MISMATCH"
    with session_factory() as session:
        after = (
            session.scalar(select(func.count()).select_from(PortfolioModel)),
            session.scalar(select(func.count()).select_from(SecurityModel)),
            session.scalar(select(func.count()).select_from(LedgerTransactionModel)),
            session.scalar(select(func.count()).select_from(SettingModel)),
        )
        portfolio_ids = session.scalars(select(PortfolioModel.id)).all()
    assert after == before
    assert portfolio_ids == [first.portfolio_id]


def test_seed_opening_instant_uses_local_midnight_and_fingerprint_is_scale_stable(
    settings: Settings,
) -> None:
    localized = Settings.model_validate(
        {
            **settings.model_dump(),
            "inception_date": date(2026, 8, 31),
            "valuation_timezone": "Asia/Hong_Kong",
        }
    )
    assert opening_at(localized) == datetime(2026, 8, 30, 16, 0, tzinfo=UTC)
    alternate_scale = Settings.model_validate(
        {
            **localized.model_dump(),
            "initial_capital": Decimal("20000.00"),
            "initial_units": Decimal("200.000"),
            "initial_nav": Decimal("100.0"),
        }
    )
    assert seed_configuration_fingerprint(localized) == seed_configuration_fingerprint(
        alternate_scale
    )
