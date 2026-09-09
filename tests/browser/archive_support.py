"""Synthetic market facts only; never a production provider or connection."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, cast
from zoneinfo import ZoneInfo

from sqlalchemy import update

from ai_infra_quant.application.market_data_archive import MarketDataArchiveService
from ai_infra_quant.backend.dependencies import AppContainer
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import (
    PROVIDER_FUTU_QUOTE,
    DailyBar,
    MarketDataSecurity,
    MinuteBar,
    ProviderResult,
    TradingDay,
    TradingDayType,
    TradingSessionSegment,
)
from ai_infra_quant.core.ports.market_data import ReadOnlyMarketDataProvider
from ai_infra_quant.database.models.security import SecurityModel
from ai_infra_quant.database.repositories.market_data_archive import SQLAlchemyMarketDataArchive

NOW = datetime(2026, 9, 8, 22, tzinfo=UTC)
PRICE = Decimal("12345678901234567890.123456789012345678")


class SyntheticArchiveProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.closed = 0
        self.price = PRICE
        self.minute_count = 601
        self.fail: set[str] = set()
        self.now = NOW
        self.daily_offset = 0
        self.duplicate = False
        self.conflict = False
        self.delay = 0.0

    def __enter__(self) -> SyntheticArchiveProvider:
        self.calls.append("enter")
        return self

    def __exit__(self, *args: Any) -> None:
        self.closed += 1

    def result(self, kind: str, rows: Any) -> ProviderResult[Any]:
        import time as clock

        clock.sleep(self.delay)
        self.calls.append(kind)
        if kind in self.fail:
            raise RuntimeError("synthetic-private-path/token MUST NOT ESCAPE")
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER_FUTU_QUOTE,
            retrieved_at=self.now,
            data=rows,
        )

    def get_daily_bars(
        self, security: MarketDataSecurity, limit: int
    ) -> ProviderResult[tuple[DailyBar, ...]]:
        assert limit == 1500
        day = date(2026, 9, 7) + timedelta(days=self.daily_offset)
        bar = DailyBar(
            security.display_symbol,
            day,
            datetime.combine(day, time(), ZoneInfo(security.market_timezone)).astimezone(UTC),
            self.price,
            self.price,
            self.price,
            self.price,
            Decimal("10.000000000000000001"),
            True,
            self.now,
        )
        rows = (bar, bar) if self.duplicate else (bar,)
        if self.conflict:
            from dataclasses import replace

            rows = (bar, replace(bar, volume=Decimal("11")))
        return self.result("D1", rows)

    def get_recent_minute_bars(
        self, security: MarketDataSecurity, lookback_days: int
    ) -> ProviderResult[tuple[MinuteBar, ...]]:
        assert lookback_days == 30
        start = datetime(2026, 9, 7, 8, tzinfo=UTC)
        rows = tuple(
            MinuteBar(
                security.display_symbol,
                start + timedelta(minutes=i),
                start + timedelta(minutes=i + 1),
                self.price,
                self.price,
                self.price,
                self.price,
                Decimal("0.000000000000000001"),
                True,
                self.now,
            )
            for i in range(self.minute_count)
        )
        return self.result("M1", rows)

    def get_trading_days(
        self, market: str, start_date: date, end_date: date
    ) -> ProviderResult[tuple[TradingDay, ...]]:
        assert (end_date - start_date).days <= 3000
        segments = (
            (
                TradingSessionSegment(time(9, 30), time(12)),
                TradingSessionSegment(time(13), time(16)),
            )
            if market == "HK"
            else (TradingSessionSegment(time(9, 30), time(16)),)
        )
        day = TradingDay(
            market,
            date(2026, 9, 7),
            "Asia/Hong_Kong" if market == "HK" else "America/New_York",
            TradingDayType.FULL,
            "SYNTHETIC_FULL",
            segments,
            PROVIDER_FUTU_QUOTE,
            self.now,
        )
        return self.result("calendar", (day,))


def install(
    container: AppContainer, provider: SyntheticArchiveProvider
) -> MarketDataArchiveService:
    with container.session_factory.begin() as session:
        session.execute(update(SecurityModel).values(verification_status="VERIFIED"))
    service = MarketDataArchiveService(
        container.market_data_queries,
        SQLAlchemyMarketDataArchive(container.session_factory),
        provider_name=PROVIDER_FUTU_QUOTE,
        provider_factory=lambda: cast(ReadOnlyMarketDataProvider, provider),
        now=lambda: provider.now,
    )
    container.market_data_archive = service
    return service
