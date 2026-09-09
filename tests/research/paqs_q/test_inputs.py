"""Local-only wire and accepted session-normalization boundary tests."""

import json
import socket
import sqlite3
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from tools.research.paqs_q.engine import evaluate, prepare
from tools.research.paqs_q.fixtures import synthetic
from tools.research.paqs_q.integrations.local_archive import load_capture, normalize_capture
from tools.research.paqs_q.io import read_dataset, write_dataset


def capture_fixture(
    market: str, day: date, half: bool = False
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    zone = ZoneInfo("America/New_York" if market == "US" else "Asia/Hong_Kong")
    segments = (
        [(time(9, 30), time(13 if half else 16))]
        if market == "US"
        else [(time(9, 30), time(12)), (time(13), time(16))]
    )
    observed = datetime.combine(day + timedelta(days=1), time.min, UTC).isoformat()
    capture: dict[str, Any] = {
        "capture_id": "SYNTHETIC",
        "market": market,
        "symbol": "AVGO" if market == "US" else "00700",
        "market_timezone": zone.key,
        "completed_at": observed,
        "provider": "SYNTHETIC",
        "adjustment_basis": "SYNTHETIC",
        "calendar": [
            {
                "market": market,
                "market_date": day.isoformat(),
                "market_timezone": zone.key,
                "day_type": "MORNING_ONLY" if half else "FULL",
                "provider_day_type": "SYNTHETIC",
                "session_segments": [
                    {"start": a.isoformat(), "end": b.isoformat()} for a, b in segments
                ],
                "provider": "SYNTHETIC",
                "retrieved_at": observed,
            }
        ],
    }
    # The synthetic supplied calendar declares the rest of this week, so one D1
    # observation cannot be relabelled a complete week.
    first = capture["calendar"][0]
    capture["calendar"] = [
        {**first, "market_date": (day + timedelta(days=i)).isoformat()} for i in range(5)
    ]
    daily = [
        {
            "session_date": day.isoformat(),
            "provider_time": observed,
            "open": "100",
            "high": "102",
            "low": "99",
            "close": "101",
            "volume": "1000",
            "retrieved_at": observed,
            "version_hash": "SYNTHETIC",
        }
    ]
    minutes = []
    for start, end in segments:
        left = datetime.combine(day, start, zone).astimezone(UTC)
        right = datetime.combine(day, end, zone).astimezone(UTC)
        while left < right:
            minutes.append(
                {
                    "interval_start": left.isoformat(),
                    "interval_end": (left + timedelta(minutes=1)).isoformat(),
                    "open": "100",
                    "high": "102",
                    "low": "99",
                    "close": "101",
                    "volume": "1",
                    "retrieved_at": observed,
                }
            )
            left += timedelta(minutes=1)
    return capture, {"D1": daily, "M1": minutes}


@pytest.mark.parametrize(
    "market,half,buckets", [("US", False, 13), ("US", True, 7), ("HK", False, 11)]
)
def test_archive_normalization_regular_sessions_breaks_and_half_days(
    market: str, half: bool, buckets: int
) -> None:
    capture, batches = capture_fixture(market, date(2026, 7, 6), half)
    weekly, daily, m30 = normalize_capture(capture, batches)
    assert len(m30.bars) == buckets
    assert all(b.available_at is None and b.volume == Decimal(30) for b in m30.bars)
    assert m30.mode == "OBSERVATIONAL" and m30.quality == "PARTIAL"
    assert not any(b.completed for b in weekly.bars)
    assert daily.bars[0].completed_at == daily.bars[0].end
    if market == "HK":
        assert all(b.start.astimezone(ZoneInfo("Asia/Hong_Kong")).hour != 12 for b in m30.bars)
    # A missing minute remains missing; never forward-filled into a COMPLETE bucket.
    batches["M1"].pop(12)
    partial = normalize_capture(capture, batches)[2]
    assert len(prepare(partial, datetime.fromisoformat(capture["completed_at"]))) == buckets - 1


def test_archive_normalization_us_dst_completion() -> None:
    winter = normalize_capture(*capture_fixture("US", date(2026, 3, 6)))[2]
    summer = normalize_capture(*capture_fixture("US", date(2026, 3, 9)))[2]
    assert winter.bars[0].start.hour == 14
    assert summer.bars[0].start.hour == 13
    assert not prepare(winter, winter.bars[0].end - timedelta(microseconds=1))


def test_archive_connection_is_read_only_even_when_schema_is_missing(tmp_path: Path) -> None:
    database = tmp_path / "archive.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE unrelated(value TEXT)")
        connection.execute("INSERT INTO unrelated VALUES ('retain')")
    before = database.read_bytes()
    with pytest.raises(sqlite3.OperationalError, match="no such table"):
        load_capture(database, "missing")
    assert database.read_bytes() == before
    with pytest.raises(ValueError, match="NOT_FOUND"):
        load_capture(tmp_path / "absent.db", "missing")
    assert not (tmp_path / "absent.db").exists()


def test_json_roundtrip_decimal_required_and_cli(tmp_path: Path) -> None:
    data = synthetic()
    path = tmp_path / "fixture.json"
    write_dataset(path, data)
    assert read_dataset(path) == data
    output = tmp_path / "result.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.research.paqs_q",
            "analyze",
            str(path),
            "--cutoff",
            data.bars[-1].completed_at.isoformat(),
            "--output",
            str(output),
        ],
        check=True,
    )
    assert (
        json.loads(output.read_text())["semantic_hash"]
        == evaluate(data, data.bars[-1].completed_at).semantic_hash
    )
    raw = json.loads(path.read_text())
    raw["dataset"]["bars"][0]["close"] = 123.45
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="DECIMAL_TEXT"):
        read_dataset(path)


def test_ordinary_calculation_never_opens_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", forbidden)
    data = synthetic()
    assert (
        evaluate(data, data.bars[-1].completed_at).document()["decision"]["input_status"]
        == "COMPLETE"
    )


def test_identity_overlap_timezone_and_nonregular_m30_rejected() -> None:
    data = synthetic("M30")
    for bad in (
        replace(data, market_timezone="Asia/Hong_Kong"),
        replace(data, bars=(*data.bars[:-1], replace(data.bars[-1], session="EXTENDED"))),
        replace(
            data,
            bars=(
                *data.bars[:-1],
                replace(data.bars[-1], start=data.bars[-2].start + timedelta(minutes=1)),
            ),
        ),
    ):
        decision = evaluate(bad, data.bars[-1].completed_at).document()["decision"]
        assert decision["input_status"] == "INVALID" and decision["regime"] == "UNCERTAIN"
