"""Causal price-prefix signals; no portfolio state and no formal PAQS qualification."""

from decimal import localcontext
from typing import Any

from ai_infra_quant.core.strategy.paqs_q.local import raw
from ai_infra_quant.core.strategy.paqs_structure import (
    BarReference,
    StructureBar,
    StructureTimeframe,
    calculate_atr,
)
from tools.research.paqs_q.types import CONTEXT, Dataset, digest

from .model import STRATEGY, Config


def signals(data: Dataset, config: Config) -> dict[str, Any]:
    """Only read j-2..j+1 at confirmation; activate after that close."""
    with localcontext(CONTEXT):
        return _signals(data, config)


def _signals(data: Dataset, config: Config) -> dict[str, Any]:
    bars = data.bars
    atr = calculate_atr(
        tuple(
            StructureBar(
                b.security,
                StructureTimeframe.D1,
                BarReference(i, b.ref),
                b.open,
                b.high,
                b.low,
                b.close,
                b.volume,
                b.completed,
                b.coverage,
            )
            for i, b in enumerate(bars)
        )
    )
    high, low, close = (
        tuple(getattr(b, field) for b in bars) for field in ("high", "low", "close")
    )
    points: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    output: list[dict[str, Any]] = []
    level: dict[str, Any] | None = None
    watch: dict[str, Any] | None = None
    for i, bar in enumerate(bars):
        a = atr[i].value
        if a is not None and a > 0:
            if watch is not None:
                price = watch["level"]["price"]
                elapsed = i - watch["breakout_index"]
                if bar.close < price - config.failure_buffer * a:
                    events.append({"index": i, "type": "RETEST_FAILED", "price": price})
                    watch = None
                elif elapsed <= config.retest_window:
                    touched = (
                        bar.low <= price + config.outer * a and bar.high >= price - config.inner * a
                    )
                    if watch["touch_index"] is None and touched:
                        watch["touch_index"] = i
                        watch["min_low"] = bar.low
                        events.append({"index": i, "type": "RETEST_START", "price": price})
                    elif watch["touch_index"] is not None:
                        watch["min_low"] = min(watch["min_low"], bar.low)
                        span = bar.high - bar.low
                        strong = (
                            span > 0
                            and bar.close > bar.open
                            and bar.close > price
                            and (bar.close - bar.open) / span >= config.body_min
                            and (bar.close - bar.low) / span >= config.clv_min
                            and span / a >= config.range_min
                        )
                        if strong:
                            stop = watch["min_low"] - config.stop_buffer * a
                            if stop > 0:
                                signal = {
                                    "index": i,
                                    "signal_time": bar.completed_at,
                                    "level": price,
                                    "level_extreme_index": watch["level"]["extreme_index"],
                                    "level_known_index": watch["level"]["known_index"],
                                    "level_known_time": watch["level"]["known_time"],
                                    "level_support_refs": watch["level"]["support_refs"],
                                    "breakout_index": watch["breakout_index"],
                                    "touch_index": watch["touch_index"],
                                    "stop": stop,
                                    "atr": a,
                                    "signal_bar_ref": bar.ref,
                                    "reason": (
                                        "已确认局部高点突破后首次回踩;"
                                        "后续强阳线且收盘高于冻结点价位"
                                    ),
                                }
                                signal["signal_id"] = digest(STRATEGY, (config, signal))
                                output.append(signal)
                                events.append({"index": i, "type": "SIGNAL", "price": bar.close})
                            else:
                                events.append({"index": i, "type": "INVALID_STOP", "price": price})
                            watch = None
                    if watch is not None and elapsed == config.retest_window:
                        events.append({"index": i, "type": "RETEST_EXPIRED", "price": price})
                        watch = None
            elif level is not None and i > level["known_index"]:
                price = level["price"]
                if bars[i - 1].close <= price and bar.close > price + config.breakout_buffer * a:
                    watch = {
                        "level": level,
                        "breakout_index": i,
                        "touch_index": None,
                        "min_low": None,
                    }
                    events.append({"index": i, "type": "BREAKOUT", "price": price})
                    level = None
        # A newly confirmed point cannot affect this bar's decisions. While a watch is
        # active it is diagnostic only; completed watches do not resurrect old points.
        j = i - 1
        if j >= 2:
            down, up = raw(high, low, close, j)
            if down and not up and not any(raw(high, low, close, j - 1)):
                point = {
                    "extreme_index": j,
                    "known_index": i,
                    "known_time": bar.completed_at,
                    "price": bars[j].high,
                    "support_refs": [b.ref for b in bars[j - 2 : j + 2]],
                }
                points.append(point)
                if watch is None:
                    level = point
    return {"signals": output, "points": points, "events": events, "pending_watch": watch}
