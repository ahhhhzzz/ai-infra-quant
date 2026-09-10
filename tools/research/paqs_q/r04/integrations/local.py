"""Read only frozen authorized exports; no network, credentials or database access."""

import json
from datetime import UTC, date, datetime, time, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from ...io import read_dataset
from ...types import Dataset
from ..calendar import Fact


def stamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def captured_fact(r: dict[str, Any], capture_id: str) -> Fact:
    day = date.fromisoformat(r["market_date"])
    zone = ZoneInfo(r["market_timezone"])
    segments = tuple(
        (
            datetime.combine(day, time.fromisoformat(s["start"]), zone).astimezone(UTC),
            datetime.combine(day, time.fromisoformat(s["end"]), zone).astimezone(UTC),
        )
        for s in r["session_segments"]
    )
    return Fact(
        day,
        r["market"],
        zone.key,
        "OPEN" if r["day_type"] in {"FULL", "MORNING_ONLY", "AFTERNOON_ONLY"} else "UNKNOWN",
        segments,
        "capture:" + capture_id,
        stamp(r["retrieved_at"]),
        None,
        False,
    )


def load(
    root: Path, data_dir: Path, calendar_file: Path
) -> tuple[dict[str, Dataset], tuple[Fact, ...], dict[str, Any]]:
    freeze = json.loads((root / "docs/evidence/TASK_006B_Q/research-04/freeze.json").read_text())
    original: dict[str, Dataset] = {}
    for name, expected in freeze["observation_hashes"].items():
        path = data_dir / name
        if sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("ORIGINAL_SOURCE_HASH_MISMATCH")
        data = read_dataset(path)
        original[data.timeframe] = data
    if sha256(calendar_file.read_bytes()).hexdigest() != freeze["calendar_export_sha256"]:
        raise ValueError("CALENDAR_SOURCE_HASH_MISMATCH")
    raw = json.loads(calendar_file.read_text(encoding="utf-8"))
    zone = ZoneInfo("America/New_York")
    by_day = {}
    for r in raw["calendar"]:
        f = captured_fact(r, raw["capture_id"])
        if f.day in by_day:
            raise ValueError("DUPLICATE_CAPTURE_CALENDAR_DAY")
        by_day[f.day] = f
    first = date.fromisoformat(raw["batch"]["requested_start"])
    last = date.fromisoformat(raw["batch"]["requested_end"])
    closures = {date.fromisoformat(d) for d in freeze["calendar_closures_2026"]}
    for i in range((last - first).days + 1):
        day = first + timedelta(days=i)
        if day in closures and day in by_day:
            raise ValueError("CAPTURE_CLOSURE_CONFLICT")
        if day not in by_day:
            known = day.weekday() >= 5 or day in closures
            by_day[day] = Fact(
                day,
                "US",
                zone.key,
                "CLOSED" if known else "UNKNOWN",
                (),
                freeze["calendar_source"] if known else "NO_EVIDENCED_SESSION_OR_CLOSURE",
                stamp(freeze["calendar_checked_at"]),
                None,
                False,
            )
    facts = tuple(by_day[k] for k in sorted(by_day))
    metadata = {
        "calendar_export_sha256": freeze["calendar_export_sha256"],
        "calendar_batch": raw["batch"],
        "capture_id": raw["capture_id"],
        "calendar_fact_counts": {
            kind: sum(f.kind == kind for f in facts) for kind in ("OPEN", "CLOSED", "UNKNOWN")
        },
        "historical_calendar_availability": "UNKNOWN",
        "calendar_mapping": "observational US vendor-market; MIC not certified",
        "calendar_sources": [freeze["calendar_source"], freeze["calendar_crosscheck"]],
        "price_hashes": freeze["observation_hashes"],
        "source_paths": str(data_dir),
        "calendar_path": str(calendar_file),
        "additional_usable_equities": 0,
        "price_requests": 0,
        "opend_history_requests": 0,
        "original_data_preserved": True,
        "raw_normalizer_match": "verified before freeze; no in-place changes",
    }
    return original, facts, metadata
