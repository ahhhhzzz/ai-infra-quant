"""Quote-only Futu OpenD adapter with canonical, truthful result handling."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from importlib import import_module
from types import TracebackType
from typing import Any, Protocol, cast
from zoneinfo import ZoneInfo

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
from ai_infra_quant.integrations.futu_quote.symbols import futu_code_for

MAX_HISTORY_PAGES = 100
MAX_DAILY_BARS = 1500
MAX_MINUTE_LOOKBACK_DAYS = 31


class TabularResponse(Protocol):
    def to_dict(self, orient: str) -> list[dict[str, object]]: ...


class FutuQuoteContext(Protocol):
    def get_market_snapshot(self, code_list: list[str]) -> tuple[object, object]: ...

    def get_market_state(self, code_list: list[str]) -> tuple[object, object]: ...

    def request_history_kline(
        self,
        code: str,
        start: str,
        end: str,
        ktype: object,
        autype: object,
        max_count: int,
        page_req_key: object | None,
        session: object = ...,
    ) -> tuple[object, object, object]: ...

    def request_trading_days(
        self, market: object, start: str, end: str
    ) -> tuple[object, object]: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class FutuSdkBindings:
    context_factory: Callable[..., FutuQuoteContext]
    ret_ok: object
    k_day: object
    k_1m: object
    au_qfq: object
    session_all: object
    trade_date_market_us: object
    trade_date_market_hk: object
    sdk_version: str | None


def load_futu_sdk() -> FutuSdkBindings:
    """Load the optional official Futu SDK without exposing it to core code."""
    try:
        sdk = import_module("futu")
    except ImportError as exc:
        raise RuntimeError("optional dependency missing; install project extra 'futu'") from exc
    try:
        return FutuSdkBindings(
            context_factory=cast(Callable[..., FutuQuoteContext], sdk.OpenQuoteContext),
            ret_ok=sdk.RET_OK,
            k_day=sdk.KLType.K_DAY,
            k_1m=sdk.KLType.K_1M,
            au_qfq=sdk.AuType.QFQ,
            session_all=sdk.Session.ALL,
            trade_date_market_us=sdk.TradeDateMarket.US,
            trade_date_market_hk=sdk.TradeDateMarket.HK,
            sdk_version=cast(str | None, getattr(sdk, "__version__", None)),
        )
    except AttributeError as exc:
        raise RuntimeError("installed Futu SDK lacks required quote-only capability") from exc


BindingsLoader = Callable[[], FutuSdkBindings]
Clock = Callable[[], datetime]


class FutuQuoteAdapter:
    """Minimal provider adapter that owns exactly one quote context."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        bindings_loader: BindingsLoader = load_futu_sdk,
        now: Clock | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._bindings_loader = bindings_loader
        self._now = now or (lambda: datetime.now(UTC))
        self._bindings: FutuSdkBindings | None = None
        self._context: FutuQuoteContext | None = None

    def __enter__(self) -> FutuQuoteAdapter:
        try:
            bindings = self._bindings_loader()
            context = bindings.context_factory(host=self._host, port=self._port)
        except Exception as exc:
            raise RuntimeError(_safe_reason(exc)) from exc
        self._bindings = bindings
        self._context = context
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        context, self._context = self._context, None
        if context is not None:
            context.close()

    def provider_status(self) -> ProviderResult[ProviderStatus]:
        retrieved_at = self._retrieved_at()
        if self._context is None or self._bindings is None:
            return _failure(
                DataAvailabilityStatus.UNAVAILABLE, retrieved_at, "quote context is closed"
            )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            retrieved_at=retrieved_at,
            data=ProviderStatus(quote_context_open=True, sdk_version=self._bindings.sdk_version),
        )

    def get_latest_quote(self, security: MarketDataSecurity) -> ProviderResult[QuoteSnapshot]:
        retrieved_at = self._retrieved_at()
        call = self._call("get_market_snapshot", [futu_code_for(security)])
        if isinstance(call, ProviderResult):
            return cast(ProviderResult[QuoteSnapshot], call)
        rows = _rows(call, retrieved_at)
        if isinstance(rows, ProviderResult):
            return cast(ProviderResult[QuoteSnapshot], rows)
        try:
            row = _matching_row(rows, futu_code_for(security))
            quote_time = _provider_datetime(row["update_time"], security)
            quote = QuoteSnapshot(
                security=security.display_symbol,
                price=_decimal(row["last_price"], "last_price"),
                currency=security.currency,
                latest_quote_at=quote_time,
                retrieved_at=retrieved_at,
            )
        except (KeyError, TypeError, ValueError) as exc:
            return _failure(DataAvailabilityStatus.INVALID, retrieved_at, _safe_reason(exc))
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE, retrieved_at=retrieved_at, data=quote
        )

    def get_market_status(
        self, security: MarketDataSecurity
    ) -> ProviderResult[MarketStatusSnapshot]:
        retrieved_at = self._retrieved_at()
        call = self._call("get_market_state", [futu_code_for(security)])
        if isinstance(call, ProviderResult):
            return cast(ProviderResult[MarketStatusSnapshot], call)
        rows = _rows(call, retrieved_at)
        if isinstance(rows, ProviderResult):
            return cast(ProviderResult[MarketStatusSnapshot], rows)
        try:
            row = _matching_row(rows, futu_code_for(security))
            raw_state = str(row["market_state"]).strip()
            if not raw_state:
                raise ValueError("market_state is empty")
            snapshot = MarketStatusSnapshot(
                security=security.display_symbol,
                state=_market_state(raw_state),
                provider_state=raw_state,
                retrieved_at=retrieved_at,
            )
        except (KeyError, TypeError, ValueError) as exc:
            return _failure(DataAvailabilityStatus.INVALID, retrieved_at, _safe_reason(exc))
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE, retrieved_at=retrieved_at, data=snapshot
        )

    def get_daily_bars(
        self, security: MarketDataSecurity, limit: int = 10
    ) -> ProviderResult[tuple[DailyBar, ...]]:
        if not 1 <= limit <= MAX_DAILY_BARS:
            raise ValueError(f"daily bar limit must be between 1 and {MAX_DAILY_BARS}")
        retrieved_at = self._retrieved_at()
        market_timezone = ZoneInfo(security.market_timezone)
        market_today = retrieved_at.astimezone(market_timezone).date()
        rows = self._history_rows(
            security,
            start=market_today - timedelta(days=max(14, limit * 2)),
            end=market_today,
            ktype=self._require_bindings().k_day,
        )
        if isinstance(rows, ProviderResult):
            return cast(ProviderResult[tuple[DailyBar, ...]], rows)
        try:
            rows_with_session_dates = tuple(
                (
                    row,
                    _provider_datetime(row["time_key"], security)
                    .astimezone(market_timezone)
                    .date(),
                )
                for row in rows
            )
            has_current_session_bar = any(
                session_date == market_today for _, session_date in rows_with_session_dates
            )
            current_regular_session_closed = False
            if has_current_session_bar:
                market_status = self.get_market_status(security)
                current_regular_session_closed = (
                    market_status.status is DataAvailabilityStatus.AVAILABLE
                    and market_status.data is not None
                    and _regular_session_is_closed(
                        security,
                        market_status.data.provider_state,
                    )
                )
            bars_by_session = {
                session_date: _daily_bar(row, security, retrieved_at)
                for row, session_date in rows_with_session_dates
                if session_date < market_today
                or (session_date == market_today and current_regular_session_closed)
            }
            bars = tuple(bars_by_session[key] for key in sorted(bars_by_session))
        except (KeyError, TypeError, ValueError) as exc:
            return _failure(DataAvailabilityStatus.INVALID, retrieved_at, _safe_reason(exc))
        if not bars:
            reason = "no completed daily bars"
            if has_current_session_bar and not current_regular_session_closed:
                reason = (
                    "current daily bar excluded because provider market state does not "
                    "authoritatively show the regular session is closed"
                )
            return _failure(
                DataAvailabilityStatus.UNAVAILABLE,
                retrieved_at,
                reason,
            )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            retrieved_at=retrieved_at,
            data=bars[-limit:],
        )

    def get_recent_minute_bars(
        self, security: MarketDataSecurity, lookback_days: int = 30
    ) -> ProviderResult[tuple[MinuteBar, ...]]:
        if not 1 <= lookback_days <= MAX_MINUTE_LOOKBACK_DAYS:
            raise ValueError(
                f"minute lookback must be between 1 and {MAX_MINUTE_LOOKBACK_DAYS} days"
            )
        retrieved_at = self._retrieved_at()
        market_timezone = ZoneInfo(security.market_timezone)
        market_retrieved_at = retrieved_at.astimezone(market_timezone)
        window_start = (market_retrieved_at - timedelta(days=lookback_days)).astimezone(UTC)
        request_start = window_start.astimezone(market_timezone).date()
        if security.market == "US":
            request_start -= timedelta(days=1)
        rows = self._history_rows(
            security,
            start=request_start,
            end=market_retrieved_at.date(),
            ktype=self._require_bindings().k_1m,
            session=(self._require_bindings().session_all if security.market == "US" else None),
        )
        if isinstance(rows, ProviderResult):
            return cast(ProviderResult[tuple[MinuteBar, ...]], rows)
        try:
            bars_by_interval: dict[datetime, MinuteBar] = {}
            for row in rows:
                interval_start = _provider_datetime(row["time_key"], security)
                interval_end = interval_start + timedelta(minutes=1)
                if interval_start < window_start:
                    continue
                if interval_end > retrieved_at:
                    continue
                bars_by_interval[interval_start] = _minute_bar(
                    row, security, interval_start, interval_end, retrieved_at
                )
            bars = tuple(bars_by_interval[key] for key in sorted(bars_by_interval))
        except (KeyError, TypeError, ValueError) as exc:
            return _failure(DataAvailabilityStatus.INVALID, retrieved_at, _safe_reason(exc))
        if not bars:
            return _failure(
                DataAvailabilityStatus.UNAVAILABLE,
                retrieved_at,
                "no completed 1-minute bars in requested lookback window",
            )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            retrieved_at=retrieved_at,
            data=bars,
        )

    def get_trading_days(
        self, market: str, start_date: date, end_date: date
    ) -> ProviderResult[tuple[TradingDay, ...]]:
        normalized_market = market.strip().upper()
        if normalized_market not in {"US", "HK"}:
            raise ValueError("trading calendar supports only US and HK")
        if end_date < start_date:
            raise ValueError("trading calendar end date must not precede start date")
        retrieved_at = self._retrieved_at()
        bindings = self._require_bindings()
        provider_market = (
            bindings.trade_date_market_us
            if normalized_market == "US"
            else bindings.trade_date_market_hk
        )
        try:
            ret, payload = self._require_context().request_trading_days(
                market=provider_market,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
            )
        except Exception as exc:
            return _provider_failure(retrieved_at, exc)
        if ret != bindings.ret_ok:
            return _provider_failure(retrieved_at, payload)
        rows = _rows(payload, retrieved_at)
        if isinstance(rows, ProviderResult):
            return cast(ProviderResult[tuple[TradingDay, ...]], rows)
        try:
            days_by_date: dict[date, TradingDay] = {}
            for row in rows:
                market_date = date.fromisoformat(str(row["time"]).strip())
                raw_type = _provider_enum_text(row["trade_date_type"])
                day_type, segments = _calendar_semantics(normalized_market, raw_type)
                days_by_date[market_date] = TradingDay(
                    market=normalized_market,
                    market_date=market_date,
                    market_timezone=(
                        "America/New_York" if normalized_market == "US" else "Asia/Hong_Kong"
                    ),
                    day_type=day_type,
                    provider_day_type=raw_type,
                    session_segments=segments,
                    provider="futu_opend_quote",
                    retrieved_at=retrieved_at,
                )
            days = tuple(days_by_date[key] for key in sorted(days_by_date))
        except (KeyError, TypeError, ValueError) as exc:
            return _failure(DataAvailabilityStatus.INVALID, retrieved_at, _safe_reason(exc))
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            retrieved_at=retrieved_at,
            data=days,
        )

    def _call(self, method_name: str, code_list: list[str]) -> object | ProviderResult[Any]:
        retrieved_at = self._retrieved_at()
        try:
            method = getattr(self._require_context(), method_name)
            ret, payload = method(code_list)
        except Exception as exc:
            return _provider_failure(retrieved_at, exc)
        if ret != self._require_bindings().ret_ok:
            return _provider_failure(retrieved_at, payload)
        return cast(object, payload)

    def _history_rows(
        self,
        security: MarketDataSecurity,
        *,
        start: date,
        end: date,
        ktype: object,
        session: object | None = None,
    ) -> list[Mapping[str, object]] | ProviderResult[Any]:
        retrieved_at = self._retrieved_at()
        page_req_key: object | None = None
        combined_rows: list[Mapping[str, object]] = []
        for _page_number in range(1, MAX_HISTORY_PAGES + 1):
            try:
                if session is None:
                    ret, payload, next_page_req_key = self._require_context().request_history_kline(
                        code=futu_code_for(security),
                        start=start.isoformat(),
                        end=end.isoformat(),
                        ktype=ktype,
                        autype=self._require_bindings().au_qfq,
                        max_count=1000,
                        page_req_key=page_req_key,
                    )
                else:
                    ret, payload, next_page_req_key = self._require_context().request_history_kline(
                        code=futu_code_for(security),
                        start=start.isoformat(),
                        end=end.isoformat(),
                        ktype=ktype,
                        autype=self._require_bindings().au_qfq,
                        max_count=1000,
                        page_req_key=page_req_key,
                        session=session,
                    )
            except Exception as exc:
                return _provider_failure(retrieved_at, exc)
            if ret != self._require_bindings().ret_ok:
                return _provider_failure(retrieved_at, payload)
            page_rows = _rows(payload, retrieved_at)
            if isinstance(page_rows, ProviderResult):
                return page_rows
            combined_rows.extend(page_rows)
            if next_page_req_key is None:
                return combined_rows
            page_req_key = next_page_req_key
        return _failure(
            DataAvailabilityStatus.PROVIDER_ERROR,
            retrieved_at,
            f"historical K-line pagination exceeded {MAX_HISTORY_PAGES} pages",
        )

    def _retrieved_at(self) -> datetime:
        value = self._now()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("adapter clock must return a timezone-aware instant")
        return value.astimezone(UTC)

    def _require_context(self) -> FutuQuoteContext:
        if self._context is None:
            raise RuntimeError("quote context is closed")
        return self._context

    def _require_bindings(self) -> FutuSdkBindings:
        if self._bindings is None:
            raise RuntimeError("quote context is closed")
        return self._bindings


def _rows(
    payload: object, retrieved_at: datetime
) -> list[Mapping[str, object]] | ProviderResult[Any]:
    if payload is None:
        return _failure(DataAvailabilityStatus.UNAVAILABLE, retrieved_at, "empty provider result")
    if isinstance(payload, Sequence) and not isinstance(payload, str | bytes | bytearray):
        raw_rows = list(payload)
    elif hasattr(payload, "to_dict"):
        raw_rows = cast(TabularResponse, payload).to_dict(orient="records")
    else:
        return _failure(
            DataAvailabilityStatus.INVALID,
            retrieved_at,
            "provider result is not tabular",
        )
    if not raw_rows:
        return _failure(DataAvailabilityStatus.UNAVAILABLE, retrieved_at, "empty provider result")
    if not all(isinstance(row, Mapping) for row in raw_rows):
        return _failure(DataAvailabilityStatus.INVALID, retrieved_at, "provider rows are malformed")
    return cast(list[Mapping[str, object]], raw_rows)


def _matching_row(rows: Sequence[Mapping[str, object]], code: str) -> Mapping[str, object]:
    for row in rows:
        if str(row.get("code", "")).strip().upper() == code:
            return row
    raise ValueError(f"provider result omitted {code}")


def _provider_datetime(value: object, security: MarketDataSecurity) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.strip())
        except ValueError as exc:
            raise ValueError("provider timestamp is invalid") from exc
    else:
        raise ValueError("provider timestamp is invalid")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(security.market_timezone))
    return parsed.astimezone(UTC)


def _decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} is invalid")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} is invalid") from exc
    if not result.is_finite():
        raise ValueError(f"{field_name} is invalid")
    return result


def _ohlcv(row: Mapping[str, object]) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        _decimal(row["open"], "open"),
        _decimal(row["high"], "high"),
        _decimal(row["low"], "low"),
        _decimal(row["close"], "close"),
        _decimal(row["volume"], "volume"),
    )


def _daily_bar(
    row: Mapping[str, object], security: MarketDataSecurity, retrieved_at: datetime
) -> DailyBar:
    provider_time = _provider_datetime(row["time_key"], security)
    open_value, high, low, close, volume = _ohlcv(row)
    return DailyBar(
        security=security.display_symbol,
        session_date=provider_time.astimezone(ZoneInfo(security.market_timezone)).date(),
        provider_time=provider_time,
        open=open_value,
        high=high,
        low=low,
        close=close,
        volume=volume,
        is_completed=True,
        retrieved_at=retrieved_at,
    )


def _minute_bar(
    row: Mapping[str, object],
    security: MarketDataSecurity,
    interval_start: datetime,
    interval_end: datetime,
    retrieved_at: datetime,
) -> MinuteBar:
    open_value, high, low, close, volume = _ohlcv(row)
    return MinuteBar(
        security=security.display_symbol,
        interval_start=interval_start,
        interval_end=interval_end,
        open=open_value,
        high=high,
        low=low,
        close=close,
        volume=volume,
        is_completed=True,
        retrieved_at=retrieved_at,
    )


def _market_state(raw_state: str) -> CanonicalMarketState:
    normalized = raw_state.upper()
    exact = {
        "MORNING": CanonicalMarketState.OPEN,
        "AFTERNOON": CanonicalMarketState.OPEN,
        "OPEN": CanonicalMarketState.OPEN,
        "PRE_MARKET_BEGIN": CanonicalMarketState.PRE_MARKET,
        "PRE_MARKET_END": CanonicalMarketState.PRE_MARKET,
        "AFTER_HOURS_BEGIN": CanonicalMarketState.AFTER_HOURS,
        "AFTER_HOURS_END": CanonicalMarketState.AFTER_HOURS,
        "REST": CanonicalMarketState.BREAK,
        "CLOSED": CanonicalMarketState.CLOSED,
    }
    return exact.get(normalized, CanonicalMarketState.UNKNOWN)


def _provider_enum_text(value: object) -> str:
    name = getattr(value, "name", None)
    raw = str(name if isinstance(name, str) else value).strip().upper()
    if "." in raw:
        raw = raw.rsplit(".", 1)[-1]
    if not raw:
        raise ValueError("provider trading-day type is empty")
    return raw


def _calendar_semantics(
    market: str, provider_day_type: str
) -> tuple[TradingDayType, tuple[TradingSessionSegment, ...]]:
    morning = TradingSessionSegment(time(9, 30), time(12, 0))
    hk_afternoon = TradingSessionSegment(time(13, 0), time(16, 0))
    if provider_day_type == "WHOLE":
        if market == "US":
            return TradingDayType.FULL, (TradingSessionSegment(time(9, 30), time(16, 0)),)
        return TradingDayType.FULL, (morning, hk_afternoon)
    if provider_day_type == "MORNING":
        if market == "US":
            return (
                TradingDayType.MORNING_ONLY,
                (TradingSessionSegment(time(9, 30), time(13, 0)),),
            )
        return TradingDayType.MORNING_ONLY, (morning,)
    if provider_day_type == "AFTERNOON":
        if market == "HK":
            return TradingDayType.AFTERNOON_ONLY, (hk_afternoon,)
        return TradingDayType.AFTERNOON_ONLY, ()
    return TradingDayType.UNKNOWN, ()


def _regular_session_is_closed(
    security: MarketDataSecurity,
    provider_state: str,
) -> bool:
    normalized = provider_state.strip().upper()
    if security.market == "US":
        return normalized in {
            "AFTER_HOURS_BEGIN",
            "AFTER_HOURS_END",
            "OVERNIGHT",
            "CLOSED",
        }
    if security.market == "HK":
        return normalized == "CLOSED"
    return False


def _provider_failure(retrieved_at: datetime, error: object) -> ProviderResult[Any]:
    reason = _safe_reason(error)
    normalized = reason.lower()
    if any(marker in normalized for marker in ("permission", "entitlement", "data right")):
        status = DataAvailabilityStatus.NOT_ENTITLED
    elif any(
        marker in normalized
        for marker in ("connection refused", "not connected", "connect failed", "timed out")
    ):
        status = DataAvailabilityStatus.UNAVAILABLE
    else:
        status = DataAvailabilityStatus.PROVIDER_ERROR
    return _failure(status, retrieved_at, reason)


def _failure(
    status: DataAvailabilityStatus, retrieved_at: datetime, reason: str
) -> ProviderResult[Any]:
    return ProviderResult(status=status, retrieved_at=retrieved_at, reason=reason)


def _safe_reason(error: object) -> str:
    text = str(error).strip()
    return text[:500] if text else type(error).__name__
