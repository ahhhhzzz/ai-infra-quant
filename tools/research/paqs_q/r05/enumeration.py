"""Frozen exact local OHLC enumeration, deliberately separate from market sampling."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from itertools import product
from typing import Any

from ..r03.models import raw
from ..r04.calendar import Fact, support
from ..types import Bar, canonical
from .model import accepts

ALPHABET = tuple(
    (Decimal(low), Decimal(close), Decimal(high))
    for low, close, high in product((1, 2, 3), repeat=3)
    if low <= close <= high
)
STATES = ("COMPLETE", "J2_UNKNOWN", "J2_MISSING", "PROHIBITED_SEGMENT")


def domains() -> dict[str, bool]:
    """Actual calendar helper, independent of prices; cache eligibility for the finite domain."""
    day = date(2026, 1, 5)
    known = datetime(2020, 1, 1, tzinfo=UTC)
    start = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    f = Fact(
        day,
        "US",
        "America/New_York",
        "OPEN",
        ((start, start + timedelta(hours=6, minutes=30)),),
        "SYNTHETIC-ENUM",
        known,
        known,
        True,
    )
    bars = tuple(
        Bar(
            "US.TEST",
            "M30",
            start + timedelta(minutes=30 * i),
            start + timedelta(minutes=30 * (i + 1)),
            start + timedelta(minutes=30 * (i + 1)),
            start + timedelta(minutes=30 * (i + 1)),
            start + timedelta(minutes=30 * (i + 1)),
            Decimal(2),
            Decimal(3),
            Decimal(1),
            Decimal(2),
            Decimal(1),
        )
        for i in range(4)
    )
    support(bars, {day: f}, "AS_OF")
    # The two incomplete domains express absent/unknown extra observation; the
    # current triple remains supported. The fourth crosses a different session.
    from dataclasses import replace

    changed = replace(
        bars[0], start=bars[0].start - timedelta(days=1), end=bars[0].end - timedelta(days=1)
    )
    prior_day = day - timedelta(days=1)
    prior = replace(
        f,
        day=prior_day,
        segments=(
            (start - timedelta(days=1), start - timedelta(days=1) + timedelta(hours=6, minutes=30)),
        ),
    )
    for calendar in (
        {day: f},
        {day: f, prior_day: replace(prior, kind="UNKNOWN")},
        {day: f, prior_day: prior},
    ):
        support(bars[1:], calendar, "AS_OF")
        try:
            support((changed, *bars[1:]), calendar, "AS_OF")
        except ValueError:
            pass
        else:
            raise AssertionError("INELIGIBLE_QUARTET_ACCEPTED")
    return {s: s == "COMPLETE" for s in STATES}


def enumerate_domain() -> dict[str, Any]:
    eligibility = domains()
    stream = sha256()
    counts = {s: {"inputs": 0, "B0": 0, "A1": 0, "veto": 0} for s in STATES}
    witness = None
    for sequence in product(ALPHABET, repeat=4):
        lows, closes, highs = (tuple(b[k] for b in sequence) for k in (0, 1, 2))
        previous, current = raw(highs, lows, closes, 1), raw(highs, lows, closes, 2)
        assert not (previous[0] and current[0]) and not (previous[1] and current[1])
        # Independent literal inequalities, not the candidate classifier.
        scale = highs[1] - lows[1]
        down = (
            scale > 0
            and highs[2] > highs[1]
            and highs[2] > highs[3]
            and highs[2] - closes[3] >= scale
        )
        up = scale > 0 and lows[2] < lows[1] and lows[2] < lows[3] and closes[3] - lows[2] >= scale
        assert current == (down, up)
        for state in STATES:
            eligible = eligibility[state]
            b = eligible and down != up and not any(previous)
            a = accepts(current, eligible)
            veto = eligible and down != up and any(previous)
            assert not b or a
            assert int(a) - int(b) == int(veto)
            counts[state]["inputs"] += 1
            counts[state]["B0"] += b
            counts[state]["A1"] += a
            counts[state]["veto"] += veto
            stream.update((canonical((sequence, state, b, a, veto)) + "\n").encode())
            if veto and witness is None:
                witness = {
                    "OHLC_open_equals_close": sequence,
                    "state": state,
                    "previous_raw": previous,
                    "current_raw": current,
                }
    assert witness is not None
    return {
        "status": "PASS",
        "synthetic_only": True,
        "alphabet": ALPHABET,
        "calendar_states": STATES,
        "input_count": len(ALPHABET) ** 4 * len(STATES),
        "ordered_input_and_output_sha256": stream.hexdigest(),
        "counts": counts,
        "veto_accept_witness": witness,
        "adjacent_same_kind_raw_counterexamples": 0,
        "set_or_bijection_failures": 0,
    }
