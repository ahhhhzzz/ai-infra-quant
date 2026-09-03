from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from ai_infra_quant.core.domain.common import require_utc
from ai_infra_quant.core.domain.enums import (
    DataAvailabilityStatus,
    InstrumentType,
    SnapshotQualityStatus,
)
from ai_infra_quant.core.domain.market_data import (
    CanonicalMarketState,
    DailyBar,
    MarketStatusSnapshot,
    PriceKind,
    ProviderResult,
    QuoteSnapshot,
)
from ai_infra_quant.core.domain.money import canonical_decimal_string, parse_decimal
from ai_infra_quant.core.domain.paqs_input import (
    AdjustmentBasis,
    DerivedBar,
    DerivedCoverage,
    PaqsInputBundle,
)
from ai_infra_quant.core.domain.security import Security

PAQS_MARKET_SNAPSHOT_SCHEMA_VERSION = "paqs-market-snapshot-v1"
W1_SNAPSHOT_CAP = 156
D1_SNAPSHOT_CAP = 500
M30_SNAPSHOT_CAP = 200


@dataclass(frozen=True, slots=True)
class SnapshotSecurity:
    security_id: str
    market: str
    symbol: str
    display_symbol: str
    display_name: str | None
    currency: str
    instrument_type: InstrumentType
    market_timezone: str


@dataclass(frozen=True, slots=True)
class SnapshotDailyBar:
    session_date: date
    provider_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    is_completed: bool
    retrieved_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_time", require_utc(self.provider_time))
        object.__setattr__(self, "retrieved_at", require_utc(self.retrieved_at))
        for field_name in ("open", "high", "low", "close", "volume"):
            object.__setattr__(self, field_name, parse_decimal(getattr(self, field_name)))
        if not self.is_completed:
            raise ValueError("snapshot D1 bars must be completed")


@dataclass(frozen=True, slots=True)
class SnapshotDerivedBar:
    interval_start: datetime
    interval_end: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    market_timezone: str
    session_type: str | None
    source_bar_count: int
    expected_source_bar_count: int | None
    coverage: DerivedCoverage
    is_completed: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "interval_start", require_utc(self.interval_start))
        object.__setattr__(self, "interval_end", require_utc(self.interval_end))
        if self.interval_end <= self.interval_start:
            raise ValueError("snapshot derived bar interval must be positive")
        for field_name in ("open", "high", "low", "close", "volume"):
            object.__setattr__(self, field_name, parse_decimal(getattr(self, field_name)))


@dataclass(frozen=True, slots=True)
class CurrentPriceReference:
    status: DataAvailabilityStatus
    provider: str
    retrieved_at: datetime
    reason: str | None
    price: Decimal | None
    currency: str | None
    latest_quote_at: datetime | None
    price_kind: PriceKind | None
    provider_delay_seconds: int | None
    reference_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "retrieved_at", require_utc(self.retrieved_at))
        if self.latest_quote_at is not None:
            object.__setattr__(self, "latest_quote_at", require_utc(self.latest_quote_at))
        if self.price is not None:
            object.__setattr__(self, "price", parse_decimal(self.price))
        if self.provider_delay_seconds is not None and self.provider_delay_seconds < 0:
            raise ValueError("provider delay cannot be negative")
        present = (
            self.price is not None,
            self.currency is not None,
            self.latest_quote_at is not None,
            self.price_kind is not None,
        )
        if any(present) and not all(present):
            raise ValueError("quote factual payload must be complete or absent")
        if not self.reference_only:
            raise ValueError("current price is reference-only")


@dataclass(frozen=True, slots=True)
class MarketStateReference:
    status: DataAvailabilityStatus
    provider: str
    retrieved_at: datetime
    reason: str | None
    canonical_state: CanonicalMarketState | None
    provider_state: str | None
    reference_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "retrieved_at", require_utc(self.retrieved_at))
        if (self.canonical_state is None) != (self.provider_state is None):
            raise ValueError("market-state factual payload must be complete or absent")
        if not self.reference_only:
            raise ValueError("market state is reference-only")


@dataclass(frozen=True, slots=True)
class SnapshotCalendarMetadata:
    status: DataAvailabilityStatus
    provider: str
    retrieved_at: datetime
    reason: str | None
    market_timezone: str
    trading_day_count: int
    unknown_session_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "retrieved_at", require_utc(self.retrieved_at))
        if self.trading_day_count < 0 or self.unknown_session_count < 0:
            raise ValueError("calendar counts cannot be negative")
        if self.unknown_session_count > self.trading_day_count:
            raise ValueError("unknown session count cannot exceed trading-day count")


@dataclass(frozen=True, slots=True)
class SnapshotAdjustmentMetadata:
    basis: AdjustmentBasis
    adjustment_as_of: datetime
    historical_replay_safe: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "adjustment_as_of", require_utc(self.adjustment_as_of))


@dataclass(frozen=True, slots=True)
class SnapshotSourceCoverage:
    d1_source_count: int
    w1_completed_count: int
    w1_partial_count: int
    w1_unknown_count: int
    minute_source_count: int
    m30_completed_count: int
    m30_partial_count: int

    def __post_init__(self) -> None:
        if any(value < 0 for value in asdict(self).values()):
            raise ValueError("source-coverage counts cannot be negative")


@dataclass(frozen=True, slots=True)
class TimeframeEvidence:
    source_status: DataAvailabilityStatus
    authoritative_bar_count: int
    excluded_partial_count: int = 0
    excluded_unknown_count: int = 0
    missing_elapsed_bucket_count: int | None = None

    def __post_init__(self) -> None:
        counts = (
            self.authoritative_bar_count,
            self.excluded_partial_count,
            self.excluded_unknown_count,
        )
        if any(value < 0 for value in counts):
            raise ValueError("timeframe evidence counts cannot be negative")
        if self.missing_elapsed_bucket_count is not None and self.missing_elapsed_bucket_count < 0:
            raise ValueError("missing elapsed bucket count cannot be negative")


@dataclass(frozen=True, slots=True)
class TimeframeEvidenceStatus:
    w1: TimeframeEvidence
    d1: TimeframeEvidence
    m30: TimeframeEvidence


@dataclass(frozen=True, slots=True)
class SnapshotProviderMetadata:
    input_provider: str
    quote_provider: str
    market_state_provider: str


@dataclass(frozen=True, slots=True)
class PaqsMarketSnapshot:
    snapshot_schema_version: str
    snapshot_hash: str
    security: SnapshotSecurity
    as_of_timestamp: datetime
    created_at: datetime
    w1_bars: tuple[SnapshotDerivedBar, ...]
    d1_bars: tuple[SnapshotDailyBar, ...]
    m30_bars: tuple[SnapshotDerivedBar, ...]
    current_price_reference: CurrentPriceReference
    market_state_reference: MarketStateReference
    calendar_metadata: SnapshotCalendarMetadata
    adjustment_metadata: SnapshotAdjustmentMetadata
    data_quality: SnapshotQualityStatus
    warnings: tuple[str, ...]
    source_coverage: SnapshotSourceCoverage
    timeframe_evidence_status: TimeframeEvidenceStatus
    provider_metadata: SnapshotProviderMetadata

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_timestamp", require_utc(self.as_of_timestamp))
        object.__setattr__(self, "created_at", require_utc(self.created_at))
        if self.snapshot_schema_version != PAQS_MARKET_SNAPSHOT_SCHEMA_VERSION:
            raise ValueError("unsupported PAQS market snapshot schema version")
        if self.created_at < self.as_of_timestamp:
            raise ValueError("created_at cannot precede as_of_timestamp")
        if len(self.w1_bars) > W1_SNAPSHOT_CAP:
            raise ValueError("W1 snapshot cap exceeded")
        if len(self.d1_bars) > D1_SNAPSHOT_CAP:
            raise ValueError("D1 snapshot cap exceeded")
        if len(self.m30_bars) > M30_SNAPSHOT_CAP:
            raise ValueError("M30 snapshot cap exceeded")
        if any(
            not bar.is_completed or bar.coverage is not DerivedCoverage.COMPLETE
            for bar in self.w1_bars
        ):
            raise ValueError("W1 snapshot bars must be completed COMPLETE evidence")
        if any(
            not bar.is_completed
            or bar.coverage is not DerivedCoverage.COMPLETE
            or bar.session_type != "REGULAR"
            for bar in self.m30_bars
        ):
            raise ValueError("M30 snapshot bars must be completed COMPLETE REGULAR evidence")
        _require_strict_order(self.w1_bars, lambda bar: (bar.interval_start, bar.interval_end))
        _require_strict_order(self.d1_bars, lambda bar: bar.session_date)
        _require_strict_order(self.m30_bars, lambda bar: (bar.interval_start, bar.interval_end))
        evidence = self.timeframe_evidence_status
        if evidence.w1.authoritative_bar_count != len(self.w1_bars):
            raise ValueError("W1 authoritative count does not match payload")
        if evidence.d1.authoritative_bar_count != len(self.d1_bars):
            raise ValueError("D1 authoritative count does not match payload")
        if evidence.m30.authoritative_bar_count != len(self.m30_bars):
            raise ValueError("M30 authoritative count does not match payload")
        if self.snapshot_hash != self.expected_snapshot_hash():
            raise ValueError("snapshot_hash does not match canonical factual payload")

    def canonical_hash_payload(self) -> dict[str, Any]:
        return {
            "snapshot_schema_version": self.snapshot_schema_version,
            "security": self.security,
            "as_of_timestamp": self.as_of_timestamp,
            "w1_bars": self.w1_bars,
            "d1_bars": self.d1_bars,
            "m30_bars": self.m30_bars,
            "current_price_reference": self.current_price_reference,
            "market_state_reference": self.market_state_reference,
            "calendar_metadata": self.calendar_metadata,
            "adjustment_metadata": self.adjustment_metadata,
            "data_quality": self.data_quality,
            "warnings": self.warnings,
            "source_coverage": self.source_coverage,
            "timeframe_evidence_status": {
                "W1": self.timeframe_evidence_status.w1,
                "D1": self.timeframe_evidence_status.d1,
                "M30": self.timeframe_evidence_status.m30,
            },
            "provider_metadata": self.provider_metadata,
        }

    def canonical_hash_text(self) -> str:
        return canonical_json(self.canonical_hash_payload())

    def expected_snapshot_hash(self) -> str:
        return hashlib.sha256(self.canonical_hash_text().encode("utf-8")).hexdigest()


def build_paqs_market_snapshot(
    *,
    bundle: PaqsInputBundle,
    security: Security,
    quote_result: ProviderResult[QuoteSnapshot],
    market_state_result: ProviderResult[MarketStatusSnapshot],
    d1_source_status: DataAvailabilityStatus,
    minute_source_status: DataAvailabilityStatus,
    created_at: datetime,
) -> PaqsMarketSnapshot:
    if bundle.security_id != security.id:
        raise ValueError("snapshot Security does not match PAQS input bundle")
    if bundle.market != security.market or bundle.symbol != security.symbol:
        raise ValueError("snapshot Security identity conflicts with PAQS input bundle")

    w1_candidates = tuple(bundle.completed_w1_bars)
    _reject_duplicate_keys(
        list(w1_candidates),
        lambda bar: (bar.interval_start, bar.interval_end),
        "W1",
    )
    _reject_duplicate_keys(
        list(bundle.completed_30m_bars),
        lambda bar: (bar.interval_start, bar.interval_end),
        "M30",
    )
    eligible_w1 = tuple(
        bar
        for bar in w1_candidates
        if bar.is_completed and bar.coverage is DerivedCoverage.COMPLETE
    )
    eligible_m30 = tuple(
        bar
        for bar in bundle.completed_30m_bars
        if bar.is_completed
        and bar.coverage is DerivedCoverage.COMPLETE
        and bar.session_type == "REGULAR"
    )
    w1_bars = _canonical_derived_bars(eligible_w1, W1_SNAPSHOT_CAP)
    d1_bars = _canonical_daily_bars(bundle.completed_d1_bars, D1_SNAPSHOT_CAP)
    m30_bars = _canonical_derived_bars(eligible_m30, M30_SNAPSHOT_CAP)

    quote = _current_price_reference(quote_result)
    market_state = _market_state_reference(market_state_result)
    calendar = SnapshotCalendarMetadata(
        status=bundle.calendar.status,
        provider=bundle.calendar.provider,
        retrieved_at=bundle.calendar.retrieved_at,
        reason=bundle.calendar.reason,
        market_timezone=bundle.market_timezone,
        trading_day_count=len(bundle.calendar.trading_days),
        unknown_session_count=sum(
            1 for trading_day in bundle.calendar.trading_days if not trading_day.session_segments
        ),
    )
    adjustment = SnapshotAdjustmentMetadata(
        basis=bundle.adjustment.basis,
        adjustment_as_of=bundle.adjustment.adjustment_as_of,
        historical_replay_safe=bundle.adjustment.historical_replay_safe,
    )
    excluded_candidate_partial = sum(
        1 for bar in w1_candidates if bar.coverage is DerivedCoverage.PARTIAL
    )
    excluded_unknown = sum(1 for bar in w1_candidates if bar.coverage is DerivedCoverage.UNKNOWN)
    excluded_partial = max(
        bundle.source_coverage.w1_partial_count,
        excluded_candidate_partial,
    )
    source_coverage = SnapshotSourceCoverage(
        d1_source_count=bundle.source_coverage.d1_source_count,
        w1_completed_count=bundle.source_coverage.w1_completed_count,
        w1_partial_count=bundle.source_coverage.w1_partial_count,
        w1_unknown_count=excluded_unknown,
        minute_source_count=bundle.source_coverage.minute_source_count,
        m30_completed_count=bundle.source_coverage.m30_completed_count,
        m30_partial_count=bundle.source_coverage.m30_partial_count,
    )
    timeframe_evidence = TimeframeEvidenceStatus(
        w1=TimeframeEvidence(
            source_status=_combined_source_status(
                d1_source_status,
                bundle.calendar.status,
            ),
            authoritative_bar_count=len(w1_bars),
            excluded_partial_count=excluded_partial,
            excluded_unknown_count=excluded_unknown,
        ),
        d1=TimeframeEvidence(
            source_status=d1_source_status,
            authoritative_bar_count=len(d1_bars),
        ),
        m30=TimeframeEvidence(
            source_status=_combined_source_status(
                minute_source_status,
                bundle.calendar.status,
            ),
            authoritative_bar_count=len(m30_bars),
            missing_elapsed_bucket_count=bundle.source_coverage.m30_partial_count,
        ),
    )
    provider_metadata = SnapshotProviderMetadata(
        input_provider=bundle.provider,
        quote_provider=quote_result.provider,
        market_state_provider=market_state_result.provider,
    )
    as_of_candidates = [
        bundle.as_of_timestamp,
        quote.retrieved_at,
        market_state.retrieved_at,
        calendar.retrieved_at,
        adjustment.adjustment_as_of,
        *(bar.retrieved_at for bar in d1_bars),
        *(bar.provider_time for bar in d1_bars),
        *(bar.interval_end for bar in m30_bars),
    ]
    if quote.latest_quote_at is not None:
        as_of_candidates.append(quote.latest_quote_at)
    as_of_timestamp = max(require_utc(value) for value in as_of_candidates)
    final_created_at = max(require_utc(created_at), as_of_timestamp)
    normalized_warnings = tuple(sorted(set(bundle.warnings)))
    values: dict[str, Any] = {
        "snapshot_schema_version": PAQS_MARKET_SNAPSHOT_SCHEMA_VERSION,
        "security": SnapshotSecurity(
            security_id=security.id,
            market=security.market,
            symbol=security.symbol,
            display_symbol=security.display_symbol,
            display_name=security.display_name,
            currency=security.currency,
            instrument_type=security.instrument_type,
            market_timezone=bundle.market_timezone,
        ),
        "as_of_timestamp": as_of_timestamp,
        "created_at": final_created_at,
        "w1_bars": w1_bars,
        "d1_bars": d1_bars,
        "m30_bars": m30_bars,
        "current_price_reference": quote,
        "market_state_reference": market_state,
        "calendar_metadata": calendar,
        "adjustment_metadata": adjustment,
        "data_quality": bundle.data_quality,
        "warnings": normalized_warnings,
        "source_coverage": source_coverage,
        "timeframe_evidence_status": timeframe_evidence,
        "provider_metadata": provider_metadata,
    }
    hash_values = _hash_payload_from_values(values)
    hash_values["timeframe_evidence_status"] = {
        "W1": timeframe_evidence.w1,
        "D1": timeframe_evidence.d1,
        "M30": timeframe_evidence.m30,
    }
    snapshot_hash = hashlib.sha256(canonical_json(hash_values).encode("utf-8")).hexdigest()
    return PaqsMarketSnapshot(snapshot_hash=snapshot_hash, **values)


def canonical_json(value: object) -> str:
    return json.dumps(
        _canonical_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _hash_payload_from_values(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if key != "created_at"}


def _combined_source_status(
    primary: DataAvailabilityStatus,
    calendar: DataAvailabilityStatus,
) -> DataAvailabilityStatus:
    statuses = {primary, calendar}
    for status in (
        DataAvailabilityStatus.PROVIDER_ERROR,
        DataAvailabilityStatus.NOT_ENTITLED,
        DataAvailabilityStatus.INVALID,
        DataAvailabilityStatus.NOT_SUPPORTED,
        DataAvailabilityStatus.UNAVAILABLE,
        DataAvailabilityStatus.MISSING,
        DataAvailabilityStatus.STALE,
        DataAvailabilityStatus.DELAYED,
    ):
        if status in statuses:
            return status
    return DataAvailabilityStatus.AVAILABLE


def _canonical_value(value: object) -> object:
    if isinstance(value, Decimal):
        return canonical_decimal_string(value)
    if isinstance(value, datetime):
        return require_utc(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field_name: _canonical_value(field_value)
            for field_name, field_value in asdict(value).items()
        }
    if isinstance(value, dict):
        return {str(key): _canonical_value(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_canonical_value(item) for item in value]
    if value is None or isinstance(value, str | int | bool):
        return value
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def _canonical_daily_bars(bars: tuple[DailyBar, ...], cap: int) -> tuple[SnapshotDailyBar, ...]:
    ordered = sorted(bars, key=lambda bar: bar.session_date)
    _reject_duplicate_keys(ordered, lambda bar: bar.session_date, "D1")
    return tuple(
        SnapshotDailyBar(
            session_date=bar.session_date,
            provider_time=bar.provider_time,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
            is_completed=bar.is_completed,
            retrieved_at=bar.retrieved_at,
        )
        for bar in ordered[-cap:]
    )


def _canonical_derived_bars(
    bars: tuple[DerivedBar, ...], cap: int
) -> tuple[SnapshotDerivedBar, ...]:
    ordered = sorted(bars, key=lambda bar: (bar.interval_start, bar.interval_end))
    _reject_duplicate_keys(
        ordered,
        lambda bar: (bar.interval_start, bar.interval_end),
        "derived",
    )
    return tuple(
        SnapshotDerivedBar(
            interval_start=bar.interval_start,
            interval_end=bar.interval_end,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
            market_timezone=bar.market_timezone,
            session_type=bar.session_type,
            source_bar_count=bar.source_bar_count,
            expected_source_bar_count=bar.expected_source_bar_count,
            coverage=bar.coverage,
            is_completed=bar.is_completed,
        )
        for bar in ordered[-cap:]
    )


def _current_price_reference(
    result: ProviderResult[QuoteSnapshot],
) -> CurrentPriceReference:
    data = result.data
    return CurrentPriceReference(
        status=result.status,
        provider=result.provider,
        retrieved_at=result.retrieved_at,
        reason=result.reason,
        price=None if data is None else data.price,
        currency=None if data is None else data.currency,
        latest_quote_at=None if data is None else data.latest_quote_at,
        price_kind=None if data is None else data.price_kind,
        provider_delay_seconds=result.provider_delay_seconds,
    )


def _market_state_reference(
    result: ProviderResult[MarketStatusSnapshot],
) -> MarketStateReference:
    data = result.data
    return MarketStateReference(
        status=result.status,
        provider=result.provider,
        retrieved_at=result.retrieved_at,
        reason=result.reason,
        canonical_state=None if data is None else data.state,
        provider_state=None if data is None else data.provider_state,
    )


def _reject_duplicate_keys[ValueT, KeyT](
    values: list[ValueT], key: Callable[[ValueT], KeyT], timeframe: str
) -> None:
    keys = [key(value) for value in values]
    if len(keys) != len(set(keys)):
        raise ValueError(f"duplicate canonical {timeframe} bar identity")


def _require_strict_order[ValueT](values: tuple[ValueT, ...], key: Callable[[ValueT], Any]) -> None:
    keys = [key(value) for value in values]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise ValueError("snapshot bars must have unique chronological identities")
