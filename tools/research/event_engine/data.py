"""Explicit local input adapters and labelled synthetic demonstration, without acquisition."""

import json
from dataclasses import asdict
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON
from ai_infra_quant.core.domain.paqs_q.inputs import Bar, Fact, QInput
from tools.research.paqs_q.io import read_dataset

D = Decimal


def read_input(path: Path, calendar: Path | None, mode: str) -> QInput:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if raw.get("schema_version") == "paqs-q-input-v1":
        data = decode_input(raw)
        if data.mode != mode:
            raise ValueError("MODE_MUST_MATCH_CANONICAL_INPUT")
        if calendar is not None:
            raise ValueError("CANONICAL_INPUT_ALREADY_CONTAINS_CALENDAR")
        return data
    dataset = read_dataset(path)
    if calendar is None:
        raise ValueError("CALENDAR_FILE_REQUIRED")
    bars = tuple(Bar(**asdict(b)) for b in dataset.bars)
    facts = read_calendar(calendar)
    known = [b.completed_at for b in bars]
    known += [b.available_at for b in bars if b.available_at is not None]
    known += [f.available_at for f in facts if f.available_at is not None]
    if not known:
        raise ValueError("EMPTY_INPUT_REQUIRES_EXPLICIT_CANONICAL_AS_OF")
    market = dataset.security.split(".")[0]
    return QInput(
        dataset.security,
        market,
        "USD" if market == "US" else "HKD",
        dataset.market_timezone,
        dataset.timeframe,
        max(known),
        bars,
        facts,
        dataset.quality,
        mode,
        provenance=FrozenJSON.of(
            {
                "adapter": "qstr-observations-v1/capture-calendar-v1",
                "input_file_sha256": sha256(path.read_bytes()).hexdigest(),
                "calendar_file_sha256": sha256(calendar.read_bytes()).hexdigest(),
                "original_provenance": dataset.provenance,
                "as_of_policy": (
                    "latest supplied completion/known availability; not historical certification"
                ),
            }
        ),
    )


def read_calendar(path: Path) -> tuple[Fact, ...]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    result = []
    for row in raw["calendar"]:
        day = date.fromisoformat(row["market_date"])
        zone = ZoneInfo(row["market_timezone"])
        segments = tuple(
            (
                datetime.combine(day, time.fromisoformat(s["start"]), zone),
                datetime.combine(day, time.fromisoformat(s["end"]), zone),
            )
            for s in row["session_segments"]
        )
        kind = {
            "FULL": "OPEN",
            "MORNING_ONLY": "OPEN",
            "AFTERNOON_ONLY": "OPEN",
            "CLOSED": "CLOSED",
        }.get(row["day_type"], "UNKNOWN")
        # Capture time is retrieval, never fabricated historical calendar availability.
        available = row.get("available_at")
        result.append(
            Fact(
                day,
                row["market"],
                row["market_timezone"],
                kind,
                segments,
                row["provider"],
                datetime.fromisoformat(row["retrieved_at"]),
                datetime.fromisoformat(available) if available else None,
                row.get("complete", False),
            )
        )
    return tuple(result)


def decode_input(raw: dict[str, Any]) -> QInput:
    """Read F1's own payload, checking declared per-fact versions instead of dropping fields."""
    data = dict(raw)
    if data.pop("schema_version") != "paqs-q-input-v1":
        raise ValueError("INPUT_SCHEMA")
    bars = []
    for row in data.pop("bars"):
        values = dict(row)
        ref = values.pop("version_ref")
        values["security"] = values.pop("security_id")
        values["start"] = values.pop("start_utc")
        for field in ("open", "high", "low", "close", "volume"):
            if not isinstance(values[field], str):
                raise ValueError("DECIMAL_TEXT_REQUIRED")
            values[field] = D(values[field])
        for field in ("start", "end", "completed_at", "retrieved_at", "available_at"):
            if values[field] is not None:
                values[field] = datetime.fromisoformat(values[field])
        bar = Bar(**values)
        if bar.version_ref != ref:
            raise ValueError("INPUT_PRICE_VERSION_MISMATCH")
        bars.append(bar)
    facts = []
    for row in data.pop("calendar"):
        values = dict(row)
        ref = values.pop("version_ref")
        values["day"] = date.fromisoformat(values.pop("date"))
        values["segments"] = tuple(
            (datetime.fromisoformat(a), datetime.fromisoformat(b)) for a, b in values["segments"]
        )
        for field in ("retrieved_at", "available_at"):
            if values[field] is not None:
                values[field] = datetime.fromisoformat(values[field])
        fact = Fact(**values)
        if fact.ref != ref:
            raise ValueError("INPUT_CALENDAR_VERSION_MISMATCH")
        facts.append(fact)
    data["security"] = data.pop("security_id")
    data["market_timezone"] = data.pop("timezone")
    data["mode"] = data.pop("qualification_mode")
    data["as_of"] = datetime.fromisoformat(data["as_of"])
    data["provenance"] = FrozenJSON.of(data["provenance"])
    return QInput(**data, bars=tuple(bars), calendar=tuple(facts))


def daily_input(values: list[tuple[str, str, str, str]], *, mode: str = "AS_OF") -> QInput:
    """Every price/calendar fact is explicitly synthetic, including weekday sessions."""
    bars: list[Bar] = []
    facts: list[Fact] = []
    day = date(2025, 1, 6)
    zone = ZoneInfo("America/New_York")
    known = datetime(2025, 1, 1, tzinfo=UTC)
    while len(bars) < len(values):
        start = datetime.combine(day, time(9, 30), zone)
        end = datetime.combine(day, time(16), zone)
        opened = day.weekday() < 5
        facts.append(
            Fact(
                day,
                "US",
                str(zone),
                "OPEN" if opened else "CLOSED",
                ((start, end),) if opened else (),
                "SYNTHETIC",
                known,
                known,
                True,
            )
        )
        if opened:
            o, h, low, c = map(D, values[len(bars)])
            bars.append(Bar("US.SYNTH", "D1", start, end, end, end, end, o, h, low, c, D(100)))
        day += timedelta(days=1)
    return QInput(
        "US.SYNTH",
        "US",
        "USD",
        str(zone),
        "D1",
        bars[-1].completed_at,
        tuple(bars),
        tuple(facts),
        mode=mode,
        provenance=FrozenJSON.of({"source": "SYNTHETIC_EVENT_DEMO_V1"}),
    )


def demo_input(*, mirror: bool = False, mode: str = "AS_OF") -> QInput:
    # Repeated 100..110 swings seed independent touches and an active range.
    closes = list(range(100, 111)) + list(range(109, 99, -1))
    closes += (list(range(101, 111)) + list(range(109, 99, -1))) * 3
    closes += [
        102,
        105,
        108,
        110,
        113,
        115,
        112,
        111,
        113,
        116,
        118,
        116,
        113,
        115,
        119,
        122,
        119,
        116,
        118,
        120,
        110,
        99,
        101,
        104,
        106,
        103,
        99,
        95,
        98,
        102,
        105,
        108,
        110,
        108,
        104,
        100,
        95,
        90,
        94,
        98,
        97,
        96,
    ]
    result: list[tuple[str, str, str, str]] = []
    previous = D(closes[0])
    for value in closes:
        close = D(value)
        opened = previous
        high, low = max(opened, close) + D(".2"), min(opened, close) - D(".2")
        if len(result) == 88:
            low = D("110.3")
        if mirror:
            row = (D(300) - opened, D(300) - low, D(300) - high, D(300) - close)
        else:
            row = (opened, high, low, close)
        result.append((str(row[0]), str(row[1]), str(row[2]), str(row[3])))
        previous = close
    return daily_input(result, mode=mode)
