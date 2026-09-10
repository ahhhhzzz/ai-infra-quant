"""Independent synthetic session and price oracles; never real market samples."""

import json
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, Inexact, localcontext
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo

import pytest

from tools.research.paqs_q.io import read_dataset, write_dataset
from tools.research.paqs_q.r04.calendar import Fact, select, slot, support
from tools.research.paqs_q.r04.model import compare, evaluate
from tools.research.paqs_q.types import Bar, Dataset, Timeframe, canonical

KNOWN = datetime(2019, 1, 1, tzinfo=UTC)


def fact(day: date, market: str = "US", closed: bool = False, early: bool = False) -> Fact:
    zone = ZoneInfo("America/New_York" if market == "US" else "Asia/Hong_Kong")
    pairs = [(time(9, 30), time(13) if early else time(16))]
    if market == "HK":
        pairs = [(time(9, 30), time(12)), (time(13), time(16))]
    segments = tuple(
        (
            datetime.combine(day, a, zone).astimezone(UTC),
            datetime.combine(day, b, zone).astimezone(UTC),
        )
        for a, b in pairs
    )
    return Fact(
        day,
        market,
        zone.key,
        "CLOSED" if closed else "OPEN",
        () if closed else segments,
        "SYNTHETIC-ORACLE",
        KNOWN,
        KNOWN,
        True,
    )


def bar(start: datetime, end: datetime, tf: str = "D1", market: str = "US") -> Bar:
    assert tf in {"D1", "M30", "W1"}
    return Bar(
        ("US.TEST" if market == "US" else "HK.00005"),
        cast(Timeframe, tf),
        start,
        end,
        end,
        end,
        end,
        Decimal(100),
        Decimal(101),
        Decimal(99),
        Decimal(100),
        Decimal(1),
    )


def sample(market: str = "US", count: int = 313) -> tuple[Dataset, tuple[Fact, ...]]:
    day = date(2024, 1, 1)
    facts: list[Fact] = []
    bars: list[Bar] = []
    while len(bars) < count:
        f = fact(day, market, day.weekday() >= 5)
        facts.append(f)
        if f.kind == "OPEN":
            bars.append(bar(f.segments[0][0], f.segments[-1][1], market=market))
        day += timedelta(days=1)
    for i in (85, 89):
        bars[i] = replace(bars[i], high=Decimal(110), open=Decimal(105), close=Decimal(105))
    return Dataset(
        ("US.TEST" if market == "US" else "HK.00005"), "D1", facts[0].timezone, tuple(bars)
    ), tuple(facts)


def row(result: dict[str, Any], center: Bar) -> dict[str, Any]:
    return next(r for r in result["census"] if r["center"] == center.ref)


@pytest.mark.parametrize("market", ["US", "HK"])
@pytest.mark.parametrize("mode", ["AS_OF", "OBSERVATIONAL"])
def test_hand_exact_repeated_kind_and_rolling_support(market: str, mode: str) -> None:
    data, facts = sample(market)
    old = evaluate(data, facts, data.bars[-2].end, mode)
    new = evaluate(data, facts, data.bars[-1].end, mode)
    assert old["status"] == new["status"] == "VALID"
    assert [(e["kind"], e["price"]) for e in old["events"]] == [("HIGH", Decimal(110))] * 2
    assert old["events"][1]["same_kind_as_previous"]
    assert old["events"][1]["separation"] == 4
    assert old["events"][1]["amplitude_local_range"] == 0
    assert old["events"][0]["available_at"] == data.bars[86].end
    assert row(old, data.bars[85])["price_support"] == tuple(b.ref for b in data.bars[83:87])
    metrics = compare(old, new, data)
    assert metrics["endpoint_opportunities"] == metrics["full_support_opportunities"] == 2
    assert metrics["lost"] == metrics["rediscovered"] == metrics["full_support_lost"] == 0
    assert metrics["same_endpoint_witness_changed"] == 0


@pytest.mark.parametrize("closure", ["weekend", "holiday", "exceptional"])
def test_known_closed_gap_is_not_missing_session(closure: str) -> None:
    first = date(2026, 3, 6)
    dates = [first + timedelta(days=i) for i in range(4)]
    facts = [fact(d, closed=i in (1, 2)) for i, d in enumerate(dates)]
    facts[1] = replace(facts[1], source="SYNTHETIC-" + closure)
    bars = tuple(bar(f.segments[0][0], f.segments[-1][1]) for f in (facts[0], facts[3]))
    used = support(bars, {f.day: f for f in facts}, "AS_OF")
    assert len(used) == 4 and used[1].kind == used[2].kind == "CLOSED"
    assert bars[0].start.hour == 14 and bars[1].start.hour == 13  # US DST, same 09:30 local.


@pytest.mark.parametrize(
    "kind,reason", [("OPEN", "MISSING_EXPECTED_SESSION"), ("UNKNOWN", "CALENDAR_UNKNOWN")]
)
def test_calendar_gap_not_inferred_from_arrived_bars(kind: str, reason: str) -> None:
    fs = [fact(date(2026, 4, 1) + timedelta(days=i)) for i in range(3)]
    fs[1] = replace(fs[1], kind=kind)
    bs = tuple(bar(f.segments[0][0], f.segments[-1][1]) for f in (fs[0], fs[2]))
    with pytest.raises(ValueError, match=reason):
        support(bs, {f.day: f for f in fs}, "OBSERVATIONAL")


@pytest.mark.parametrize("market", ["US", "HK"])
def test_segment_and_missing_bucket_oracles(market: str) -> None:
    f = fact(date(2026, 3, 9), market)
    start = f.segments[0][0]
    half = timedelta(minutes=30)
    a, b = (
        bar(start, start + half, "M30", market),
        bar(start + 2 * half, start + 3 * half, "M30", market),
    )
    with pytest.raises(ValueError, match="MISSING_EXPECTED_BUCKET"):
        support((a, b), {f.day: f}, "AS_OF")
    nxt = fact(f.day + timedelta(days=1), market)
    c = bar(nxt.segments[0][0], nxt.segments[0][0] + half, "M30", market)
    with pytest.raises(ValueError, match="PROHIBITED_SEGMENT_BOUNDARY"):
        support((a, c), {f.day: f, nxt.day: nxt}, "AS_OF")
    if market == "HK":
        c = bar(f.segments[1][0], f.segments[1][0] + half, "M30", market)
        with pytest.raises(ValueError, match="PROHIBITED_SEGMENT_BOUNDARY"):
            support((a, c), {f.day: f}, "AS_OF")


@pytest.mark.parametrize(
    "change,reason",
    [
        ("extended", "OUTSIDE_REGULAR_SEGMENT"),
        ("short", "BUCKET_ALIGNMENT"),
        ("partial", "BUCKET_NOT_COMPLETE_REGULAR"),
    ],
)
def test_early_close_and_illegal_buckets(change: str, reason: str) -> None:
    f = fact(date(2026, 11, 27), early=True)
    end = f.segments[0][1]
    b = bar(end - timedelta(minutes=30), end, "M30")
    assert slot(b, {f.day: f}, "AS_OF")[1].endswith(":0")
    if change == "extended":
        b = replace(b, start=end, end=end + timedelta(minutes=30))
    elif change == "short":
        b = replace(b, start=end - timedelta(minutes=15))
    else:
        b = replace(b, coverage="PARTIAL")
    with pytest.raises(ValueError, match=reason):
        slot(b, {f.day: f}, "AS_OF")


def test_completed_holiday_week_uses_factual_close_before_nominal_endpoint() -> None:
    monday = date(2026, 3, 30)
    fs = [fact(monday + timedelta(days=i), closed=i >= 4) for i in range(7)]
    zone = ZoneInfo(fs[0].timezone)
    b = bar(
        datetime.combine(monday, time.min, zone),
        datetime.combine(monday + timedelta(days=7), time.min, zone),
        "W1",
    )
    b = replace(b, completed_at=fs[3].segments[-1][1], available_at=fs[3].segments[-1][1])
    assert len(slot(b, {f.day: f for f in fs}, "AS_OF")[0]) == 7
    with pytest.raises(ValueError, match="WEEK_FACTUAL_COMPLETION"):
        slot(replace(b, completed_at=b.end), {f.day: f for f in fs}, "AS_OF")
    with pytest.raises(ValueError, match="CALENDAR_UNKNOWN"):
        slot(b, {f.day: f for f in fs[:-1]}, "OBSERVATIONAL")


@pytest.mark.parametrize("mode", ["AS_OF", "OBSERVATIONAL"])
@pytest.mark.parametrize("coverage", ["INVALID", "made-up", "UNKNOWN", "PARTIAL"])
def test_quality_not_upgraded_public_and_json(mode: str, coverage: str, tmp_path: Path) -> None:
    data, facts = sample(count=312)
    bars = list(data.bars)
    bars[85] = replace(bars[85], coverage=coverage)
    broken = replace(data, bars=tuple(bars))
    write_dataset(tmp_path / "input.json", broken)
    for d in (broken, read_dataset(tmp_path / "input.json")):
        result = evaluate(d, facts, bars[-1].end, mode)
        assert result["status"] == "INVALID" and result["events"] == []
    if coverage in {"PARTIAL", "UNKNOWN"}:
        lawful = replace(broken, quality=coverage)
        result = evaluate(lawful, facts, bars[-1].end, mode)
        assert result["quality"] == coverage
        assert (result["status"] == "VALID") == (mode == "OBSERVATIONAL")


def test_unknown_historical_evidence_cannot_become_strict() -> None:
    data, facts = sample(count=312)
    data = replace(
        data,
        quality="PARTIAL",
        bars=tuple(
            replace(b, available_at=None, adjustment="PROVIDER_QFQ_CURRENT") for b in data.bars
        ),
    )
    facts = tuple(replace(f, available_at=None, complete=False) for f in facts)
    obs = evaluate(data, facts, data.bars[-1].end)
    strict = evaluate(data, facts, data.bars[-1].end, "AS_OF")
    assert len(obs["events"]) == 2 and not obs["strict_confirmation"]
    assert all(e["available_at"] is None for e in obs["events"])
    assert strict["status"] == "INSUFFICIENT" and not strict["events"]


def test_calendar_version_isolation_and_changed_witness() -> None:
    data, facts = sample()
    old_cutoff, new_cutoff = data.bars[-2].end, data.bars[-1].end
    target = next(
        f
        for f in facts
        if f.day == data.bars[84].start.astimezone(ZoneInfo(data.market_timezone)).date()
    )
    revision = replace(target, available_at=new_cutoff, source="SYNTHETIC-REVISED")
    old = evaluate(data, facts, old_cutoff, "AS_OF")
    assert canonical(evaluate(data, (*facts, revision), old_cutoff, "AS_OF")) == canonical(old)
    new = evaluate(data, (*facts, revision), new_cutoff, "AS_OF")
    m = compare(old, new, data)
    assert m["calendar_revision_count"] == m["same_endpoint_witness_changed"] == 1
    assert m["coverage_excluded"] == 1 and m["lost"] == 0
    # Late unknown day never certifies old cutoff.
    late = tuple(replace(f, available_at=new_cutoff) if f == target else f for f in facts)
    assert (
        row(evaluate(data, late, old_cutoff, "AS_OF"), data.bars[85])["reason"]
        == "CALENDAR_UNKNOWN"
    )


@pytest.mark.parametrize("mode", ["OBSERVATIONAL", "AS_OF"])
def test_conflicting_calendar_and_future_payload_isolation(mode: str) -> None:
    data, facts = sample(count=312)
    cutoff = data.bars[-1].end
    target = facts[100]
    conflict = replace(target, kind="CLOSED", segments=())
    assert evaluate(data, (*facts, conflict), cutoff, mode)["status"] == "INVALID"
    future = replace(conflict, kind="MALFORMED", available_at=cutoff + timedelta(days=1))
    assert canonical(evaluate(data, (*facts, future), cutoff, mode)) == canonical(
        evaluate(data, facts, cutoff, mode)
    )


def test_negative_veto_missing_fourth_input_not_false_and_insertion() -> None:
    data, facts = sample(count=313)
    missing = data.bars[83]
    d = replace(data, bars=tuple(b for b in data.bars if b != missing))
    r = evaluate(d, facts, d.bars[-1].end)
    assert row(r, data.bars[85])["raw"] == (True, False)
    assert row(r, data.bars[85])["previous_raw"] is None
    assert row(r, data.bars[85])["reason"] == "MISSING_EXPECTED_SESSION"
    restored = evaluate(data, facts, data.bars[-1].end)
    assert any(e["extreme_ref"] == data.bars[85].ref for e in restored["events"])


@pytest.mark.parametrize("shape", ["dual", "tie", "zero"])
def test_local_ambiguity_not_forced(shape: str) -> None:
    data, facts = sample(count=312)
    bars = list(data.bars)
    if shape == "dual":
        bars[85] = replace(bars[85], low=Decimal(90))
    elif shape == "tie":
        bars[86] = replace(bars[86], high=Decimal(110))
    else:
        bars[84] = replace(bars[84], high=Decimal(100), low=Decimal(100))
    r = evaluate(replace(data, bars=tuple(bars)), facts, bars[-1].end)
    assert not any(e["extreme_ref"] == bars[85].ref for e in r["events"])


def test_all_price_input_time_checks_versions_and_transport_origin(tmp_path: Path) -> None:
    data, facts = sample(count=313)
    old_cutoff, new_cutoff = data.bars[-2].end, data.bars[-1].end
    base = evaluate(data, facts, old_cutoff, "AS_OF")
    revision = replace(data.bars[85], high=Decimal(111), available_at=new_cutoff)
    revised = replace(data, bars=(*data.bars, revision))
    assert canonical(evaluate(revised, facts, old_cutoff, "AS_OF")) == canonical(base)
    result = evaluate(revised, facts, new_cutoff, "AS_OF")
    assert (
        compare(base, result, revised)["price_information_change"]["revised_historical_count"] == 1
    )
    transport = replace(
        data, bars=tuple(replace(b, source_ref="OTHER", retrieved_at=new_cutoff) for b in data.bars)
    )
    with localcontext() as context:
        context.prec = 6
        context.traps[Inexact] = True
        altered = evaluate(transport, facts, old_cutoff, "AS_OF")
    assert canonical(altered["events"]) == canonical(base["events"])
    assert altered["audit"]["violation_count"] == 0
    write_dataset(tmp_path / "roundtrip.json", revised)
    assert canonical(
        evaluate(read_dataset(tmp_path / "roundtrip.json"), facts, old_cutoff, "AS_OF")
    ) == canonical(base)
    assert json.loads(canonical(result))["events"][0]["price"] == "111"


def test_genuine_active_expiry() -> None:
    data, facts = sample(count=340)
    old = evaluate(data, facts, data.bars[311].end)
    new = evaluate(data, facts, data.bars[-1].end)
    assert compare(old, new, data)["expired"] == 1


def test_calendar_strict_completeness_and_unknown_version_order() -> None:
    f = fact(date(2026, 1, 1))
    b = bar(f.segments[0][0], f.segments[-1][1])
    with pytest.raises(ValueError, match="CALENDAR_NOT_STRICT"):
        slot(b, {f.day: replace(f, complete=False)}, "AS_OF")
    with pytest.raises(ValueError, match="CALENDAR_UNKNOWN_VERSION_ORDER"):
        select(
            (f, replace(f, available_at=None, kind="CLOSED", segments=())), b.end, "OBSERVATIONAL"
        )
