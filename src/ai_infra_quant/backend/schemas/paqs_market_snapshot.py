from __future__ import annotations

from pydantic import Field

from ai_infra_quant.backend.schemas.common import StrictSchema
from ai_infra_quant.core.domain.enums import (
    DataAvailabilityStatus,
    InstrumentType,
    SnapshotQualityStatus,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot


class SnapshotSecurityRead(StrictSchema):
    security_id: str
    market: str
    symbol: str
    display_symbol: str
    display_name: str | None
    currency: str
    instrument_type: InstrumentType
    market_timezone: str


class SnapshotDailyBarRead(StrictSchema):
    session_date: str
    provider_time: str
    open: str
    high: str
    low: str
    close: str
    volume: str
    is_completed: bool
    retrieved_at: str


class SnapshotDerivedBarRead(StrictSchema):
    interval_start: str
    interval_end: str
    open: str
    high: str
    low: str
    close: str
    volume: str
    market_timezone: str
    session_type: str | None
    source_bar_count: int
    expected_source_bar_count: int | None
    coverage: str
    is_completed: bool


class CurrentPriceReferenceRead(StrictSchema):
    status: DataAvailabilityStatus
    provider: str
    retrieved_at: str
    reason: str | None
    price: str | None
    currency: str | None
    latest_quote_at: str | None
    price_kind: str | None
    provider_delay_seconds: int | None
    reference_only: bool


class MarketStateReferenceRead(StrictSchema):
    status: DataAvailabilityStatus
    provider: str
    retrieved_at: str
    reason: str | None
    canonical_state: str | None
    provider_state: str | None
    reference_only: bool


class SnapshotCalendarMetadataRead(StrictSchema):
    status: DataAvailabilityStatus
    provider: str
    retrieved_at: str
    reason: str | None
    market_timezone: str
    trading_day_count: int
    unknown_session_count: int


class SnapshotAdjustmentMetadataRead(StrictSchema):
    basis: str
    adjustment_as_of: str
    historical_replay_safe: bool


class SnapshotSourceCoverageRead(StrictSchema):
    d1_source_count: int
    w1_completed_count: int
    w1_partial_count: int
    w1_unknown_count: int
    minute_source_count: int
    m30_completed_count: int
    m30_partial_count: int


class TimeframeEvidenceRead(StrictSchema):
    source_status: DataAvailabilityStatus
    authoritative_bar_count: int
    excluded_partial_count: int
    excluded_unknown_count: int
    missing_elapsed_bucket_count: int | None


class TimeframeEvidenceStatusRead(StrictSchema):
    w1: TimeframeEvidenceRead = Field(alias="W1")
    d1: TimeframeEvidenceRead = Field(alias="D1")
    m30: TimeframeEvidenceRead = Field(alias="M30")


class SnapshotProviderMetadataRead(StrictSchema):
    input_provider: str
    quote_provider: str
    market_state_provider: str


class PaqsMarketSnapshotRead(StrictSchema):
    snapshot_schema_version: str
    snapshot_hash: str
    security: SnapshotSecurityRead
    as_of_timestamp: str
    created_at: str
    w1_bars: list[SnapshotDerivedBarRead]
    d1_bars: list[SnapshotDailyBarRead]
    m30_bars: list[SnapshotDerivedBarRead]
    current_price_reference: CurrentPriceReferenceRead
    market_state_reference: MarketStateReferenceRead
    calendar_metadata: SnapshotCalendarMetadataRead
    adjustment_metadata: SnapshotAdjustmentMetadataRead
    data_quality: SnapshotQualityStatus
    warnings: list[str]
    source_coverage: SnapshotSourceCoverageRead
    timeframe_evidence_status: TimeframeEvidenceStatusRead
    provider_metadata: SnapshotProviderMetadataRead


def paqs_market_snapshot_read(snapshot: PaqsMarketSnapshot) -> PaqsMarketSnapshotRead:
    payload = snapshot.canonical_hash_payload()
    payload["snapshot_hash"] = snapshot.snapshot_hash
    payload["created_at"] = snapshot.created_at
    return PaqsMarketSnapshotRead.model_validate_json(canonical_api_json(payload))


def canonical_api_json(value: object) -> str:
    from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json

    return canonical_json(value)
