"""Independent research-clock, census and chart-selection assertions."""

import json
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from tools.research.paqs_q.r04.calendar import Fact
from tools.research.paqs_q.r04.model import evaluate
from tools.research.paqs_q.r04.study import costs, recognize, select_cases, write_new
from tools.research.paqs_q.types import Bar, Dataset, canonical

from .test_calendar_model import bar, fact, row, sample


def test_research_recognition_clock_is_actual_not_scheduled_and_idempotent() -> None:
    data, facts = sample(count=312)
    result = evaluate(data, facts, data.bars[-1].end)
    records: dict[str, Any] = {}
    now = datetime(2026, 9, 10, tzinfo=UTC)
    recognize(result, records, now)
    recognize(result, records, now + timedelta(minutes=1))
    assert len(records) == 2
    assert all(
        r["recognized_at"] == now > r["first_seen_scheduled_cutoff"] for r in records.values()
    )
    with pytest.raises(ValueError, match="RECOGNITION_BEFORE"):
        recognize(result, {}, data.bars[0].end)


def test_deterministic_cases_have_no_future_bars_and_zero_categories() -> None:
    data, facts = sample()
    result = evaluate(data, facts, data.bars[-2].end)
    cases: dict[str, Any] = {}
    select_cases(result, cases)
    assert set(cases) == {"accepted", "repeated-kind"}
    assert cases["accepted"]["selected"]["index"] == 85
    assert cases["repeated-kind"]["selected"]["index"] == 89
    before = canonical(cases)
    select_cases(evaluate(data, facts, data.bars[-1].end), cases)
    assert canonical(cases) == before
    for case in cases.values():
        assert len(case["bars"]) <= 40
        assert all(b.completed_at <= case["cutoff"] for b in case["bars"])
    stats = costs(result)
    assert stats["all_centers"] == 312 and stats["active_centers"] == 252
    assert sum(stats["reasons_all"].values()) == 312
    assert stats["repeated_same_kind_pairs"] == stats["pair_denominator"] == 1


def test_evidence_writer_never_overwrites(tmp_path: Path) -> None:
    p = tmp_path / "evidence.json"
    write_new(p, {"original": True})
    before = p.read_bytes()
    with pytest.raises(FileExistsError):
        write_new(p, {"replacement": True})
    assert p.read_bytes() == before


@pytest.mark.parametrize("market", ["US", "HK"])
def test_public_m30_same_segment_qualification_and_boundary_cost(market: str) -> None:
    data, daily = sample(market, count=90)
    bars: list[Bar] = []
    facts: list[Fact] = []
    half = timedelta(minutes=30)
    for f in daily:
        facts.append(f)
        for start, end in f.segments:
            while start + half <= end and len(bars) < 200:
                bars.append(bar(start, start + half, "M30", market))
                start += half
    # Fifth bucket of a later afternoon/session is a hand-valid quartet.
    index = next(
        i
        for i in range(50, 150)
        if bars[i - 2].end == bars[i - 1].start
        and bars[i - 1].end == bars[i].start
        and bars[i].end == bars[i + 1].start
    )
    bars[index] = replace(bars[index], high=Decimal(110), close=Decimal(105))
    result = evaluate(
        Dataset(data.security, "M30", data.market_timezone, tuple(bars)),
        tuple(facts),
        bars[-1].end,
        "AS_OF",
    )
    assert result["status"] == "VALID"
    assert any(e["extreme_ref"] == bars[index].ref for e in result["events"])
    assert any(r["reason"] == "PROHIBITED_SEGMENT_BOUNDARY" for r in result["census"])
    assert len(result["census"]) == 200


def test_unfinished_future_and_delayed_selected_price_not_silently_used() -> None:
    data, facts = sample(count=313)
    cutoff = data.bars[-2].end
    b = replace(data.bars[-1], high=Decimal("NaN"), completed=False)
    result = evaluate(replace(data, bars=(*data.bars[:-1], b)), facts, cutoff)
    assert result["status"] == "VALID" and result["audit"]["violation_count"] == 0
    delayed = replace(data.bars[85], available_at=data.bars[-1].end)
    raw = list(data.bars)
    raw[85] = delayed
    old = evaluate(replace(data, bars=tuple(raw)), facts, cutoff, "AS_OF")
    assert old["status"] == "INSUFFICIENT"
    new = evaluate(replace(data, bars=tuple(raw)), facts, data.bars[-1].end, "AS_OF")
    assert new["status"] == "VALID" and any(e["extreme_ref"] == delayed.ref for e in new["events"])


def test_calendar_identity_and_malformed_segment_fail_closed_for_witness() -> None:
    data, facts = sample(count=312)
    index = next(i for i, f in enumerate(facts) if f.day == data.bars[85].start.date())
    f = facts[index]
    for bad in (
        replace(f, market="HK"),
        replace(f, segments=((f.segments[0][1], f.segments[0][0]),)),
    ):
        changed = (*facts[:index], bad, *facts[index + 1 :])
        result = evaluate(data, changed, data.bars[-1].end)
        assert row(result, data.bars[85])["support_hash"] is None
        assert not any(e["extreme_ref"] == data.bars[85].ref for e in result["events"])


def assert_segment_conservation(stats: dict[str, Any]) -> None:
    for field, total in (
        ("centers", "active_centers"),
        ("support", "complete_support_active"),
        ("events", "events"),
    ):
        assert sum(s[field] for s in stats["segments"].values()) == stats[total]


def test_public_w1_unresolved_segment_is_counted_without_changing_census() -> None:
    # Hypothetical weekday calendar, with one explicitly unknown active week.
    monday = date(2020, 1, 6)
    facts = [fact(monday + timedelta(days=i), closed=i % 7 >= 5) for i in range(130 * 7)]
    zone = ZoneInfo(facts[0].timezone)
    bars = []
    for i in range(130):
        start = datetime.combine(monday + timedelta(weeks=i), time.min, zone)
        end = datetime.combine(monday + timedelta(weeks=i + 1), time.min, zone)
        completion = facts[i * 7 + 4].segments[-1][1]
        bars.append(
            replace(bar(start, end, "W1"), completed_at=completion, available_at=completion)
        )
    bars[85] = replace(bars[85], high=Decimal(110), close=Decimal(105))
    facts[50 * 7] = replace(facts[50 * 7], kind="UNKNOWN", segments=())
    result = evaluate(Dataset("US.TEST", "W1", zone.key, tuple(bars)), tuple(facts), bars[-1].end)
    assert result["status"] == "VALID" and len(result["events"]) == 1
    unresolved = [r for r in result["census"] if r["active"] and r["segment"] is None]
    assert len(unresolved) == 1 and unresolved[0]["support_hash"] is None
    before = canonical(result)
    stats = costs(result)
    assert "None" not in stats["segments"]
    assert stats["segments"]["UNRESOLVED_SEGMENT"] == {"centers": 1, "support": 0, "events": 0}
    assert stats["active_centers"] == 104
    assert_segment_conservation(stats)
    assert canonical(result) == before


@pytest.mark.parametrize("timeframe", ["W1", "D1", "M30"])
@pytest.mark.parametrize("mode", ["OBSERVATIONAL", "AS_OF"])
def test_retained_census_segment_accounting(timeframe: str, mode: str) -> None:
    # Decode immutable evidence, not its defective derived segment counts.
    path = Path(__file__).resolve().parents[4] / "docs/evidence/TASK_006B_Q/research-04"
    doc = json.loads(
        (path / "study-02" / f"US.AVGO.{timeframe}.{mode}.json").read_text(encoding="utf-8")
    )
    unresolved_total = 0
    for record in doc["rows"]:
        result = {
            "census": [
                dict(doc["census_catalog"][identity], active=index >= record["active_start"])
                for index, identity in enumerate(record["census_ids"])
            ],
            "events": [dict(doc["event_catalog"][e["identity"]], **e) for e in record["events"]],
        }
        stats = costs(result)
        assert_segment_conservation(stats)
        assert "None" not in stats["segments"]
        unresolved = sum(r["active"] and r["segment"] is None for r in result["census"])
        unresolved_total += unresolved
        if unresolved:
            assert record["status"] == "VALID" and timeframe == "W1"
            assert stats["segments"]["UNRESOLVED_SEGMENT"]["centers"] == unresolved
        else:
            assert stats["segments"] == record["costs"]["segments"]
        if record["status"] != "VALID":
            assert stats["segments"] == {} and stats["active_centers"] == 0
    assert unresolved_total == (1921 if timeframe == "W1" and mode == "OBSERVATIONAL" else 0)


@pytest.mark.parametrize("status", ["INVALID", "INSUFFICIENT"])
def test_rejected_input_does_not_fabricate_segment_coverage(status: str) -> None:
    data, facts = sample(count=312)
    data = (
        replace(data, quality="INVALID")
        if status == "INVALID"
        else replace(data, bars=data.bars[:-1])
    )
    result = evaluate(data, facts, data.bars[-1].end)
    assert result["status"] == status
    stats = costs(result)
    assert stats["segments"] == {} and stats["event_density"] is None
    assert stats["active_centers"] == stats["complete_support_active"] == stats["events"] == 0
    assert_segment_conservation(stats)
