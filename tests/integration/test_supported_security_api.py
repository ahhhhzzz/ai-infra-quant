from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import TracebackType

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.application.market_data_queries import MarketDataQueries
from ai_infra_quant.application.supported_security_service import SupportedSecurityService
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
    TradingDay,
)
from ai_infra_quant.database.models.security import SecurityModel, WatchlistItemModel
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork

NOW = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
PROVIDER = "validated_quote_provider"


class SupportedFakeProvider:
    def __init__(self) -> None:
        self.quote_status = DataAvailabilityStatus.AVAILABLE
        self.quote_reason: str | None = None
        self.quote_security_override: str | None = None
        self.raise_quote: Exception | None = None
        self.on_quote: Callable[[MarketDataSecurity], None] | None = None
        self.seen: list[str] = []

    def __enter__(self) -> SupportedFakeProvider:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def provider_status(self) -> ProviderResult[ProviderStatus]:
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=ProviderStatus(True, "fake"),
        )

    def get_latest_quote(self, security: MarketDataSecurity) -> ProviderResult[QuoteSnapshot]:
        self.seen.append(security.display_symbol)
        if self.on_quote is not None:
            self.on_quote(security)
        if self.raise_quote is not None:
            raise self.raise_quote
        data = None
        if self.quote_status is DataAvailabilityStatus.AVAILABLE:
            data = QuoteSnapshot(
                security=self.quote_security_override or security.display_symbol,
                price=Decimal("100.25"),
                currency=security.currency,
                latest_quote_at=NOW,
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
                security.display_symbol,
                CanonicalMarketState.CLOSED,
                "CLOSED",
                NOW,
            ),
        )

    def get_daily_bars(
        self, security: MarketDataSecurity, limit: int
    ) -> ProviderResult[tuple[DailyBar, ...]]:
        bar = DailyBar(
            security.display_symbol,
            date(2026, 9, 1),
            datetime(2026, 9, 1, tzinfo=UTC),
            Decimal("99"),
            Decimal("102"),
            Decimal("98"),
            Decimal("101"),
            Decimal("1000"),
            True,
            NOW,
        )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=(bar,),
        )

    def get_recent_minute_bars(
        self, security: MarketDataSecurity, lookback_days: int
    ) -> ProviderResult[tuple[MinuteBar, ...]]:
        bar = MinuteBar(
            security.display_symbol,
            NOW - timedelta(minutes=2),
            NOW - timedelta(minutes=1),
            Decimal("100"),
            Decimal("101"),
            Decimal("99"),
            Decimal("100.5"),
            Decimal("25"),
            True,
            NOW,
        )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=(bar,),
        )

    def get_trading_days(
        self, market: str, start_date: date, end_date: date
    ) -> ProviderResult[tuple[TradingDay, ...]]:
        return ProviderResult(
            status=DataAvailabilityStatus.UNAVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            reason="not needed by this test",
        )


@pytest.fixture
def supported_provider() -> SupportedFakeProvider:
    return SupportedFakeProvider()


@pytest.fixture
def supported_app(
    settings: Settings,
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    supported_provider: SupportedFakeProvider,
) -> FastAPI:
    application = create_app(settings, migrated_engine)

    def uow_factory() -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory)

    def provider_factory() -> SupportedFakeProvider:
        return supported_provider

    application.state.container.supported_security_service = SupportedSecurityService(
        uow_factory,
        provider_name=PROVIDER,
        provider_factory=provider_factory,
    )
    application.state.container.market_data_queries = MarketDataQueries(
        uow_factory,
        provider_name=PROVIDER,
        provider_factory=provider_factory,
        now=lambda: NOW,
    )
    return application


@pytest.fixture
def supported_client(supported_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(supported_app) as test_client:
        yield test_client


def _counts(session_factory: sessionmaker[Session]) -> tuple[int, int]:
    with session_factory() as session:
        securities = session.scalar(select(func.count()).select_from(SecurityModel))
        memberships = session.scalar(
            select(func.count())
            .select_from(WatchlistItemModel)
            .where(WatchlistItemModel.removed_at.is_(None))
        )
    return int(securities or 0), int(memberships or 0)


@pytest.mark.parametrize(
    ("payload", "display_symbol", "currency"),
    [
        ({"market": "us", "symbol": "nvda"}, "US.NVDA", "USD"),
        ({"market": "hk", "symbol": "700"}, "HK.00700", "HKD"),
    ],
)
def test_supported_add_normalizes_and_is_idempotent(
    supported_client: TestClient,
    payload: dict[str, str],
    display_symbol: str,
    currency: str,
) -> None:
    first = supported_client.post("/api/v1/watchlist/supported-securities", json=payload)
    second = supported_client.post("/api/v1/watchlist/supported-securities", json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["created_security"] is True
    assert first.json()["created_watchlist_item"] is True
    assert second.json()["created_security"] is False
    assert second.json()["created_watchlist_item"] is False
    security = first.json()["item"]["security"]
    assert security["display_symbol"] == display_symbol
    assert security["currency"] == currency
    assert security["instrument_type"] == "EQUITY"
    assert first.json()["provider_validation"]["status"] == "AVAILABLE"
    detail = supported_client.get(f"/api/v1/securities/{security['id']}").json()
    assert detail["record_source"] == "USER_SUPPLIED"
    assert detail["verification_status"] == "USER_SUPPLIED_UNVERIFIED"
    assert detail["tradability_status"] == "UNVERIFIED"


@pytest.mark.parametrize(
    ("status", "expected_code", "expected_http"),
    [
        (DataAvailabilityStatus.UNAVAILABLE, "MARKET_DATA_PROVIDER_UNAVAILABLE", 503),
        (DataAvailabilityStatus.PROVIDER_ERROR, "MARKET_DATA_PROVIDER_ERROR", 502),
        (DataAvailabilityStatus.NOT_ENTITLED, "MARKET_DATA_NOT_ENTITLED", 403),
        (DataAvailabilityStatus.INVALID, "SYMBOL_VALIDATION_FAILED", 422),
    ],
)
def test_provider_failure_never_mutates_local_state(
    supported_client: TestClient,
    session_factory: sessionmaker[Session],
    supported_provider: SupportedFakeProvider,
    status: DataAvailabilityStatus,
    expected_code: str,
    expected_http: int,
) -> None:
    before = _counts(session_factory)
    supported_provider.quote_status = status
    supported_provider.quote_reason = "provider validation failure"
    response = supported_client.post(
        "/api/v1/watchlist/supported-securities",
        json={"market": "US", "symbol": "NVDA"},
    )
    assert response.status_code == expected_http
    assert response.json()["code"] == expected_code
    assert response.json()["provider_validation_status"] == status.value
    assert _counts(session_factory) == before


def test_provider_validation_and_exact_symbol_precede_mutation(
    supported_client: TestClient,
    session_factory: sessionmaker[Session],
    supported_provider: SupportedFakeProvider,
) -> None:
    before = _counts(session_factory)
    supported_provider.on_quote = lambda _security: _assert_counts(session_factory, before)
    supported_provider.quote_security_override = "US.WRONG"
    response = supported_client.post(
        "/api/v1/watchlist/supported-securities",
        json={"market": "US", "symbol": "NVDA"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "SYMBOL_VALIDATION_FAILED"
    assert _counts(session_factory) == before


def _assert_counts(session_factory: sessionmaker[Session], expected: tuple[int, int]) -> None:
    assert _counts(session_factory) == expected


def test_unsupported_market_and_currency_conflict_are_explicit(
    supported_client: TestClient,
) -> None:
    unsupported = supported_client.post(
        "/api/v1/watchlist/supported-securities",
        json={"market": "JP", "symbol": "7203"},
    )
    assert unsupported.status_code == 422
    assert unsupported.json()["code"] == "INVALID_MARKET"

    legacy = supported_client.post(
        "/api/v1/securities",
        json={
            "market": "US",
            "symbol": "NVDA",
            "currency": "HKD",
            "instrument_type": "EQUITY",
        },
    )
    assert legacy.status_code == 201
    conflict = supported_client.post(
        "/api/v1/watchlist/supported-securities",
        json={"market": "US", "symbol": "NVDA"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "SECURITY_METADATA_CONFLICT"


def test_dynamic_security_immediately_uses_existing_market_data_queries(
    supported_client: TestClient,
    supported_provider: SupportedFakeProvider,
) -> None:
    added = supported_client.post(
        "/api/v1/watchlist/supported-securities",
        json={"market": "US", "symbol": "NVDA"},
    ).json()
    security_id = added["item"]["security"]["id"]
    for suffix in ("state", "daily-bars", "minute-bars"):
        response = supported_client.get(f"/api/v1/market-data/securities/{security_id}/{suffix}")
        assert response.status_code == 200
    assert "US.NVDA" in supported_provider.seen
    symbols = {
        item["security"]["display_symbol"]
        for item in supported_client.get("/api/v1/watchlist").json()["items"]
    }
    assert {"US.AVGO", "US.VRT", "HK.09698", "US.NVDA"} <= symbols


def test_provider_none_rejects_before_mutation(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    before = _counts(session_factory)
    response = client.post(
        "/api/v1/watchlist/supported-securities",
        json={"market": "US", "symbol": "NVDA"},
    )
    assert response.status_code == 503
    assert response.json()["code"] == "MARKET_DATA_PROVIDER_NOT_CONFIGURED"
    assert _counts(session_factory) == before
