from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from types import TracebackType
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.application.market_data_queries import MarketDataQueries
from ai_infra_quant.application.paqs_input_queries import PaqsInputQueries
from ai_infra_quant.backend.main import create_app
from ai_infra_quant.config import Settings
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import (
    PROVIDER_FUTU_QUOTE,
    DailyBar,
    MarketDataSecurity,
    MarketStatusSnapshot,
    MinuteBar,
    ProviderResult,
    ProviderStatus,
    QuoteSnapshot,
    TradingDay,
    TradingDayType,
    TradingSessionSegment,
)
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork

NOW = datetime(2026, 7, 10, 22, tzinfo=UTC)


class PaqsFakeProvider:
    def __enter__(self) -> PaqsFakeProvider:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def provider_status(self) -> ProviderResult[ProviderStatus]:
        raise NotImplementedError

    def get_latest_quote(self, security: MarketDataSecurity) -> ProviderResult[QuoteSnapshot]:
        raise NotImplementedError

    def get_market_status(
        self, security: MarketDataSecurity
    ) -> ProviderResult[MarketStatusSnapshot]:
        raise NotImplementedError

    def get_daily_bars(
        self, security: MarketDataSecurity, limit: int
    ) -> ProviderResult[tuple[DailyBar, ...]]:
        bars = tuple(
            DailyBar(
                security=security.display_symbol,
                session_date=date(2026, 7, 6) + timedelta(days=offset),
                provider_time=datetime(2026, 7, 6 + offset, tzinfo=UTC),
                open=Decimal("100") + offset,
                high=Decimal("102") + offset,
                low=Decimal("99") + offset,
                close=Decimal("101") + offset,
                volume=Decimal("1000"),
                is_completed=True,
                retrieved_at=NOW,
            )
            for offset in range(5)
        )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER_FUTU_QUOTE,
            retrieved_at=NOW,
            data=bars[-limit:],
        )

    def get_recent_minute_bars(
        self, security: MarketDataSecurity, lookback_days: int
    ) -> ProviderResult[tuple[MinuteBar, ...]]:
        local = datetime.combine(
            date(2026, 7, 10), time(9, 30), tzinfo=ZoneInfo(security.market_timezone)
        ).astimezone(UTC)
        bars = tuple(
            MinuteBar(
                security=security.display_symbol,
                interval_start=local + timedelta(minutes=offset),
                interval_end=local + timedelta(minutes=offset + 1),
                open=Decimal("104"),
                high=Decimal("106"),
                low=Decimal("103"),
                close=Decimal("105"),
                volume=Decimal("10"),
                is_completed=True,
                retrieved_at=NOW,
            )
            for offset in range(30)
        )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER_FUTU_QUOTE,
            retrieved_at=NOW,
            data=bars,
        )

    def get_trading_days(
        self, market: str, start_date: date, end_date: date
    ) -> ProviderResult[tuple[TradingDay, ...]]:
        days = tuple(
            TradingDay(
                market=market,
                market_date=date(2026, 7, 6) + timedelta(days=offset),
                market_timezone="America/New_York",
                day_type=TradingDayType.FULL,
                provider_day_type="WHOLE",
                session_segments=(TradingSessionSegment(time(9, 30), time(16, 0)),),
                provider=PROVIDER_FUTU_QUOTE,
                retrieved_at=NOW,
            )
            for offset in range(5)
        )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER_FUTU_QUOTE,
            retrieved_at=NOW,
            data=days,
        )


@pytest.fixture
def paqs_app(
    settings: Settings,
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
) -> FastAPI:
    application = create_app(settings, migrated_engine)

    def uow_factory() -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory)

    provider = PaqsFakeProvider()
    queries = MarketDataQueries(
        uow_factory,
        provider_name=PROVIDER_FUTU_QUOTE,
        provider_factory=lambda: provider,
        now=lambda: NOW,
    )
    application.state.container.market_data_queries = queries
    application.state.container.paqs_input_queries = PaqsInputQueries(
        queries,
        provider_name=PROVIDER_FUTU_QUOTE,
        now=lambda: NOW,
    )
    return application


@pytest.fixture
def paqs_client(paqs_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(paqs_app) as test_client:
        yield test_client


def _avgo_id(client: TestClient) -> str:
    items = client.get("/api/v1/watchlist").json()["items"]
    return str(
        next(
            item["security"]["id"]
            for item in items
            if item["security"]["display_symbol"] == "US.AVGO"
        )
    )


def test_input_status_exposes_only_foundation_diagnostics(
    paqs_client: TestClient,
) -> None:
    response = paqs_client.get(
        f"/api/v1/strategies/paqs/securities/{_avgo_id(paqs_client)}/input-status"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == PROVIDER_FUTU_QUOTE
    assert body["market_timezone"] == "America/New_York"
    assert body["d1_source_count"] == 5
    assert body["completed_w1_count"] == 1
    assert body["minute_source_count"] == 30
    assert body["completed_m30_count"] == 1
    assert body["adjustment_basis"] == "PROVIDER_QFQ_CURRENT"
    assert body["historical_replay_safe"] is False
    assert body["latest_completed_w1_at"] is not None
    assert body["latest_completed_d1_session"] == "2026-07-10"
    assert body["latest_completed_m30_at"] is not None
    forbidden_fields = {
        "advisory",
        "score",
        "regime",
        "setup",
        "target",
        "risk_reward",
    }
    assert forbidden_fields.isdisjoint(body)


def test_paqs_research_eligibility_does_not_require_tradability_verification(
    paqs_client: TestClient,
) -> None:
    security_id = _avgo_id(paqs_client)
    security = paqs_client.get(f"/api/v1/securities/{security_id}").json()
    assert security["tradability_status"] == "UNVERIFIED"
    response = paqs_client.get(f"/api/v1/strategies/paqs/securities/{security_id}/input-status")
    assert response.status_code == 200


def test_provider_none_input_status_is_truthfully_unavailable(client: TestClient) -> None:
    security_id = _avgo_id(client)
    response = client.get(f"/api/v1/strategies/paqs/securities/{security_id}/input-status")
    assert response.status_code == 200
    body = response.json()
    assert body["data_quality"] == "INVALID"
    assert body["adjustment_basis"] == "UNAVAILABLE"
    assert body["historical_replay_safe"] is False
    assert body["d1_source_count"] == body["minute_source_count"] == 0
    assert body["completed_w1_count"] == body["completed_m30_count"] == 0
    assert any("not configured" in warning for warning in body["warnings"])
