"""Calendar-qualified fixed local rule, complete census and explicit qualification."""

from dataclasses import replace
from datetime import datetime
from decimal import localcontext
from typing import Any

from ..engine import prepare, validate_window
from ..r03.models import raw, version
from ..temporal import availability_check, information_change
from ..types import CONTEXT, Dataset, Parameters, digest, q
from .calendar import Fact, select, slot, support

RULE = "PROPOSED_SEMANTICS:R04-CALENDAR-LOCAL-1"


def evaluate(
    data: Dataset, facts: tuple[Fact, ...], cutoff: datetime, mode: str = "OBSERVATIONAL"
) -> dict[str, Any]:
    if mode not in {"AS_OF", "OBSERVATIONAL"}:
        raise ValueError("MODE")
    params = Parameters.default(data.timeframe)
    out: dict[str, Any] = {
        "rule": RULE,
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
    source = replace(data, mode=mode)
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
                audit=availability_check(bars, source, cutoff),
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
                    elif any(row["previous_raw"]):
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
                        event["identity"] = digest(RULE, (event["key"], event["support_hash"]))
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


def compare(old: dict[str, Any], new: dict[str, Any], data: Dataset) -> dict[str, Any]:
    if old["status"] != "VALID" or new["status"] != "VALID":
        return {"status": "UNAVAILABLE_PAIR"}
    params = Parameters.default(data.timeframe)
    common = {b.ref for b in old["bars"][params.warm :]} & {
        b.ref for b in new["bars"][params.warm :]
    }
    a = {e["key"]: e for e in old["events"]}
    b = {e["key"]: e for e in new["events"]}
    opportunities = {k for k, e in a.items() if {e["extreme_ref"], e["confirmation_ref"]} <= common}
    new_rows = {r["center"]: r for r in new["census"]}
    full = {
        k
        for k in opportunities
        if new_rows[a[k]["extreme_ref"]]["support_hash"] == a[k]["support_hash"]
    }
    losses = sorted(opportunities - b.keys())
    changed = information_change(old["bars"], new["bars"], old["cutoff"], new["bars"][0].start)
    cal_changed = sum(
        old["calendar"][k] != new["calendar"][k]
        for k in old["calendar"].keys() & new["calendar"].keys()
    )
    redis = [
        k
        for k, e in b.items()
        if k not in a
        and e["reversal_time"] <= old["cutoff"]
        and {e["extreme_ref"], e["confirmation_ref"]} <= common
    ]
    old_bars = {bar.ref: bar for bar in old["bars"]}
    left = new["bars"][params.warm].start
    expired = sum(
        old_bars[e["extreme_ref"]].start < left or old_bars[e["confirmation_ref"]].start < left
        for e in a.values()
    )
    return {
        "status": "VALID",
        "endpoint_opportunities": len(opportunities),
        "lost": len(losses),
        "rediscovered": len(redis),
        "new_confirmations": sum(e["reversal_time"] > old["cutoff"] for e in b.values()),
        "expired": expired,
        "endpoint_information_excluded": len(a) - len(opportunities) - expired,
        "full_support_opportunities": len(full),
        "full_support_lost": len(full - b.keys()),
        "coverage_excluded": len(opportunities - full),
        "same_endpoint_witness_changed": sum(
            a[k]["identity"] != b[k]["identity"] for k in a.keys() & b.keys()
        ),
        "price_information_change": changed,
        "calendar_revision_count": cal_changed,
        "losses": losses,
        "rediscoveries": redis,
        "loss_causes": {
            k: "UNEXPLAINED_SAME_SUPPORT" if k in full else new_rows[a[k]["extreme_ref"]]["reason"]
            for k in losses
        },
    }
