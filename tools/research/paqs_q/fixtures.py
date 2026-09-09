"""Explicit synthetic oscillations; never substitute these for a missing equity."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext

from .types import CONTEXT, Bar, Dataset, Timeframe


def synthetic(
    timeframe: Timeframe = "D1", count: int = 440, pattern: str = "oscillation"
) -> Dataset:
    if (
        pattern not in {"oscillation", "bull", "bear", "flat", "path_lock", "tight_range"}
        or not 0 <= count <= 10000
    ):
        raise ValueError("SYNTHETIC_PARAMETERS_INVALID")
    step = {"W1": timedelta(days=7), "D1": timedelta(days=1), "M30": timedelta(minutes=30)}[
        timeframe
    ]
    start = datetime(2010, 1, 4, tzinfo=UTC)
    bars = []
    with localcontext(CONTEXT):
        for index in range(count):
            period = 16 if pattern == "tight_range" else 24
            wave = Decimal(min(index % period, period - index % period)) * 2
            slope = (
                Decimal(index // 24)
                if pattern == "bull"
                else -Decimal(index // 24)
                if pattern == "bear"
                else Decimal(0)
            )
            close = Decimal(100) + wave + slope
            high, low = close + 1, close - 1
            if pattern == "flat":
                close = high = low = Decimal(100)
            if pattern == "path_lock" and index == 13:
                high, low = Decimal(200), Decimal(1)
            left = start + index * step
            right = left + step
            bars.append(
                Bar(
                    "US.AVGO",
                    timeframe,
                    left,
                    right,
                    right,
                    right,
                    right,
                    close,
                    high,
                    low,
                    close,
                    Decimal(10),
                )
            )
    return Dataset(
        "US.AVGO",
        timeframe,
        "America/New_York",
        tuple(bars),
        provenance=(("label", "SYNTHETIC_NOT_MARKET_DATA"), ("generator", pattern)),
    )
