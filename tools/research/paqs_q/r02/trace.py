"""Instrumented baseline transition oracle; intervention arguments are diagnostic-only."""

from decimal import Decimal, localcontext
from typing import Any

from ..types import CONTEXT, Bar, Parameters


def trace(
    bars: tuple[Bar, ...],
    atrs: tuple[Decimal | None, ...],
    params: Parameters,
    *,
    seed_start: int = 0,
    eligible_seed: bool = False,
) -> list[dict[str, Any]]:
    """Mirror baseline state transitions, recording all operands rather than relabelling."""
    if len(bars) != len(atrs):
        raise ValueError("ATR_ALIGNMENT")
    rows: list[dict[str, Any]] = []
    state = "UNSEEDED"
    high: int | None = None
    low: int | None = None
    previous: int | None = None
    with localcontext(CONTEXT):
        for i, (bar, atr) in enumerate(zip(bars, atrs, strict=True)):
            if i < seed_start or atr is None or atr <= 0:
                continue
            before = state
            admissible = not eligible_seed or previous is None or i - previous >= 2
            if (
                admissible
                and state in {"UNSEEDED", "SEEK_HIGH"}
                and (high is None or bar.high > bars[high].high)
            ):
                high = i
            if (
                admissible
                and state in {"UNSEEDED", "SEEK_LOW"}
                and (low is None or bar.low < bars[low].low)
            ):
                low = i
            threshold = params.pivot_lambda * atr
            down = high is not None and high < i and bars[high].high - bar.close >= threshold
            up = low is not None and low < i and bar.close - bars[low].low >= threshold
            kind: str | None = None
            extreme: int | None = None
            if state == "UNSEEDED" and down != up:
                kind, extreme = ("HIGH", high) if down else ("LOW", low)
            elif state == "SEEK_HIGH" and down and high is not None and previous is not None:
                if high - previous >= 2:
                    kind, extreme = "HIGH", high
            elif (
                state == "SEEK_LOW"
                and up
                and low is not None
                and previous is not None
                and low - previous >= 2
            ):
                kind, extreme = "LOW", low
            row = {
                "index": i,
                "ref": bar.ref,
                "start": bar.start,
                "completed_at": bar.completed_at,
                "state_before": before,
                "atr": atr,
                "threshold": threshold,
                "close": bar.close,
                "high": high,
                "low": low,
                "high_ref": bars[high].ref if high is not None else None,
                "low_ref": bars[low].ref if low is not None else None,
                "high_price": bars[high].high if high is not None else None,
                "low_price": bars[low].low if low is not None else None,
                "down_distance": bars[high].high - bar.close if high is not None else None,
                "up_distance": bar.close - bars[low].low if low is not None else None,
                "down": down,
                "up": up,
                "dual": before == "UNSEEDED" and down and up,
                "high_separation": high - previous
                if high is not None and previous is not None
                else None,
                "low_separation": low - previous
                if low is not None and previous is not None
                else None,
                "emitted": (kind, bars[extreme].ref, bar.ref) if extreme is not None else None,
            }
            if kind is not None and extreme is not None:
                previous = extreme
                state = "SEEK_LOW" if kind == "HIGH" else "SEEK_HIGH"
                if kind == "HIGH":
                    low = i if not eligible_seed or i - extreme >= 2 else None
                else:
                    high = i if not eligible_seed or i - extreme >= 2 else None
            row["state_after"] = state
            rows.append(row)
    return rows


def events(rows: list[dict[str, Any]], active_refs: set[str]) -> list[Any]:
    return [
        r["emitted"]
        for r in rows
        if r["emitted"] and r["emitted"][1] in active_refs and r["emitted"][2] in active_refs
    ]
