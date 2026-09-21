"""Minimal R04/R05 local-certificate port, without study orchestration or data access.

Legacy digest domains are preserved only for semantic parity/lineage. New public
result and record identities are added by the versioned plugin adapter.
"""

from collections import Counter
from datetime import datetime
from decimal import Decimal, localcontext
from typing import Any

from ai_infra_quant.core.domain.paqs_q.canonical import legacy_digest as digest
from ai_infra_quant.core.domain.paqs_q.inputs import CONTEXT, Bar, Fact, QInput, q

from .calendar import select, slot, support
from .qualification import Parameters, prepare, validate_window

RULE = "PROPOSED_SEMANTICS:R04-CALENDAR-LOCAL-1"
A1_RULE = "PROPOSED_SEMANTICS:R05-NO-PRIOR-RAW-VETO-4SUPPORT-1"


def version(bar: Bar) -> str:
    return bar.version_ref


def raw(
    high: tuple[Decimal, ...], low: tuple[Decimal, ...], close: tuple[Decimal, ...], j: int
) -> tuple[bool, bool]:
    """Pure arithmetic kernel. Public callers validate shape/quality/time first."""
    scale = high[j - 1] - low[j - 1]
    down = scale > 0 and high[j] > max(high[j - 1], high[j + 1]) and high[j] - close[j + 1] >= scale
    up = scale > 0 and low[j] < min(low[j - 1], low[j + 1]) and close[j + 1] - low[j] >= scale
    return down, up


def evaluate(
    data: QInput,
    facts: tuple[Fact, ...],
    cutoff: datetime,
    mode: str = "AS_OF",
    *,
    prior_raw_veto: bool = True,
) -> dict[str, Any]:
    if mode not in {"AS_OF", "OBSERVATIONAL"}:
        raise ValueError("MODE")
    params = Parameters.default(data.timeframe)
    out: dict[str, Any] = {
        "rule": RULE if prior_raw_veto else A1_RULE,
        "security": data.security,
        "timeframe": data.timeframe,
        "cutoff": cutoff,
        "mode": mode,
        "quality": data.quality,
        "status": "INVALID",
        "reason": "INVALID",
        "events": [],
        "census": [],
        "bars": (),
        "calendar": {},
        "strict_confirmation": False,
    }
    source = data
    with localcontext(CONTEXT):
        try:
            bars = prepare(source, cutoff)[-params.total :]
            validate_window(bars, source)
            if data.quality == "INVALID":
                raise ValueError("SOURCE_QUALITY_INVALID")
            days = select(facts, cutoff, mode)
            out.update(
                bars=bars,
                calendar={k.isoformat(): v.ref for k, v in days.items()},
                window_hash=digest("r04-window", tuple(b.ref for b in bars)),
                calendar_hash=digest("r04-calendar-view", tuple(v.ref for v in days.values())),
            )
            out["unknown_price_availability"] = sum(
                b.available_at is None
                for b in data.bars
                if b.completed_at <= cutoff and b.completed
            )
            if len(bars) != params.total:
                out.update(status="INSUFFICIENT", reason="INSUFFICIENT_HORIZON_OR_AVAILABILITY")
                return out
            if mode == "AS_OF" and (
                data.quality != "COMPLETE"
                or any(
                    b.coverage != "COMPLETE" or b.adjustment == "PROVIDER_QFQ_CURRENT" for b in bars
                )
            ):
                out.update(status="UNQUALIFIED", reason="PRICE_NOT_STRICT")
                return out
            out.update(
                status="VALID",
                reason="OBSERVED_PATTERN_ONLY" if mode == "OBSERVATIONAL" else "CONDITIONAL_AS_OF",
                strict_confirmation=mode == "AS_OF",
            )
            high, low, close = (
                tuple(getattr(b, k) for b in bars) for k in ("high", "low", "close")
            )
            for j, bar in enumerate(bars):
                row: dict[str, Any] = {
                    "index": j,
                    "center": bar.ref,
                    "extreme_time": bar.end,
                    "active": j >= params.warm,
                    "raw": None,
                    "previous_raw": None,
                    "reason": "NO_RAW",
                    "support_hash": None,
                    "segment": None,
                }
                out["census"].append(row)
                try:
                    _, row["segment"] = slot(bar, days, mode)
                    if j >= 1 and j + 1 < len(bars):
                        support(bars[j - 1 : j + 2], days, mode)
                        row["raw"] = raw(high, low, close, j)
                    if j < 2:
                        raise ValueError("LEFT_SUPPORT_MISSING")
                    if j + 1 >= len(bars):
                        raise ValueError("RIGHT_CONFIRMATION_MISSING")
                    used = support(bars[j - 2 : j + 2], days, mode)
                    row["previous_raw"] = raw(high, low, close, j - 1)
                    quartet = bars[j - 2 : j + 2]
                    ordered = (
                        tuple((b.ref, version(b)) for b in quartet),
                        tuple(f.ref for f in used),
                    )
                    row.update(
                        price_support=tuple(b.ref for b in quartet),
                        calendar_support=tuple((f.day.isoformat(), f.ref) for f in used),
                        support_hash=digest("r04-support", (RULE, mode, data.quality, ordered)),
                        calendar_unknown_availability=sum(f.available_at is None for f in used),
                        calendar_uncertified=sum(not f.complete for f in used),
                    )
                    down, up = row["raw"]
                    row["scale"] = high[j - 1] - low[j - 1]
                    if down and up:
                        row["reason"] = "DUAL"
                    elif not down and not up:
                        row["reason"] = "ZERO_SCALE" if row["scale"] <= 0 else "NO_RAW"
                    elif prior_raw_veto and any(row["previous_raw"]):
                        row["reason"] = "PRIOR_RAW_VETO"
                    else:
                        row["reason"] = "ACCEPTED_ACTIVE" if row["active"] else "ACCEPTED_WARM"
                        price = bar.high if down else bar.low
                        kind = "HIGH" if down else "LOW"
                        availability = [b.available_at for b in quartet] + [
                            f.available_at for f in used
                        ]
                        event = {
                            "kind": kind,
                            "price": price,
                            "extreme_ref": bar.ref,
                            "confirmation_ref": bars[j + 1].ref,
                            "extreme_time": bar.end,
                            "reversal_time": bars[j + 1].completed_at,
                            "scale": row["scale"],
                            "available_at": None
                            if None in availability
                            else max(t for t in availability if t is not None),
                            "support_hash": row["support_hash"],
                            "index": j,
                            "mode": mode,
                            "segment": row["segment"],
                        }
                        event["key"] = digest("endpoint", (kind, price, bar.ref, bars[j + 1].ref))
                        event["identity"] = digest(
                            out["rule"], (event["key"], event["support_hash"])
                        )
                        if row["active"]:
                            out["events"].append(event)
                except ValueError as exc:
                    row["reason"] = str(exc)
            previous = None
            for event in out["events"]:
                event["age_bars"] = len(bars) - 1 - event["index"]
                if previous is not None:
                    event.update(
                        same_kind_as_previous=event["kind"] == previous["kind"],
                        separation=event["index"] - previous["index"],
                        amplitude_local_range=q(
                            abs(event["price"] - previous["price"]) / event["scale"]
                        ),
                    )
                previous = event
            for row in out["census"]:
                if (
                    not row["active"]
                    or row["raw"] is None
                    or row["raw"][0] == row["raw"][1]
                    or row["reason"].startswith("ACCEPTED")
                ):
                    continue
                kind = "HIGH" if row["raw"][0] else "LOW"
                prior = [
                    e for e in out["events"] if e["kind"] == kind and e["index"] < row["index"]
                ]
                if prior:
                    price = high[row["index"]] if kind == "HIGH" else low[row["index"]]
                    row.update(
                        omission_reference=prior[-1]["key"],
                        omitted_price=price,
                        more_extreme=price > prior[-1]["price"]
                        if kind == "HIGH"
                        else price < prior[-1]["price"],
                    )
        except (ValueError, TypeError, ArithmeticError) as exc:
            out.update(status="INVALID", reason=str(exc), events=[], census=[])
    return out


def _segment_key(segment: str | None) -> str:
    """Normalize unresolved slots consistently without changing the source census."""
    return "UNRESOLVED_SEGMENT" if segment is None else segment


def costs(result: dict[str, Any]) -> dict[str, Any]:
    rows, events = result["census"], result["events"]
    active = [r for r in rows if r["active"]]
    accepted = sum(r["reason"] == "ACCEPTED_ACTIVE" for r in active)
    return {
        "all_centers": len(rows),
        "active_centers": len(active),
        "reasons_all": Counter(r["reason"] for r in rows),
        "reasons_active": Counter(r["reason"] for r in active),
        "raw_unambiguous_active": sum(
            r["raw"] is not None and r["raw"][0] != r["raw"][1] for r in active
        ),
        "raw_unavailable_active": sum(r["raw"] is None for r in active),
        "complete_support_active": sum(r["support_hash"] is not None for r in active),
        "events": len(events),
        "event_density": q(Decimal(accepted) / len(active)) if active else None,
        "repeated_same_kind_pairs": sum(e.get("same_kind_as_previous", False) for e in events),
        "pair_denominator": max(0, len(events) - 1),
        "omission_reference_opportunities": sum("omission_reference" in r for r in active),
        "more_extreme_omitted": sum(r.get("more_extreme", False) for r in active),
        "omission_reasons": Counter(r["reason"] for r in active if r.get("more_extreme", False)),
        "ages": [e["age_bars"] for e in events],
        "separations": [e["separation"] for e in events if "separation" in e],
        "amplitudes_current_prior_range": [
            e["amplitude_local_range"] for e in events if "separation" in e
        ],
        "segments": {
            segment: {
                "centers": sum(_segment_key(r["segment"]) == segment for r in active),
                "support": sum(
                    _segment_key(r["segment"]) == segment and r["support_hash"] is not None
                    for r in active
                ),
                "events": sum(_segment_key(e["segment"]) == segment for e in events),
            }
            for segment in sorted({_segment_key(r["segment"]) for r in active})
        },
    }
