"""Independent bounded ATR and directional-change engine; no production calls."""

import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext

from .types import (
    CONTEXT,
    RULE,
    Bar,
    Dataset,
    Evidence,
    Label,
    Parameters,
    Pivot,
    Result,
    canonical,
    digest,
    q,
    utc,
)
from .zones import build_zones, ranges, select_zones


def prepare(data: Dataset, cutoff: datetime) -> tuple[Bar, ...]:
    """Select versions before price validation, so unavailable future payloads cannot leak."""
    utc(cutoff)
    expected = {"US": "America/New_York", "HK": "Asia/Hong_Kong"}
    market, _, symbol = data.security.partition(".")
    if market not in expected or data.market_timezone != expected[market]:
        raise ValueError("IDENTITY_TIMEZONE_CONFLICT")
    pattern = r"[A-Z0-9]+(?:[.-][A-Z0-9]+)*" if market == "US" else r"[0-9]{5}"
    if len(symbol) > 32 or re.fullmatch(pattern, symbol) is None:
        raise ValueError("CANONICAL_IDENTITY_INVALID")
    if data.quality not in {"COMPLETE", "PARTIAL", "UNKNOWN", "INVALID"}:
        raise ValueError("QUALITY_INVALID")
    if data.mode not in {"AS_OF", "OBSERVATIONAL"}:
        raise ValueError("OBSERVATION_MODE_INVALID")
    if len(data.bars) > 100000:
        raise ValueError("INPUT_BOUND")
    versions: dict[datetime, list[Bar]] = {}
    for bar in data.bars:
        if utc(bar.completed_at) > cutoff or not bar.completed:
            continue
        if bar.available_at is not None and utc(bar.available_at) > cutoff:
            continue
        if bar.available_at is None and data.mode == "AS_OF":
            continue
        if bar.timeframe in {"W1", "M30"} and bar.coverage != "COMPLETE":
            continue
        versions.setdefault(utc(bar.start), []).append(bar)
    selected: list[Bar] = []
    minimum = datetime.min.replace(tzinfo=UTC)
    for key in sorted(versions):
        group = versions[key]
        latest = max(utc(b.available_at) if b.available_at is not None else minimum for b in group)
        finalists = [
            b
            for b in group
            if (utc(b.available_at) if b.available_at is not None else minimum) == latest
        ]
        if len({canonical(b.observation()) for b in finalists}) != 1:
            raise ValueError("CONFLICTING_TIME_VERSION")
        if (
            any(b.available_at is None for b in group)
            and any(b.available_at is not None for b in group)
            and len({canonical(b.observation()) for b in group}) != 1
        ):
            raise ValueError("UNORDERABLE_UNKNOWN_VERSION")
        selected.append(finalists[0])
    return tuple(selected)


def validate_window(bars: tuple[Bar, ...], data: Dataset) -> None:
    previous: Bar | None = None
    for bar in bars:
        if type(bar.completed) is not bool:
            raise ValueError("COMPLETION_FLAG_NOT_BOOLEAN")
        if (bar.security, bar.timeframe) != (data.security, data.timeframe):
            raise ValueError("BAR_IDENTITY_CONFLICT")
        start, end, completed = utc(bar.start), utc(bar.end), utc(bar.completed_at)
        utc(bar.retrieved_at)
        if end <= start or completed < start:
            raise ValueError("BAR_TIME_INVALID")
        if bar.available_at is not None and utc(bar.available_at) < completed:
            raise ValueError("AVAILABLE_BEFORE_COMPLETION")
        if previous is not None and start < previous.end:
            raise ValueError("OVERLAPPING_INTERVALS")
        if bar.timeframe != "W1" and completed < end:
            raise ValueError("COMPLETION_BEFORE_END")
        if bar.timeframe == "M30" and (
            end - start != timedelta(minutes=30) or bar.session != "REGULAR"
        ):
            raise ValueError("M30_SESSION_INVALID")
        values = (bar.open, bar.high, bar.low, bar.close, bar.volume)
        for value in values:
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError("NONFINITE_OR_NONDECIMAL")
            if abs(value) >= Decimal("1e20") or q(value) != value:
                raise ValueError("DECIMAL_38_18_BOUND")
        if min(values[:4]) <= 0 or bar.volume < 0:
            raise ValueError("NONPOSITIVE_PRICE_OR_NEGATIVE_VOLUME")
        if bar.high < max(bar.open, bar.low, bar.close) or bar.low > min(
            bar.open, bar.high, bar.close
        ):
            raise ValueError("OHLC_INVALID")
        previous = bar
    if len({bar.adjustment for bar in bars}) > 1:
        raise ValueError("ADJUSTMENT_BASIS_MISMATCH")


def atr_series(bars: tuple[Bar, ...]) -> tuple[Decimal | None, ...]:
    with localcontext(CONTEXT):
        true_ranges: list[Decimal] = []
        output: list[Decimal | None] = []
        last: Decimal | None = None
        alpha = Decimal(2) / 15
        for index, bar in enumerate(bars):
            tr = bar.high - bar.low
            if index:
                tr = max(
                    tr, abs(bar.high - bars[index - 1].close), abs(bar.low - bars[index - 1].close)
                )
            true_ranges.append(q(tr))
            if index == 13:
                last = q(sum(true_ranges, Decimal(0)) / 14)
            elif index > 13 and last is not None:
                last = q(alpha * true_ranges[-1] + (1 - alpha) * last)
            output.append(last)
        return tuple(output)


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
            if state in {"UNSEEDED", "SEEK_HIGH"} and (high is None or bar.high > bars[high].high):
                high = index
            if state in {"UNSEEDED", "SEEK_LOW"} and (low is None or bar.low < bars[low].low):
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
            identity = digest("qstr-pivot", (RULE, params.config_hash, kind, price, refs))
            output.append(Pivot(kind, price, extreme, index, *refs, atr, proof, identity))
            state = "SEEK_LOW" if kind == "HIGH" else "SEEK_HIGH"
            if kind == "HIGH":
                low = index
            else:
                high = index
        return tuple(output), tuple(ambiguous)


def labels(all_pivots: tuple[Pivot, ...], active_left: int) -> tuple[Label, ...]:
    with localcontext(CONTEXT):
        previous: dict[str, Pivot] = {}
        result: list[Label] = []
        for p in all_pivots:
            before = previous.get(p.kind)
            if before is not None and p.extreme >= active_left and p.confirmed >= active_left:
                tolerance = q(Decimal("0.25") * p.atr)
                direction = (
                    "H"
                    if p.price > before.price + tolerance
                    else "L"
                    if p.price < before.price - tolerance
                    else "E"
                )
                value = direction + ("H" if p.kind == "HIGH" else "L")
                proof = Evidence(
                    "QSTR-008",
                    (("current", p.price), ("previous", before.price)),
                    "> previous+tolerance / < previous-tolerance / equality",
                    tolerance,
                    (p.extreme_ref, before.extreme_ref),
                )
                result.append(
                    Label(
                        p.identity,
                        before.identity,
                        value,
                        before.extreme >= active_left and before.confirmed >= active_left,
                        proof,
                    )
                )
            previous[p.kind] = p
        return tuple(result)


def regime(
    active: tuple[Pivot, ...], swing: tuple[Label, ...], close: Decimal
) -> tuple[str, str, Evidence]:
    by_id = {p.identity: p for p in active}
    latest = {
        kind: next((p for p in reversed(active) if p.kind == kind), None)
        for kind in ("HIGH", "LOW")
    }
    by_pivot = {label.pivot: label for label in swing}
    high, low = latest["HIGH"], latest["LOW"]
    lh = by_pivot.get(high.identity) if high else None
    ll = by_pivot.get(low.identity) if low else None
    operands = (
        ("latest_high_label", lh.value if lh else None),
        ("latest_low_label", ll.value if ll else None),
        ("close", close),
    )
    if (
        not high
        or not low
        or not lh
        or not ll
        or not lh.directional_eligible
        or not ll.directional_eligible
    ):
        return (
            "UNCERTAIN",
            "ACTIVE_TWO_SIDED_HISTORY_INSUFFICIENT",
            Evidence("QSTR-008", operands, "two active comparable highs AND lows", 4),
        )
    refs = tuple(by_id[i].extreme_ref for i in (lh.pivot, lh.previous, ll.pivot, ll.previous))
    if (lh.value, ll.value) == ("HH", "HL"):
        coherent = close >= low.price
        return (
            "BULL_TREND" if coherent else "UNCERTAIN",
            "DIRECTIONAL_EVIDENCE" if coherent else "CLOSE_BELOW_HL",
            Evidence("QSTR-008", operands, "close>=HL", low.price, refs),
        )
    if (lh.value, ll.value) == ("LH", "LL"):
        coherent = close <= high.price
        return (
            "BEAR_TREND" if coherent else "UNCERTAIN",
            "DIRECTIONAL_EVIDENCE" if coherent else "CLOSE_ABOVE_LH",
            Evidence("QSTR-008", operands, "close<=LH", high.price, refs),
        )
    return (
        "UNCERTAIN",
        "EQUAL_OR_CONFLICTING_LABELS",
        Evidence("QSTR-008", operands, "HH+HL or LH+LL", None, refs),
    )


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
        "config_hash": params.config_hash,
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
            "config_hash": params.config_hash,
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
