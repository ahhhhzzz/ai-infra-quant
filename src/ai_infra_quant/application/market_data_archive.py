"""Explicit bounded observation; no collection is performed by local archive reads."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import date, datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from ai_infra_quant.application.market_data_queries import (
    MarketDataProviderFactory,
    MarketDataQueries,
    MarketDataSecurityMetadataConflict,
    MarketDataSecurityNotSupported,
)
from ai_infra_quant.core.domain.common import utc_now
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus, VerificationStatus
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
from ai_infra_quant.core.domain.market_data_archive import (
    CALENDAR_DAYS,
    DAILY_LIMIT,
    DISCLAIMER,
    LOOKBACK_DAYS,
    MINUTE_LIMIT,
    SCHEMA,
    ArchivedBar,
    freeze_bars,
    instant,
)
from ai_infra_quant.core.ports.market_data_archive import MarketDataArchive


class ArchiveUnavailable(RuntimeError):
    def __init__(self, batches: dict[str, Any]) -> None:
        super().__init__("No valid bar batch available; no capture saved")
        self.batches = batches


def _failure(code: str, status: str = "ERROR") -> dict[str, Any]:
    return {
        "status": status,
        "reason_code": code,
        "count": 0,
        "retrieved_at": None,
        "coverage_complete": False,
        "missing_count": None,
    }


def _call(operation: Callable[[], ProviderResult[Any]]) -> ProviderResult[Any] | None:
    try:
        return operation()
    except Exception:
        # SDK exceptions may contain credentials/paths; never expose their text.
        return None


def _batch(result: ProviderResult[Any] | None, provider: str) -> dict[str, Any]:
    if result is None:
        return _failure("PROVIDER_ERROR")
    if result.provider != provider:
        return _failure("PROVIDER_MISMATCH")
    meta = _failure("NO_DATA", "UNAVAILABLE")
    meta.update(
        provider=provider,
        retrieved_at=instant(result.retrieved_at),
        provider_status=result.status.value,
        provider_delay_seconds=result.provider_delay_seconds,
    )
    if result.status == DataAvailabilityStatus.AVAILABLE:
        meta.update(status="AVAILABLE", reason_code=None)
    elif result.status not in {
        DataAvailabilityStatus.UNAVAILABLE,
        DataAvailabilityStatus.NOT_SUPPORTED,
    }:
        meta.update(status="ERROR", reason_code="PROVIDER_INVALID")
    return meta


def _calendar(
    result: ProviderResult[Any] | None,
    security: MarketDataSecurity,
    start: date,
    end: date,
    observed: datetime,
    provider: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    meta = _batch(result, provider)
    meta.update(requested_start=start.isoformat(), requested_end=end.isoformat())
    if meta["status"] != "AVAILABLE" or result is None:
        return meta, []
    days: dict[str, dict[str, Any]] = {}
    try:
        if not isinstance(result.data, tuple) or len(result.data) > CALENDAR_DAYS:
            raise ValueError("CALENDAR_BOUND")
        if result.retrieved_at > observed:
            raise ValueError("CALENDAR_RETRIEVAL")
        for day in result.data:
            if (
                not isinstance(day, TradingDay)
                or day.market != security.market
                or day.market_timezone != security.market_timezone
                or day.provider != provider
                or not start <= day.market_date <= end
                or day.retrieved_at > observed
                or len(day.provider_day_type) > 128
                or any(ord(c) < 32 for c in day.provider_day_type)
                or len(day.session_segments) > 4
            ):
                raise ValueError("CALENDAR_IDENTITY")
            if day.day_type != TradingDayType.UNKNOWN and not day.session_segments:
                raise ValueError("CALENDAR_SESSIONS")
            # Revalidate frozen input at the persistence boundary, including segment overlap.
            day = replace(
                day,
                session_segments=tuple(
                    TradingSessionSegment(segment.start, segment.end)
                    for segment in day.session_segments
                ),
            )
            key = day.market_date.isoformat()
            row = {
                "market": day.market,
                "market_date": key,
                "market_timezone": day.market_timezone,
                "day_type": day.day_type.value,
                "provider_day_type": day.provider_day_type,
                "provider": day.provider,
                "retrieved_at": instant(day.retrieved_at),
                "session_segments": [
                    {"start": s.start.isoformat(), "end": s.end.isoformat()}
                    for s in day.session_segments
                ],
            }
            if key in days and days[key] != row:
                raise ValueError("CALENDAR_DUPLICATE")
            days[key] = row
    except (ValueError, TypeError, AttributeError):
        meta.update(status="ERROR", reason_code="CALENDAR_INVALID")
        return meta, []
    rows = [days[key] for key in sorted(days)]
    unknown = sum(row["day_type"] == "UNKNOWN" for row in rows)
    meta.update(count=len(rows), unknown_day_count=unknown, coverage_complete=False)
    if not rows or unknown:
        meta.update(status="PARTIAL" if rows else "UNAVAILABLE", reason_code="CALENDAR_INCOMPLETE")
    return meta, rows


def _coverage(
    batches: dict[str, Any],
    bars: tuple[ArchivedBar, ...],
    days: list[dict[str, Any]],
    started: datetime,
    security: MarketDataSecurity,
) -> None:
    """Expected regular-session gaps only; extended sessions remain stored, not invented."""
    zone = ZoneInfo(security.market_timezone)
    local_start = started.astimezone(zone)
    reliable = batches["calendar"]["status"] == "AVAILABLE" and bool(days)
    for timeframe in ("D1", "M1"):
        meta = batches[timeframe]
        selected = [bar for bar in bars if bar.timeframe == timeframe]
        meta.update(
            actual_start=selected[0].sort_key if selected else None,
            actual_end=(
                selected[-1].payload.get("interval_end", selected[-1].sort_key)
                if selected
                else None
            ),
            coverage_complete=False,
            coverage_basis="OBSERVED_ONLY",
        )
        if not selected:
            continue
        if reliable:
            keys = {bar.sort_key for bar in selected}
            expected: set[str] = set()
            for day in days:
                day_date = date.fromisoformat(day["market_date"])
                if timeframe == "D1":
                    if selected[0].sort_key <= day["market_date"] <= local_start.date().isoformat():
                        closing = datetime.fromisoformat(
                            day["market_date"] + "T" + day["session_segments"][-1]["end"]
                        ).replace(tzinfo=zone)
                        if closing <= local_start:
                            expected.add(day["market_date"])
                elif (
                    local_start.date() - timedelta(days=LOOKBACK_DAYS)
                    <= day_date
                    <= local_start.date()
                ):
                    for segment in day["session_segments"]:
                        point = datetime.fromisoformat(
                            day["market_date"] + "T" + segment["start"]
                        ).replace(tzinfo=zone)
                        end = datetime.fromisoformat(
                            day["market_date"] + "T" + segment["end"]
                        ).replace(tzinfo=zone)
                        while point < end and point + timedelta(minutes=1) <= local_start:
                            if point >= local_start - timedelta(days=LOOKBACK_DAYS):
                                expected.add(instant(point))
                            point += timedelta(minutes=1)
            meta.update(
                missing_count=len(expected - keys),
                expected_regular_count=len(expected),
                coverage_basis="RETURNED_CALENDAR_REGULAR_SESSIONS",
            )
        # Calendar availability does not certify omitted dates or provider history completeness.
        meta.update(status="PARTIAL", reason_code="OBSERVATIONAL_COVERAGE_NOT_CERTIFIED")


class MarketDataArchiveService:
    def __init__(
        self,
        queries: MarketDataQueries,
        repository: MarketDataArchive,
        *,
        provider_name: str,
        provider_factory: MarketDataProviderFactory | None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.queries = queries
        self.repository = repository
        self.provider_name = provider_name
        self.provider_factory = provider_factory
        self.now = now

    def capture(self, security_id: str) -> dict[str, Any]:
        security, market_security = self.queries.resolve_research_security(security_id)
        if security.verification_status != VerificationStatus.VERIFIED:
            raise MarketDataSecurityMetadataConflict("Archive requires verified canonical Security")
        if self.provider_name != PROVIDER_FUTU_QUOTE or self.provider_factory is None:
            raise MarketDataSecurityNotSupported("Archive provider is unavailable")
        started = self.now()
        zone = ZoneInfo(market_security.market_timezone)
        local_start = started.astimezone(zone)
        batches: dict[str, Any] = {
            name: _failure("PROVIDER_ERROR") for name in ("D1", "M1", "calendar")
        }
        bars: tuple[ArchivedBar, ...] = ()
        days: list[dict[str, Any]] = []
        calls = {"D1": 0, "M1": 0, "calendar": 0}
        try:
            # One context for all three capabilities; no long-lived database transaction here.
            with self.provider_factory() as provider:
                for timeframe, operation in (
                    ("D1", lambda: provider.get_daily_bars(market_security, DAILY_LIMIT)),
                    ("M1", lambda: provider.get_recent_minute_bars(market_security, LOOKBACK_DAYS)),
                ):
                    calls[timeframe] += 1
                    result: ProviderResult[tuple[DailyBar, ...] | tuple[MinuteBar, ...]] | None = (
                        _call(operation)
                    )
                    meta = _batch(result, self.provider_name)
                    if meta["status"] == "AVAILABLE" and result is not None:
                        try:
                            if result.data is None or result.retrieved_at > self.now():
                                raise ValueError("BATCH_TIME_OR_DATA")
                            accepted = freeze_bars(
                                result.data,
                                security_id=security.id,
                                security=market_security,
                                provider=self.provider_name,
                                timeframe=timeframe,
                                observed_at=result.retrieved_at,
                            )
                            bars += accepted
                            meta.update(
                                count=len(accepted),
                                raw_count=len(result.data),
                                duplicate_count=len(result.data) - len(accepted),
                                request_window_end=instant(result.retrieved_at),
                            )
                            if not accepted:
                                meta.update(status="UNAVAILABLE", reason_code="EMPTY_BATCH")
                        except (ValueError, TypeError, AttributeError) as exc:
                            code = str(exc)
                            allowed = {
                                "ROW_BOUND",
                                "BAR_IDENTITY_OR_COMPLETION",
                                "FUTURE_RETRIEVAL",
                                "DAILY_TIME",
                                "MINUTE_TIME",
                                "BAR_SHAPE",
                                "OHLCV_INVALID",
                                "CONFLICTING_DUPLICATE",
                                "BATCH_TIME_OR_DATA",
                            }
                            meta.update(
                                status="ERROR",
                                reason_code=code if code in allowed else "BAR_BATCH_INVALID",
                            )
                    batches[timeframe] = meta
                dates = [date.fromisoformat(bar.payload["session_date"]) for bar in bars]
                start = min([*dates, local_start.date() - timedelta(days=LOOKBACK_DAYS)])
                end = local_start.date()
                if (end - start).days >= CALENDAR_DAYS:
                    batches["calendar"] = _failure("CALENDAR_BOUND")
                else:
                    calls["calendar"] += 1
                    result_calendar = _call(
                        lambda: provider.get_trading_days(security.market, start, end)
                    )
                    batches["calendar"], days = _calendar(
                        result_calendar, market_security, start, end, self.now(), self.provider_name
                    )
        except Exception:
            # Failed context entry/exit is not a success; already accepted batches remain explicit.
            batches["context"] = _failure("PROVIDER_CONTEXT_ERROR")
        if not bars:
            raise ArchiveUnavailable(batches)
        _coverage(batches, bars, days, started, market_security)
        completed = self.now()
        capture: dict[str, Any] = {
            "schema_version": SCHEMA,
            "capture_id": str(uuid4()),
            "security_id": security.id,
            "symbol": security.symbol,
            "market": security.market,
            "currency": security.currency,
            "market_timezone": market_security.market_timezone,
            "provider": self.provider_name,
            "status": "PARTIAL",
            "started_at": instant(started),
            "completed_at": instant(completed),
            "recorded_at": instant(self.now()),
            "batches": batches,
            "calendar": days,
            "request": {
                "D1_limit": DAILY_LIMIT,
                "D1_lookback_calendar_days": 3000,
                "M1_lookback_calendar_days": LOOKBACK_DAYS,
                "M1_limit": MINUTE_LIMIT,
                "M1_window_start": instant(local_start - timedelta(days=LOOKBACK_DAYS)),
                "window_end": instant(started),
                "calendar_max_days": CALENDAR_DAYS,
            },
            "adjustment_basis": "PROVIDER_QFQ_CURRENT",
            "adjustment_epoch": None,
            "historical_as_of_safe": False,
            "atomic_provider_snapshot": False,
            "provider_capability_calls": calls,
            "disclaimer": DISCLAIMER,
        }
        self.repository.record(capture, bars)
        return capture
