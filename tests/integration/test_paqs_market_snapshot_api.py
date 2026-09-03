from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from types import TracebackType
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.application.market_data_queries import MarketDataQueries
from ai_infra_quant.application.paqs_input_queries import PaqsInputQueries
from ai_infra_quant.application.paqs_market_snapshot_queries import PaqsMarketSnapshotQueries
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
    TradingDayType,
    TradingSessionSegment,
)
from ai_infra_quant.database.models.security import SecurityModel, WatchlistItemModel
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork

NOW = datetime(2026, 9, 3, 22, tzinfo=UTC)
PROVIDER = "synthetic_provider"
COMPLETE_WEEK = tuple(date(2026, 8, 3) + timedelta(days=index) for index in range(5))
PARTIAL_WEEK = tuple(date(2026, 8, 10) + timedelta(days=index) for index in range(3))
UNKNOWN_WEEK = tuple(date(2026, 8, 17) + timedelta(days=index) for index in range(5))


class SnapshotFakeProvider:
    def __init__(self) -> None:
        self.quote_status = DataAvailabilityStatus.AVAILABLE
        self.quote_delay: int | None = 12
        self.daily_status = DataAvailabilityStatus.AVAILABLE
        self.minute_status = DataAvailabilityStatus.AVAILABLE
        self.large_history = False
        self.events: list[str] = []

    def daily_dates(self) -> tuple[date, ...]:
        if self.large_history:
            return tuple(date(2023, 5, 1) + timedelta(days=index) for index in range(1200))
        return (*COMPLETE_WEEK, *PARTIAL_WEEK, *UNKNOWN_WEEK)

    def minute_dates(self) -> tuple[date, ...]:
        if self.large_history:
            return tuple(date(2026, 8, 19) + timedelta(days=index) for index in range(16))
        return (date(2026, 9, 3),)

    def __enter__(self) -> SnapshotFakeProvider:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc, traceback

    def provider_status(self) -> ProviderResult[ProviderStatus]:
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=ProviderStatus(quote_context_open=True, sdk_version="test"),
        )

    def get_latest_quote(self, security: MarketDataSecurity) -> ProviderResult[QuoteSnapshot]:
        self.events.append("quote")
        if self.quote_status is not DataAvailabilityStatus.AVAILABLE:
            return ProviderResult(
                status=self.quote_status,
                provider=PROVIDER,
                retrieved_at=NOW,
                reason="synthetic quote failure",
                provider_delay_seconds=self.quote_delay,
            )
        return ProviderResult(
            status=self.quote_status,
            provider=PROVIDER,
            retrieved_at=NOW,
            provider_delay_seconds=self.quote_delay,
            data=QuoteSnapshot(
                security=security.display_symbol,
                price=Decimal("123.4500"),
                currency=security.currency,
                latest_quote_at=NOW - timedelta(seconds=1),
                retrieved_at=NOW,
                is_equity=True,
            ),
        )

    def get_market_status(
        self, security: MarketDataSecurity
    ) -> ProviderResult[MarketStatusSnapshot]:
        self.events.append("market_state")
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=MarketStatusSnapshot(
                security=security.display_symbol,
                state=CanonicalMarketState.CLOSED,
                provider_state="CLOSED",
                retrieved_at=NOW,
            ),
        )

    def get_daily_bars(
        self, security: MarketDataSecurity, limit: int
    ) -> ProviderResult[tuple[DailyBar, ...]]:
        self.events.append("daily")
        if self.daily_status is not DataAvailabilityStatus.AVAILABLE:
            return ProviderResult(
                status=self.daily_status,
                provider=PROVIDER,
                retrieved_at=NOW,
                reason="synthetic D1 failure",
            )
        bars = tuple(
            DailyBar(
                security=security.display_symbol,
                session_date=session_date,
                provider_time=datetime.combine(session_date, time.min, tzinfo=UTC),
                open=Decimal("100"),
                high=Decimal("102"),
                low=Decimal("99"),
                close=Decimal("101"),
                volume=Decimal("1000"),
                is_completed=True,
                retrieved_at=NOW,
            )
            for session_date in self.daily_dates()
        )
        return ProviderResult(
            status=self.daily_status,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=bars[-limit:],
        )

    def get_recent_minute_bars(
        self, security: MarketDataSecurity, lookback_days: int
    ) -> ProviderResult[tuple[MinuteBar, ...]]:
        self.events.append("minute")
        del lookback_days
        if self.minute_status is not DataAvailabilityStatus.AVAILABLE:
            return ProviderResult(
                status=self.minute_status,
                provider=PROVIDER,
                retrieved_at=NOW,
                reason="synthetic minute failure",
            )
        minutes_per_day = 390 if self.large_history else 30
        bars = tuple(
            MinuteBar(
                security=security.display_symbol,
                interval_start=datetime.combine(
                    market_date,
                    time(9, 30),
                    tzinfo=ZoneInfo(security.market_timezone),
                ).astimezone(UTC)
                + timedelta(minutes=index),
                interval_end=datetime.combine(
                    market_date,
                    time(9, 30),
                    tzinfo=ZoneInfo(security.market_timezone),
                ).astimezone(UTC)
                + timedelta(minutes=index + 1),
                open=Decimal("120"),
                high=Decimal("122"),
                low=Decimal("119"),
                close=Decimal("121"),
                volume=Decimal("10"),
                is_completed=True,
                retrieved_at=NOW,
            )
            for market_date in self.minute_dates()
            for index in range(minutes_per_day)
        )
        return ProviderResult(
            status=self.minute_status,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=bars,
        )

    def get_trading_days(
        self, market: str, start_date: date, end_date: date
    ) -> ProviderResult[tuple[TradingDay, ...]]:
        self.events.append("calendar")
        timezone = "America/New_York" if market == "US" else "Asia/Hong_Kong"
        session_segments = (
            (TradingSessionSegment(time(9, 30), time(16, 0)),)
            if market == "US"
            else (
                TradingSessionSegment(time(9, 30), time(12, 0)),
                TradingSessionSegment(time(13, 0), time(16, 0)),
            )
        )
        calendar_daily_dates = (
            self.daily_dates()
            if self.large_history
            else (*COMPLETE_WEEK, *(date(2026, 8, 10) + timedelta(days=i) for i in range(5)))
        )
        available_dates = tuple(sorted(set(calendar_daily_dates) | set(self.minute_dates())))
        days = tuple(
            TradingDay(
                market=market,
                market_date=market_date,
                market_timezone=timezone,
                day_type=TradingDayType.FULL,
                provider_day_type="WHOLE",
                session_segments=session_segments,
                provider=PROVIDER,
                retrieved_at=NOW,
            )
            for market_date in available_dates
            if start_date <= market_date <= end_date
        )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            data=days,
        )


@pytest.fixture
def snapshot_provider() -> SnapshotFakeProvider:
    return SnapshotFakeProvider()


@pytest.fixture
def snapshot_app(
    settings: Settings,
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    snapshot_provider: SnapshotFakeProvider,
) -> FastAPI:
    application = create_app(settings, migrated_engine)

    def uow_factory() -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory)

    market_queries = MarketDataQueries(
        uow_factory,
        provider_name=PROVIDER,
        provider_factory=lambda: snapshot_provider,
        now=lambda: NOW,
    )
    input_queries = PaqsInputQueries(
        market_queries,
        provider_name=PROVIDER,
        now=lambda: NOW,
    )
    application.state.container.market_data_queries = market_queries
    application.state.container.paqs_input_queries = input_queries
    application.state.container.paqs_market_snapshot_queries = PaqsMarketSnapshotQueries(
        input_queries,
        market_queries,
        now=lambda: NOW,
    )
    return application


@pytest.fixture
def snapshot_client(snapshot_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(snapshot_app) as client:
        yield client


def _security_id(client: TestClient, display_symbol: str) -> str:
    items = client.get("/api/v1/watchlist").json()["items"]
    return str(
        next(
            item["security"]["id"]
            for item in items
            if item["security"]["display_symbol"] == display_symbol
        )
    )


def _keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in _keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _keys(item)}
    return set()


@pytest.mark.parametrize("display_symbol", ["US.AVGO", "HK.09698"])
def test_supported_us_and_hk_snapshot_is_factual_and_stable(
    snapshot_client: TestClient,
    display_symbol: str,
) -> None:
    security_id = _security_id(snapshot_client, display_symbol)
    first = snapshot_client.get(f"/api/v1/paqs/securities/{security_id}/market-snapshot")
    second = snapshot_client.get(f"/api/v1/paqs/securities/{security_id}/market-snapshot")
    assert first.status_code == 200
    body = first.json()
    assert body["snapshot_schema_version"] == "paqs-market-snapshot-v1"
    assert body["snapshot_hash"] == second.json()["snapshot_hash"]
    assert body["security"]["display_symbol"] == display_symbol
    assert body["current_price_reference"]["reference_only"] is True
    assert body["current_price_reference"]["provider_delay_seconds"] == 12
    assert body["market_state_reference"]["reference_only"] is True
    assert body["adjustment_metadata"] == {
        "basis": "PROVIDER_QFQ_CURRENT" if PROVIDER == "futu_quote" else "UNAVAILABLE",
        "adjustment_as_of": "2026-09-03T22:00:00Z",
        "historical_replay_safe": False,
    }
    assert all(bar["coverage"] == "COMPLETE" for bar in body["w1_bars"])
    assert all(
        bar["coverage"] == "COMPLETE" and bar["session_type"] == "REGULAR"
        for bar in body["m30_bars"]
    )
    evidence = body["timeframe_evidence_status"]
    assert evidence["W1"]["authoritative_bar_count"] == len(body["w1_bars"]) == 1
    assert evidence["W1"]["excluded_partial_count"] == 1
    assert evidence["W1"]["excluded_unknown_count"] == 1
    assert evidence["D1"]["source_status"] == "AVAILABLE"
    assert evidence["D1"]["authoritative_bar_count"] == len(body["d1_bars"])
    assert evidence["M30"]["source_status"] == "AVAILABLE"
    assert evidence["M30"]["authoritative_bar_count"] == len(body["m30_bars"])
    assert evidence["M30"]["missing_elapsed_bucket_count"] >= 0
    response_keys = {key.lower() for key in _keys(body)}
    for forbidden in (
        "pivot",
        "zone",
        "base_regime",
        "setup",
        "advisory",
        "risk_reward",
        "composite_score",
    ):
        assert forbidden not in response_keys


def test_quote_failure_and_source_failures_remain_truthful(
    snapshot_client: TestClient,
    snapshot_provider: SnapshotFakeProvider,
) -> None:
    snapshot_provider.quote_status = DataAvailabilityStatus.PROVIDER_ERROR
    snapshot_provider.quote_delay = None
    snapshot_provider.daily_status = DataAvailabilityStatus.PROVIDER_ERROR
    snapshot_provider.minute_status = DataAvailabilityStatus.UNAVAILABLE
    security_id = _security_id(snapshot_client, "US.AVGO")
    response = snapshot_client.get(f"/api/v1/paqs/securities/{security_id}/market-snapshot")
    assert response.status_code == 200
    body = response.json()
    quote = body["current_price_reference"]
    assert quote["status"] == "PROVIDER_ERROR"
    assert quote["price"] is quote["latest_quote_at"] is None
    assert quote["provider_delay_seconds"] is None
    evidence = body["timeframe_evidence_status"]
    assert evidence["W1"]["source_status"] == "PROVIDER_ERROR"
    assert evidence["D1"]["source_status"] == "PROVIDER_ERROR"
    assert evidence["M30"]["source_status"] == "UNAVAILABLE"
    assert body["data_quality"] == "PARTIAL"
    assert body["warnings"]


def test_snapshot_endpoint_enforces_all_context_caps(
    snapshot_client: TestClient,
    snapshot_provider: SnapshotFakeProvider,
) -> None:
    snapshot_provider.large_history = True
    security_id = _security_id(snapshot_client, "US.AVGO")
    response = snapshot_client.get(f"/api/v1/paqs/securities/{security_id}/market-snapshot")
    assert response.status_code == 200
    body = response.json()
    assert len(body["w1_bars"]) == 156
    assert len(body["d1_bars"]) == 500
    assert len(body["m30_bars"]) == 200
    evidence = body["timeframe_evidence_status"]
    assert evidence["W1"]["authoritative_bar_count"] == 156
    assert evidence["D1"]["authoritative_bar_count"] == 500
    assert evidence["M30"]["authoritative_bar_count"] == 200


def test_snapshot_route_has_only_path_parameter_and_get_does_not_mutate(
    snapshot_client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    operation = snapshot_client.get("/openapi.json").json()["paths"][
        "/api/v1/paqs/securities/{security_id}/market-snapshot"
    ]["get"]
    assert [(item["name"], item["in"]) for item in operation["parameters"]] == [
        ("security_id", "path")
    ]
    with session_factory() as session:
        before = (
            session.scalar(select(func.count()).select_from(SecurityModel)),
            session.scalar(select(func.count()).select_from(WatchlistItemModel)),
        )
    security_id = _security_id(snapshot_client, "US.AVGO")
    assert (
        snapshot_client.get(f"/api/v1/paqs/securities/{security_id}/market-snapshot").status_code
        == 200
    )
    with session_factory() as session:
        after = (
            session.scalar(select(func.count()).select_from(SecurityModel)),
            session.scalar(select(func.count()).select_from(WatchlistItemModel)),
        )
    assert after == before


def test_snapshot_clock_is_read_after_all_provider_components(
    snapshot_provider: SnapshotFakeProvider,
    session_factory: sessionmaker[Session],
    snapshot_client: TestClient,
) -> None:
    def uow_factory() -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory)

    market_queries = MarketDataQueries(
        uow_factory,
        provider_name=PROVIDER,
        provider_factory=lambda: snapshot_provider,
        now=lambda: NOW,
    )
    input_queries = PaqsInputQueries(
        market_queries,
        provider_name=PROVIDER,
        now=lambda: NOW,
    )

    def clock() -> datetime:
        snapshot_provider.events.append("clock")
        return NOW - timedelta(days=1)

    query = PaqsMarketSnapshotQueries(input_queries, market_queries, now=clock)
    query.current_snapshot(_security_id(snapshot_client, "US.AVGO"))
    assert snapshot_provider.events == [
        "daily",
        "minute",
        "calendar",
        "quote",
        "market_state",
        "clock",
    ]


def test_unknown_security_is_structured_not_found(snapshot_client: TestClient) -> None:
    response = snapshot_client.get(
        "/api/v1/paqs/securities/00000000-0000-4000-8000-000000000099/market-snapshot"
    )
    assert response.status_code == 404
    assert response.json()["code"] == "SECURITY_NOT_FOUND"
