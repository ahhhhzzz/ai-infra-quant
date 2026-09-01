from __future__ import annotations

from ai_infra_quant.application.market_data_queries import (
    DailyBarsView,
    MarketStateView,
    MinuteBarsView,
)
from ai_infra_quant.backend.schemas.common import StrictSchema
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import DailyBar, MinuteBar
from ai_infra_quant.core.domain.money import decimal_string


class MarketStateRead(StrictSchema):
    security_id: str
    market: str
    symbol: str
    currency: str
    market_timezone: str
    provider: str
    latest_price: str | None
    latest_quote_at: str | None
    market_state: str | None
    provider_market_state: str | None
    retrieved_at: str
    provider_delay_seconds: int | None
    quote_status: DataAvailabilityStatus
    market_status: DataAvailabilityStatus
    reason: str | None


class DailyBarRead(StrictSchema):
    session_date: str
    open: str
    high: str
    low: str
    close: str
    volume: str
    provider_time: str
    is_completed: bool


class DailyBarsRead(StrictSchema):
    security_id: str
    market_timezone: str
    provider: str
    status: DataAvailabilityStatus
    retrieved_at: str
    latest_completed_daily_session: str | None
    bars: list[DailyBarRead]
    reason: str | None


class MinuteBarRead(StrictSchema):
    interval_start: str
    interval_end: str
    open: str
    high: str
    low: str
    close: str
    volume: str
    is_completed: bool


class MinuteBarsRead(StrictSchema):
    security_id: str
    market_timezone: str
    provider: str
    status: DataAvailabilityStatus
    session_date: str
    retrieved_at: str
    latest_completed_minute_bar_at: str | None
    bars: list[MinuteBarRead]
    reason: str | None


def _utc_string(value: object) -> str:
    from datetime import datetime

    if not isinstance(value, datetime):
        raise TypeError("expected datetime")
    return value.isoformat().replace("+00:00", "Z")


def _reasons(*items: tuple[str, str | None]) -> str | None:
    reasons = [f"{name}: {reason}" for name, reason in items if reason]
    return "; ".join(reasons) or None


def market_state_read(view: MarketStateView) -> MarketStateRead:
    quote = view.quote
    market_status = view.market_status
    quote_data = quote.data
    status_data = market_status.data
    return MarketStateRead(
        security_id=view.security.id,
        market=view.security.market,
        symbol=view.security.symbol,
        currency=view.security.currency,
        market_timezone=view.market_timezone,
        provider=quote.provider,
        latest_price=None if quote_data is None else decimal_string(quote_data.price),
        latest_quote_at=(None if quote_data is None else _utc_string(quote_data.latest_quote_at)),
        market_state=None if status_data is None else status_data.state.value,
        provider_market_state=(None if status_data is None else status_data.provider_state),
        retrieved_at=_utc_string(max(quote.retrieved_at, market_status.retrieved_at)),
        provider_delay_seconds=(
            quote.provider_delay_seconds
            if quote.provider_delay_seconds is not None
            else market_status.provider_delay_seconds
        ),
        quote_status=quote.status,
        market_status=market_status.status,
        reason=_reasons(("latest", quote.reason), ("market_status", market_status.reason)),
    )


def _daily_bar_read(bar: DailyBar) -> DailyBarRead:
    return DailyBarRead(
        session_date=bar.session_date.isoformat(),
        open=decimal_string(bar.open),
        high=decimal_string(bar.high),
        low=decimal_string(bar.low),
        close=decimal_string(bar.close),
        volume=decimal_string(bar.volume),
        provider_time=_utc_string(bar.provider_time),
        is_completed=bar.is_completed,
    )


def daily_bars_read(view: DailyBarsView) -> DailyBarsRead:
    data = view.result.data or ()
    return DailyBarsRead(
        security_id=view.security.id,
        market_timezone=view.market_timezone,
        provider=view.result.provider,
        status=view.result.status,
        retrieved_at=_utc_string(view.result.retrieved_at),
        latest_completed_daily_session=(
            None if not data else max(bar.session_date for bar in data).isoformat()
        ),
        bars=[_daily_bar_read(bar) for bar in data],
        reason=view.result.reason,
    )


def _minute_bar_read(bar: MinuteBar) -> MinuteBarRead:
    return MinuteBarRead(
        interval_start=_utc_string(bar.interval_start),
        interval_end=_utc_string(bar.interval_end),
        open=decimal_string(bar.open),
        high=decimal_string(bar.high),
        low=decimal_string(bar.low),
        close=decimal_string(bar.close),
        volume=decimal_string(bar.volume),
        is_completed=bar.is_completed,
    )


def minute_bars_read(view: MinuteBarsView) -> MinuteBarsRead:
    data = view.result.data or ()
    return MinuteBarsRead(
        security_id=view.security.id,
        market_timezone=view.market_timezone,
        provider=view.result.provider,
        status=view.result.status,
        session_date=view.session_date,
        retrieved_at=_utc_string(view.result.retrieved_at),
        latest_completed_minute_bar_at=(
            None if not data else _utc_string(max(bar.interval_end for bar in data))
        ),
        bars=[_minute_bar_read(bar) for bar in data],
        reason=view.result.reason,
    )
