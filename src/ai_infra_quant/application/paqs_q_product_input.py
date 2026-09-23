"""Truthful observational Q inputs from one frozen product market capture.

The current provider snapshot is not historical price/calendar version evidence. In
particular, a completed M30 OHLC does not prove its opening price was separately
observed when the interval opened.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import TradingDay, TradingDayType
from ai_infra_quant.core.domain.paqs_input import PaqsInputBundle
from ai_infra_quant.core.domain.paqs_market_snapshot import (
    PaqsMarketSnapshot,
    SnapshotDailyBar,
    SnapshotDerivedBar,
)
from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON
from ai_infra_quant.core.domain.paqs_q.inputs import Bar, Fact, QInput
from ai_infra_quant.core.domain.paqs_q.setup_reference import MultiInput


@dataclass(frozen=True, slots=True)
class ProductQInputs:
    snapshot_hash: str
    multi_input: MultiInput
    diagnostics: tuple[str, ...]


def _same_prices(left: object, right: object) -> bool:
    return all(
        getattr(left, field) == getattr(right, field)
        for field in ("open", "high", "low", "close", "volume")
    )


def _require_same_capture(snapshot: PaqsMarketSnapshot, source: PaqsInputBundle) -> None:
    security = snapshot.security
    if (
        security.security_id != source.security_id
        or security.market != source.market
        or security.symbol != source.symbol
        or security.market_timezone != source.market_timezone
        or snapshot.provider_metadata.input_provider != source.provider
        or snapshot.calendar_metadata.provider != source.calendar.provider
        or snapshot.calendar_metadata.retrieved_at != source.calendar.retrieved_at
        or snapshot.calendar_metadata.trading_day_count != len(source.calendar.trading_days)
        or snapshot.adjustment_metadata.basis != source.adjustment.basis
        or snapshot.adjustment_metadata.adjustment_as_of != source.adjustment.adjustment_as_of
        or snapshot.adjustment_metadata.historical_replay_safe
        != source.adjustment.historical_replay_safe
        or source.as_of_timestamp > snapshot.as_of_timestamp
    ):
        raise ValueError("SNAPSHOT_SOURCE_CAPTURE_MISMATCH")
    daily = {bar.session_date: bar for bar in source.completed_d1_bars}
    weekly = {(bar.interval_start, bar.interval_end): bar for bar in source.completed_w1_bars}
    intraday = {(bar.interval_start, bar.interval_end): bar for bar in source.completed_30m_bars}
    if (
        any(bar.security != security.display_symbol for bar in source.completed_d1_bars)
        or any(bar.security != security.display_symbol for bar in source.completed_w1_bars)
        or any(bar.security != security.display_symbol for bar in source.completed_30m_bars)
    ):
        raise ValueError("SNAPSHOT_SOURCE_SECURITY_MISMATCH")
    if (
        any(
            bar.session_date not in daily
            or not _same_prices(bar, daily[bar.session_date])
            or bar.retrieved_at != daily[bar.session_date].retrieved_at
            or bar.provider_time != daily[bar.session_date].provider_time
            or bar.is_completed != daily[bar.session_date].is_completed
            for bar in snapshot.d1_bars
        )
        or any(
            (bar.interval_start, bar.interval_end) not in weekly
            or not _same_prices(bar, weekly[(bar.interval_start, bar.interval_end)])
            or bar.coverage != weekly[(bar.interval_start, bar.interval_end)].coverage
            or bar.is_completed != weekly[(bar.interval_start, bar.interval_end)].is_completed
            for bar in snapshot.w1_bars
        )
        or any(
            (bar.interval_start, bar.interval_end) not in intraday
            or not _same_prices(bar, intraday[(bar.interval_start, bar.interval_end)])
            or bar.coverage != intraday[(bar.interval_start, bar.interval_end)].coverage
            or bar.session_type != intraday[(bar.interval_start, bar.interval_end)].session_type
            or bar.is_completed != intraday[(bar.interval_start, bar.interval_end)].is_completed
            for bar in snapshot.m30_bars
        )
    ):
        raise ValueError("SNAPSHOT_SOURCE_BAR_MISMATCH")


def _actual_open_facts(snapshot: PaqsMarketSnapshot, source: PaqsInputBundle) -> tuple[Fact, ...]:
    facts: list[Fact] = []
    seen: set[date] = set()
    for day in source.calendar.trading_days:
        if (
            day.market != snapshot.security.market
            or day.market_timezone != snapshot.security.market_timezone
            or day.provider != source.calendar.provider
        ):
            raise ValueError("SNAPSHOT_CALENDAR_SOURCE_MISMATCH")
        if day.market_date in seen:
            raise ValueError("SNAPSHOT_CALENDAR_DUPLICATE_DAY")
        seen.add(day.market_date)
        if day.day_type is TradingDayType.UNKNOWN or not day.session_segments:
            continue
        segments = _segments(day)
        if (
            day.retrieved_at > snapshot.as_of_timestamp
            or segments[-1][1] > snapshot.as_of_timestamp
        ):
            continue
        facts.append(
            Fact(
                day=day.market_date,
                market=day.market,
                timezone=day.market_timezone,
                kind="OPEN",
                segments=segments,
                source=day.provider,
                retrieved_at=day.retrieved_at,
                available_at=None,
                complete=source.calendar.status is DataAvailabilityStatus.AVAILABLE,
            )
        )
    return tuple(facts)


def _segments(day: TradingDay) -> tuple[tuple[datetime, datetime], ...]:
    zone = ZoneInfo(day.market_timezone)
    return tuple(
        (
            datetime.combine(day.market_date, item.start, tzinfo=zone).astimezone(UTC),
            datetime.combine(day.market_date, item.end, tzinfo=zone).astimezone(UTC),
        )
        for item in day.session_segments
    )


def _daily(
    bars: tuple[SnapshotDailyBar, ...], security: str, calendar: dict[date, Fact], source: str
) -> tuple[Bar, ...] | None:
    result = []
    for bar in bars:
        fact = calendar.get(bar.session_date)
        if fact is None:
            return None
        start, end = fact.segments[0][0], fact.segments[-1][1]
        result.append(
            Bar(
                security=security,
                timeframe="D1",
                start=start,
                end=end,
                completed_at=end,
                available_at=None,
                retrieved_at=bar.retrieved_at,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                completed=bar.is_completed,
                coverage="COMPLETE",
                adjustment=source,
                session="REGULAR",
                source_ref=f"D1:{bar.session_date}:{bar.provider_time.isoformat()}",
            )
        )
    return tuple(result)


def _weekly(
    bars: tuple[SnapshotDerivedBar, ...],
    security: str,
    calendar: dict[date, Fact],
    adjustment: str,
    observed_at: datetime,
) -> tuple[Bar, ...] | None:
    result = []
    zone = ZoneInfo("America/New_York" if security.startswith("US.") else "Asia/Hong_Kong")
    for bar in bars:
        first = bar.interval_start.astimezone(zone).date()
        known_sessions = [
            calendar[first + timedelta(days=i)]
            for i in range(7)
            if first + timedelta(days=i) in calendar
        ]
        if not known_sessions:
            return None
        # A derived W1 bar ends at the following Monday; its factual completion
        # is the last actually supplied regular session close.
        completed_at = known_sessions[-1].segments[-1][1]
        result.append(
            Bar(
                security=security,
                timeframe="W1",
                start=bar.interval_start,
                end=bar.interval_end,
                completed_at=completed_at,
                available_at=None,
                retrieved_at=observed_at,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                completed=bar.is_completed,
                coverage=bar.coverage.value,
                adjustment=adjustment,
                session="REGULAR",
                source_ref=f"DERIVED_W1:{bar.interval_start.isoformat()}:{bar.interval_end.isoformat()}",
            )
        )
    return tuple(result)


def _m30(
    bars: tuple[SnapshotDerivedBar, ...], security: str, adjustment: str, observed_at: datetime
) -> tuple[Bar, ...]:
    return tuple(
        Bar(
            security=security,
            timeframe="M30",
            start=bar.interval_start,
            end=bar.interval_end,
            completed_at=bar.interval_end,
            available_at=None,
            retrieved_at=observed_at,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
            completed=bar.is_completed,
            coverage=bar.coverage.value,
            adjustment=adjustment,
            session=bar.session_type or "UNKNOWN",
            source_ref=f"DERIVED_M30:{bar.interval_start.isoformat()}:{bar.interval_end.isoformat()}",
        )
        for bar in bars
    )


def adapt_snapshot(snapshot: PaqsMarketSnapshot, source: PaqsInputBundle) -> ProductQInputs:
    """Build only the evidence the frozen product capture can actually support.

    `available_at` stays unknown. Derived-bar `retrieved_at` records the frozen
    capture observation, not a claimed historical provider observation.
    """
    _require_same_capture(snapshot, source)
    facts = _actual_open_facts(snapshot, source)
    calendar = {fact.day: fact for fact in facts}
    security = snapshot.security.display_symbol
    adjustment = snapshot.adjustment_metadata.basis.value
    diagnostics = [
        "HISTORICAL_PRICE_AVAILABILITY_UNKNOWN",
        "HISTORICAL_CALENDAR_AVAILABILITY_UNKNOWN",
        "CLOSED_DAY_FACTS_UNAVAILABLE",
        "DERIVED_BAR_SOURCE_RETRIEVAL_UNAVAILABLE",
        "INDEPENDENT_M30_OPEN_REFERENCE_MISSING",
    ]
    if not snapshot.adjustment_metadata.historical_replay_safe:
        diagnostics.append("ADJUSTMENT_HISTORY_NOT_POINT_IN_TIME")
    if adjustment == "PROVIDER_QFQ_CURRENT":
        diagnostics.append("CURRENT_QFQ_NOT_POINT_IN_TIME")
    if snapshot.calendar_metadata.status is not DataAvailabilityStatus.AVAILABLE:
        diagnostics.append("CALENDAR_SOURCE_NOT_AVAILABLE")
    if any(day.retrieved_at > snapshot.as_of_timestamp for day in source.calendar.trading_days):
        diagnostics.append("CALENDAR_FUTURE_RETRIEVAL_EXCLUDED")
    if snapshot.timeframe_evidence_status.m30.missing_elapsed_bucket_count:
        diagnostics.append("M30_COVERAGE_INCOMPLETE")
    if snapshot.w1_bars:
        first = (
            snapshot.w1_bars[0]
            .interval_start.astimezone(ZoneInfo(snapshot.security.market_timezone))
            .date()
        )
        last = snapshot.w1_bars[-1].interval_start.astimezone(
            ZoneInfo(snapshot.security.market_timezone)
        ).date() + timedelta(days=6)
        absent = sum(
            first + timedelta(days=i) not in calendar for i in range((last - first).days + 1)
        )
        if absent:
            diagnostics.append(f"CALENDAR_DATE_FACTS_MISSING:{absent}")
    provenance = FrozenJSON.of(
        {
            "source": f"product-snapshot:{snapshot.snapshot_hash}",
            "snapshot_hash": snapshot.snapshot_hash,
            "snapshot_schema_version": snapshot.snapshot_schema_version,
            "input_provider": source.provider,
            "calendar_provider": source.calendar.provider,
            "calendar_retrieved_at": source.calendar.retrieved_at,
            "adjustment_basis": adjustment,
            "adjustment_as_of": source.adjustment.adjustment_as_of,
            "historical_replay_safe": source.adjustment.historical_replay_safe,
            "derived_bar_retrieval": "SNAPSHOT_OBSERVATION_ONLY",
        }
    )

    def qinput(timeframe: str, bars: tuple[Bar, ...] | None) -> QInput | None:
        if bars is None or not bars:
            diagnostics.append(f"{timeframe}_INPUT_MISSING")
            return None
        return QInput(
            security=security,
            market=snapshot.security.market,
            currency=snapshot.security.currency,
            market_timezone=snapshot.security.market_timezone,
            timeframe=timeframe,
            as_of=snapshot.as_of_timestamp,
            bars=bars,
            calendar=facts,
            quality=snapshot.data_quality.value,
            mode="OBSERVATIONAL",
            snapshot_identity=snapshot.snapshot_hash,
            provenance=provenance,
        )

    daily = _daily(snapshot.d1_bars, security, calendar, adjustment)
    if daily is None:
        diagnostics.append("D1_SESSION_FACT_MISSING")
    weekly = _weekly(snapshot.w1_bars, security, calendar, adjustment, snapshot.as_of_timestamp)
    if weekly is None:
        diagnostics.append("W1_SESSION_FACT_MISSING")
    intraday = _m30(snapshot.m30_bars, security, adjustment, snapshot.as_of_timestamp)
    return ProductQInputs(
        snapshot_hash=snapshot.snapshot_hash,
        multi_input=MultiInput(
            qinput("W1", weekly), qinput("D1", daily), qinput("M30", intraday), ()
        ),
        diagnostics=tuple(dict.fromkeys(diagnostics)),
    )
