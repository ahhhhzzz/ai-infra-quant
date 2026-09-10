"""Canonical archive day-type regression, independent of market output."""

from datetime import date

import pytest

from tools.research.paqs_q.r04.calendar import slot
from tools.research.paqs_q.r04.integrations.local import captured_fact

from .test_calendar_model import bar


@pytest.mark.parametrize(
    "kind,start,end",
    [
        ("FULL", "09:30:00", "16:00:00"),
        ("MORNING_ONLY", "09:30:00", "13:00:00"),
        ("AFTERNOON_ONLY", "13:00:00", "16:00:00"),
    ],
)
def test_canonical_partial_day_preserves_evidenced_segments(
    kind: str, start: str, end: str
) -> None:
    f = captured_fact(
        {
            "market_date": "2026-11-27",
            "market": "US",
            "market_timezone": "America/New_York",
            "day_type": kind,
            "session_segments": [{"start": start, "end": end}],
            "retrieved_at": "2026-12-01T00:00:00Z",
        },
        "SYNTHETIC-ARCHIVE-SCHEMA",
    )
    assert f.kind == "OPEN" and f.day == date(2026, 11, 27)
    assert f.available_at is None and not f.complete
    b = bar(f.segments[0][0], f.segments[0][1])
    assert slot(b, {f.day: f}, "OBSERVATIONAL")[0] == (f,)
    with pytest.raises(ValueError, match="CALENDAR_NOT_STRICT"):
        slot(b, {f.day: f}, "AS_OF")


@pytest.mark.parametrize("kind", ["UNKNOWN", "HALF", "invalid"])
def test_undocumented_enum_never_certifies(kind: str) -> None:
    f = captured_fact(
        {
            "market_date": "2026-11-27",
            "market": "US",
            "market_timezone": "America/New_York",
            "day_type": kind,
            "session_segments": [{"start": "09:30:00", "end": "13:00:00"}],
            "retrieved_at": "2026-12-01T00:00:00Z",
        },
        "SYNTHETIC-ARCHIVE-SCHEMA",
    )
    with pytest.raises(ValueError, match="CALENDAR_UNKNOWN"):
        slot(bar(f.segments[0][0], f.segments[0][1]), {f.day: f}, "OBSERVATIONAL")
