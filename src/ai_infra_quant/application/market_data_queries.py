from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from ai_infra_quant.application.unit_of_work import UnitOfWorkFactory
from ai_infra_quant.core.domain.common import utc_now
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus, InstrumentType
from ai_infra_quant.core.domain.market_data import (
    DailyBar,
    MarketDataSecurity,
    MarketStatusSnapshot,
    MinuteBar,
    ProviderResult,
    QuoteSnapshot,
    TradingDay,
)
from ai_infra_quant.core.domain.security import Security
from ai_infra_quant.core.ports.market_data import ReadOnlyMarketDataProvider

MarketDataProviderFactory = Callable[[], ReadOnlyMarketDataProvider]


class MarketDataSecurityNotFound(LookupError):
    pass


class MarketDataSecurityNotSupported(ValueError):
    pass


class MarketDataSecurityMetadataConflict(ValueError):
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


@dataclass(frozen=True, slots=True)
class TradingDaysView:
    security: Security
    market_timezone: str
    start_date: date
    end_date: date
    result: ProviderResult[tuple[TradingDay, ...]]


class MarketDataQueries:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        *,
        provider_name: str,
        provider_factory: MarketDataProviderFactory | None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._uow_factory = uow_factory
        self._provider_name = provider_name
        self._provider_factory = provider_factory
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

    def trading_days(self, security_id: str, start_date: date, end_date: date) -> TradingDaysView:
        security, market_security = self._resolve_security(security_id)
        result = self._single_capability(
            lambda provider: provider.get_trading_days(market_security.market, start_date, end_date)
        )
        return TradingDaysView(
            security=security,
            market_timezone=market_security.market_timezone,
            start_date=start_date,
            end_date=end_date,
            result=result,
        )

    def resolve_research_security(self, security_id: str) -> tuple[Security, MarketDataSecurity]:
        return self._resolve_security(security_id)

    def _resolve_security(self, security_id: str) -> tuple[Security, MarketDataSecurity]:
        with self._uow_factory() as uow:
            security = uow.securities.get(security_id)
        if security is None:
            raise MarketDataSecurityNotFound
        return security, market_data_security_for_equity(security)

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


def market_data_security_for_equity(
    security: Security,
) -> MarketDataSecurity:
    if not security.enabled or security.instrument_type is not InstrumentType.EQUITY:
        raise MarketDataSecurityNotSupported
    contract = {
        "US": ("USD", "America/New_York"),
        "HK": ("HKD", "Asia/Hong_Kong"),
    }.get(security.market)
    if contract is None:
        raise MarketDataSecurityNotSupported
    currency, market_timezone = contract
    if security.currency != currency:
        raise MarketDataSecurityMetadataConflict(
            f"stored currency {security.currency} conflicts with "
            f"{security.market} contract {currency}"
        )
    if security.market_timezone is not None and security.market_timezone != market_timezone:
        raise MarketDataSecurityMetadataConflict(
            "stored market timezone conflicts with the canonical market-data contract"
        )
    return MarketDataSecurity(
        market=security.market,
        symbol=security.symbol,
        currency=currency,
        market_timezone=market_timezone,
    )


def paqs_research_eligible(security: Security) -> bool:
    try:
        market_data_security_for_equity(security)
    except (MarketDataSecurityNotSupported, MarketDataSecurityMetadataConflict):
        return False
    return True
