"""Read a supplied 0004 Capture with SQLite mode=ro; no app startup or provider."""

import json
import sqlite3
from datetime import UTC, date, datetime, time
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.market_data import (
    DailyBar,
    MinuteBar,
    TradingDay,
    TradingDayType,
    TradingSessionSegment,
)
from ai_infra_quant.core.domain.market_data_archive import digest as archive_digest
from ai_infra_quant.core.domain.paqs_input import derive_m30_bars, derive_weekly_bars

from ..types import CONTEXT, Bar, Dataset, Timeframe


def stamp(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("NAIVE_ARCHIVE_TIMESTAMP")
    return result.astimezone(UTC)


def load_capture(
    path: Path, capture_id: str
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    if not path.is_file():
        raise ValueError("ARCHIVE_FILE_NOT_FOUND")
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        row = connection.execute(
            "SELECT * FROM market_archive_captures WHERE capture_id=?", (capture_id,)
        ).fetchone()
        if row is None:
            raise ValueError("CAPTURE_NOT_FOUND")
        capture = json.loads(row["payload_json"])
        if (
            archive_digest(capture) != row["payload_hash"]
            or capture["capture_id"] != capture_id
            or capture["security_id"] != row["security_id"]
        ):
            raise ValueError("CAPTURE_INTEGRITY")
        batches: dict[str, list[dict[str, Any]]] = {}
        for timeframe in ("D1", "M1"):
            rows = connection.execute(
                "SELECT v.*,m.ordinal,m.retrieved_at,m.security_id AS owner "
                "FROM market_archive_memberships m "
                "JOIN market_archive_bar_versions v ON v.version_hash=m.version_hash "
                "WHERE m.capture_id=? AND m.timeframe=? ORDER BY m.ordinal",
                (capture_id, timeframe),
            ).fetchall()
            if len(rows) != capture["batches"][timeframe]["count"]:
                raise ValueError("MEMBERSHIP_COUNT")
            values = []
            for index, entry in enumerate(rows):
                payload = json.loads(entry["payload_json"])
                if entry["ordinal"] != index or archive_digest(payload) != entry["version_hash"]:
                    raise ValueError("MEMBERSHIP_INTEGRITY")
                if (
                    entry["owner"] != capture["security_id"]
                    or entry["security_id"] != entry["owner"]
                    or entry["timeframe"] != timeframe
                ):
                    raise ValueError("MEMBERSHIP_IDENTITY")
                if payload["security_id"] != entry["owner"] or payload["timeframe"] != timeframe:
                    raise ValueError("PAYLOAD_IDENTITY")
                if (
                    payload["is_completed"] is not True
                    or payload["security"] != capture["market"] + "." + capture["symbol"]
                    or any(
                        payload[k] != capture[k]
                        for k in (
                            "market",
                            "market_timezone",
                            "currency",
                            "provider",
                            "adjustment_basis",
                        )
                    )
                ):
                    raise ValueError("ARCHIVE_COMPLETION_OR_SOURCE_CONFLICT")
                for field in ("open", "high", "low", "close", "volume"):
                    if not isinstance(payload[field], str) or Decimal(payload[field]) != Decimal(
                        entry[field]
                    ):
                        raise ValueError("DECIMAL_COLUMN_INTEGRITY")
                values.append(
                    {
                        **payload,
                        "retrieved_at": entry["retrieved_at"],
                        "version_hash": entry["version_hash"],
                    }
                )
            batches[timeframe] = values
    return capture, batches


def normalize_capture(
    capture: dict[str, Any], batches: dict[str, list[dict[str, Any]]]
) -> tuple[Dataset, ...]:
    """Reuse 006A at the capture observation; no historical availability claim."""
    with localcontext(CONTEXT):
        security = capture["market"] + "." + capture["symbol"]
        zone = ZoneInfo(capture["market_timezone"])
        observed = stamp(capture["completed_at"])
        calendar = tuple(
            TradingDay(
                row["market"],
                date.fromisoformat(row["market_date"]),
                row["market_timezone"],
                TradingDayType(row["day_type"]),
                row["provider_day_type"],
                tuple(
                    TradingSessionSegment(
                        time.fromisoformat(s["start"]), time.fromisoformat(s["end"])
                    )
                    for s in row["session_segments"]
                ),
                row["provider"],
                stamp(row["retrieved_at"]),
            )
            for row in capture["calendar"]
        )
        days = {day.market_date: day for day in calendar}
        daily = tuple(
            DailyBar(
                security,
                date.fromisoformat(r["session_date"]),
                stamp(r["provider_time"]),
                Decimal(r["open"]),
                Decimal(r["high"]),
                Decimal(r["low"]),
                Decimal(r["close"]),
                Decimal(r["volume"]),
                True,
                stamp(r["retrieved_at"]),
            )
            for r in batches["D1"]
        )
        minute = tuple(
            MinuteBar(
                security,
                stamp(r["interval_start"]),
                stamp(r["interval_end"]),
                Decimal(r["open"]),
                Decimal(r["high"]),
                Decimal(r["low"]),
                Decimal(r["close"]),
                Decimal(r["volume"]),
                True,
                stamp(r["retrieved_at"]),
            )
            for r in batches["M1"]
        )
        weekly = derive_weekly_bars(
            security=security,
            market_timezone=zone.key,
            daily_bars=daily,
            trading_days=calendar,
            as_of=observed,
        )
        minute_days = tuple(
            d
            for d in calendar
            if minute
            and minute[0].interval_start.astimezone(zone).date()
            <= d.market_date
            <= minute[-1].interval_end.astimezone(zone).date()
        )
        m30 = derive_m30_bars(
            security=security,
            market_timezone=zone.key,
            minute_bars=minute,
            trading_days=minute_days,
            as_of=observed,
        )
        output: dict[str, list[Bar]] = {"D1": [], "W1": [], "M30": []}
        for bar, row in zip(daily, batches["D1"], strict=True):
            day = days.get(bar.session_date)
            if day is None or not day.session_segments:
                continue  # Do not invent a close instant for an unknown session.
            start = datetime.combine(
                day.market_date, day.session_segments[0].start, zone
            ).astimezone(UTC)
            end = datetime.combine(day.market_date, day.session_segments[-1].end, zone).astimezone(
                UTC
            )
            output["D1"].append(
                Bar(
                    security,
                    "D1",
                    start,
                    end,
                    end,
                    None,
                    bar.retrieved_at,
                    bar.open,
                    bar.high,
                    bar.low,
                    bar.close,
                    bar.volume,
                    adjustment=capture["adjustment_basis"],
                    source_ref=row["version_hash"],
                )
            )
        for derived in weekly + m30:
            tf = derived.timeframe.value
            completed = derived.interval_end
            if tf == "W1":
                week_days = [
                    d
                    for d in calendar
                    if derived.interval_start.astimezone(zone).date()
                    <= d.market_date
                    < derived.interval_end.astimezone(zone).date()
                ]
                if not week_days or not week_days[-1].session_segments:
                    continue
                # Incomplete left boundary of the supplied calendar cannot certify a full week.
                if (
                    calendar
                    and derived.interval_start.astimezone(zone).date() < calendar[0].market_date
                ):
                    continue
                last = week_days[-1]
                completed = datetime.combine(
                    last.market_date, last.session_segments[-1].end, zone
                ).astimezone(UTC)
            output[tf].append(
                Bar(
                    security,
                    derived.timeframe.value,
                    derived.interval_start,
                    derived.interval_end,
                    completed,
                    None,
                    observed,
                    derived.open,
                    derived.high,
                    derived.low,
                    derived.close,
                    derived.volume,
                    completed=derived.is_completed,
                    coverage=derived.coverage.value,
                    adjustment=capture["adjustment_basis"],
                    session=derived.session_type or "REGULAR",
                    source_ref=derived.interval_start.isoformat(),
                )
            )
        provenance = (
            ("provider", capture["provider"]),
            ("capture_id", capture["capture_id"]),
            ("capture_hash", archive_digest(capture)),
            ("retrieved_at", capture["completed_at"]),
            (
                "calendar_origin",
                "immutable Capture calendar; not independent calendar completeness certification",
            ),
            ("adjustment", capture["adjustment_basis"]),
            ("precision", "exact stored decimal text; upstream SDK/source precision not certified"),
            ("historical_availability", "unknown; retrospective observation only"),
            (
                "normalizer",
                "unchanged 006A derive_weekly_bars/derive_m30_bars; "
                "first partial calendar week excluded",
            ),
        )
        return tuple(
            Dataset(
                security,
                cast(Timeframe, tf),
                zone.key,
                tuple(output[tf]),
                "PARTIAL",
                "OBSERVATIONAL",
                provenance,
            )
            for tf in ("W1", "D1", "M30")
        )


def read_archive(path: Path, capture_id: str) -> tuple[Dataset, ...]:
    return normalize_capture(*load_capture(path, capture_id))
