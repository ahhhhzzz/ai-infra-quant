"""Availability audit for every observation consumed by a diagnostic arm."""

from datetime import datetime
from typing import Any

from .types import Bar, Dataset, digest, utc


def availability_check(bars: tuple[Bar, ...], data: Dataset, cutoff: datetime) -> dict[str, Any]:
    completed_bad = sum(not b.completed or utc(b.completed_at) > utc(cutoff) for b in bars)
    available_bad = sum(
        b.available_at is not None and utc(b.available_at) > utc(cutoff) for b in bars
    )
    unknown = sum(b.available_at is None for b in bars)
    missing_bad = unknown if data.mode == "AS_OF" else 0
    return {
        "cutoff": utc(cutoff).isoformat(),
        "observation_count": len(bars),
        "completion_violations": completed_bad,
        "availability_violations": available_bad,
        "unknown_availability_count": unknown,
        "as_of_unknown_violations": missing_bad,
        "violation_count": completed_bad + available_bad + missing_bad,
        "availability_status": "OBSERVATIONAL_UNKNOWN" if unknown else "EXPLICIT_AS_OF",
        "evidence_time_hash": digest(
            "qstr-evidence-times", tuple((b.ref, b.completed_at, b.available_at) for b in bars)
        ),
    }


def information_change(
    old: tuple[Bar, ...], new: tuple[Bar, ...], old_cutoff: datetime, left: datetime
) -> dict[str, int]:
    """Compare historical versions separately from adding the new right bar."""
    previous = {b.start: b for b in old if b.start >= left}
    current = {b.start: b for b in new if b.start >= left and b.completed_at <= old_cutoff}
    shared = previous.keys() & current.keys()
    revised = sum(
        (previous[k].observation(), previous[k].available_at)
        != (current[k].observation(), current[k].available_at)
        for k in shared
    )
    return {
        "revised_historical_count": revised,
        "newly_available_historical_count": len(current.keys() - previous.keys()),
        "missing_at_new_cutoff_count": len(previous.keys() - current.keys()),
    }
