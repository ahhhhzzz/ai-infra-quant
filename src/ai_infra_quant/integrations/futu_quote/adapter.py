"""Quote-only Futu OpenD adapter with canonical, truthful result handling."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
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
)
from ai_infra_quant.integrations.futu_quote.symbols import futu_code_for


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
    ) -> tuple[object, object, object]: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class FutuSdkBindings:
    context_factory: Callable[..., FutuQuoteContext]
    ret_ok: object
    k_day: object
    k_1m: object
    au_qfq: object
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

    def get_daily_bars(self, security: MarketDataSecurity) -> ProviderResult[tuple[DailyBar, ...]]:
        retrieved_at = self._retrieved_at()
        market_today = retrieved_at.astimezone(ZoneInfo(security.market_timezone)).date()
        call = self._history_call(
            security,
            start=market_today - timedelta(days=14),
            end=market_today,
            ktype=self._require_bindings().k_day,
        )
        if isinstance(call, ProviderResult):
            return cast(ProviderResult[tuple[DailyBar, ...]], call)
        rows = _rows(call, retrieved_at)
        if isinstance(rows, ProviderResult):
            return cast(ProviderResult[tuple[DailyBar, ...]], rows)
        try:
            bars = tuple(
                _daily_bar(row, security, retrieved_at)
                for row in rows
                if _provider_datetime(row["time_key"], security).date() < market_today
            )
        except (KeyError, TypeError, ValueError) as exc:
            return _failure(DataAvailabilityStatus.INVALID, retrieved_at, _safe_reason(exc))
        if not bars:
            return _failure(
                DataAvailabilityStatus.UNAVAILABLE, retrieved_at, "no completed daily bars"
            )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE, retrieved_at=retrieved_at, data=bars
        )

    def get_current_session_minute_bars(
        self, security: MarketDataSecurity
    ) -> ProviderResult[tuple[MinuteBar, ...]]:
        retrieved_at = self._retrieved_at()
        market_today = retrieved_at.astimezone(ZoneInfo(security.market_timezone)).date()
        call = self._history_call(
            security,
            start=market_today,
            end=market_today,
            ktype=self._require_bindings().k_1m,
        )
        if isinstance(call, ProviderResult):
            return cast(ProviderResult[tuple[MinuteBar, ...]], call)
        rows = _rows(call, retrieved_at)
        if isinstance(rows, ProviderResult):
            return cast(ProviderResult[tuple[MinuteBar, ...]], rows)
        try:
            bars = []
            for row in rows:
                interval_start = _provider_datetime(row["time_key"], security)
                interval_end = interval_start + timedelta(minutes=1)
                if (
                    interval_start.astimezone(ZoneInfo(security.market_timezone)).date()
                    != market_today
                ):
                    continue
                if interval_end > retrieved_at:
                    continue
                bars.append(_minute_bar(row, security, interval_start, interval_end, retrieved_at))
        except (KeyError, TypeError, ValueError) as exc:
            return _failure(DataAvailabilityStatus.INVALID, retrieved_at, _safe_reason(exc))
        if not bars:
            return _failure(
                DataAvailabilityStatus.UNAVAILABLE,
                retrieved_at,
                "no completed current-session 1-minute bars",
            )
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            retrieved_at=retrieved_at,
            data=tuple(bars),
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

    def _history_call(
        self, security: MarketDataSecurity, *, start: date, end: date, ktype: object
    ) -> object | ProviderResult[Any]:
        retrieved_at = self._retrieved_at()
        try:
            ret, payload, _page_req_key = self._require_context().request_history_kline(
                code=futu_code_for(security),
                start=start.isoformat(),
                end=end.isoformat(),
                ktype=ktype,
                autype=self._require_bindings().au_qfq,
                max_count=1000,
            )
        except Exception as exc:
            return _provider_failure(retrieved_at, exc)
        if ret != self._require_bindings().ret_ok:
            return _provider_failure(retrieved_at, payload)
        return payload

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
