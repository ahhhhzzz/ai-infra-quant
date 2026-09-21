"""Reuse the research observation format and accept explicit CSV/calendar exports."""

import csv
import json
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from tools.research.paqs_q.io import read_dataset
from tools.research.paqs_q.types import Bar, Dataset, primitive

from ..model import Input


def stamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("TIME_REQUIRES_OFFSET")
    return parsed.astimezone(UTC)


def number(value: str) -> Decimal:
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError("DECIMAL_TEXT_REQUIRED")
    parsed = Decimal(value)
    if not parsed.is_finite() or abs(parsed) > Decimal("1e18"):
        raise ValueError("NONFINITE_OR_EXCESSIVE_VALUE")
    return parsed


def calendar(path: Path) -> tuple[dict[date, tuple[datetime, datetime]], dict[str, Any]]:
    sessions: dict[date, tuple[datetime, datetime]] = {}
    metadata: dict[str, Any] = {"sha256": sha256(path.read_bytes()).hexdigest()}
    if path.suffix.lower() == ".json":
        source = json.loads(path.read_text(encoding="utf-8-sig"))
        metadata.update(
            coverage_certified=source["batch"]["coverage_complete"] is True,
            source="006B1 captured calendar; observed schedule, not historical certification",
        )
        rows = []
        for row in source["calendar"]:
            segments = row["session_segments"]
            if row["day_type"] not in {"FULL", "MORNING_ONLY", "AFTERNOON_ONLY"}:
                raise ValueError("UNKNOWN_CALENDAR_DAY")
            zone = ZoneInfo(row["market_timezone"])
            day = date.fromisoformat(row["market_date"])
            rows.append(
                {
                    "date": day.isoformat(),
                    "open": datetime.combine(
                        day, time.fromisoformat(segments[0]["start"]), zone
                    ).isoformat(),
                    "close": datetime.combine(
                        day, time.fromisoformat(segments[-1]["end"]), zone
                    ).isoformat(),
                }
            )
    else:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        metadata.update(
            coverage_certified=False, source="user-supplied expected sessions; unverified"
        )
    for row in rows:
        day = date.fromisoformat(row["date"])
        pair = stamp(row["open"]), stamp(row["close"])
        if day in sessions or pair[0] >= pair[1]:
            raise ValueError("DUPLICATE_OR_INVALID_CALENDAR")
        sessions[day] = pair
    return sessions, metadata


def validate(data: Dataset, sessions: dict[date, tuple[datetime, datetime]]) -> None:
    if data.timeframe != "D1" or not 1 <= len(data.bars) <= 20000:
        raise ValueError("D1_SINGLE_SERIES_REQUIRED:1..20000 bars")
    zone = ZoneInfo(data.market_timezone)
    days: list[date] = []
    adjustments = set()
    for bar in data.bars:
        if bar.security != data.security or bar.timeframe != "D1" or bar.session != "REGULAR":
            raise ValueError("BAR_IDENTITY_CONFLICT")
        for value in (bar.start, bar.end, bar.completed_at, bar.retrieved_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("TIME_REQUIRES_OFFSET")
        if bar.available_at is not None and bar.available_at.tzinfo is None:
            raise ValueError("TIME_REQUIRES_OFFSET")
        if not bar.completed or bar.coverage != "COMPLETE":
            raise ValueError("UNFINISHED_OR_INCOMPLETE_BAR")
        if not bar.start < bar.end == bar.completed_at <= bar.retrieved_at:
            raise ValueError("INVALID_COMPLETION_TIME")
        if bar.completed_at > datetime.now(UTC):
            raise ValueError("FUTURE_COMPLETION")
        values = [number(str(getattr(bar, k))) for k in ("open", "high", "low", "close", "volume")]
        if min(values[:4]) <= 0 or values[4] < 0:
            raise ValueError("INVALID_PRICE_VOLUME")
        if bar.low > min(bar.open, bar.close) or bar.high < max(bar.open, bar.close, bar.low):
            raise ValueError("INVALID_OHLC")
        day = bar.start.astimezone(zone).date()
        if days and day <= days[-1]:
            raise ValueError("UNSORTED_OR_DUPLICATE_SESSION")
        if sessions.get(day) != (bar.start, bar.end):
            raise ValueError(f"CALENDAR_BAR_MISMATCH:{day}")
        days.append(day)
        adjustments.add(bar.adjustment)
    if len(adjustments) != 1 or next(iter(adjustments)) not in {
        "PROVIDER_QFQ_CURRENT",
        "SYNTHETIC",
        "UNADJUSTED",
        "SPLIT_ADJUSTED",
        "TOTAL_RETURN_ADJUSTED",
    }:
        raise ValueError("MIXED_OR_UNKNOWN_ADJUSTMENT")
    expected = sorted(day for day in sessions if days[0] <= day <= days[-1])
    if days != expected:
        raise ValueError("MISSING_SCHEDULED_BAR:do not skip or fill missing sessions")
    if data.quality == "INVALID":
        raise ValueError("INVALID_DATASET_QUALITY")


def load(path: Path, calendar_path: Path, timezone: str, currency: str) -> Input:
    if path.stat().st_size > 100_000_000 or calendar_path.stat().st_size > 20_000_000:
        raise ValueError("FILE_BOUND")
    if path.suffix.lower() == ".json":
        data = read_dataset(path)
    else:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if not rows:
            raise ValueError("EMPTY_CSV")
        bars = []
        for row in rows:
            bars.append(
                Bar(
                    security=row["security"],
                    timeframe="D1",
                    start=stamp(row["start"]),
                    end=stamp(row["end"]),
                    completed_at=stamp(row["end"]),
                    available_at=None,
                    retrieved_at=datetime.now(UTC),
                    open=number(row["open"]),
                    high=number(row["high"]),
                    low=number(row["low"]),
                    close=number(row["close"]),
                    volume=number(row["volume"]),
                    completed=row["completed"] == "true",
                    coverage=row["coverage"],
                    adjustment=row["adjustment"],
                    source_ref="LOCAL_CSV",
                )
            )
        data = Dataset(rows[0]["security"], "D1", timezone, tuple(bars), mode="OBSERVATIONAL")
    sessions, calendar_metadata = calendar(calendar_path)
    validate(data, sessions)
    if currency not in {"USD", "HKD"}:
        raise ValueError("CURRENCY_REQUIRED_USD_OR_HKD")
    expected = {"US": ("USD", "America/New_York"), "HK": ("HKD", "Asia/Hong_Kong")}
    if expected.get(data.security.split(".")[0]) != (currency, data.market_timezone):
        raise ValueError("SECURITY_CURRENCY_TIMEZONE_CONFLICT")
    return Input(
        data,
        currency,
        {
            "data_kind": "SYNTHETIC"
            if data.bars[0].adjustment == "SYNTHETIC"
            else "REAL_OBSERVATIONS",
            "mode": "EXPLORATORY_NOT_POINT_IN_TIME",
            "input_sha256": sha256(path.read_bytes()).hexdigest(),
            "calendar": calendar_metadata,
            "original_quality": data.quality,
            "original_provenance": primitive(data.provenance),
            "adjustment": data.bars[0].adjustment,
            "unknown_historical_availability": sum(b.available_at is None for b in data.bars),
            "late_historical_availability": sum(
                b.available_at is not None and b.available_at > b.completed_at for b in data.bars
            ),
            "limitations": [
                "事后观察/当前复权;不具备严格 point-in-time 历史版本认证。",
                "只核对所给日历中的缺失日;日历覆盖未经独立完整认证。",
                "当前复权价下名义股数;未建模拆股路径、股息、停牌/涨跌停、成交量及实际税费。",
            ],
        },
    )


def demo(directory: Path) -> tuple[Path, Path]:
    """Small deterministic paths with a winner, a gap stop and an open position."""
    directory.mkdir(parents=True, exist_ok=True)
    source, schedule = directory / "synthetic.csv", directory / "sessions.csv"
    rows: list[list[str]] = []
    calendar_rows = []
    day = date(2020, 1, 2)
    # Warmup then three identical signal prefixes; outcomes intentionally differ.
    prices = [("100", "101", "99", "100")] * 18
    setup = [
        ("100", "104", "99", "102"),
        ("101", "102", "99", "100"),
        ("100", "102", "99", "101"),
        ("102", "106", "101", "105"),
        ("105", "105.5", "103.8", "104.5"),
        ("104", "108", "103.8", "107.5"),
    ]
    for outcome in ("win", "gap", "open"):
        prices.extend(setup)
        prices.append(("108", "109", "107", "108"))
        if outcome == "win":
            prices.extend([("110", "121", "109", "120"), ("120", "121", "119", "120")])
        elif outcome == "gap":
            prices.append(("99", "101", "97", "100"))
        if outcome != "open":
            prices.extend([("100", "101", "99", "100")] * 18)
    for o, h, low, c in prices:
        while day.weekday() >= 5:
            day += timedelta(days=1)
        start = datetime.combine(day, time(9, 30), ZoneInfo("America/New_York"))
        end = datetime.combine(day, time(16), ZoneInfo("America/New_York"))
        rows.append(
            [
                "US.SYNTHETIC",
                start.isoformat(),
                end.isoformat(),
                o,
                h,
                low,
                c,
                "100000",
                "true",
                "COMPLETE",
                "SYNTHETIC",
            ]
        )
        calendar_rows.append([day.isoformat(), start.isoformat(), end.isoformat()])
        day += timedelta(days=1)
    for path, header, content in (
        (
            source,
            "security,start,end,open,high,low,close,volume,completed,coverage,adjustment",
            rows,
        ),
        (schedule, "date,open,close", calendar_rows),
    ):
        with path.open("x", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(header.split(","))
            writer.writerows(content)
    return source, schedule
