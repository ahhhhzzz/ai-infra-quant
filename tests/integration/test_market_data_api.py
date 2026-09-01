from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import TracebackType
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.application.market_data_queries import MarketDataQueries
from ai_infra_quant.backend.main import create_app
from ai_infra_quant.config import Settings
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import (
    CanonicalMarketState,
    DailyBar,
    MarketDataSecurity,
    MarketStatusSnapshot,
    MinuteBar,
    ProviderResult,
    ProviderStatus,
    QuoteSnapshot,
)
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork
from ai_infra_quant.integrations.futu_quote.symbols import POC_SECURITIES

NOW = datetime(2026, 9, 1, 14, 35, 30, tzinfo=UTC)
PROVIDER = "test_quote_provider"


class FakeMarketDataProvider:
    def __init__(self) -> None:
        self.closed = False
        self.enter_count = 0
        self.daily_limit: int | None = None
        self.quote_status = DataAvailabilityStatus.AVAILABLE
        self.quote_reason: str | None = None
        self.quote_error = False

    def __enter__(self) -> FakeMarketDataProvider:
        self.enter_count += 1
        self.closed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.closed = True

    def provider_status(self) -> ProviderResult[ProviderStatus]:
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=ProviderStatus(quote_context_open=True, sdk_version="fake"),
        )

    def get_latest_quote(self, security: MarketDataSecurity) -> ProviderResult[QuoteSnapshot]:
        if self.quote_error:
            raise RuntimeError("provider quote call failed")
        data = None
        if self.quote_status is DataAvailabilityStatus.AVAILABLE:
            data = QuoteSnapshot(
                security=security.display_symbol,
                price=Decimal("123.4500"),
                currency=security.currency,
                latest_quote_at=NOW - timedelta(seconds=12),
                retrieved_at=NOW,
            )
        return ProviderResult(
            status=self.quote_status,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=data,
            reason=self.quote_reason,
        )

    def get_market_status(
        self, security: MarketDataSecurity
    ) -> ProviderResult[MarketStatusSnapshot]:
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=MarketStatusSnapshot(
                security=security.display_symbol,
                state=CanonicalMarketState.OPEN,
                provider_state="MORNING",
                retrieved_at=NOW,
            ),
        )

    def get_daily_bars(
        self, security: MarketDataSecurity, limit: int
    ) -> ProviderResult[tuple[DailyBar, ...]]:
        self.daily_limit = limit
        bars = tuple(
            DailyBar(
                security=security.display_symbol,
                session_date=session_date,
                provider_time=datetime.combine(session_date, datetime.min.time(), tzinfo=UTC),
                open=Decimal("100.10"),
                high=Decimal("104.40"),
                low=Decimal("99.90"),
                close=close,
                volume=Decimal("12345.000"),
                is_completed=True,
                retrieved_at=NOW,
            )
            for session_date, close in (
                (date(2026, 8, 29), Decimal("101.20")),
                (date(2026, 8, 31), Decimal("103.30")),
            )
        )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=bars,
        )

    def get_current_session_minute_bars(
        self, security: MarketDataSecurity
    ) -> ProviderResult[tuple[MinuteBar, ...]]:
        bars = tuple(
            MinuteBar(
                security=security.display_symbol,
                interval_start=NOW.replace(second=0, microsecond=0) - timedelta(minutes=offset),
                interval_end=NOW.replace(second=0, microsecond=0) - timedelta(minutes=offset - 1),
                open=Decimal("120.10"),
                high=Decimal("121.40"),
                low=Decimal("119.90"),
                close=Decimal("121.20"),
                volume=Decimal("345.000"),
                is_completed=True,
                retrieved_at=NOW,
            )
            for offset in (2, 1)
        )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=bars,
        )


@pytest.fixture
def fake_provider() -> FakeMarketDataProvider:
    return FakeMarketDataProvider()


@pytest.fixture
def market_app(
    settings: Settings,
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    fake_provider: FakeMarketDataProvider,
) -> FastAPI:
    application = create_app(settings, migrated_engine)

    def uow_factory() -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory)

    def provider_factory() -> FakeMarketDataProvider:
        return fake_provider

    application.state.container.market_data_queries = MarketDataQueries(
        uow_factory,
        provider_name=PROVIDER,
        provider_factory=provider_factory,
        supported_securities=POC_SECURITIES,
        now=lambda: NOW,
    )
    return application


@pytest.fixture
def market_client(market_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(market_app) as test_client:
        yield test_client


def _security_ids(client: TestClient) -> dict[str, str]:
    items = client.get("/api/v1/watchlist").json()["items"]
    return {item["security"]["display_symbol"]: item["security"]["id"] for item in items}


def test_state_route_uses_canonical_security_and_serializes_decimal_utc(
    market_client: TestClient,
    fake_provider: FakeMarketDataProvider,
) -> None:
    security_id = _security_ids(market_client)["US.AVGO"]
    response = market_client.get(f"/api/v1/market-data/securities/{security_id}/state")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "security_id": security_id,
        "market": "US",
        "symbol": "AVGO",
        "currency": "USD",
        "market_timezone": "America/New_York",
        "provider": PROVIDER,
        "latest_price": "123.4500",
        "latest_quote_at": "2026-09-01T14:35:18Z",
        "market_state": "OPEN",
        "provider_market_state": "MORNING",
        "retrieved_at": "2026-09-01T14:35:30Z",
        "provider_delay_seconds": None,
        "quote_status": "AVAILABLE",
        "market_status": "AVAILABLE",
        "reason": None,
    }
    assert "close" not in response.json()
    assert fake_provider.closed is True


def test_daily_and_minute_routes_return_completed_canonical_bars(
    market_client: TestClient,
    fake_provider: FakeMarketDataProvider,
) -> None:
    security_id = _security_ids(market_client)["HK.09698"]
    daily = market_client.get(f"/api/v1/market-data/securities/{security_id}/daily-bars?limit=1")
    minute = market_client.get(f"/api/v1/market-data/securities/{security_id}/minute-bars")

    assert daily.status_code == minute.status_code == 200
    assert daily.json()["status"] == minute.json()["status"] == "AVAILABLE"
    assert daily.json()["market_timezone"] == minute.json()["market_timezone"]
    assert daily.json()["market_timezone"] == "Asia/Hong_Kong"
    assert daily.json()["latest_completed_daily_session"] == "2026-08-31"
    assert len(daily.json()["bars"]) == 1
    assert daily.json()["bars"][0]["close"] == "103.30"
    assert daily.json()["bars"][0]["is_completed"] is True
    assert daily.json()["bars"][0]["provider_time"].endswith("Z")
    assert fake_provider.daily_limit == 1
    assert minute.json()["session_date"] == "2026-09-01"
    assert minute.json()["latest_completed_minute_bar_at"] == "2026-09-01T14:35:00Z"
    assert all(bar["is_completed"] is True for bar in minute.json()["bars"])
    assert all(isinstance(bar["open"], str) for bar in minute.json()["bars"])
    assert "FakeMarketDataProvider" not in response_text(daily, minute)


def response_text(*responses: object) -> str:
    return " ".join(str(getattr(response, "text", "")) for response in responses)


def test_provider_none_and_entitlement_partial_failure_are_structured(
    client: TestClient,
    market_client: TestClient,
    fake_provider: FakeMarketDataProvider,
) -> None:
    security_id = _security_ids(client)["US.VRT"]
    offline = client.get(f"/api/v1/market-data/securities/{security_id}/state")
    assert offline.status_code == 200
    assert offline.json()["quote_status"] == "UNAVAILABLE"
    assert offline.json()["market_status"] == "UNAVAILABLE"

    fake_provider.quote_status = DataAvailabilityStatus.NOT_ENTITLED
    fake_provider.quote_reason = "quote entitlement unavailable"
    security_id = _security_ids(market_client)["US.VRT"]
    partial = market_client.get(f"/api/v1/market-data/securities/{security_id}/state")
    assert partial.status_code == 200
    assert partial.json()["latest_price"] is None
    assert partial.json()["quote_status"] == "NOT_ENTITLED"
    assert partial.json()["market_status"] == "AVAILABLE"
    assert "entitlement" in partial.json()["reason"]

    fake_provider.quote_error = True
    failed_quote = market_client.get(f"/api/v1/market-data/securities/{security_id}/state")
    assert failed_quote.status_code == 200
    assert failed_quote.json()["quote_status"] == "PROVIDER_ERROR"
    assert failed_quote.json()["market_status"] == "AVAILABLE"
    assert failed_quote.json()["reason"] == "latest: provider quote call failed"


def test_provider_none_daily_and_minute_routes_are_structured(client: TestClient) -> None:
    security_id = _security_ids(client)["US.AVGO"]
    daily = client.get(f"/api/v1/market-data/securities/{security_id}/daily-bars")
    minute = client.get(f"/api/v1/market-data/securities/{security_id}/minute-bars")

    assert daily.status_code == minute.status_code == 200
    assert daily.json()["status"] == minute.json()["status"] == "UNAVAILABLE"
    assert daily.json()["bars"] == minute.json()["bars"] == []
    assert daily.json()["reason"] == "market data provider is not configured"
    assert minute.json()["reason"] == "market data provider is not configured"


def test_security_not_found_unsupported_and_limit_validation_are_stable(
    market_client: TestClient,
) -> None:
    missing = market_client.get(f"/api/v1/market-data/securities/{uuid4()}/state")
    assert missing.status_code == 404
    assert missing.json()["code"] == "SECURITY_NOT_FOUND"

    unsupported_id = market_client.post(
        "/api/v1/securities",
        json={
            "market": "US",
            "symbol": "NVDA",
            "currency": "USD",
            "instrument_type": "EQUITY",
        },
    ).json()["id"]
    unsupported = market_client.get(f"/api/v1/market-data/securities/{unsupported_id}/state")
    assert unsupported.status_code == 422
    assert unsupported.json()["code"] == "MARKET_DATA_SECURITY_NOT_SUPPORTED"

    security_id = _security_ids(market_client)["US.AVGO"]
    invalid_limit = market_client.get(
        f"/api/v1/market-data/securities/{security_id}/daily-bars?limit=261"
    )
    assert invalid_limit.status_code == 422
