"""Current provider schedules, not invented bars or historical availability."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from ai_infra_quant.application.observed_calendar import (
    ScheduledCalendarMetadata,
    ScheduledTradingDays,
)
from ai_infra_quant.application.paqs_q_product_input import adapt_snapshot
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import TradingDayType
from ai_infra_quant.core.strategy.paqs_q.event_calendar import qualify
from tests.unit.test_futu_quote_adapter import FakeQuoteContext, _adapter
from tests.unit.test_paqs_q_product_input import CLOSE, NOW, fixture_capture


def scheduled_capture():
    snapshot, source, _ = fixture_capture()
    calendar = source.calendar
    return snapshot, replace(
        source,
        calendar=ScheduledCalendarMetadata(
            status=calendar.status,
            provider=calendar.provider,
            retrieved_at=calendar.retrieved_at,
            trading_days=calendar.trading_days,
            coverage_start=date(2026, 9, 21),
            coverage_end=date(2026, 9, 27),
            schedule_basis="SYNTHETIC_EXHAUSTIVE_SCHEDULE",
        ),
    )


def test_bounded_schedule_complement_unblocks_w1_without_changing_history_claims():
    snapshot, source = scheduled_capture()
    result = adapt_snapshot(snapshot, source)
    w1 = result.multi_input.w1
    assert w1 is not None
    assert len(w1.calendar) == 7
    assert w1.bars[0].completed_at == CLOSE  # last OPEN, not nominal Sunday
    assert [fact.kind for fact in w1.calendar] == ["OPEN"] + ["CLOSED"] * 6
    assert all(fact.available_at is None and fact.retrieved_at == NOW for fact in w1.calendar)
    assert "OBSERVATIONAL_NOT_POINT_IN_TIME" in qualify(w1)
    assert "CLOSED_DAY_FACTS_UNAVAILABLE" not in result.diagnostics
    assert "SCHEDULED_CALENDAR_EXCLUDES_EMERGENCY_CLOSURES" in result.diagnostics
    assert result.multi_input.entry_references == ()
    assert "calendar_schedule_evidence" in w1.payload()["provenance"]
    with pytest.raises(ValueError, match="STRICT_ADJUSTMENT_UNPROVEN"):
        qualify(replace(w1, mode="AS_OF"))
    # Isolate the calendar gate with explicitly synthetic, timely price evidence.
    synthetic_prices = tuple(
        replace(b, adjustment="SYNTHETIC", available_at=b.completed_at) for b in w1.bars
    )
    with pytest.raises(ValueError, match="STRICT_CALENDAR_UNPROVEN"):
        qualify(replace(w1, mode="AS_OF", bars=synthetic_prices))


def test_unbounded_old_capture_stays_insufficient_and_unknown_is_not_closed():
    snapshot, old, _ = fixture_capture()
    assert len(adapt_snapshot(snapshot, old).multi_input.w1.calendar) == 1
    snapshot, source = scheduled_capture()
    unknown = replace(
        source.calendar.trading_days[0], day_type=TradingDayType.UNKNOWN, session_segments=()
    )
    source = replace(source, calendar=replace(source.calendar, trading_days=(unknown,)))
    result = adapt_snapshot(snapshot, source)
    assert result.multi_input.d1 is None and result.multi_input.w1 is None
    assert all(fact.day != unknown.market_date for fact in result.multi_input.m30.calendar)


def test_future_or_failed_calendar_never_completes_schedule():
    snapshot, source = scheduled_capture()
    # A source retrieval after the snapshot is rejected as a mismatched capture.
    future = replace(
        source, calendar=replace(source.calendar, retrieved_at=NOW + timedelta(days=1))
    )
    with pytest.raises(ValueError, match="CAPTURE_MISMATCH"):
        adapt_snapshot(snapshot, future)
    failed = replace(
        source, calendar=replace(source.calendar, status=DataAvailabilityStatus.INVALID)
    )
    assert not any(
        f.kind == "CLOSED" for f in adapt_snapshot(snapshot, failed).multi_input.w1.calendar
    )


def test_calendar_adapter_retains_scope_and_rejects_invalid_rows():
    context = FakeQuoteContext()
    with _adapter(context) as adapter:
        result = adapter.get_trading_days("US", date(2026, 8, 30), date(2026, 9, 6))
        assert isinstance(result, ScheduledTradingDays)
        assert (result.coverage_start, result.coverage_end) == (date(2026, 8, 30), date(2026, 9, 6))
        assert "EXCLUDES_EMERGENCY_CLOSURES" in result.schedule_basis
        for rows in (
            [{"time": "2026-08-29", "trade_date_type": "WHOLE"}],
            [{"time": "2026-09-01", "trade_date_type": "WHOLE"}] * 2,
        ):
            context.calendar_result = (0, rows)
            rejected = adapter.get_trading_days("US", date(2026, 8, 30), date(2026, 9, 6))
            assert rejected.status is DataAvailabilityStatus.INVALID and rejected.data is None
