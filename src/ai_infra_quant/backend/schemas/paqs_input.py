from __future__ import annotations

from ai_infra_quant.backend.schemas.common import StrictSchema
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus, SnapshotQualityStatus
from ai_infra_quant.core.domain.paqs_input import PaqsInputBundle


class PaqsInputStatusRead(StrictSchema):
    security_id: str
    market: str
    symbol: str
    display_symbol: str
    as_of_timestamp: str
    market_timezone: str
    provider: str
    data_quality: SnapshotQualityStatus
    adjustment_basis: str
    adjustment_as_of: str
    historical_replay_safe: bool
    calendar_status: DataAvailabilityStatus
    calendar_day_count: int
    calendar_unknown_day_type_count: int
    d1_source_count: int
    completed_w1_count: int
    partial_w1_count: int
    minute_source_count: int
    completed_m30_count: int
    partial_m30_count: int
    latest_completed_w1_at: str | None
    latest_completed_d1_session: str | None
    latest_completed_m30_at: str | None
    warnings: list[str]


def paqs_input_status_read(bundle: PaqsInputBundle) -> PaqsInputStatusRead:
    coverage = bundle.source_coverage
    return PaqsInputStatusRead(
        security_id=bundle.security_id,
        market=bundle.market,
        symbol=bundle.symbol,
        display_symbol=f"{bundle.market}.{bundle.symbol}",
        as_of_timestamp=_utc(bundle.as_of_timestamp),
        market_timezone=bundle.market_timezone,
        provider=bundle.provider,
        data_quality=bundle.data_quality,
        adjustment_basis=bundle.adjustment.basis.value,
        adjustment_as_of=_utc(bundle.adjustment.adjustment_as_of),
        historical_replay_safe=bundle.adjustment.historical_replay_safe,
        calendar_status=bundle.calendar.status,
        calendar_day_count=len(bundle.calendar.trading_days),
        calendar_unknown_day_type_count=sum(
            1 for item in bundle.calendar.trading_days if not item.session_segments
        ),
        d1_source_count=coverage.d1_source_count,
        completed_w1_count=coverage.w1_completed_count,
        partial_w1_count=coverage.w1_partial_count,
        minute_source_count=coverage.minute_source_count,
        completed_m30_count=coverage.m30_completed_count,
        partial_m30_count=coverage.m30_partial_count,
        latest_completed_w1_at=(
            None
            if not bundle.completed_w1_bars
            else _utc(max(bar.interval_end for bar in bundle.completed_w1_bars))
        ),
        latest_completed_d1_session=(
            None
            if not bundle.completed_d1_bars
            else max(bar.session_date for bar in bundle.completed_d1_bars).isoformat()
        ),
        latest_completed_m30_at=(
            None
            if not bundle.completed_30m_bars
            else _utc(max(bar.interval_end for bar in bundle.completed_30m_bars))
        ),
        warnings=list(bundle.warnings),
    )


def _utc(value: object) -> str:
    from datetime import datetime

    if not isinstance(value, datetime):
        raise TypeError("expected datetime")
    return value.isoformat().replace("+00:00", "Z")
