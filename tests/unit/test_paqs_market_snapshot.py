from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

import pytest

from ai_infra_quant.core.domain.enums import (
    DataAvailabilityStatus,
    InstrumentType,
    RecordSource,
    SnapshotQualityStatus,
    TradabilityStatus,
    VerificationStatus,
)
from ai_infra_quant.core.domain.market_data import (
    CanonicalMarketState,
    DailyBar,
    MarketStatusSnapshot,
    ProviderResult,
    QuoteSnapshot,
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
    derive_weekly_bars,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import (
    D1_SNAPSHOT_CAP,
    M30_SNAPSHOT_CAP,
    PAQS_MARKET_SNAPSHOT_SCHEMA_VERSION,
    W1_SNAPSHOT_CAP,
    PaqsMarketSnapshot,
    build_paqs_market_snapshot,
    canonical_json,
)
from ai_infra_quant.core.domain.security import Security

NOW = datetime(2026, 9, 3, 12, tzinfo=UTC)
SECURITY_ID = "00000000-0000-4000-8000-000000000001"
PROVIDER = "synthetic_provider"


def _security() -> Security:
    return Security(
        id=SECURITY_ID,
        market="US",
        symbol="AVGO",
        currency="USD",
        display_name="Broadcom",
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


def _daily(index: int, close: str = "101") -> DailyBar:
    return DailyBar(
        security="US.AVGO",
        session_date=date(2020, 1, 1) + timedelta(days=index),
        provider_time=datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=index),
        open=Decimal("100"),
        high=Decimal("102"),
        low=Decimal("99"),
        close=Decimal(close),
        volume=Decimal("1000.00"),
        is_completed=True,
        retrieved_at=NOW,
    )


def _derived(
    index: int,
    timeframe: DerivedTimeframe,
    *,
    coverage: DerivedCoverage = DerivedCoverage.COMPLETE,
    completed: bool = True,
    session_type: str | None = None,
) -> DerivedBar:
    minutes = 30 if timeframe is DerivedTimeframe.M30 else 7 * 24 * 60
    start = datetime(2020, 1, 6, tzinfo=UTC) + timedelta(minutes=minutes * index)
    return DerivedBar(
        security="US.AVGO",
        timeframe=timeframe,
        interval_start=start,
        interval_end=start + timedelta(minutes=minutes),
        open=Decimal("100.0"),
        high=Decimal("102.00"),
        low=Decimal("99.0"),
        close=Decimal("101.000"),
        volume=Decimal("1000.00"),
        market_timezone="America/New_York",
        session_type=session_type,
        source_bar_count=30 if timeframe is DerivedTimeframe.M30 else 5,
        expected_source_bar_count=30 if timeframe is DerivedTimeframe.M30 else 5,
        coverage=coverage,
        is_completed=completed,
    )


def _bundle(
    *,
    daily: tuple[DailyBar, ...] | None = None,
    weekly: tuple[DerivedBar, ...] | None = None,
    m30: tuple[DerivedBar, ...] | None = None,
    as_of: datetime = NOW,
    quality: SnapshotQualityStatus = SnapshotQualityStatus.PARTIAL,
    warnings: tuple[str, ...] = ("second", "first", "second"),
    missing_m30: int = 3,
) -> PaqsInputBundle:
    d1_bars = (_daily(0), _daily(1)) if daily is None else daily
    w1_bars = (_derived(0, DerivedTimeframe.W1),) if weekly is None else weekly
    m30_bars = (_derived(0, DerivedTimeframe.M30, session_type="REGULAR"),) if m30 is None else m30
    return PaqsInputBundle(
        security_id=SECURITY_ID,
        market="US",
        symbol="AVGO",
        market_timezone="America/New_York",
        provider=PROVIDER,
        as_of_timestamp=as_of,
        completed_w1_bars=w1_bars,
        completed_d1_bars=d1_bars,
        completed_30m_bars=m30_bars,
        calendar=CalendarMetadata(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=NOW,
            trading_days=(),
        ),
        adjustment=AdjustmentMetadata(
            basis=AdjustmentBasis.PROVIDER_QFQ_CURRENT,
            adjustment_as_of=NOW,
            historical_replay_safe=False,
        ),
        data_quality=quality,
        warnings=warnings,
        source_coverage=SourceCoverage(
            d1_source_count=len(d1_bars),
            w1_completed_count=sum(1 for bar in w1_bars if bar.is_completed),
            w1_partial_count=sum(1 for bar in w1_bars if bar.coverage is DerivedCoverage.PARTIAL),
            minute_source_count=len(m30_bars) * 30,
            m30_completed_count=sum(1 for bar in m30_bars if bar.is_completed),
            m30_partial_count=missing_m30,
        ),
    )


def _quote(
    *,
    status: DataAvailabilityStatus = DataAvailabilityStatus.AVAILABLE,
    delay: int | None = 15,
    price: str = "123.4500",
    retrieved_at: datetime = NOW,
    latest_quote_at: datetime | None = None,
) -> ProviderResult[QuoteSnapshot]:
    if status is not DataAvailabilityStatus.AVAILABLE:
        return ProviderResult(
            status=status,
            provider=PROVIDER,
            retrieved_at=retrieved_at,
            reason="quote unavailable",
            provider_delay_seconds=delay,
        )
    quote_at = latest_quote_at or retrieved_at
    return ProviderResult(
        status=status,
        provider=PROVIDER,
        retrieved_at=retrieved_at,
        provider_delay_seconds=delay,
        data=QuoteSnapshot(
            security="US.AVGO",
            price=Decimal(price),
            currency="USD",
            latest_quote_at=quote_at,
            retrieved_at=retrieved_at,
            is_equity=True,
        ),
    )


def _market_state(
    status: DataAvailabilityStatus = DataAvailabilityStatus.AVAILABLE,
    *,
    retrieved_at: datetime = NOW,
) -> ProviderResult[MarketStatusSnapshot]:
    if status is not DataAvailabilityStatus.AVAILABLE:
        return ProviderResult(
            status=status,
            provider=PROVIDER,
            retrieved_at=retrieved_at,
            reason="state unavailable",
        )
    return ProviderResult(
        status=status,
        provider=PROVIDER,
        retrieved_at=retrieved_at,
        data=MarketStatusSnapshot(
            security="US.AVGO",
            state=CanonicalMarketState.OPEN,
            provider_state="MORNING",
            retrieved_at=retrieved_at,
        ),
    )


def _snapshot(
    *,
    bundle: PaqsInputBundle | None = None,
    quote: ProviderResult[QuoteSnapshot] | None = None,
    state: ProviderResult[MarketStatusSnapshot] | None = None,
    d1_status: DataAvailabilityStatus = DataAvailabilityStatus.AVAILABLE,
    minute_status: DataAvailabilityStatus = DataAvailabilityStatus.AVAILABLE,
    created_at: datetime = NOW,
) -> PaqsMarketSnapshot:
    return build_paqs_market_snapshot(
        bundle=bundle or _bundle(),
        security=_security(),
        quote_result=quote or _quote(),
        market_state_result=state or _market_state(),
        d1_source_status=d1_status,
        minute_source_status=minute_status,
        created_at=created_at,
    )


def test_snapshot_is_immutable_versioned_self_consistent_and_utc() -> None:
    snapshot = _snapshot()
    assert snapshot.snapshot_schema_version == PAQS_MARKET_SNAPSHOT_SCHEMA_VERSION
    assert snapshot.snapshot_hash == snapshot.expected_snapshot_hash()
    assert snapshot.as_of_timestamp.utcoffset() == timedelta(0)
    assert snapshot.created_at >= snapshot.as_of_timestamp
    with pytest.raises(FrozenInstanceError):
        snapshot.snapshot_hash = "0" * 64  # type: ignore[misc]
    with pytest.raises(ValueError, match="snapshot_hash"):
        replace(snapshot, snapshot_hash="0" * 64)
    with pytest.raises(ValueError, match="timezone-aware"):
        _snapshot(created_at=datetime(2026, 9, 3, 12))


def test_canonical_order_duplicate_rejection_and_exact_caps() -> None:
    daily = tuple(_daily(index) for index in reversed(range(D1_SNAPSHOT_CAP + 2)))
    weekly = tuple(
        _derived(index, DerivedTimeframe.W1) for index in reversed(range(W1_SNAPSHOT_CAP + 2))
    )
    m30 = tuple(
        _derived(index, DerivedTimeframe.M30, session_type="REGULAR")
        for index in reversed(range(M30_SNAPSHOT_CAP + 2))
    )
    snapshot = _snapshot(bundle=_bundle(daily=daily, weekly=weekly, m30=m30))
    assert len(snapshot.w1_bars) == W1_SNAPSHOT_CAP
    assert len(snapshot.d1_bars) == D1_SNAPSHOT_CAP
    assert len(snapshot.m30_bars) == M30_SNAPSHOT_CAP
    assert snapshot.d1_bars[0].session_date == _daily(2).session_date
    assert snapshot.w1_bars[0].interval_start == _derived(2, DerivedTimeframe.W1).interval_start
    with pytest.raises(ValueError, match="duplicate canonical D1"):
        _snapshot(bundle=_bundle(daily=(_daily(0), _daily(0))))
    duplicate_w1 = _derived(0, DerivedTimeframe.W1)
    with pytest.raises(ValueError, match="duplicate canonical W1"):
        _snapshot(bundle=_bundle(weekly=(duplicate_w1, duplicate_w1)))


def test_w1_and_m30_eligibility_and_machine_readable_provenance() -> None:
    weekly = (
        _derived(2, DerivedTimeframe.W1, coverage=DerivedCoverage.UNKNOWN),
        _derived(0, DerivedTimeframe.W1),
        _derived(1, DerivedTimeframe.W1, coverage=DerivedCoverage.PARTIAL),
    )
    m30 = (
        _derived(0, DerivedTimeframe.M30, session_type="REGULAR"),
        _derived(1, DerivedTimeframe.M30, coverage=DerivedCoverage.PARTIAL, session_type="REGULAR"),
        _derived(2, DerivedTimeframe.M30, session_type="EXTENDED"),
        _derived(3, DerivedTimeframe.M30, completed=False, session_type="REGULAR"),
    )
    snapshot = _snapshot(
        bundle=_bundle(weekly=weekly, m30=m30, missing_m30=7),
        d1_status=DataAvailabilityStatus.PROVIDER_ERROR,
        minute_status=DataAvailabilityStatus.UNAVAILABLE,
    )
    assert len(snapshot.w1_bars) == 1
    assert len(snapshot.m30_bars) == 1
    evidence = snapshot.timeframe_evidence_status
    assert evidence.w1.source_status is DataAvailabilityStatus.PROVIDER_ERROR
    assert evidence.w1.authoritative_bar_count == 1
    assert evidence.w1.excluded_partial_count == 1
    assert evidence.w1.excluded_unknown_count == 1
    assert evidence.d1.source_status is DataAvailabilityStatus.PROVIDER_ERROR
    assert evidence.d1.authoritative_bar_count == len(snapshot.d1_bars)
    assert evidence.m30.source_status is DataAvailabilityStatus.UNAVAILABLE
    assert evidence.m30.authoritative_bar_count == 1
    assert evidence.m30.missing_elapsed_bucket_count == 7
    assert snapshot.source_coverage.w1_unknown_count == 1


def test_calendar_failure_is_preserved_for_calendar_dependent_timeframes() -> None:
    bundle = _bundle()
    degraded_calendar = replace(
        bundle,
        calendar=replace(
            bundle.calendar,
            status=DataAvailabilityStatus.PROVIDER_ERROR,
            reason="calendar failed",
        ),
    )
    evidence = _snapshot(bundle=degraded_calendar).timeframe_evidence_status
    assert evidence.w1.source_status is DataAvailabilityStatus.PROVIDER_ERROR
    assert evidence.d1.source_status is DataAvailabilityStatus.AVAILABLE
    assert evidence.m30.source_status is DataAvailabilityStatus.PROVIDER_ERROR


def test_quote_and_market_state_are_reference_only_and_never_fabricated() -> None:
    unavailable = _snapshot(
        quote=_quote(status=DataAvailabilityStatus.PROVIDER_ERROR, delay=None),
        state=_market_state(DataAvailabilityStatus.UNAVAILABLE),
    )
    quote = unavailable.current_price_reference
    assert quote.reference_only is True
    assert quote.price is quote.latest_quote_at is quote.provider_delay_seconds is None
    assert quote.reason == "quote unavailable"
    market_state = unavailable.market_state_reference
    assert market_state.reference_only is True
    assert market_state.canonical_state is market_state.provider_state is None
    available = _snapshot(quote=_quote(delay=0))
    assert available.current_price_reference.provider_delay_seconds == 0
    available_without_delay = _snapshot(quote=_quote(delay=None))
    assert available_without_delay.current_price_reference.provider_delay_seconds is None
    assert available_without_delay.snapshot_hash != _snapshot().snapshot_hash


def test_as_of_is_after_all_facts_and_clock_is_applied_last() -> None:
    latest_quote_at = NOW + timedelta(seconds=10)
    snapshot = _snapshot(
        quote=_quote(
            retrieved_at=NOW + timedelta(seconds=5),
            latest_quote_at=latest_quote_at,
        ),
        created_at=NOW - timedelta(days=1),
    )
    assert snapshot.as_of_timestamp == latest_quote_at
    assert snapshot.created_at == latest_quote_at


@pytest.mark.parametrize(
    ("session_dates", "request_time"),
    [
        (
            tuple(date(2026, 8, 3) + timedelta(days=index) for index in range(5)),
            datetime(2026, 8, 7, 21, tzinfo=UTC),
        ),
        (
            tuple(date(2026, 8, 3) + timedelta(days=index) for index in range(4)),
            datetime(2026, 8, 6, 21, tzinfo=UTC),
        ),
    ],
    ids=("friday-final-session", "holiday-shortened-thursday-final-session"),
)
def test_completed_w1_nominal_future_interval_does_not_advance_as_of(
    session_dates: tuple[date, ...],
    request_time: datetime,
) -> None:
    trading_days = tuple(
        TradingDay(
            market="US",
            market_date=session_date,
            market_timezone="America/New_York",
            day_type=TradingDayType.FULL,
            provider_day_type="WHOLE",
            session_segments=(TradingSessionSegment(time(9, 30), time(16, 0)),),
            provider=PROVIDER,
            retrieved_at=request_time,
        )
        for session_date in session_dates
    )
    daily = tuple(
        DailyBar(
            security="US.AVGO",
            session_date=session_date,
            provider_time=datetime.combine(session_date, time(20), tzinfo=UTC),
            open=Decimal("100"),
            high=Decimal("102"),
            low=Decimal("99"),
            close=Decimal("101"),
            volume=Decimal("1000"),
            is_completed=True,
            retrieved_at=request_time,
        )
        for session_date in session_dates
    )
    weekly = derive_weekly_bars(
        security="US.AVGO",
        market_timezone="America/New_York",
        daily_bars=daily,
        trading_days=trading_days,
        as_of=request_time,
    )
    assert len(weekly) == 1
    assert weekly[0].is_completed is True
    assert weekly[0].coverage is DerivedCoverage.COMPLETE
    nominal_next_monday = datetime(2026, 8, 10, 4, tzinfo=UTC)
    assert weekly[0].interval_end == nominal_next_monday
    assert nominal_next_monday > request_time

    bundle = _bundle(
        daily=daily,
        weekly=weekly,
        m30=(),
        as_of=request_time,
        warnings=(),
        missing_m30=0,
    )
    bundle = replace(
        bundle,
        calendar=CalendarMetadata(
            status=DataAvailabilityStatus.AVAILABLE,
            provider=PROVIDER,
            retrieved_at=request_time,
            trading_days=trading_days,
        ),
        adjustment=AdjustmentMetadata(
            basis=AdjustmentBasis.PROVIDER_QFQ_CURRENT,
            adjustment_as_of=request_time,
            historical_replay_safe=False,
        ),
    )
    snapshot = _snapshot(
        bundle=bundle,
        quote=_quote(
            retrieved_at=request_time,
            latest_quote_at=request_time,
        ),
        state=_market_state(retrieved_at=request_time),
        created_at=request_time,
    )

    assert len(snapshot.w1_bars) == 1
    assert snapshot.w1_bars[0].interval_end == nominal_next_monday
    assert snapshot.as_of_timestamp == request_time
    assert snapshot.created_at == request_time
    assert snapshot.as_of_timestamp < nominal_next_monday
    assert snapshot.created_at < nominal_next_monday
    assert nominal_next_monday.isoformat().replace("+00:00", "Z") in snapshot.canonical_hash_text()

    changed_geometry = replace(weekly[0], interval_end=nominal_next_monday + timedelta(hours=1))
    changed_snapshot = _snapshot(
        bundle=replace(bundle, completed_w1_bars=(changed_geometry,)),
        quote=_quote(
            retrieved_at=request_time,
            latest_quote_at=request_time,
        ),
        state=_market_state(retrieved_at=request_time),
        created_at=request_time,
    )
    assert changed_snapshot.as_of_timestamp == request_time
    assert changed_snapshot.snapshot_hash != snapshot.snapshot_hash


def test_hash_normalizes_nonsemantic_order_and_decimal_scale() -> None:
    first = _snapshot(
        bundle=_bundle(
            daily=(_daily(1, "101.0"), _daily(0, "101.00")),
            warnings=("z", "a", "z"),
        )
    )
    second = _snapshot(
        bundle=_bundle(
            daily=(_daily(0, "101.000"), _daily(1, "101")),
            warnings=("a", "z"),
        ),
        created_at=NOW + timedelta(hours=1),
    )
    assert first.canonical_hash_text() == second.canonical_hash_text()
    assert first.snapshot_hash == second.snapshot_hash
    assert "created_at" not in first.canonical_hash_payload()
    assert "snapshot_hash" not in first.canonical_hash_payload()
    assert "101.0" not in first.canonical_hash_text()
    later_created_at = replace(first, created_at=first.created_at + timedelta(seconds=1))
    assert later_created_at.snapshot_hash == first.snapshot_hash


def test_schema_version_is_in_hash_payload_and_adjustment_provenance_changes_hash() -> None:
    snapshot = _snapshot()
    payload = snapshot.canonical_hash_payload()
    payload["snapshot_schema_version"] = "paqs-market-snapshot-v2"
    changed_version_hash = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    changed_adjustment = replace(
        _bundle(),
        adjustment=AdjustmentMetadata(
            basis=AdjustmentBasis.PROVIDER_QFQ_CURRENT,
            adjustment_as_of=NOW + timedelta(seconds=1),
            historical_replay_safe=False,
        ),
    )
    assert changed_version_hash != snapshot.snapshot_hash
    assert _snapshot(bundle=changed_adjustment).snapshot_hash != snapshot.snapshot_hash


@pytest.mark.parametrize(
    "changed",
    [
        lambda: _snapshot(bundle=_bundle(as_of=NOW + timedelta(seconds=1))),
        lambda: _snapshot(bundle=_bundle(daily=(_daily(0, "100.5"),))),
        lambda: _snapshot(quote=_quote(price="124")),
        lambda: _snapshot(quote=_quote(delay=16)),
        lambda: _snapshot(bundle=_bundle(quality=SnapshotQualityStatus.COMPLETE)),
        lambda: _snapshot(bundle=_bundle(warnings=("changed",))),
        lambda: _snapshot(bundle=_bundle(missing_m30=4)),
        lambda: _snapshot(d1_status=DataAvailabilityStatus.PROVIDER_ERROR),
    ],
)
def test_model_visible_fact_or_provenance_change_changes_hash(changed: object) -> None:
    assert _snapshot().snapshot_hash != changed().snapshot_hash  # type: ignore[operator]


def test_finite_decimal_validation_and_known_golden_hash() -> None:
    with pytest.raises(ValueError, match="finite"):
        _snapshot(bundle=_bundle(daily=(_daily(0, "NaN"),)))
    assert _snapshot().snapshot_hash == (
        "f7ea67ef938a0842f3ddcdfa8909c67aedf38a77b265c62252f6b0e5d5e0e692"
    )
