"""Counterfactual acceptance, retained dependencies and structural metric oracles."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from tests.research.paqs_q.r04.test_calendar_model import bar, fact, sample
from tools.research.paqs_q.r04.calendar import Fact, support
from tools.research.paqs_q.r04.model import compare
from tools.research.paqs_q.r04.model import evaluate as baseline
from tools.research.paqs_q.r04.study import recognize, write_new
from tools.research.paqs_q.r05.cases import choose, finalize
from tools.research.paqs_q.r05.enumeration import enumerate_domain
from tools.research.paqs_q.r05.metrics import metrics
from tools.research.paqs_q.r05.model import ablate, dependency_audit, evaluate, verify_pair
from tools.research.paqs_q.types import Bar, Dataset, canonical


def synthetic(tf: str, market: str = "US") -> tuple[Dataset, tuple[Fact, ...], int]:
    from datetime import date, datetime, time
    from zoneinfo import ZoneInfo

    data, facts = sample(market, count=340)
    bars = [replace(b, high=Decimal(101), open=Decimal(100), close=Decimal(100)) for b in data.bars]
    if tf == "W1":
        monday = date(2020, 1, 6)
        facts = tuple(
            fact(monday + timedelta(days=i), market, closed=i % 7 >= 5) for i in range(140 * 7)
        )
        zone = ZoneInfo(data.market_timezone)
        bars = []
        for i in range(140):
            start = datetime.combine(monday + timedelta(weeks=i), time.min, zone)
            end = datetime.combine(monday + timedelta(weeks=i + 1), time.min, zone)
            completion = facts[i * 7 + 4].segments[-1][1]
            bars.append(
                replace(
                    bar(start, end, tf, market), completed_at=completion, available_at=completion
                )
            )
        bars = bars[:131]
    elif tf == "M30":
        bars = []
        for f in facts:
            for start, end in f.segments:
                while start + timedelta(minutes=30) <= end and len(bars) < 201:
                    bars.append(bar(start, start + timedelta(minutes=30), tf, market))
                    start += timedelta(minutes=30)
    else:
        bars = bars[:313]
    # The first evaluation excludes the last record. A quartet and following confirmation
    # fit one segment even in the shorter HK sessions.
    j = next(i for i in range(75, 115) if _supported(tuple(bars[i - 2 : i + 3]), facts))
    bars[j] = replace(bars[j], high=Decimal(110), close=Decimal(105))
    bars[j + 1] = replace(bars[j + 1], low=Decimal(80), close=Decimal(100))
    return replace(data, timeframe=bars[0].timeframe, bars=tuple(bars)), facts, j


def _supported(bars: tuple[Bar, ...], facts: tuple[Fact, ...]) -> bool:
    try:
        support(bars, {f.day: f for f in facts}, "AS_OF")
        return True
    except ValueError:
        return False


@pytest.mark.parametrize("tf", ["W1", "D1", "M30"])
@pytest.mark.parametrize("market", ["US", "HK"])
@pytest.mark.parametrize("mode", ["OBSERVATIONAL", "AS_OF"])
def test_exact_opposite_veto_bijection_and_shared_support(tf: str, market: str, mode: str) -> None:
    data, facts, j = synthetic(tf, market)
    cutoff = data.bars[-2].completed_at
    b = baseline(data, facts, cutoff, mode)
    frozen = canonical(b)
    a = ablate(b, facts)
    delta = verify_pair(b, a)
    assert b["status"] == a["status"] == "VALID"
    assert [(e["kind"], e["price"]) for e in b["events"]] == [("HIGH", Decimal(110))]
    assert [(e["kind"], e["price"]) for e in a["events"]] == [
        ("HIGH", Decimal(110)),
        ("LOW", Decimal(80)),
    ]
    assert len(delta["added"]) == 1 and delta["added"][0]["previous_raw_kind"] == "opposite"
    assert b["events"][0]["key"] == a["events"][0]["key"]
    assert b["events"][0]["identity"] != a["events"][0]["identity"]
    witness = next(r for r in a["census"] if r["center"] == data.bars[j + 1].ref)
    assert witness["price_support"] == tuple(x.ref for x in data.bars[j - 1 : j + 3])
    assert canonical(b) == frozen
    m = metrics(a)
    assert m["same_kind_pairs"] == 0 and m["opposite_kind_pairs"] == 1
    assert m["separation_one_pairs"] == 1 and m["max_unit_gap_chain_events"] == 2
    new = evaluate(data, facts, data.bars[-1].completed_at, mode)
    transition = compare(a, new, data)
    assert transition["full_support_opportunities"] == 2
    assert transition["lost"] == transition["rediscovered"] == transition["full_support_lost"] == 0


@pytest.mark.parametrize(
    "change", ["tie", "dual", "zero", "missing", "calendar", "late", "invalid", "insufficient"]
)
def test_no_promotion_of_unqualified_centers(change: str) -> None:
    data, facts, j = synthetic("D1")
    bars = list(data.bars)
    cutoff = bars[-2].end
    target = j + 1
    if change == "tie":
        bars[target + 1] = replace(bars[target + 1], low=Decimal(80))
    elif change == "dual":
        bars[target] = replace(bars[target], high=Decimal(140))
    elif change == "zero":
        bars[j] = replace(
            bars[j], open=Decimal(100), high=Decimal(100), low=Decimal(100), close=Decimal(100)
        )
    elif change == "missing":
        del bars[target - 2]
    elif change == "calendar":
        facts = tuple(
            replace(f, kind="UNKNOWN") if f.day == bars[target - 2].start.date() else f
            for f in facts
        )
    elif change == "late":
        bars[target - 2] = replace(bars[target - 2], available_at=bars[-1].end)
    elif change == "invalid":
        data = replace(data, quality="INVALID")
    elif change == "insufficient":
        bars = bars[-100:]
    original = data.bars[target].ref
    changed = replace(data, bars=tuple(bars))
    b, a = baseline(changed, facts, cutoff, "AS_OF"), evaluate(changed, facts, cutoff, "AS_OF")
    verify_pair(b, a)
    assert not any(e["extreme_ref"] == original for e in a["events"])
    if change == "calendar":
        d = next(d for d in dependency_audit(b) if d["center"] == original)
        assert d["diagnostic"] == "TRIPLE_ONLY_ELIGIBLE" and not d["event"] and d["current_xor"]


def test_revision_and_calendar_information_are_not_origin_changes() -> None:
    data, facts, j = synthetic("D1")
    old_cutoff, new_cutoff = data.bars[-2].end, data.bars[-1].end
    old = evaluate(data, facts, old_cutoff, "AS_OF")
    revised = replace(
        data, bars=(*data.bars, replace(data.bars[j + 1], low=Decimal(79), available_at=new_cutoff))
    )
    assert canonical(evaluate(revised, facts, old_cutoff, "AS_OF")) == canonical(old)
    new = evaluate(revised, facts, new_cutoff, "AS_OF")
    assert compare(old, new, revised)["price_information_change"]["revised_historical_count"] == 1
    target = next(f for f in facts if f.day == data.bars[j - 1].start.date())
    amendment = replace(target, available_at=new_cutoff, source="SYNTHETIC-REVISION")
    assert canonical(evaluate(data, (*facts, amendment), old_cutoff, "AS_OF")) == canonical(old)
    changed = evaluate(data, (*facts, amendment), new_cutoff, "AS_OF")
    assert compare(old, changed, data)["calendar_revision_count"] == 1


def test_insertion_and_active_expiry_are_outside_identical_support() -> None:
    data, facts, j = synthetic("D1")
    cutoff = data.bars[-1].end
    missing = replace(data, bars=tuple(b for i, b in enumerate(data.bars) if i != j - 1))
    old = evaluate(missing, facts, cutoff)
    restored = evaluate(data, facts, cutoff)
    assert not any(e["extreme_ref"] == data.bars[j + 1].ref for e in old["events"])
    assert any(e["extreme_ref"] == data.bars[j + 1].ref for e in restored["events"])
    assert compare(old, restored, data)["coverage_excluded"] >= 0
    extended, fs = sample(count=360)
    bars = list(extended.bars)
    bars[: len(data.bars)] = data.bars
    extended = replace(extended, bars=tuple(bars))
    shifted = evaluate(extended, fs, bars[-1].end)
    assert compare(restored, shifted, extended)["expired"] == 2


def test_unknown_availability_remains_observational_and_recognition_actual() -> None:
    from datetime import UTC, datetime

    data, facts, _ = synthetic("W1")
    data = replace(
        data,
        quality="PARTIAL",
        bars=tuple(
            replace(b, available_at=None, adjustment="PROVIDER_QFQ_CURRENT") for b in data.bars
        ),
    )
    facts = tuple(replace(f, available_at=None, complete=False) for f in facts)
    obs = evaluate(data, facts, data.bars[-1].completed_at)
    strict = evaluate(data, facts, data.bars[-1].completed_at, "AS_OF")
    assert len(obs["events"]) == 2 and not obs["strict_confirmation"]
    assert strict["status"] == "INSUFFICIENT" and not strict["events"]
    records: dict[str, Any] = {}
    now = datetime(2026, 9, 12, tzinfo=UTC)
    recognize(obs, records, now)
    assert all(r["recognized_at"] == now and r["available_at"] is None for r in records.values())


def test_finite_enumeration_and_non_event_calendar_domains() -> None:
    result = enumerate_domain()
    assert result["input_count"] == 40000 and result["set_or_bijection_failures"] == 0
    assert result["counts"]["COMPLETE"]["veto"] > 0
    assert all(result["counts"][s]["A1"] == 0 for s in result["calendar_states"] if s != "COMPLETE")


def test_case_selection_repeatable_deduplicated_and_exclusive(tmp_path: Path) -> None:
    data, facts, _ = synthetic("D1")
    b = baseline(data, facts, data.bars[-1].end)
    a = ablate(b, facts)
    selected: dict[str, Any] = {}
    for _ in range(2):
        choose(b, a, verify_pair(b, a), metrics(b), metrics(a), dependency_audit(b), selected)
    cases, counts = finalize(selected)
    assert counts["first-added"] == counts["unit-gap-chain"] == 1
    assert counts["new-same-kind-pair"] == 0
    assert all(all(x.completed_at <= c["cutoff"] for x in c["bars"]) for c in cases)
    path = tmp_path / "cases.json"
    write_new(path, cases)
    with pytest.raises(FileExistsError):
        write_new(path, cases)


def retained_doc(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    """Synthetic R04 transport shape for end-to-end study tests, without market access."""
    from tools.research.paqs_q.r04.study import costs

    catalog: list[dict[str, Any]] = []
    events: dict[str, Any] = {}
    rows = []
    for snap in snapshots:
        indices = []
        for r in snap["census"]:
            indices.append(len(catalog))
            catalog.append({k: v for k, v in r.items() if k not in {"index", "active"}})
        for e in snap["events"]:
            events[e["identity"]] = e
        record = {
            k: v for k, v in snap.items() if k not in {"bars", "census", "events", "calendar"}
        }
        record.update(
            census_ids=indices,
            events=snap["events"],
            costs=costs(snap),
            active_start=next((r["index"] for r in snap["census"] if r["active"]), 0),
        )
        rows.append(record)
    import json

    result: dict[str, Any] = json.loads(
        canonical({"rows": rows, "census_catalog": catalog, "event_catalog": events})
    )
    return result


@pytest.mark.parametrize("tf", ["W1", "D1", "M30"])
@pytest.mark.parametrize("mode", ["OBSERVATIONAL", "AS_OF"])
def test_synthetic_full_frame_pipeline_and_catalog_decode(
    tf: str, mode: str, tmp_path: Path
) -> None:
    from tools.research.paqs_q.r05.study import frame, read

    data, facts, _ = synthetic(tf)
    cutoffs = [b.completed_at for b in data.bars[-2:]]
    snapshots = [baseline(data, facts, t, mode) for t in cutoffs]
    summary = frame(
        data, facts, [t.isoformat() for t in cutoffs], retained_doc(snapshots), tmp_path, mode
    )
    assert summary["valid"] == 2
    assert summary["added_occurrences"] == 2 and summary["deduplicated_added"] == 1
    assert summary["A1"]["rolling"]["full_support_lost"] == 0
    doc = read(tmp_path / "frames" / f"{tf}.{mode}.json")
    for i, row in enumerate(doc["rows"]):
        for arm in ("B0", "A1"):
            snap = snapshots[i] if arm == "B0" else ablate(snapshots[i], facts)
            packed = row[arm]
            decoded = [
                dict(doc["census_catalog"][ref], index=j, active=j >= packed["active_start"])
                for j, ref in enumerate(packed["census_ids"])
            ]
            assert canonical(decoded) == canonical(snap["census"])
            assert doc["calendar_catalog"][packed["calendar_view_id"]] == snap["calendar"]


def test_baseline_reconciliation_rejects_semantic_drift(tmp_path: Path) -> None:
    from tools.research.paqs_q.r05.study import reconcile_baseline

    old, new, changed = (tmp_path / name for name in ("old", "new", "changed"))
    for directory, value in ((old, 1), (new, 1), (changed, 2)):
        write_new(directory / "counts.json", {"value": value})
    assert reconcile_baseline(old, new)["status"] == "PASS"
    with pytest.raises(AssertionError, match="B0_REFERENCE_DRIFT"):
        reconcile_baseline(old, changed)


def test_adjacent_alternating_chain_is_exposed_not_filtered() -> None:
    data, facts, j = synthetic("D1")
    bars = list(data.bars)
    bars[j + 2] = replace(bars[j + 2], high=Decimal(140), close=Decimal(120))
    bars[j + 3] = replace(bars[j + 3], low=Decimal(50), close=Decimal(100))
    data = replace(data, bars=tuple(bars))
    b, a = baseline(data, facts, bars[-1].end), evaluate(data, facts, bars[-1].end)
    d = verify_pair(b, a)
    assert [e["kind"] for e in a["events"]] == ["HIGH", "LOW", "HIGH", "LOW"]
    assert len(d["added"]) == 3 and metrics(a)["max_unit_gap_chain_events"] == 4
    assert metrics(a)["separation_one_pairs"] == 3


def test_full_case_rejection_and_count_growth_not_a_decision_rule() -> None:
    from tools.research.paqs_q.r05.metrics import disposition

    def entry(same: int, denominator: int) -> dict[str, Any]:
        return {
            "overlapping_cutoff_totals": {"same_kind_pairs": same, "pair_denominator": denominator}
        }

    f = {
        "mode": "OBSERVATIONAL",
        "valid": 100,
        "B0": entry(1, 2),
        "A1": entry(1, 4),
        "deduplicated_restored_more_extreme": 1,
    }
    assert disposition([f]) == "RECOMMEND_CROSS_SAMPLE_ONLY"
    f["deduplicated_restored_more_extreme"] = 0
    assert disposition([f]) == "INCONCLUSIVE"
    f["A1"] = entry(3, 4)
    assert disposition([f]) == "REJECT_NO_VETO"
