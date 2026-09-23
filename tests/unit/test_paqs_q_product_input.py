"""A product snapshot cannot manufacture historical Q evidence."""

from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_infra_quant.application.market_data_queries import MarketStateView
from ai_infra_quant.application.paqs_input_queries import PaqsInputAcquisition
from ai_infra_quant.application.paqs_market_snapshot_queries import PaqsMarketSnapshotQueries
from ai_infra_quant.application.paqs_q_product_input import adapt_snapshot
from ai_infra_quant.application.paqs_q_setup_artifacts import run as run_setup
from ai_infra_quant.core.domain.enums import (
    DataAvailabilityStatus,
    InstrumentType,
    RecordSource,
    SnapshotQualityStatus,
    TradabilityStatus,
    VerificationStatus,
)
from ai_infra_quant.core.domain.market_data import (
    DailyBar,
    ProviderResult,
    TradingDay,
    TradingDayType,
    TradingSessionSegment,
)
from ai_infra_quant.core.domain.paqs_input import (
    AdjustmentBasis,
    AdjustmentMetadata,
    CalendarMetadata,
    DerivedBar,
    DerivedCoverage,
    DerivedTimeframe,
    PaqsInputBundle,
    SourceCoverage,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import build_paqs_market_snapshot
from ai_infra_quant.core.domain.security import Security

NOW = datetime(2026, 9, 23, 20, tzinfo=UTC)
OPEN = datetime(2026, 9, 21, 13, 30, tzinfo=UTC)
CLOSE = datetime(2026, 9, 21, 20, tzinfo=UTC)
SECURITY_ID = "00000000-0000-4000-8000-000000000001"
PROVIDER = "test-provider"


def fixture_capture() -> tuple[object, PaqsInputBundle, Security]:
    security = Security(
        id=SECURITY_ID,
        market="US",
        symbol="AVGO",
        currency="USD",
        display_name="Test",
        instrument_type=InstrumentType.EQUITY,
        enabled=True,
        record_source=RecordSource.SYSTEM_SEED,
        verification_status=VerificationStatus.SYSTEM_SEED_UNVERIFIED,
        tradability_status=TradabilityStatus.UNVERIFIED,
        metadata_status=DataAvailabilityStatus.UNAVAILABLE,
        created_at=NOW,
        updated_at=NOW,
        market_timezone="America/New_York",
    )
    prices = dict(
        open=Decimal("100"),
        high=Decimal("102"),
        low=Decimal("99"),
        close=Decimal("101"),
        volume=Decimal("1000"),
    )
    daily = DailyBar(
        security="US.AVGO",
        session_date=date(2026, 9, 21),
        provider_time=CLOSE,
        is_completed=True,
        retrieved_at=NOW,
        **prices,
    )
    week = DerivedBar(
        security="US.AVGO",
        timeframe=DerivedTimeframe.W1,
        interval_start=datetime(2026, 9, 21, 4, tzinfo=UTC),
        interval_end=datetime(2026, 9, 28, 4, tzinfo=UTC),
        market_timezone="America/New_York",
        session_type=None,
        source_bar_count=1,
        expected_source_bar_count=1,
        coverage=DerivedCoverage.COMPLETE,
        is_completed=True,
        **prices,
    )
    m30 = DerivedBar(
        security="US.AVGO",
        timeframe=DerivedTimeframe.M30,
        interval_start=OPEN,
        interval_end=OPEN + timedelta(minutes=30),
        market_timezone="America/New_York",
        session_type="REGULAR",
        source_bar_count=30,
        expected_source_bar_count=30,
        coverage=DerivedCoverage.COMPLETE,
        is_completed=True,
        **prices,
    )
    day = TradingDay(
        market="US",
        market_date=date(2026, 9, 21),
        market_timezone="America/New_York",
        day_type=TradingDayType.FULL,
        provider_day_type="FULL",
        provider=PROVIDER,
        retrieved_at=NOW,
        session_segments=(TradingSessionSegment(time(9, 30), time(16)),),
    )
    bundle = PaqsInputBundle(
        security_id=SECURITY_ID,
        market="US",
        symbol="AVGO",
        market_timezone="America/New_York",
        provider=PROVIDER,
        as_of_timestamp=NOW,
        completed_w1_bars=(week,),
        completed_d1_bars=(daily,),
        completed_30m_bars=(m30,),
        calendar=CalendarMetadata(DataAvailabilityStatus.AVAILABLE, PROVIDER, NOW, (day,)),
        adjustment=AdjustmentMetadata(AdjustmentBasis.PROVIDER_QFQ_CURRENT, NOW, False),
        data_quality=SnapshotQualityStatus.COMPLETE,
        warnings=(),
        source_coverage=SourceCoverage(1, 1, 0, 30, 1, 0),
    )
    no_quote = ProviderResult(
        status=DataAvailabilityStatus.UNAVAILABLE,
        provider=PROVIDER,
        retrieved_at=NOW,
        reason="not fetched",
    )
    snapshot = build_paqs_market_snapshot(
        bundle=bundle,
        security=security,
        quote_result=no_quote,
        market_state_result=no_quote,
        d1_source_status=DataAvailabilityStatus.AVAILABLE,
        minute_source_status=DataAvailabilityStatus.AVAILABLE,
        created_at=NOW,
    )
    return snapshot, bundle, security


def test_observational_adapter_preserves_known_facts_and_refuses_open_backfill() -> None:
    snapshot, bundle, _ = fixture_capture()
    adapted = adapt_snapshot(snapshot, bundle)
    assert adapted.snapshot_hash == snapshot.snapshot_hash
    assert adapted.multi_input.entry_references == ()
    assert "CLOSED_DAY_FACTS_UNAVAILABLE" in adapted.diagnostics
    assert "INDEPENDENT_M30_OPEN_REFERENCE_MISSING" in adapted.diagnostics
    assert "CURRENT_QFQ_NOT_POINT_IN_TIME" in adapted.diagnostics
    assert any(x.startswith("CALENDAR_DATE_FACTS_MISSING:") for x in adapted.diagnostics)
    w1, d1, m30 = adapted.multi_input.w1, adapted.multi_input.d1, adapted.multi_input.m30
    assert w1 is not None and d1 is not None and m30 is not None
    assert all(item.mode == "OBSERVATIONAL" for item in (w1, d1, m30))
    assert all(item.snapshot_identity == snapshot.snapshot_hash for item in (w1, d1, m30))
    assert w1.bars[0].completed_at == CLOSE
    assert d1.bars[0].retrieved_at == NOW
    assert m30.bars[0].open == Decimal("100")
    assert all(bar.available_at is None for item in (w1, d1, m30) for bar in item.bars)
    assert all(fact.available_at is None for fact in w1.calendar)
    assert {fact.kind for fact in w1.calendar} == {"OPEN"}
    result = run_setup(adapted.multi_input, Path(__file__).resolve().parents[2])
    assert result.mode == "OBSERVATIONAL"
    assert result.status == "INSUFFICIENT"
    assert not any(fact.status == "LONG_READY" for fact in result.facts)


def test_missing_calendar_and_mismatch_fail_closed() -> None:
    snapshot, bundle, security = fixture_capture()
    missing = replace(bundle, calendar=replace(bundle.calendar, trading_days=()))
    with pytest.raises(ValueError, match="SNAPSHOT_SOURCE_CAPTURE_MISMATCH"):
        adapt_snapshot(snapshot, missing)
    wrong_bar = replace(bundle.completed_d1_bars[0], close=Decimal("101.5"))
    wrong = replace(bundle, completed_d1_bars=(wrong_bar,))
    with pytest.raises(ValueError, match="SNAPSHOT_SOURCE_BAR_MISMATCH"):
        adapt_snapshot(snapshot, wrong)
    no_quote = ProviderResult(
        status=DataAvailabilityStatus.UNAVAILABLE,
        provider=PROVIDER,
        retrieved_at=NOW,
        reason="not fetched",
    )
    no_calendar_snapshot = build_paqs_market_snapshot(
        bundle=missing,
        security=security,
        quote_result=no_quote,
        market_state_result=no_quote,
        d1_source_status=DataAvailabilityStatus.AVAILABLE,
        minute_source_status=DataAvailabilityStatus.AVAILABLE,
        created_at=NOW,
    )
    adapted = adapt_snapshot(no_calendar_snapshot, missing)
    assert adapted.multi_input.w1 is None and adapted.multi_input.d1 is None
    assert adapted.multi_input.m30 is not None
    assert "D1_SESSION_FACT_MISSING" in adapted.diagnostics


def test_capture_queries_once_and_reuses_same_acquisition() -> None:
    snapshot, bundle, security = fixture_capture()
    calls = {"input": 0, "state": 0}
    no_quote = ProviderResult(
        status=DataAvailabilityStatus.UNAVAILABLE,
        provider=PROVIDER,
        retrieved_at=NOW,
        reason="not fetched",
    )

    def acquisition(_security_id: str) -> PaqsInputAcquisition:
        calls["input"] += 1
        return PaqsInputAcquisition(
            bundle, DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.AVAILABLE
        )

    def state(_security_id: str) -> MarketStateView:
        calls["state"] += 1
        return MarketStateView(security, "America/New_York", no_quote, no_quote)

    queries = PaqsMarketSnapshotQueries(
        SimpleNamespace(current_acquisition=acquisition),
        SimpleNamespace(state=state),
        now=lambda: NOW,
    )
    captured, source = queries.current_capture(SECURITY_ID)
    assert captured.snapshot_hash == snapshot.snapshot_hash
    assert source is bundle
    assert calls == {"input": 1, "state": 1}
