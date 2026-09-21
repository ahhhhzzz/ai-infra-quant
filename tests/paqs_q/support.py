"""Explicit frozen-data decoding and labelled synthetic facts; no research imports."""

import json
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.paqs_q.inputs import Bar, Fact, QInput

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = Path(__file__).parent / "golden"


def read_golden() -> dict[str, Any]:
    value: dict[str, Any] = json.loads((GOLDEN / "r05.json").read_text(encoding="utf-8"))
    return value


def decode(raw: dict[str, Any]) -> QInput:
    bars = []
    for row in raw["bars"]:
        values = dict(row)
        for key in ("open", "high", "low", "close", "volume"):
            values[key] = Decimal(values[key])
        for key in ("start", "end", "completed_at", "retrieved_at", "available_at"):
            if values[key] is not None:
                values[key] = datetime.fromisoformat(values[key])
        bars.append(Bar(**values))
    facts = []
    for row in raw["calendar"]:
        values = dict(row)
        values["day"] = date.fromisoformat(values["day"])
        values["segments"] = tuple(
            (datetime.fromisoformat(a), datetime.fromisoformat(b)) for a, b in values["segments"]
        )
        for key in ("retrieved_at", "available_at"):
            if values[key] is not None:
                values[key] = datetime.fromisoformat(values[key])
        facts.append(Fact(**values))
    market = raw["security"].split(".")[0]
    return QInput(
        raw["security"],
        market,
        "USD" if market == "US" else "HKD",
        raw["market_timezone"],
        raw["timeframe"],
        datetime.fromisoformat(raw["as_of"]),
        tuple(bars),
        tuple(facts),
        raw["quality"],
        raw["mode"],
    )


def synthetic(*, chain: bool = True) -> QInput:
    spec = json.loads((GOLDEN / "synthetic.json").read_text(encoding="utf-8"))["recipe"]
    bars: list[Bar] = []
    facts: list[Fact] = []
    zone = ZoneInfo("America/New_York")
    day = date.fromisoformat(spec["first_session"])
    available = datetime(2026, 1, 1, tzinfo=UTC)
    while len(bars) < spec["bars"]:
        start = datetime.combine(day, time(9, 30), zone).astimezone(UTC)
        end = datetime.combine(day, time(16), zone).astimezone(UTC)
        opened = day.weekday() < 5
        facts.append(
            Fact(
                day,
                "US",
                "America/New_York",
                "OPEN" if opened else "CLOSED",
                ((start, end),) if opened else (),
                "SYNTHETIC",
                available,
                available,
                True,
            )
        )
        if opened:
            for index in range(13):
                if len(bars) == spec["bars"]:
                    break
                left, right = (
                    start + timedelta(minutes=30 * index),
                    start + timedelta(minutes=30 * (index + 1)),
                )
                values = (
                    spec["overrides"].get(str(len(bars)), spec["default_ohlcv"])
                    if chain
                    else spec["default_ohlcv"]
                )
                o, h, low, c, v = (Decimal(x) for x in values)
                bars.append(
                    Bar("US.SYNTH", "M30", left, right, right, right, right, o, h, low, c, v)
                )
        day += timedelta(days=1)
    return QInput(
        "US.SYNTH",
        "US",
        "USD",
        "America/New_York",
        "M30",
        bars[-1].completed_at,
        tuple(bars),
        tuple(facts),
    )
