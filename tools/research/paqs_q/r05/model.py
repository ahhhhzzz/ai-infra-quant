"""A1 removes only the veto on an unchanged R04 four-observation eligibility domain."""

from copy import deepcopy
from datetime import datetime
from decimal import localcontext
from typing import Any

from ..r04.calendar import Fact
from ..r04.model import evaluate as baseline
from ..r04.study import costs
from ..types import CONTEXT, Dataset, canonical, digest, q

RULE = "PROPOSED_SEMANTICS:R05-NO-PRIOR-RAW-VETO-4SUPPORT-1"
OMISSIONS = {"omission_reference", "omitted_price", "more_extreme"}
SEQUENCE = {"age_bars", "same_kind_as_previous", "separation", "amplitude_local_range"}


def accepts(current: tuple[bool, bool] | None, quartet: bool) -> bool:
    return quartet and current is not None and current[0] != current[1]


def ablate(base: dict[str, Any], facts: tuple[Fact, ...]) -> dict[str, Any]:
    """Consume pure R04 qualification, never its veto decision as an A1 acceptance gate.

    Support hashes continue to identify the same R04 eligibility certificate (not minimal
    logical support). A1 event identities separately include RULE. No baseline mutation.
    """
    out = deepcopy(base)
    out["rule"] = RULE
    out["events"] = []
    if out["status"] != "VALID":
        return out
    bars, rows = out["bars"], out["census"]
    by_ref = {f.ref: f for f in facts}
    with localcontext(CONTEXT):
        for row in rows:
            for field in OMISSIONS:
                row.pop(field, None)
            if not accepts(row["raw"], row["support_hash"] is not None):
                continue
            j = row["index"]
            row["reason"] = "ACCEPTED_ACTIVE" if row["active"] else "ACCEPTED_WARM"
            if not row["active"]:
                continue
            kind = "HIGH" if row["raw"][0] else "LOW"
            price = bars[j].high if kind == "HIGH" else bars[j].low
            availability = [b.available_at for b in bars[j - 2 : j + 2]] + [
                by_ref[ref].available_at for _, ref in row["calendar_support"]
            ]
            key = digest("endpoint", (kind, price, bars[j].ref, bars[j + 1].ref))
            out["events"].append(
                {
                    "kind": kind,
                    "price": price,
                    "extreme_ref": bars[j].ref,
                    "confirmation_ref": bars[j + 1].ref,
                    "extreme_time": bars[j].end,
                    "reversal_time": bars[j + 1].completed_at,
                    "scale": row["scale"],
                    "available_at": None
                    if None in availability
                    else max(t for t in availability if t is not None),
                    "support_hash": row["support_hash"],
                    "index": j,
                    "mode": out["mode"],
                    "segment": row["segment"],
                    "key": key,
                    "identity": digest(RULE, (key, row["support_hash"])),
                    "age_bars": len(bars) - 1 - j,
                }
            )
        previous = None
        for event in out["events"]:
            if previous is not None:
                event.update(
                    same_kind_as_previous=event["kind"] == previous["kind"],
                    separation=event["index"] - previous["index"],
                    amplitude_local_range=q(
                        abs(event["price"] - previous["price"]) / event["scale"]
                    ),
                )
            previous = event
        for row in rows:
            if (
                not row["active"]
                or row["raw"] is None
                or row["raw"][0] == row["raw"][1]
                or row["reason"].startswith("ACCEPTED")
            ):
                continue
            kind = "HIGH" if row["raw"][0] else "LOW"
            prior = [e for e in out["events"] if e["kind"] == kind and e["index"] < row["index"]]
            if prior:
                price = bars[row["index"]].high if kind == "HIGH" else bars[row["index"]].low
                row.update(
                    omission_reference=prior[-1]["key"],
                    omitted_price=price,
                    more_extreme=price > prior[-1]["price"]
                    if kind == "HIGH"
                    else price < prior[-1]["price"],
                )
    return out


def evaluate(
    data: Dataset, facts: tuple[Fact, ...], cutoff: datetime, mode: str = "OBSERVATIONAL"
) -> dict[str, Any]:
    return ablate(baseline(data, facts, cutoff, mode), facts)


def dependency_audit(base: dict[str, Any]) -> list[dict[str, Any]]:
    """A populated raw value proves the current triple passed R04 support qualification.

    With that triple eligible, failure of the retained quartet is confined to the extra
    j-2 observation/edge. Include non-reversing centers; count current XOR separately.
    This diagnostic never participates in ablate() or emits an event.
    """
    return [
        {
            "diagnostic": "TRIPLE_ONLY_ELIGIBLE",
            "event": False,
            "center": r["center"],
            "index": r["index"],
            "active": r["active"],
            "segment": "UNRESOLVED_SEGMENT" if r["segment"] is None else r["segment"],
            "unavailable_dependency": r["reason"],
            "current_xor": r["raw"][0] != r["raw"][1],
        }
        for r in base["census"]
        if r["raw"] is not None and r["support_hash"] is None
    ]


def verify_pair(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Executable acceptance checks with endpoint keys independent of candidate identity."""
    assert canonical(
        {k: v for k, v in base.items() if k not in {"rule", "events", "census"}}
    ) == canonical({k: v for k, v in candidate.items() if k not in {"rule", "events", "census"}})
    b = {e["key"]: e for e in base["events"]}
    a = {e["key"]: e for e in candidate["events"]}
    assert len(b) == len(base["events"]) and len(a) == len(candidate["events"])
    assert b.keys() <= a.keys()
    assert len(base["census"]) == len(candidate["census"])
    veto = {}
    for old, new in zip(base["census"], candidate["census"], strict=True):
        expected = {k: v for k, v in old.items() if k not in OMISSIONS}
        if old["reason"] == "PRIOR_RAW_VETO":
            assert old["support_hash"] is not None and old["raw"][0] != old["raw"][1]
            expected["reason"] = "ACCEPTED_ACTIVE" if old["active"] else "ACCEPTED_WARM"
            if old["active"]:
                veto[old["center"]] = old
        assert expected == {k: v for k, v in new.items() if k not in OMISSIONS}
    added = [a[k] for k in sorted(a.keys() - b.keys())]
    assert {e["extreme_ref"] for e in added} == veto.keys()
    assert len(added) == len(veto)
    for k in b:
        assert {f: v for f, v in b[k].items() if f not in SEQUENCE | {"identity"}} == {
            f: v for f, v in a[k].items() if f not in SEQUENCE | {"identity"}
        }
    for result in (base, candidate):
        with localcontext(CONTEXT):
            stats = costs(result)
        assert "None" not in stats["segments"]
        for field, total in (
            ("centers", "active_centers"),
            ("support", "complete_support_active"),
            ("events", "events"),
        ):
            assert sum(v[field] for v in stats["segments"].values()) == stats[total]
    mappings = []
    for event in added:
        r = veto[event["extreme_ref"]]
        previous = r["previous_raw"]
        prior_kind = "dual" if all(previous) else ("HIGH" if previous[0] else "LOW")
        classification = (
            "dual"
            if prior_kind == "dual"
            else ("same" if prior_kind == event["kind"] else "opposite")
        )
        mappings.append(
            {
                "endpoint": event["key"],
                "center": r["center"],
                "index": r["index"],
                "B0_reason": r["reason"],
                "previous_raw_kind": classification,
                "previous_raw_value": previous,
                "previous_raw_separation": 1,
                "A1_event": event,
                "restored_more_extreme": r.get("more_extreme", False),
                "baseline_omission_reference": r.get("omission_reference"),
            }
        )
    return {
        "shared": sorted(b),
        "added": mappings,
        "removed": [],
        "status": base["status"],
        "invariants": "PASS",
    }
