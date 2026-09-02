from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ai_infra_quant.application.market_data_queries import MarketDataQueries
from ai_infra_quant.core.domain.common import utc_now
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus, SnapshotQualityStatus
from ai_infra_quant.core.domain.market_data import PROVIDER_FUTU_QUOTE
from ai_infra_quant.core.domain.paqs_input import (
    AdjustmentBasis,
    AdjustmentMetadata,
    CalendarMetadata,
    PaqsInputBundle,
    SourceCoverage,
    derive_m30_bars,
    derive_weekly_bars,
    expected_completed_m30_bucket_count,
)


class PaqsInputQueries:
    """Prepare current provider-agnostic PAQS inputs without strategy interpretation."""

    def __init__(
        self,
        market_data_queries: MarketDataQueries,
        *,
        provider_name: str,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._market_data_queries = market_data_queries
        self._provider_name = provider_name
        self._now = now

    def current_bundle(self, security_id: str) -> PaqsInputBundle:
        security, market_security = self._market_data_queries.resolve_research_security(security_id)
        daily_view = self._market_data_queries.daily_bars(security_id, 1500)
        minute_view = self._market_data_queries.minute_bars(security_id, 30)
        initial_as_of = self._now()
        timezone = ZoneInfo(market_security.market_timezone)
        daily = daily_view.result.data or ()
        minute = minute_view.result.data or ()
        earliest_local_date = initial_as_of.astimezone(timezone).date() - timedelta(days=35)
        if daily:
            earliest_local_date = min(earliest_local_date, min(bar.session_date for bar in daily))
        if minute:
            earliest_local_date = min(
                earliest_local_date,
                min(bar.interval_start.astimezone(timezone).date() for bar in minute),
            )
        market_date = initial_as_of.astimezone(timezone).date()
        calendar_end = market_date + timedelta(days=7 - market_date.isoweekday())
        calendar_view = self._market_data_queries.trading_days(
            security_id,
            earliest_local_date,
            calendar_end,
        )
        as_of = max(
            initial_as_of,
            daily_view.result.retrieved_at,
            minute_view.result.retrieved_at,
            calendar_view.result.retrieved_at,
        )
        trading_days = calendar_view.result.data or ()
        minute_window_start_date = minute_view.window_start.astimezone(timezone).date()
        m30_trading_days = tuple(
            item for item in trading_days if item.market_date >= minute_window_start_date
        )
        weekly = derive_weekly_bars(
            security=market_security.display_symbol,
            market_timezone=market_security.market_timezone,
            daily_bars=daily,
            trading_days=trading_days,
            as_of=as_of,
        )
        m30 = derive_m30_bars(
            security=market_security.display_symbol,
            market_timezone=market_security.market_timezone,
            minute_bars=minute,
            trading_days=m30_trading_days,
            as_of=as_of,
        )
        completed_weekly = tuple(bar for bar in weekly if bar.is_completed)
        completed_m30 = tuple(bar for bar in m30 if bar.is_completed)
        expected_m30 = expected_completed_m30_bucket_count(m30_trading_days, as_of)
        unknown_days = sum(1 for item in m30_trading_days if not item.session_segments)
        missing_m30 = max(0, expected_m30 - len(completed_m30))
        warnings = _warnings(
            daily_status=daily_view.result.status,
            daily_reason=daily_view.result.reason,
            minute_status=minute_view.result.status,
            minute_reason=minute_view.result.reason,
            calendar_status=calendar_view.result.status,
            calendar_reason=calendar_view.result.reason,
            unknown_days=unknown_days,
            missing_m30=missing_m30,
            qfq=self._provider_name == PROVIDER_FUTU_QUOTE,
        )
        data_quality = _quality(
            daily_view.result.status,
            minute_view.result.status,
            calendar_view.result.status,
            has_any_data=bool(daily or minute or trading_days),
            unknown_days=unknown_days,
            missing_m30=missing_m30,
        )
        adjustment_basis = (
            AdjustmentBasis.PROVIDER_QFQ_CURRENT
            if self._provider_name == PROVIDER_FUTU_QUOTE
            else AdjustmentBasis.UNAVAILABLE
        )
        return PaqsInputBundle(
            security_id=security.id,
            market=security.market,
            symbol=security.symbol,
            market_timezone=market_security.market_timezone,
            provider=self._provider_name,
            as_of_timestamp=as_of,
            completed_w1_bars=completed_weekly,
            completed_d1_bars=daily,
            completed_30m_bars=completed_m30,
            calendar=CalendarMetadata(
                status=calendar_view.result.status,
                provider=calendar_view.result.provider,
                retrieved_at=calendar_view.result.retrieved_at,
                trading_days=trading_days,
                reason=calendar_view.result.reason,
            ),
            adjustment=AdjustmentMetadata(
                basis=adjustment_basis,
                adjustment_as_of=as_of,
                historical_replay_safe=False,
            ),
            data_quality=data_quality,
            warnings=warnings,
            source_coverage=SourceCoverage(
                d1_source_count=len(daily),
                w1_completed_count=len(completed_weekly),
                w1_partial_count=sum(1 for bar in weekly if not bar.is_completed),
                minute_source_count=len(minute),
                m30_completed_count=len(completed_m30),
                m30_partial_count=missing_m30,
            ),
        )


def _quality(
    daily: DataAvailabilityStatus,
    minute: DataAvailabilityStatus,
    calendar: DataAvailabilityStatus,
    *,
    has_any_data: bool,
    unknown_days: int,
    missing_m30: int,
) -> SnapshotQualityStatus:
    if (
        daily is DataAvailabilityStatus.AVAILABLE
        and minute is DataAvailabilityStatus.AVAILABLE
        and calendar is DataAvailabilityStatus.AVAILABLE
        and unknown_days == 0
        and missing_m30 == 0
    ):
        return SnapshotQualityStatus.COMPLETE
    return SnapshotQualityStatus.PARTIAL if has_any_data else SnapshotQualityStatus.INVALID


def _warnings(
    *,
    daily_status: DataAvailabilityStatus,
    daily_reason: str | None,
    minute_status: DataAvailabilityStatus,
    minute_reason: str | None,
    calendar_status: DataAvailabilityStatus,
    calendar_reason: str | None,
    unknown_days: int,
    missing_m30: int,
    qfq: bool,
) -> tuple[str, ...]:
    warnings: list[str] = []
    for name, status, reason in (
        ("D1", daily_status, daily_reason),
        ("1m", minute_status, minute_reason),
        ("calendar", calendar_status, calendar_reason),
    ):
        if status is not DataAvailabilityStatus.AVAILABLE:
            warnings.append(f"{name} {status.value}: {reason or 'data unavailable'}")
    if unknown_days:
        warnings.append(f"{unknown_days} trading day(s) have unknown session metadata")
    if missing_m30:
        warnings.append(f"{missing_m30} elapsed M30 bucket(s) lack complete minute coverage")
    if qfq:
        warnings.append("Current provider QFQ data is not point-in-time-safe historical replay")
    return tuple(warnings)
