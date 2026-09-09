"""Versioned archive facts. Observation time is not content identity or historical As-Of."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.common import require_utc
from ai_infra_quant.core.domain.market_data import DailyBar, MarketDataSecurity, MinuteBar
from ai_infra_quant.core.domain.money import canonical_decimal_string, parse_decimal

SCHEMA = "market-archive-v1"
DAILY_LIMIT = 1500
MINUTE_LIMIT = 50_000
LOOKBACK_DAYS = 30
CALENDAR_DAYS = 3001
DISCLAIMER = "本地存档；当前观察到的复权数据；不等于严格历史时点回测"  # noqa: RUF001


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def instant(value: datetime) -> str:
    return require_utc(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class ArchivedBar:
    identity_hash: str
    version_hash: str
    timeframe: str
    sort_key: str
    payload: dict[str, Any]
    retrieved_at: str


def freeze_bars(
    rows: tuple[DailyBar, ...] | tuple[MinuteBar, ...],
    *,
    security_id: str,
    security: MarketDataSecurity,
    provider: str,
    timeframe: str,
    observed_at: datetime,
) -> tuple[ArchivedBar, ...]:
    limit = DAILY_LIMIT if timeframe == "D1" else MINUTE_LIMIT
    if not isinstance(rows, tuple) or len(rows) > limit:
        raise ValueError("ROW_BOUND")
    zone = ZoneInfo(security.market_timezone)
    local_now = observed_at.astimezone(zone)
    lower = local_now - timedelta(days=LOOKBACK_DAYS)
    versions: dict[str, ArchivedBar] = {}
    for bar in rows:
        if bar.security != security.display_symbol or bar.is_completed is not True:
            raise ValueError("BAR_IDENTITY_OR_COMPLETION")
        retrieved = require_utc(bar.retrieved_at)
        if retrieved > observed_at:
            raise ValueError("FUTURE_RETRIEVAL")
        identity: dict[str, Any] = {
            "schema_version": SCHEMA,
            "security_id": security_id,
            "security": security.display_symbol,
            "market": security.market,
            "currency": security.currency,
            "market_timezone": security.market_timezone,
            "provider": provider,
            "timeframe": timeframe,
            "adjustment_basis": "PROVIDER_QFQ_CURRENT",
            "adjustment_epoch": None,
        }
        if timeframe == "D1" and isinstance(bar, DailyBar):
            provider_time = require_utc(bar.provider_time)
            if (
                not local_now.date() - timedelta(days=3000) <= bar.session_date <= local_now.date()
                or provider_time.astimezone(zone).date() != bar.session_date
                or provider_time > retrieved
            ):
                raise ValueError("DAILY_TIME")
            identity["session_date"] = bar.session_date.isoformat()
            key = bar.session_date.isoformat()
            original = {"provider_time": instant(provider_time)}
        elif timeframe == "M1" and isinstance(bar, MinuteBar):
            start, end = require_utc(bar.interval_start), require_utc(bar.interval_end)
            if (
                end - start != timedelta(minutes=1)
                or start.second != 0
                or start.microsecond != 0
                or start < lower.astimezone(start.tzinfo)
                or end > retrieved
            ):
                raise ValueError("MINUTE_TIME")
            identity.update(interval_start=instant(start), interval_end=instant(end))
            key = instant(start)
            original = {"session_date": start.astimezone(zone).date().isoformat()}
        else:
            raise ValueError("BAR_SHAPE")
        values = {
            name: parse_decimal(getattr(bar, name))
            for name in ("open", "high", "low", "close", "volume")
        }
        if (
            any(values[name] <= 0 for name in ("open", "high", "low", "close"))
            or values["volume"] < 0
            or values["low"] > min(values["open"], values["close"])
            or values["high"] < max(values["open"], values["close"])
            or values["low"] > values["high"]
        ):
            raise ValueError("OHLCV_INVALID")
        payload = (
            identity
            | original
            | {name: canonical_decimal_string(value) for name, value in values.items()}
            | {"is_completed": True}
        )
        frozen = ArchivedBar(
            digest(identity), digest(payload), timeframe, key, payload, instant(retrieved)
        )
        prior = versions.get(key)
        if prior is not None and prior.version_hash != frozen.version_hash:
            raise ValueError("CONFLICTING_DUPLICATE")
        # Identical repeats select the earliest observation; batch counts disclose duplicates.
        if prior is None or frozen.retrieved_at < prior.retrieved_at:
            versions[key] = frozen
    return tuple(versions[key] for key in sorted(versions))
