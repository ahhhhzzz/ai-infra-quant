from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import (
    DailyBar,
    MarketDataSecurity,
    MinuteBar,
    QuoteSnapshot,
)
from ai_infra_quant.integrations.futu_quote.adapter import FutuQuoteAdapter, FutuSdkBindings
from ai_infra_quant.integrations.futu_quote.symbols import POC_SECURITIES, futu_code_for

FIXED_NOW = datetime(2026, 9, 1, 14, 35, 30, tzinfo=UTC)
US_AVGO = POC_SECURITIES[0]


class FakeTable:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    def to_dict(self, orient: str) -> list[dict[str, object]]:
        assert orient == "records"
        return self.rows


class FakeQuoteContext:
    def __init__(self) -> None:
        self.closed = False
        self.snapshot_result: tuple[object, object] = (
            0,
            FakeTable(
                [
                    {
                        "code": "US.AVGO",
                        "update_time": "2026-09-01 10:35:12",
                        "last_price": 351.125,
                    }
                ]
            ),
        )
        self.state_result: tuple[object, object] = (
            0,
            FakeTable([{"code": "US.AVGO", "market_state": "MORNING"}]),
        )
        self.daily_result: tuple[object, object, object] = (
            0,
            FakeTable([_bar("2026-08-31 00:00:00", close="350.25")]),
            None,
        )
        self.minute_result: tuple[object, object, object] = (
            0,
            FakeTable(
                [
                    _bar("2026-09-01 10:34:00", close="350.25"),
                    _bar("2026-09-01 10:35:00", close="351.00"),
                ]
            ),
            None,
        )

    def get_market_snapshot(self, code_list: list[str]) -> tuple[object, object]:
        assert code_list == ["US.AVGO"]
        return self.snapshot_result

    def get_market_state(self, code_list: list[str]) -> tuple[object, object]:
        assert code_list == ["US.AVGO"]
        return self.state_result

    def request_history_kline(
        self,
        code: str,
        start: str,
        end: str,
        ktype: object,
        autype: object,
        max_count: int,
    ) -> tuple[object, object, object]:
        assert code == "US.AVGO"
        assert autype == "QFQ"
        assert max_count == 1000
        assert start <= end
        return self.daily_result if ktype == "K_DAY" else self.minute_result

    def close(self) -> None:
        self.closed = True


def _bar(timestamp: str, *, close: str) -> dict[str, object]:
    return {
        "code": "US.AVGO",
        "time_key": timestamp,
        "open": "349.10",
        "high": "352.20",
        "low": "348.80",
        "close": close,
        "volume": 12345.0,
    }


def _adapter(
    context: FakeQuoteContext,
    *,
    now: Callable[[], datetime] = lambda: FIXED_NOW,
) -> FutuQuoteAdapter:
    bindings = FutuSdkBindings(
        context_factory=lambda **_kwargs: context,
        ret_ok=0,
        k_day="K_DAY",
        k_1m="K_1M",
        au_qfq="QFQ",
        sdk_version="test-sdk",
    )
    return FutuQuoteAdapter("127.0.0.1", 11111, bindings_loader=lambda: bindings, now=now)


def test_explicit_canonical_symbol_mapping() -> None:
    assert [security.display_symbol for security in POC_SECURITIES] == [
        "US.AVGO",
        "US.VRT",
        "HK.09698",
    ]
    assert [futu_code_for(security) for security in POC_SECURITIES] == [
        "US.AVGO",
        "US.VRT",
        "HK.09698",
    ]
    unsupported = MarketDataSecurity("US", "NVDA", "USD", "America/New_York")
    with pytest.raises(ValueError, match="unsupported"):
        futu_code_for(unsupported)


def test_canonical_results_do_not_expose_sdk_objects_and_use_decimal() -> None:
    context = FakeQuoteContext()
    with _adapter(context) as adapter:
        quote_result = adapter.get_latest_quote(US_AVGO)
        daily_result = adapter.get_daily_bars(US_AVGO)

    assert quote_result.status is DataAvailabilityStatus.AVAILABLE
    assert isinstance(quote_result.data, QuoteSnapshot)
    assert quote_result.data.price == Decimal("351.125")
    assert isinstance(quote_result.data.price, Decimal)
    assert quote_result.data.latest_quote_at == datetime(2026, 9, 1, 14, 35, 12, tzinfo=UTC)
    assert isinstance(daily_result.data, tuple)
    assert isinstance(daily_result.data[0], DailyBar)
    assert all(
        isinstance(value, Decimal)
        for value in (
            daily_result.data[0].open,
            daily_result.data[0].high,
            daily_result.data[0].low,
            daily_result.data[0].close,
            daily_result.data[0].volume,
        )
    )
    assert not isinstance(quote_result.data, FakeTable)
    assert not isinstance(daily_result.data, FakeTable)
    assert context.closed is True


def test_unfinished_minute_is_excluded_and_latest_is_not_daily_close() -> None:
    context = FakeQuoteContext()
    with _adapter(context) as adapter:
        quote_result = adapter.get_latest_quote(US_AVGO)
        minute_result = adapter.get_current_session_minute_bars(US_AVGO)
        daily_result = adapter.get_daily_bars(US_AVGO)

    assert isinstance(minute_result.data, tuple)
    assert len(minute_result.data) == 1
    minute = minute_result.data[0]
    assert isinstance(minute, MinuteBar)
    assert minute.interval_start == datetime(2026, 9, 1, 14, 34, tzinfo=UTC)
    assert minute.interval_end == datetime(2026, 9, 1, 14, 35, tzinfo=UTC)
    assert minute.is_completed is True
    assert isinstance(quote_result.data, QuoteSnapshot)
    assert not hasattr(quote_result.data, "close")
    assert isinstance(daily_result.data, tuple)
    assert quote_result.data.price != daily_result.data[0].close


@pytest.mark.parametrize(
    ("provider_result", "expected_status", "reason_fragment"),
    [
        ((0, FakeTable([])), DataAvailabilityStatus.UNAVAILABLE, "empty"),
        ((1, "No permission for market data"), DataAvailabilityStatus.NOT_ENTITLED, "permission"),
        ((1, "provider internal failure"), DataAvailabilityStatus.PROVIDER_ERROR, "failure"),
        ((0, FakeTable([{"code": "US.AVGO"}])), DataAvailabilityStatus.INVALID, "update_time"),
    ],
)
def test_partial_empty_error_and_invalid_responses_are_explicit(
    provider_result: tuple[object, object],
    expected_status: DataAvailabilityStatus,
    reason_fragment: str,
) -> None:
    context = FakeQuoteContext()
    context.snapshot_result = provider_result
    with _adapter(context) as adapter:
        result = adapter.get_latest_quote(US_AVGO)
    assert result.status is expected_status
    assert result.data is None
    assert result.reason is not None
    assert reason_fragment.lower() in result.reason.lower()


def test_quote_context_closes_when_body_raises() -> None:
    context = FakeQuoteContext()
    with pytest.raises(RuntimeError, match="test failure"), _adapter(context):
        raise RuntimeError("test failure")
    assert context.closed is True


def test_quote_context_closes_after_provider_method_failure() -> None:
    context = FakeQuoteContext()

    def fail(_code_list: list[str]) -> tuple[object, object]:
        raise ConnectionRefusedError("connection refused")

    context.get_market_snapshot = fail  # type: ignore[method-assign,assignment]
    with _adapter(context) as adapter:
        result = adapter.get_latest_quote(US_AVGO)
    assert result.status is DataAvailabilityStatus.UNAVAILABLE
    assert context.closed is True


def test_provider_status_is_explicit_before_and_during_context() -> None:
    context = FakeQuoteContext()
    adapter = _adapter(context)
    assert adapter.provider_status().status is DataAvailabilityStatus.UNAVAILABLE
    with adapter:
        result = adapter.provider_status()
        assert result.status is DataAvailabilityStatus.AVAILABLE
        assert result.data is not None
        assert result.data.quote_context_open is True
        assert result.data.sdk_version == "test-sdk"
