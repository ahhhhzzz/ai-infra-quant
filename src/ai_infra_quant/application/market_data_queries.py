from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from ai_infra_quant.application.unit_of_work import UnitOfWorkFactory
from ai_infra_quant.core.domain.common import utc_now
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import (
    DailyBar,
    MarketDataSecurity,
    MarketStatusSnapshot,
    MinuteBar,
    ProviderResult,
    QuoteSnapshot,
)
from ai_infra_quant.core.domain.security import Security
from ai_infra_quant.core.ports.market_data import ReadOnlyMarketDataProvider

MarketDataProviderFactory = Callable[[], ReadOnlyMarketDataProvider]


class MarketDataSecurityNotFound(LookupError):
    pass


class MarketDataSecurityNotSupported(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MarketStateView:
    security: Security
    market_timezone: str
    quote: ProviderResult[QuoteSnapshot]
    market_status: ProviderResult[MarketStatusSnapshot]


@dataclass(frozen=True, slots=True)
class DailyBarsView:
    security: Security
    market_timezone: str
    result: ProviderResult[tuple[DailyBar, ...]]


@dataclass(frozen=True, slots=True)
class MinuteBarsView:
    security: Security
    market_timezone: str
    session_date: str
    lookback_calendar_days: int
    window_start: datetime
    window_end: datetime
    result: ProviderResult[tuple[MinuteBar, ...]]


class MarketDataQueries:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        *,
        provider_name: str,
        provider_factory: MarketDataProviderFactory | None,
        supported_securities: tuple[MarketDataSecurity, ...],
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._uow_factory = uow_factory
        self._provider_name = provider_name
        self._provider_factory = provider_factory
        self._supported_securities = {
            security.display_symbol: security for security in supported_securities
        }
        self._now = now

    def state(self, security_id: str) -> MarketStateView:
        security, market_security = self._resolve_security(security_id)
        if self._provider_factory is None:
            retrieved_at = self._now()
            reason = "market data provider is not configured"
            return MarketStateView(
                security=security,
                market_timezone=market_security.market_timezone,
                quote=_failure(self._provider_name, retrieved_at, reason),
                market_status=_failure(self._provider_name, retrieved_at, reason),
            )
        try:
            with self._provider_factory() as provider:
                quote = self._safe_call(lambda: provider.get_latest_quote(market_security))
                market_status = self._safe_call(lambda: provider.get_market_status(market_security))
        except Exception as exc:
            retrieved_at = self._now()
            reason = _safe_reason(exc)
            quote = _failure(self._provider_name, retrieved_at, reason)
            market_status = _failure(self._provider_name, retrieved_at, reason)
        return MarketStateView(
            security=security,
            market_timezone=market_security.market_timezone,
            quote=quote,
            market_status=market_status,
        )

    def daily_bars(self, security_id: str, limit: int) -> DailyBarsView:
        security, market_security = self._resolve_security(security_id)
        result = self._single_capability(
            lambda provider: provider.get_daily_bars(market_security, limit)
        )
        if result.data is not None:
            result = replace(result, data=result.data[-limit:])
        return DailyBarsView(
            security=security,
            market_timezone=market_security.market_timezone,
            result=result,
        )

    def minute_bars(self, security_id: str, lookback_days: int) -> MinuteBarsView:
        security, market_security = self._resolve_security(security_id)
        result = self._single_capability(
            lambda provider: provider.get_recent_minute_bars(market_security, lookback_days)
        )
        market_timezone = ZoneInfo(market_security.market_timezone)
        market_retrieved_at = result.retrieved_at.astimezone(market_timezone)
        window_start = (market_retrieved_at - timedelta(days=lookback_days)).astimezone(UTC)
        return MinuteBarsView(
            security=security,
            market_timezone=market_security.market_timezone,
            session_date=market_retrieved_at.date().isoformat(),
            lookback_calendar_days=lookback_days,
            window_start=window_start,
            window_end=result.retrieved_at,
            result=result,
        )

    def _resolve_security(self, security_id: str) -> tuple[Security, MarketDataSecurity]:
        with self._uow_factory() as uow:
            security = uow.securities.get(security_id)
        if security is None:
            raise MarketDataSecurityNotFound
        market_security = self._supported_securities.get(security.display_symbol)
        if market_security is None:
            raise MarketDataSecurityNotSupported
        return security, market_security

    def _single_capability[ResultT](
        self,
        operation: Callable[[ReadOnlyMarketDataProvider], ProviderResult[ResultT]],
    ) -> ProviderResult[ResultT]:
        if self._provider_factory is None:
            return _failure(
                self._provider_name,
                self._now(),
                "market data provider is not configured",
            )
        try:
            with self._provider_factory() as provider:
                return self._safe_call(lambda: operation(provider))
        except Exception as exc:
            return _failure(self._provider_name, self._now(), _safe_reason(exc))

    def _safe_call[ResultT](
        self, operation: Callable[[], ProviderResult[ResultT]]
    ) -> ProviderResult[ResultT]:
        try:
            return operation()
        except Exception as exc:
            return ProviderResult(
                status=DataAvailabilityStatus.PROVIDER_ERROR,
                provider=self._provider_name,
                retrieved_at=self._now(),
                reason=_safe_reason(exc),
            )


def _failure[ResultT](
    provider: str, retrieved_at: datetime, reason: str
) -> ProviderResult[ResultT]:
    return ProviderResult(
        status=DataAvailabilityStatus.UNAVAILABLE,
        provider=provider,
        retrieved_at=retrieved_at,
        reason=reason,
    )


def _safe_reason(error: object) -> str:
    text = str(error).strip()
    return text[:500] if text else type(error).__name__
