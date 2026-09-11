"""Frozen original-cohort study, explicit run recognition and complete rejection census."""

import json
from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from pathlib import Path
from time import perf_counter
from typing import Any

from .. import engine as baseline
from ..r02 import engine as h1
from ..types import CONTEXT, Dataset, Parameters, canonical, digest, q
from .calendar import Fact
from .integrations.local import load, stamp
from .model import RULE, compare, evaluate

EVIDENCE = Path("docs/evidence/TASK_006B_Q/research-04")


def write_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(canonical(value) + "\n")


def recognize(snapshot: dict[str, Any], records: dict[str, Any], now: datetime) -> None:
    """Research-run bookkeeping only; never an inferred historical M2 ledger."""
    for event in snapshot["events"]:
        if (
            now < snapshot["cutoff"]
            or now < event["reversal_time"]
            or (event["available_at"] is not None and now < event["available_at"])
        ):
            raise ValueError("RECOGNITION_BEFORE_EVIDENCE_OR_CALCULATION")
        records.setdefault(
            event["identity"],
            {
                "event": event["identity"],
                "first_seen_scheduled_cutoff": snapshot["cutoff"],
                "recognized_at": now,
                "reversal_time": event["reversal_time"],
                "available_at": event["available_at"],
                "mode": snapshot["mode"],
                "claim": "actual research execution; scheduled cutoff is not recognition time",
            },
        )


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


def select_cases(result: dict[str, Any], chosen: dict[str, Any]) -> None:
    if result["status"] != "VALID" or result["mode"] != "OBSERVATIONAL":
        return
    rows = result["census"]
    pools = {
        "accepted": [r for r in rows if r["reason"] == "ACCEPTED_ACTIVE"],
        "repeated-kind": [
            rows[e["index"]] for e in result["events"] if e.get("same_kind_as_previous")
        ],
        "veto": [r for r in rows if r["active"] and r["reason"] == "PRIOR_RAW_VETO"],
        "calendar": [
            r
            for r in rows
            if r["active"]
            and (
                "CALENDAR" in r["reason"]
                or "BOUNDARY" in r["reason"]
                or "MISSING_EXPECTED" in r["reason"]
            )
        ],
    }
    for category, pool in pools.items():
        if category in chosen or not pool:
            continue
        selected = (
            next((r for r in pool if r.get("more_extreme")), pool[0])
            if category == "veto"
            else pool[0]
        )
        j = selected["index"]
        left = max(0, j - 19)
        right = min(len(result["bars"]), left + 40)
        bars = result["bars"][left:right]
        assert all(b.completed_at <= result["cutoff"] for b in bars)
        chosen[category] = {
            "category": category,
            "timeframe": result["timeframe"],
            "security": result["security"],
            "cutoff": result["cutoff"],
            "rule": RULE,
            "mode": result["mode"],
            "quality": result["quality"],
            "selected": selected,
            "bars": bars,
            "first_window_index": left,
            "rows": rows[left:right],
            "events": [e for e in result["events"] if left <= e["index"] < right],
            "window_hash": result["window_hash"],
            "calendar_hash": result["calendar_hash"],
            "future_candles": 0,
        }


def frame(
    data: Dataset,
    facts: tuple[Fact, ...],
    cutoffs: list[str],
    retained: list[dict[str, Any]],
    mode: str,
    output: Path,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    catalog: list[dict[str, Any]] = []
    events: dict[str, Any] = {}
    ids: dict[str, int] = {}
    recognized: dict[str, Any] = {}
    cases: dict[str, Any] = {}
    previous: dict[str, Any] | None = None
    param = Parameters.default(data.timeframe)
    status: Counter[str] = Counter()
    all_reasons: Counter[str] = Counter()
    active_reasons: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    transitions: Counter[str] = Counter()
    baseline_equal = h1_equal = 0
    for i, text in enumerate(cutoffs):
        cutoff = stamp(text)
        result = evaluate(data, facts, cutoff, mode)
        recognize(result, recognized, datetime.now(UTC))
        status[result["status"]] += 1
        stats = costs(result)
        all_reasons.update(stats["reasons_all"])
        active_reasons.update(stats["reasons_active"])
        for k, value in stats.items():
            if type(value) is int:
                totals[k] += value
        row_ids = []
        for r in result["census"]:
            payload = {k: v for k, v in r.items() if k not in {"index", "active"}}
            key = digest("census-row", payload)
            if key not in ids:
                ids[key] = len(catalog)
                catalog.append(payload)
            row_ids.append(ids[key])
        event_rows = []
        for e in result["events"]:
            events[e["identity"]] = {
                k: v
                for k, v in e.items()
                if k
                not in {
                    "index",
                    "age_bars",
                    "same_kind_as_previous",
                    "separation",
                    "amplitude_local_range",
                }
            }
            event_rows.append(
                {
                    k: e[k]
                    for k in (
                        "identity",
                        "index",
                        "age_bars",
                        "same_kind_as_previous",
                        "separation",
                        "amplitude_local_range",
                    )
                    if k in e
                }
            )
        row = {k: v for k, v in result.items() if k not in {"bars", "census", "events", "calendar"}}
        row.update(
            census_ids=row_ids,
            events=event_rows,
            costs=stats,
            selected_count=len(result["bars"]),
            active_start=param.warm,
            first_start=result["bars"][0].start if result["bars"] else None,
            last_completion=result["bars"][-1].completed_at if result["bars"] else None,
        )
        if previous is not None:
            transition = compare(previous, result, data)
            row["transition"] = transition
            transitions["scheduled_pairs"] += 1
            transitions[transition["status"] + "_pairs"] += 1
            for k, value in transition.items():
                if type(value) is int:
                    transitions[k] += value
            if any(
                c == "UNEXPLAINED_SAME_SUPPORT" for c in transition.get("loss_causes", {}).values()
            ):
                # An unexplained mechanism is preserved and selected, not hidden by an assertion.
                index = next(
                    r["index"]
                    for r in result["census"]
                    if r["center"]
                    in {
                        e["extreme_ref"]
                        for e in previous["events"]
                        if e["key"] in transition["losses"]
                    }
                )
                exceptional = dict(result)
                exceptional["census"] = [dict(r) for r in result["census"]]
                exceptional["census"][index]["reason"] = "CALENDAR_UNEXPLAINED_SAME_SUPPORT"
                temp: dict[str, Any] = {}
                select_cases(exceptional, temp)
                cases.setdefault("unexplained-same-support", temp["calendar"])
        previous = result
        if mode == "OBSERVATIONAL":
            prior = retained[i]
            assert stamp(prior["cutoff"]) == cutoff
            if prior["status"] == "VALID":
                bounded = replace(data, bars=baseline.prepare(data, cutoff)[-param.total :])
                row["controls"] = {
                    "BASELINE": baseline.evaluate(bounded, cutoff).semantic_hash,
                    "H1": h1.evaluate(bounded, cutoff).semantic_hash,
                    "comparison_domain": (
                        "original price domain; candidate additionally qualifies calendar"
                    ),
                }
                baseline_equal += row["controls"]["BASELINE"] == prior["BASELINE"]["hash"]
                h1_equal += row["controls"]["H1"] == prior["H1"]["hash"]
                assert row["controls"]["BASELINE"] == prior["BASELINE"]["hash"]
                assert row["controls"]["H1"] == prior["H1"]["hash"]
            else:
                assert result["status"] == "INSUFFICIENT"
        select_cases(result, cases)
        rows.append(row)
        if i % 20 == 0:
            print(data.timeframe, mode, i + 1, "/", len(cutoffs), flush=True)
    summary = {
        "security": data.security,
        "timeframe": data.timeframe,
        "mode": mode,
        "scheduled": len(cutoffs),
        "status": status,
        "all_reasons": all_reasons,
        "active_reasons": active_reasons,
        "totals": totals,
        "transitions": transitions,
        "baseline_hash_equal": baseline_equal,
        "h1_hash_equal": h1_equal,
        "max_window": max(r["selected_count"] for r in rows),
        "unique_event_witnesses": len(events),
        "unique_census_rows": len(catalog),
        "case_categories": {
            k: int(k in cases) for k in ("accepted", "repeated-kind", "veto", "calendar")
        },
    }
    stem = data.security + "." + data.timeframe + "." + mode
    write_new(
        output / (stem + ".json"),
        {
            "summary": summary,
            "rows": rows,
            "census_catalog": catalog,
            "event_catalog": events,
            "recognition_records": recognized,
            "census_decode": (
                "index=array position; active iff index>=active_start; all reasons in catalog"
            ),
        },
    )
    for category, case in cases.items():
        write_new(output / "cases" / (data.timeframe + "." + category + ".json"), case)
    return summary


def run(root: Path, data_dir: Path, calendar_file: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("FRESH_EXCLUSIVE_OUTPUT_REQUIRED")
    started = datetime.now(UTC)
    timer = perf_counter()
    data, facts, sources = load(root, data_dir, calendar_file)
    freeze = json.loads((root / EVIDENCE / "freeze.json").read_text(encoding="utf-8"))
    summaries = []
    with localcontext(CONTEXT):
        for tf in ("W1", "D1", "M30"):
            retained = json.loads(
                (
                    root
                    / "docs/evidence/TASK_006B_Q/research-02/comparison"
                    / f"US.AVGO.{tf}.comparison.json"
                ).read_text(encoding="utf-8")
            )["rows"]
            for mode in ("OBSERVATIONAL", "AS_OF"):
                summaries.append(
                    frame(data[tf], facts, freeze["cutoffs"][tf], retained, mode, output)
                )
    universe = json.loads(
        (root / "docs/evidence/TASK_006B_Q/universe.json").read_text(encoding="utf-8")
    )
    coverage = []
    for cohort in ("original", "additional"):
        for member in universe["members"]:
            for tf in ("W1", "D1", "M30"):
                for mode in ("OBSERVATIONAL", "AS_OF"):
                    record = next(
                        s for s in summaries if s["timeframe"] == tf and s["mode"] == mode
                    )
                    coverage.append(
                        {
                            "cohort": cohort,
                            "security": member["security"],
                            "market": member["market"],
                            "timeframe": tf,
                            "mode": mode,
                            "target": 100,
                            "status": record["status"]
                            if cohort == "original" and member["security"] == "US.AVGO"
                            else {"UNAVAILABLE": 100},
                        }
                    )
    calendar_catalog = {
        f.ref: {
            "day": f.day.isoformat(),
            "market": f.market,
            "timezone": f.timezone,
            "kind": f.kind,
            "segments": f.segments,
            "source": f.source,
            "retrieved_at": f.retrieved_at,
            "available_at": f.available_at,
            "complete": f.complete,
        }
        for f in facts
    }
    write_new(
        output / "source-calendar-manifest.json",
        {
            "sources": sources,
            "calendar_catalog": calendar_catalog,
            "cutoff_manifest_hash": digest("freeze", freeze),
            "universe_hash": digest("universe", universe),
        },
    )
    write_new(
        output / "coverage.json",
        {
            "gate": "INCOMPLETE",
            "members": coverage,
            "denominators": "40 equities, 24 US / 16 HK; 100 cutoffs per frame/mode/cohort",
            "additional_cutoff_ceiling": freeze["additional_ceiling"],
            "additional_rule": "last 100 completed slots if data existed; zero additional data",
            "strict_market_confirmation": "NOT_ESTABLISHED",
            "AVGO": "development data, current-QFQ/PARTIAL, availability unknown",
        },
    )
    summary = {
        "rule": RULE,
        "started_at": started,
        "finished_at": datetime.now(UTC),
        "runtime_seconds": str(perf_counter() - timer),
        "frames": summaries,
        "output_bytes_before_summary_and_plots": sum(
            p.stat().st_size for p in output.rglob("*") if p.is_file()
        ),
        "OpenD_history_requests": 0,
        "price_acquisition_requests": 0,
    }
    write_new(output / "summary.json", summary)
    return summary
