"""Q01: a structural target is not active before its Setup binding fact."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from ai_infra_quant.application.paqs_q_holder import conditional_holder
from ai_infra_quant.application.paqs_q_setup_artifacts import run as run_setup
from ai_infra_quant.core.domain.paqs_q.canonical import digest
from ai_infra_quant.core.domain.paqs_q.setup_reference import MultiInput, SetupFact, SetupRun
from tools.research.setup_risk.demo import demo_bundle

ROOT = Path(__file__).resolve().parents[2]
CUTOFF = datetime(2025, 5, 23, 15, 30, tzinfo=UTC)


def prefix_bundle(cutoff: datetime) -> MultiInput:
    source = demo_bundle()
    assert source.w1 is not None and source.d1 is not None and source.m30 is not None
    periods = tuple(
        replace(
            period,
            bars=tuple(bar for bar in period.bars if bar.completed_at <= cutoff),
            as_of=cutoff,
        )
        for period in (source.w1, source.d1, source.m30)
    )
    refs = tuple(ref for ref in source.entry_references if ref.available_at <= cutoff)
    return MultiInput(*periods, refs)


def test_original_ohlc_prefix_does_not_backdate_new_no_trade_target() -> None:
    source = prefix_bundle(CUTOFF)
    result = run_setup(source, ROOT)
    assert result.status == "AVAILABLE"
    assert source.m30 is not None
    holder = conditional_holder(result, source.m30)
    assert len(holder["items"]) == 2
    assert all(item["status"] != "TARGET_REACHED_REVIEW" for item in holder["items"])
    for item in holder["items"]:
        facts = [fact for fact in result.facts if fact.setup_key == item["setup_key"]]
        rejected = next(
            fact
            for fact in facts
            if fact.status == "NO_TRADE"
            and fact.effective_at == CUTOFF
            and fact.target1 is not None
            and fact.target1.effective_price == "110.2"
        )
        assert item["target1"] == "115.2"
        assert item["target_binding"]["candidate_key"] != rejected.candidate_key
        assert item["target_binding"]["fact_key"] != rejected.fact_key
        assert item["target_touch"] is None


def _real_post_binding_touch() -> tuple[MultiInput, SetupRun, datetime]:
    source = demo_bundle()
    assert source.w1 is not None and source.d1 is not None and source.m30 is not None
    touch_at = datetime(2025, 5, 23, 16, tzinfo=UTC)
    touch_high = Decimal("115.5")
    changed = tuple(
        replace(bar, high=touch_high) if bar.start == touch_at else bar for bar in source.m30.bars
    )
    assert sum(bar.start == touch_at for bar in changed) == 1
    m30 = replace(source.m30, bars=changed)
    local_day = touch_at.astimezone(ZoneInfo(source.d1.market_timezone)).date()
    d1 = replace(
        source.d1,
        bars=tuple(
            replace(bar, high=max(bar.high, touch_high))
            if bar.start.astimezone(ZoneInfo(source.d1.market_timezone)).date() == local_day
            else bar
            for bar in source.d1.bars
        ),
    )
    w1 = replace(
        source.w1,
        bars=tuple(
            replace(bar, high=max(bar.high, touch_high)) if bar.start <= touch_at < bar.end else bar
            for bar in source.w1.bars
        ),
    )
    study = MultiInput(w1, d1, m30, source.entry_references)
    return study, run_setup(study, ROOT), touch_at


def test_completed_post_binding_ohlc_touch_is_traceable() -> None:
    source, result, touch_at = _real_post_binding_touch()
    assert result.status == "AVAILABLE"
    assert source.m30 is not None
    holder = conditional_holder(result, source.m30)
    for item in holder["items"]:
        assert item["status"] == "TARGET_REACHED_REVIEW"
        assert item["target_binding"]["effective_at"] < touch_at
        assert item["target_binding"]["fact_status"] == "ENTRY_PENDING_REVALIDATION"
        assert item["target_touch"]["start"] == touch_at
        bar = next(bar for bar in source.m30.bars if bar.start == touch_at)
        assert item["target_touch"]["bar_version_ref"] == bar.version_ref
        assert item["target_binding"]["fact_key"] in item["evidence_fact_keys"]


def test_crossing_the_binding_instant_is_not_a_post_binding_touch() -> None:
    source = demo_bundle()
    result = run_setup(source, ROOT)
    assert source.m30 is not None
    crossing = source.m30.bars[-1]
    original = next(fact for fact in result.facts if fact.status == "ENTRY_PENDING_REVALIDATION")
    assert original.target1 is not None
    price = str(crossing.high)
    target = original.target1.model_copy(
        update={"effective_price": price, "lower": price, "upper": price}
    )
    stage_a = original.model_copy(
        update={
            "fact_key": "a" * 64,
            "effective_at": crossing.start + timedelta(minutes=15),
            "target1": target,
        }
    )
    isolated = result.model_copy(update={"facts": (stage_a,)})
    item = conditional_holder(isolated, source.m30)["items"][0]
    assert item["target_binding"]["effective_at"] > crossing.start
    assert item["status"] == "UNDETERMINED"
    assert item["target_touch"] is None


def test_qualified_same_candidate_new_target_binds_only_at_stage_b() -> None:
    source = prefix_bundle(CUTOFF)
    result = run_setup(source, ROOT)
    assert source.m30 is not None
    first = next(fact for fact in result.facts if fact.status == "ENTRY_PENDING_REVALIDATION")
    assert first.target1 is not None
    original_b = next(
        fact
        for fact in result.facts
        if fact.setup_key == first.setup_key
        and fact.candidate_key == first.candidate_key
        and fact.status == "LONG_READY"
    )
    tighter = first.target1.model_copy(
        update={"effective_price": "110.2", "lower": "110.2", "upper": "110.2"}
    )
    new_b = original_b.model_copy(
        update={"fact_key": "e" * 64, "effective_at": CUTOFF, "target1": tighter}
    )
    isolated = result.model_copy(update={"facts": (first, new_b)})
    item = conditional_holder(isolated, source.m30)["items"][0]
    assert item["target1"] == "110.2"
    assert item["target_binding"]["candidate_key"] == first.candidate_key
    assert item["target_binding"]["fact_key"] == new_b.fact_key
    assert item["target_binding"]["effective_at"] == CUTOFF
    assert item["status"] == "UNDETERMINED"
    assert item["target_touch"] is None


def test_repeat_and_other_candidate_cannot_reset_or_replace_bound_target() -> None:
    source, result, touch_at = _real_post_binding_touch()
    assert source.m30 is not None
    first = next(fact for fact in result.facts if fact.status == "ENTRY_PENDING_REVALIDATION")
    assert first.target1 is not None
    repeated = first.model_copy(
        update={
            "fact_key": "b" * 64,
            "effective_at": touch_at + timedelta(hours=1),
        }
    )
    other_target = first.target1.model_copy(
        update={"effective_price": "110.2", "lower": "110.2", "upper": "110.2"}
    )
    other = first.model_copy(
        update={
            "fact_key": "c" * 64,
            "candidate_key": "d" * 64,
            "effective_at": touch_at + timedelta(hours=2),
            "target1": other_target,
        }
    )
    repeated_only = result.model_copy(update={"facts": (first, repeated)})
    item = conditional_holder(repeated_only, source.m30)["items"][0]
    assert item["status"] == "TARGET_REACHED_REVIEW"
    assert item["target1"] == first.target1.effective_price
    assert item["target_binding"]["candidate_key"] == first.candidate_key
    assert item["target_binding"]["fact_key"] == first.fact_key
    assert item["target_touch"]["start"] == touch_at
    ambiguous = result.model_copy(update={"facts": (first, repeated, other)})
    unknown = conditional_holder(ambiguous, source.m30)["items"][0]
    assert unknown["status"] == "UNDETERMINED"
    assert unknown["target_binding"] is None
    assert "MULTIPLE_CANDIDATE_TARGETS_AMBIGUOUS" in unknown["reasons"]


def _two_qualified_candidates() -> tuple[MultiInput, SetupRun, tuple[SetupFact, ...]]:
    source = demo_bundle()
    result = run_setup(source, ROOT)
    assert result.status == "AVAILABLE" and source.m30 is not None
    first = next(f for f in result.facts if f.status == "ENTRY_PENDING_REVALIDATION")
    assert first.candidate_key is not None
    second = next(
        f
        for f in result.facts
        if f.status == "ENTRY_PENDING_REVALIDATION"
        and f.setup_key == first.setup_key
        and f.candidate_key != first.candidate_key
    )
    stages = []
    for stage_a in (first, second):
        stage_b = next(
            f
            for f in result.facts
            if f.setup_key == stage_a.setup_key
            and f.candidate_key == stage_a.candidate_key
            and f.status == "LONG_READY"
        )
        stages.extend((stage_a, stage_b))
    assert all(f.target1 is not None and f.target1.effective_price == "115.2" for f in stages)
    return source, result, tuple(stages)


def test_other_candidate_qualified_stage_b_target_conflict_is_undetermined() -> None:
    source, result, stages = _two_qualified_candidates()
    second_b = stages[3]
    assert second_b.target1 is not None
    assert second_b.reference_price is not None and second_b.risk_reference_price is not None
    changed = second_b.model_dump()
    changed["target1"] = second_b.target1.model_copy(
        update={"effective_price": "115.1", "lower": "115.1", "upper": "115.1"}
    ).model_dump()
    entry = Decimal(second_b.reference_price)
    stop = Decimal(second_b.risk_reference_price)
    changed["rr_t1"] = str((Decimal("115.1") - entry) / (entry - stop))
    assert Decimal(changed["rr_t1"]) > 2
    changed["fact_key"] = digest(
        "paqs-q/setup-fact/v1.0.1", {k: v for k, v in changed.items() if k != "fact_key"}
    )
    revised_b = SetupFact.model_validate(changed)
    assert revised_b.fact_key == digest(
        "paqs-q/setup-fact/v1.0.1", revised_b.model_dump(exclude={"fact_key"})
    )
    isolated = result.model_copy(update={"facts": (*stages[:3], revised_b)})
    holder = conditional_holder(isolated, source.m30)
    assert holder["holder_version"] == "1.0.2"
    item = holder["items"][0]
    assert item["status"] == "UNDETERMINED"
    assert item["target_binding"] is None
    assert item["target1"] is None
    assert "MULTIPLE_CANDIDATE_TARGETS_AMBIGUOUS" in item["reasons"]


def test_other_candidate_qualified_stage_b_same_target_is_not_a_conflict() -> None:
    source, result, stages = _two_qualified_candidates()
    isolated = result.model_copy(update={"facts": stages})
    item = conditional_holder(isolated, source.m30)["items"][0]
    assert item["status"] == "THESIS_VALID"
    assert item["target1"] == "115.2"
    assert item["target_binding"]["candidate_key"] == stages[0].candidate_key
    assert item["target_binding"]["fact_key"] == stages[0].fact_key
