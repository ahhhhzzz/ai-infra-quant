"""Independent research-clock, census and chart-selection assertions."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from tools.research.paqs_q.r04.calendar import Fact
from tools.research.paqs_q.r04.model import evaluate
from tools.research.paqs_q.r04.study import costs, recognize, select_cases, write_new
from tools.research.paqs_q.types import Bar, Dataset, canonical

from .test_calendar_model import bar, row, sample


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
