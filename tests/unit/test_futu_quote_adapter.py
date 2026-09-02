from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import (
    DailyBar,
    MarketDataSecurity,
    MinuteBar,
    QuoteSnapshot,
    TradingDayType,
)
from ai_infra_quant.integrations.futu_quote import adapter as adapter_module
from ai_infra_quant.integrations.futu_quote.adapter import (
    FutuQuoteAdapter,
    FutuSdkBindings,
    load_futu_sdk,
)
from ai_infra_quant.integrations.futu_quote.symbols import POC_SECURITIES, futu_code_for

FIXED_NOW = datetime(2026, 9, 1, 14, 35, 30, tzinfo=UTC)
US_AVGO = POC_SECURITIES[0]
HK_09698 = POC_SECURITIES[2]


class FakeTable:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    def to_dict(self, orient: str) -> list[dict[str, object]]:
        assert orient == "records"
        return self.rows


class FakeQuoteContext:
    def __init__(self) -> None:
        self.closed = False
        self.history_calls: list[dict[str, object]] = []
        self.history_pages: dict[tuple[object, object | None], tuple[object, object, object]] = {}
        self.expected_code = "US.AVGO"
        self.snapshot_result: tuple[object, object] = (
            0,
            FakeTable(
                [
                    {
                        "code": "US.AVGO",
                        "update_time": "2026-09-01 10:35:12",
                        "last_price": 351.125,
                        "equity_valid": True,
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
        self.calendar_result: tuple[object, object] = (
            0,
            [
                {"time": "2026-08-31", "trade_date_type": "WHOLE"},
                {"time": "2026-09-01", "trade_date_type": "MORNING"},
            ],
        )
        self.calendar_calls: list[dict[str, object]] = []

    def get_market_snapshot(self, code_list: list[str]) -> tuple[object, object]:
        assert code_list == [self.expected_code]
        return self.snapshot_result

    def get_market_state(self, code_list: list[str]) -> tuple[object, object]:
        assert code_list == [self.expected_code]
        return self.state_result

    def request_history_kline(
        self,
        code: str,
        start: str,
        end: str,
        ktype: object,
        autype: object,
        max_count: int,
        page_req_key: object | None,
        session: object = "DEFAULT",
    ) -> tuple[object, object, object]:
        assert code == self.expected_code
        assert autype == "QFQ"
        assert max_count == 1000
        assert start <= end
        self.history_calls.append(
            {
                "code": code,
                "start": start,
                "end": end,
                "ktype": ktype,
                "page_req_key": page_req_key,
                "session": session,
            }
        )
        page = self.history_pages.get((ktype, page_req_key))
        if page is not None:
            return page
        return self.daily_result if ktype == "K_DAY" else self.minute_result

    def request_trading_days(self, market: object, start: str, end: str) -> tuple[object, object]:
        self.calendar_calls.append({"market": market, "start": start, "end": end})
        return self.calendar_result

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
        session_all="ALL",
        trade_date_market_us="US_CALENDAR",
        trade_date_market_hk="HK_CALENDAR",
        sdk_version="test-sdk",
    )
    return FutuQuoteAdapter("127.0.0.1", 11111, bindings_loader=lambda: bindings, now=now)


def _configure_daily_result(
    context: FakeQuoteContext,
    security: MarketDataSecurity,
    provider_state: str,
    timestamps: list[str],
) -> None:
    context.expected_code = security.display_symbol
    context.state_result = (
        0,
        FakeTable([{"code": security.display_symbol, "market_state": provider_state}]),
    )
    context.daily_result = (
        0,
        FakeTable([_bar(timestamp, close="350.25") for timestamp in timestamps]),
        None,
    )


def test_dynamic_canonical_symbol_mapping_preserves_original_symbols() -> None:
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
    assert futu_code_for(unsupported) == "US.NVDA"
    assert futu_code_for(MarketDataSecurity("HK", "700", "HKD", "Asia/Hong_Kong")) == "HK.00700"


def test_canonical_results_do_not_expose_sdk_objects_and_use_decimal() -> None:
    context = FakeQuoteContext()
    with _adapter(context) as adapter:
        quote_result = adapter.get_latest_quote(US_AVGO)
        daily_result = adapter.get_daily_bars(US_AVGO)

    assert quote_result.status is DataAvailabilityStatus.AVAILABLE
    assert isinstance(quote_result.data, QuoteSnapshot)
    assert quote_result.data.price == Decimal("351.125")
    assert isinstance(quote_result.data.price, Decimal)
    assert quote_result.data.is_equity is True
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
        minute_result = adapter.get_recent_minute_bars(US_AVGO, 1)
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


def test_hk_current_day_daily_bar_is_excluded_during_market_hours() -> None:
    context = FakeQuoteContext()
    _configure_daily_result(
        context,
        HK_09698,
        "AFTERNOON",
        ["2026-08-31 00:00:00", "2026-09-01 00:00:00"],
    )
    hk_market_hours = datetime(2026, 9, 1, 4, 0, tzinfo=UTC)

    with _adapter(context, now=lambda: hk_market_hours) as adapter:
        result = adapter.get_daily_bars(HK_09698)

    assert isinstance(result.data, tuple)
    assert [bar.session_date.isoformat() for bar in result.data] == ["2026-08-31"]


def test_hk_current_day_daily_bar_is_included_after_authoritative_close() -> None:
    context = FakeQuoteContext()
    _configure_daily_result(
        context,
        HK_09698,
        "CLOSED",
        ["2026-08-31 00:00:00", "2026-09-01 00:00:00"],
    )
    hk_after_close = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)

    with _adapter(context, now=lambda: hk_after_close) as adapter:
        result = adapter.get_daily_bars(HK_09698)

    assert isinstance(result.data, tuple)
    assert [bar.session_date.isoformat() for bar in result.data] == [
        "2026-08-31",
        "2026-09-01",
    ]
    current_bar = result.data[-1]
    assert current_bar.provider_time == datetime(2026, 8, 31, 16, 0, tzinfo=UTC)
    assert current_bar.provider_time.date() != current_bar.session_date


@pytest.mark.parametrize(
    ("provider_state", "current_session_is_completed"),
    [
        ("AFTERNOON", False),
        ("AFTER_HOURS_BEGIN", True),
        ("AFTER_HOURS_END", True),
        ("OVERNIGHT", True),
    ],
)
def test_us_current_day_daily_completion_uses_regular_session_provider_state(
    provider_state: str,
    current_session_is_completed: bool,
) -> None:
    context = FakeQuoteContext()
    _configure_daily_result(
        context,
        US_AVGO,
        provider_state,
        ["2026-08-31 00:00:00", "2026-09-01 00:00:00"],
    )

    with _adapter(context) as adapter:
        market_status = adapter.get_market_status(US_AVGO)
        result = adapter.get_daily_bars(US_AVGO)

    assert market_status.data is not None
    assert market_status.data.provider_state == provider_state
    assert isinstance(result.data, tuple)
    expected_sessions = ["2026-08-31"]
    if current_session_is_completed:
        expected_sessions.append("2026-09-01")
    assert [bar.session_date.isoformat() for bar in result.data] == expected_sessions


def test_us_daily_completion_is_not_inferred_from_wall_clock_alone() -> None:
    context = FakeQuoteContext()
    _configure_daily_result(
        context,
        US_AVGO,
        "AFTERNOON",
        ["2026-08-31 00:00:00", "2026-09-01 00:00:00"],
    )
    after_regular_close_by_clock = datetime(2026, 9, 1, 21, 0, tzinfo=UTC)

    with _adapter(context, now=lambda: after_regular_close_by_clock) as adapter:
        result = adapter.get_daily_bars(US_AVGO)

    assert isinstance(result.data, tuple)
    assert [bar.session_date.isoformat() for bar in result.data] == ["2026-08-31"]


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


def test_futu_equity_classification_is_mapped_without_price_inference() -> None:
    context = FakeQuoteContext()
    context.snapshot_result = (
        0,
        FakeTable(
            [
                {
                    "code": "US.AVGO",
                    "update_time": "2026-09-01 10:35:12",
                    "last_price": "351.125",
                    "equity_valid": False,
                }
            ]
        ),
    )

    with _adapter(context) as adapter:
        result = adapter.get_latest_quote(US_AVGO)

    assert result.status is DataAvailabilityStatus.AVAILABLE
    assert result.data is not None
    assert result.data.price == Decimal("351.125")
    assert result.data.is_equity is False


@pytest.mark.parametrize("equity_valid", [None, "UNKNOWN", 1])
def test_futu_invalid_equity_classification_maps_to_unknown(equity_valid: object) -> None:
    context = FakeQuoteContext()
    context.snapshot_result = (
        0,
        FakeTable(
            [
                {
                    "code": "US.AVGO",
                    "update_time": "2026-09-01 10:35:12",
                    "last_price": "351.125",
                    "equity_valid": equity_valid,
                }
            ]
        ),
    )

    with _adapter(context) as adapter:
        result = adapter.get_latest_quote(US_AVGO)

    assert result.status is DataAvailabilityStatus.AVAILABLE
    assert result.data is not None
    assert result.data.price == Decimal("351.125")
    assert result.data.is_equity is None


def test_futu_missing_equity_classification_maps_to_unknown() -> None:
    context = FakeQuoteContext()
    context.snapshot_result = (
        0,
        FakeTable(
            [
                {
                    "code": "US.AVGO",
                    "update_time": "2026-09-01 10:35:12",
                    "last_price": "351.125",
                }
            ]
        ),
    )

    with _adapter(context) as adapter:
        result = adapter.get_latest_quote(US_AVGO)

    assert result.status is DataAvailabilityStatus.AVAILABLE
    assert result.data is not None
    assert result.data.is_equity is None


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


def test_lazy_sdk_bindings_include_official_session_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdk = SimpleNamespace(
        OpenQuoteContext=object,
        RET_OK=0,
        KLType=SimpleNamespace(K_DAY="K_DAY", K_1M="K_1M"),
        AuType=SimpleNamespace(QFQ="QFQ"),
        Session=SimpleNamespace(ALL="ALL"),
        TradeDateMarket=SimpleNamespace(US="US_CALENDAR", HK="HK_CALENDAR"),
        __version__="test-sdk",
    )
    monkeypatch.setattr(adapter_module, "import_module", lambda _name: sdk)

    bindings = load_futu_sdk()

    assert bindings.session_all == "ALL"
    assert bindings.trade_date_market_us == "US_CALENDAR"
    assert bindings.trade_date_market_hk == "HK_CALENDAR"


def test_trading_calendar_maps_known_and_unknown_provider_rows() -> None:
    context = FakeQuoteContext()
    context.calendar_result = (
        0,
        [
            {"time": "2026-08-31", "trade_date_type": "WHOLE"},
            {"time": "2026-09-01", "trade_date_type": "SURPRISE"},
        ],
    )
    with _adapter(context) as adapter:
        result = adapter.get_trading_days("US", date(2026, 8, 31), date(2026, 9, 1))

    assert result.status is DataAvailabilityStatus.AVAILABLE
    assert result.data is not None
    assert result.data[0].day_type is TradingDayType.FULL
    assert result.data[0].market_timezone == "America/New_York"
    assert result.data[0].session_segments[0].start.isoformat() == "09:30:00"
    assert result.data[1].day_type is TradingDayType.UNKNOWN
    assert result.data[1].session_segments == ()
    assert context.calendar_calls == [
        {"market": "US_CALENDAR", "start": "2026-08-31", "end": "2026-09-01"}
    ]


def test_trading_calendar_provider_error_is_explicit() -> None:
    context = FakeQuoteContext()
    context.calendar_result = (1, "No permission for trading calendar")
    with _adapter(context) as adapter:
        result = adapter.get_trading_days("HK", date(2026, 8, 31), date(2026, 9, 1))
    assert result.status is DataAvailabilityStatus.NOT_ENTITLED
    assert result.data is None


def test_us_minute_history_uses_session_all_and_hk_omits_it() -> None:
    us_context = FakeQuoteContext()
    with _adapter(us_context) as adapter:
        adapter.get_recent_minute_bars(US_AVGO, 30)

    us_call = us_context.history_calls[0]
    assert us_call["session"] == "ALL"
    assert us_call["page_req_key"] is None
    assert us_call["start"] == "2026-08-01"

    hk_context = FakeQuoteContext()
    hk_context.expected_code = HK_09698.display_symbol
    with _adapter(hk_context) as adapter:
        adapter.get_recent_minute_bars(HK_09698, 30)

    hk_call = hk_context.history_calls[0]
    assert hk_call["session"] == "DEFAULT"
    assert hk_call["start"] == "2026-08-02"


def test_hk_recent_minute_history_keeps_provider_returned_multi_day_sessions() -> None:
    context = FakeQuoteContext()
    context.expected_code = HK_09698.display_symbol
    context.minute_result = (
        0,
        FakeTable(
            [
                _bar("2026-08-31 10:00:00", close="350.00"),
                _bar("2026-09-01 10:34:00", close="351.00"),
            ]
        ),
        None,
    )

    with _adapter(context) as adapter:
        result = adapter.get_recent_minute_bars(HK_09698, 2)

    assert result.status is DataAvailabilityStatus.AVAILABLE
    assert result.data is not None
    assert [
        bar.interval_start.astimezone(ZoneInfo(HK_09698.market_timezone)).date()
        for bar in result.data
    ] == [date(2026, 8, 31), date(2026, 9, 1)]
    assert context.history_calls[0]["session"] == "DEFAULT"


def test_history_paging_passes_keys_sorts_and_deduplicates() -> None:
    context = FakeQuoteContext()
    context.history_pages = {
        ("K_1M", None): (
            0,
            FakeTable(
                [
                    _bar("2026-08-31 20:01:00", close="351.00"),
                    _bar("2026-08-31 20:02:00", close="352.00"),
                ]
            ),
            b"page-2",
        ),
        ("K_1M", b"page-2"): (
            0,
            FakeTable(
                [
                    _bar("2026-08-31 20:00:00", close="350.00"),
                    _bar("2026-08-31 20:01:00", close="351.50"),
                ]
            ),
            None,
        ),
    }

    with _adapter(context) as adapter:
        result = adapter.get_recent_minute_bars(US_AVGO, 30)

    assert [call["page_req_key"] for call in context.history_calls] == [None, b"page-2"]
    assert result.status is DataAvailabilityStatus.AVAILABLE
    assert result.data is not None
    assert [bar.interval_start for bar in result.data] == sorted(
        bar.interval_start for bar in result.data
    )
    assert len(result.data) == 3
    assert result.data[1].close == Decimal("351.50")


def test_later_history_page_failure_does_not_return_partial_available() -> None:
    context = FakeQuoteContext()
    context.history_pages = {
        ("K_1M", None): (
            0,
            FakeTable([_bar("2026-08-31 20:00:00", close="350.00")]),
            "page-2",
        ),
        ("K_1M", "page-2"): (1, "provider later-page failure", None),
    }

    with _adapter(context) as adapter:
        result = adapter.get_recent_minute_bars(US_AVGO, 30)

    assert result.status is DataAvailabilityStatus.PROVIDER_ERROR
    assert result.data is None
    assert result.reason == "provider later-page failure"


def test_history_pagination_ceiling_prevents_provider_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = FakeQuoteContext()
    context.history_pages = {
        ("K_1M", None): (
            0,
            FakeTable([_bar("2026-08-31 20:00:00", close="350.00")]),
            "loop",
        ),
        ("K_1M", "loop"): (
            0,
            FakeTable([_bar("2026-08-31 20:00:00", close="350.00")]),
            "loop",
        ),
    }
    monkeypatch.setattr(adapter_module, "MAX_HISTORY_PAGES", 2)

    with _adapter(context) as adapter:
        result = adapter.get_recent_minute_bars(US_AVGO, 30)

    assert result.status is DataAvailabilityStatus.PROVIDER_ERROR
    assert result.reason == "historical K-line pagination exceeded 2 pages"
    assert len(context.history_calls) == 2


def test_rolling_minute_window_filters_boundary_and_unfinished_bar() -> None:
    context = FakeQuoteContext()
    context.minute_result = (
        0,
        FakeTable(
            [
                _bar("2026-08-02 10:34:00", close="349.00"),
                _bar("2026-08-02 10:36:00", close="350.00"),
                _bar("2026-08-31 20:00:00", close="351.00"),
                _bar("2026-09-01 10:35:00", close="352.00"),
            ]
        ),
        None,
    )

    with _adapter(context) as adapter:
        result = adapter.get_recent_minute_bars(US_AVGO, 30)

    assert result.data is not None
    assert [bar.interval_start for bar in result.data] == [
        datetime(2026, 8, 2, 14, 36, tzinfo=UTC),
        datetime(2026, 9, 1, 0, 0, tzinfo=UTC),
    ]
    assert all(bar.interval_start >= FIXED_NOW - timedelta(days=30) for bar in result.data)
    assert all(bar.interval_end <= FIXED_NOW for bar in result.data)


def test_daily_five_year_limit_pages_past_one_thousand() -> None:
    context = FakeQuoteContext()
    first_dates = [
        datetime(2022, 1, 1, tzinfo=UTC) + timedelta(days=offset) for offset in range(1000)
    ]
    second_dates = [
        datetime(2024, 9, 26, tzinfo=UTC) + timedelta(days=offset) for offset in range(400)
    ]
    context.history_pages = {
        ("K_DAY", None): (
            0,
            FakeTable(
                [_bar(value.strftime("%Y-%m-%d 00:00:00"), close="350.00") for value in first_dates]
            ),
            "daily-2",
        ),
        ("K_DAY", "daily-2"): (
            0,
            FakeTable(
                [
                    _bar(value.strftime("%Y-%m-%d 00:00:00"), close="351.00")
                    for value in second_dates
                ]
            ),
            None,
        ),
    }

    with _adapter(context) as adapter:
        result = adapter.get_daily_bars(US_AVGO, 1300)

    assert result.status is DataAvailabilityStatus.AVAILABLE
    assert result.data is not None
    assert len(result.data) == 1300
    assert len(context.history_calls) == 2
    assert result.data == tuple(sorted(result.data, key=lambda bar: bar.session_date))
