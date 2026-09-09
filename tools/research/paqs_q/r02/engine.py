"""H1 eligible opposite-candidate seeding; baseline mathematics otherwise retained.

Calculation pipeline and transition implementation adapted from the immutable d50d73e
research engine. No monkeypatching, baseline output relabelling, or product integration.
"""

from datetime import datetime
from decimal import Decimal, localcontext

from ..engine import atr_series, labels, prepare, regime, validate_window
from ..types import (
    CONTEXT,
    Bar,
    Dataset,
    Evidence,
    Parameters,
    Pivot,
    Result,
    canonical,
    digest,
    utc,
)
from ..zones import build_zones, ranges, select_zones

RULE = "QSTR-R02-ELIGIBLE-SEED-1"


def config_hash(params: Parameters) -> str:
    return digest("qstr-config", (RULE, params, params.warm, params.active))


def pivots(
    bars: tuple[Bar, ...], atrs: tuple[Decimal | None, ...], params: Parameters
) -> tuple[tuple[Pivot, ...], tuple[int, ...]]:
    if len(bars) != len(atrs):
        raise ValueError("ATR_ALIGNMENT")
    with localcontext(CONTEXT):
        state = "UNSEEDED"
        high: int | None = None
        low: int | None = None
        output: list[Pivot] = []
        ambiguous: list[int] = []
        for index, (bar, atr) in enumerate(zip(bars, atrs, strict=True)):
            if atr is None or atr <= 0:
                continue
            admissible = not output or index - output[-1].extreme >= 2
            if (
                admissible
                and state in {"UNSEEDED", "SEEK_HIGH"}
                and (high is None or bar.high > bars[high].high)
            ):
                high = index
            if (
                admissible
                and state in {"UNSEEDED", "SEEK_LOW"}
                and (low is None or bar.low < bars[low].low)
            ):
                low = index
            threshold = params.pivot_lambda * atr
            down = high is not None and high < index and bars[high].high - bar.close >= threshold
            up = low is not None and low < index and bar.close - bars[low].low >= threshold
            kind: str | None = None
            extreme: int | None = None
            if state == "UNSEEDED":
                if down and up:
                    ambiguous.append(index)
                if down != up:
                    kind, extreme = ("HIGH", high) if down else ("LOW", low)
            elif state == "SEEK_HIGH" and down and high is not None:
                if high - output[-1].extreme >= 2:
                    kind, extreme = "HIGH", high
            elif state == "SEEK_LOW" and up and low is not None:
                if low - output[-1].extreme >= 2:
                    kind, extreme = "LOW", low
            if kind is None or extreme is None:
                continue
            price = bars[extreme].high if kind == "HIGH" else bars[extreme].low
            distance = price - bar.close if kind == "HIGH" else bar.close - price
            refs = (bars[extreme].ref, bar.ref)
            proof = Evidence(
                "QSTR-005",
                (
                    ("distance", distance),
                    ("lambda", params.pivot_lambda),
                    ("atr", atr),
                    ("extreme_index", extreme),
                    ("confirmation_index", index),
                    ("previous_extreme", output[-1].extreme if output else None),
                ),
                ">=; extreme<confirmation; separation>=2 after seed",
                threshold,
                refs,
            )
            identity = digest("qstr-pivot", (RULE, config_hash(params), kind, price, refs))
            output.append(Pivot(kind, price, extreme, index, *refs, atr, proof, identity))
            state = "SEEK_LOW" if kind == "HIGH" else "SEEK_HIGH"
            if kind == "HIGH":
                low = index if index - extreme >= 2 else None
            else:
                high = index if index - extreme >= 2 else None
        return tuple(output), tuple(ambiguous)


def evaluate(data: Dataset, cutoff: datetime, params: Parameters | None = None) -> Result:
    params = params or Parameters.default(data.timeframe)
    with localcontext(CONTEXT):
        try:
            bars = prepare(data, cutoff)[-params.total :]
            return calculate_window(data, bars, cutoff, params, params.warm)
        except (ValueError, TypeError, ArithmeticError) as exc:
            return failure(
                data,
                cutoff,
                params,
                str(exc) if isinstance(exc, ValueError) else "INVALID_NUMERIC_INPUT",
            )


def failure(data: Dataset, cutoff: datetime, params: Parameters, cause: str) -> Result:
    body = {
        "rule": RULE,
        "security": data.security,
        "timeframe": data.timeframe,
        "cutoff": cutoff,
        "config_hash": config_hash(params),
        "input_status": "INVALID",
        "structure_status": "INVALID_INPUT",
        "regime": "UNCERTAIN",
        "reasons": (cause,),
        "active_pivots": (),
        "zones": (),
        "range": None,
    }
    return Result(canonical(body), canonical({"failure": cause}), "INVALID_INPUT", data.provenance)


def calculate_window(
    data: Dataset,
    bars: tuple[Bar, ...],
    cutoff: datetime,
    params: Parameters,
    active_left: int,
    *,
    diagnostic: bool = False,
) -> Result:
    """Diagnostic-only arms may supply N-1/N+1; normal callers always require exactly N."""
    with localcontext(CONTEXT):
        if params.timeframe != data.timeframe:
            raise ValueError("CONFIG_TIMEFRAME_MISMATCH")
        for bar in bars:
            if not bar.completed or utc(bar.completed_at) > utc(cutoff):
                raise ValueError("WINDOW_COMPLETION_AFTER_CUTOFF")
            if bar.available_at is not None and utc(bar.available_at) > utc(cutoff):
                raise ValueError("WINDOW_AVAILABILITY_AFTER_CUTOFF")
            if bar.available_at is None and data.mode == "AS_OF":
                raise ValueError("WINDOW_AVAILABILITY_UNKNOWN")
        validate_window(bars, data)
        if data.quality == "INVALID":
            return failure(data, cutoff, params, "SOURCE_QUALITY_INVALID")
        warnings = []
        if data.mode == "OBSERVATIONAL":
            warnings.append("OBSERVATIONAL_NOT_HISTORICAL_INFORMATION_SET")
        if any(b.available_at is None for b in bars):
            warnings.append("HISTORICAL_AVAILABILITY_UNKNOWN")
        if any(b.adjustment == "PROVIDER_QFQ_CURRENT" for b in bars):
            warnings.append("CURRENT_QFQ_NOT_POINT_IN_TIME_SAFE")
        atrs = atr_series(bars)
        terminal_atr = atrs[-1] if atrs else None
        enough = len(bars) >= params.total if not diagnostic else len(bars) >= 14
        history = (
            "INSUFFICIENT_FOR_Q_HORIZON"
            if not enough
            else "NONPOSITIVE_ATR"
            if terminal_atr is None or terminal_atr <= 0
            else "READY"
        )
        all_pivots, ambiguity = pivots(bars, atrs, params) if history == "READY" else ((), ())
        active = tuple(
            p for p in all_pivots if p.extreme >= active_left and p.confirmed >= active_left
        )
        swing = labels(all_pivots, active_left)
        counts: dict[str, int] = {}
        all_zones = build_zones(active, params, counts) if data.timeframe == "D1" else ()
        eligible, decision_zones = (
            select_zones(all_zones, len(bars) - 1, bars[-1].close, params) if bars else ((), ())
        )
        valid_boxes = (
            ranges(bars, atrs, decision_zones, params, counts) if data.timeframe == "D1" else ()
        )
        uncapped_boxes = (
            ranges(bars, atrs, eligible, params, counts) if data.timeframe == "D1" else ()
        )
        box = valid_boxes[0] if valid_boxes else None
        value, sufficiency = "UNCERTAIN", history
        proof = Evidence(
            "QSTR-004",
            (("bar_count", len(bars)), ("terminal_atr", terminal_atr)),
            "N bars AND ATR>0",
            params.total,
        )
        if history == "READY":
            if box:
                value, sufficiency = "RANGE", "CURRENT_RANGE"
                proof = Evidence(
                    "QSTR-008", (("range_id", box.identity),), "D1 current range precedence", True
                )
            else:
                value, sufficiency, proof = regime(active, swing, bars[-1].close)
        if active and len(bars) - 1 - active[-1].extreme > params.active // 2:
            warnings.append("ACTIVE_PIVOT_STALE")
        body = {
            "rule": RULE,
            "security": data.security,
            "timeframe": data.timeframe,
            "cutoff": cutoff,
            "config_hash": config_hash(params),
            "parameters": params,
            "window": {
                "count": len(bars),
                "warm": active_left,
                "first": bars[0].ref if bars else None,
                "last": bars[-1].ref if bars else None,
            },
            "evaluation_hash": digest("qstr-window", tuple(b.observation() for b in bars)),
            "observations": tuple(b.observation() for b in bars),
            "input_status": data.quality,
            "structure_status": sufficiency,
            "regime": value,
            "atr": terminal_atr,
            "active_pivots": active,
            "labels": swing,
            "zones": decision_zones,
            "range": box,
            "reasons": (sufficiency,),
            "evidence": proof,
            "warnings": tuple(warnings),
        }
        diagnostics = {
            "diagnostic_horizon": diagnostic,
            "source_unknown_availability_count": sum(b.available_at is None for b in data.bars),
            "all_pivots": all_pivots,
            "ambiguous_indices": ambiguity,
            "zones": all_zones,
            "expired_zone_count": sum(
                len(bars) - 1 - max(p.extreme for p in z.touches) > params.zone_age
                for z in all_zones
            ),
            "valid_ranges": valid_boxes,
            "uncapped_ranges": uncapped_boxes,
            "cap_suppressed_range_count": len(
                {b.identity for b in uncapped_boxes} - {b.identity for b in valid_boxes}
            ),
            "comparison_counts": counts,
        }
        try:
            source_hash = digest("qstr-source", data)
        except (ValueError, TypeError, ArithmeticError):
            # Excluded, unavailable records are not part of decision validation.
            source_hash = "NONCANONICAL_SOURCE_ENVELOPE"
        return Result(canonical(body), canonical(diagnostics), source_hash, data.provenance)
