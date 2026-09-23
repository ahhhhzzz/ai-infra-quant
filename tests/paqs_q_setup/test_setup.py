"""Causal OHLC-to-advisory acceptance and hard risk geometry boundaries."""

import ast
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from ai_infra_quant.application.paqs_q_event_artifacts import load_event_registry
from ai_infra_quant.application.paqs_q_setup_artifacts import FILES, run, verify
from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON
from ai_infra_quant.core.domain.paqs_q.event_reference import ContextEvidence, EventEvidence
from ai_infra_quant.core.domain.paqs_q.setup_reference import MultiInput
from ai_infra_quant.core.strategy.paqs_q.event_context import CONTEXT_ID, EVENT_ID
from ai_infra_quant.core.strategy.paqs_q.setup_rules import Period, Replay, State
from ai_infra_quant.core.strategy.paqs_q.setup_targets import Obstacle, regular_open_gaps, targets
from tools.research.setup_risk.__main__ import write_bundle
from tools.research.setup_risk.demo import demo_bundle

ROOT = Path(__file__).resolve().parents[2]
D = Decimal


@pytest.fixture(scope="module")
def right():
    bundle = demo_bundle()
    return bundle, run(bundle, ROOT)


@pytest.fixture(scope="module")
def reclaim():
    bundle = demo_bundle(daily_count=81, weekly_history=80, offset=D("0"), range_failure=True)
    return bundle, run(bundle, ROOT)


@pytest.fixture(scope="module")
def pullback():
    bundle = demo_bundle(daily_count=68, weekly_history=101, offset=D("-5.5"), trend_pullback=True)
    return bundle, run(bundle, ROOT)


@pytest.mark.parametrize(
    ("fixture_name", "family", "variant"),
    [
        ("pullback", "TREND_PULLBACK_LONG", "SUPPORT_ZONE"),
        ("reclaim", "RANGE_FAILED_BREAKDOWN_LONG", "RECLAIM"),
        ("right", "RIGHT_SIDE_BREAKOUT_LONG", "FOLLOW_THROUGH"),
        ("right", "RIGHT_SIDE_BREAKOUT_LONG", "RETEST"),
    ],
)
def test_real_ohlc_to_context_event_setup_and_next_open_ready(
    request, fixture_name, family, variant
):
    bundle, result = request.getfixturevalue(fixture_name)
    assert result.status == "AVAILABLE" and result.strict_confirmation
    assert [b.timeframe for b in result.bindings] == ["W1", "D1", "M30"]
    assert all(b.structure_version == b.event_version == "1.0.1" for b in result.bindings)
    facts = [f for f in result.facts if (f.family, f.variant) == (family, variant)]
    assert {
        "CREATED",
        "TRIGGER_PENDING",
        "FOLLOW_THROUGH_CONFIRMED",
        "ENTRY_PENDING_REVALIDATION",
        "LONG_READY",
    } <= {f.status for f in facts}
    first_ready = next(f for f in facts if f.status == "LONG_READY")
    previous = next(
        f
        for f in facts
        if f.status == "ENTRY_PENDING_REVALIDATION" and f.candidate_key == first_ready.candidate_key
    )
    assert first_ready.effective_at == bundle.m30.bars[first_ready.m30_index].start
    assert first_ready.effective_at >= previous.effective_at
    assert first_ready.m30_index == previous.m30_index + 1
    assert first_ready.entry_reference_source == "SYNTHETIC_OPEN"
    assert first_ready.entry_advisory == "LONG_READY"
    assert D(first_ready.rr_t1) >= 2
    assert D(first_ready.target1.effective_price) > D(first_ready.reference_price)
    assert D(first_ready.reference_price) > D(first_ready.risk_reference_price) > 0
    assert len({f.setup_key for f in facts if f.status == "CREATED"}) >= 1


def test_right_variants_share_origin_but_not_opportunity_identity(right):
    _, result = right
    created = [
        f for f in result.facts if f.family == "RIGHT_SIDE_BREAKOUT_LONG" and f.status == "CREATED"
    ]
    ft = next(f for f in created if f.variant == "FOLLOW_THROUGH")
    retest = next(f for f in created if f.variant == "RETEST")
    assert ft.origin_event_key == retest.origin_event_key
    assert ft.source_key == retest.source_key
    assert ft.setup_key != retest.setup_key


def test_missing_period_mode_basis_and_scale_are_not_downgraded(right):
    bundle, _ = right
    assert run(MultiInput(None, bundle.d1, bundle.m30), ROOT).reasons == ("W1_INPUT_MISSING",)
    assert run(MultiInput(bundle.w1, bundle.d1, None), ROOT).reasons == ("M30_INPUT_MISSING",)
    wrong_mode = replace(bundle.w1, mode="OBSERVATIONAL")
    assert run(MultiInput(wrong_mode, bundle.d1, bundle.m30), ROOT).status == "INVALID"
    bars = tuple(replace(b, adjustment="UNADJUSTED") for b in bundle.m30.bars)
    wrong_basis = replace(bundle.m30, bars=bars)
    assert (
        "MULTIPERIOD_ADJUSTMENT_OR_PROVENANCE_MISMATCH"
        in run(MultiInput(bundle.w1, bundle.d1, wrong_basis), ROOT).reasons
    )
    scaled = replace(
        bundle.m30,
        bars=tuple(
            replace(b, open=b.open * 2, high=b.high * 2, low=b.low * 2, close=b.close * 2)
            for b in bundle.m30.bars
        ),
    )
    assert (
        "MULTIPERIOD_PRICE_SCALE_CONFLICT"
        in run(MultiInput(bundle.w1, bundle.d1, scaled), ROOT).reasons
    )


def test_wrong_w1_or_missing_range_source_blocks_family():
    wrong_w1 = demo_bundle(daily_count=68, weekly_history=80, offset=D("-5.5"), trend_pullback=True)
    assert not any(
        f.family == "TREND_PULLBACK_LONG" and f.status == "CREATED"
        for f in run(wrong_w1, ROOT).facts
    )
    no_range_excursion = demo_bundle(daily_count=81, weekly_history=80, offset=D("0"))
    assert not any(
        f.family == "RANGE_FAILED_BREAKDOWN_LONG" and f.status == "CREATED" and f.d1_index == 80
        for f in run(no_range_excursion, ROOT).facts
    )


def test_no_open_reference_or_late_reference_cannot_backdate_long_ready(right):
    bundle, normal = right
    no_refs = run(replace(bundle, entry_references=()), ROOT)
    assert "ENTRY_REFERENCE_UNAVAILABLE_AT_OPEN" in no_refs.reasons
    assert not any(f.status == "LONG_READY" for f in no_refs.facts)
    ready = next(f for f in normal.facts if f.status == "LONG_READY")
    refs = tuple(
        replace(ref, available_at=bundle.m30.bars[ready.m30_index].completed_at)
        if ref.price_at == ready.entry_reference_price_at
        else ref
        for ref in bundle.entry_references
    )
    late = run(replace(bundle, entry_references=refs), ROOT)
    assert not any(
        f.status == "LONG_READY" and f.candidate_key == ready.candidate_key for f in late.facts
    )
    assert any("LATE_OPEN_REFERENCE_NOT_OPEN_TIME_QUALIFICATION" in f.reasons for f in late.facts)


def test_independent_open_qualifies_before_next_m30_candle_completes(right):
    bundle, full = right
    ready = next(f for f in full.facts if f.status == "LONG_READY")
    stage_a = next(
        f
        for f in full.facts
        if f.candidate_key == ready.candidate_key and f.status == "ENTRY_PENDING_REVALIDATION"
    )
    cutoff = ready.entry_reference_price_at
    w1 = replace(
        bundle.w1, bars=tuple(b for b in bundle.w1.bars if b.completed_at <= cutoff), as_of=cutoff
    )
    d1 = replace(
        bundle.d1, bars=tuple(b for b in bundle.d1.bars if b.completed_at <= cutoff), as_of=cutoff
    )
    m30 = replace(bundle.m30, bars=bundle.m30.bars[: stage_a.m30_index + 1], as_of=cutoff)
    assert m30.bars[-1].completed_at == stage_a.effective_at < cutoff
    assert all(bar.start != cutoff for bar in m30.bars)
    ref = next(r for r in bundle.entry_references if r.price_at == cutoff)
    partial = run(MultiInput(w1, d1, m30, (ref,)), ROOT)
    assert partial.status == "AVAILABLE"
    assert any(
        f.status == "LONG_READY"
        and f.candidate_key == ready.candidate_key
        and f.reference_price == ready.reference_price
        for f in partial.facts
    )


def test_d1_wick_equal_close_and_below_close_invalidation(right):
    bundle, _ = right
    periods = _periods(bundle)
    index = 90
    original = bundle.d1.bars[index]
    atr = D(periods["D1"].context.frames[index].atr)
    anchor = original.close - D("0.5") * atr
    threshold = anchor - D("0.15") * atr
    state = State(
        "a" * 64,
        "RIGHT_SIDE_BREAKOUT_LONG",
        "RETEST",
        "b" * 64,
        None,
        anchor,
        D("0.15"),
        86,
        bundle.d1.bars[86].completed_at,
    )

    def evaluated(close: Decimal, low: Decimal):
        changed = replace(original, close=close, low=min(original.low, low))
        data = replace(
            bundle.d1, bars=(*bundle.d1.bars[:index], changed, *bundle.d1.bars[index + 1 :])
        )
        replay = Replay(
            replace(bundle, d1=data), {**periods, "D1": replace(periods["D1"], data=data)}
        )
        current = replace(state)
        replay.states.append(current)
        replay._on_d1_close(index)
        return current, replay

    wick, _ = evaluated(original.close, threshold - D("1"))
    equal, _ = evaluated(threshold, threshold)
    below, replay = evaluated(threshold - D("0.001"), threshold - D("0.001"))
    assert not wick.terminal and not equal.terminal
    assert below.terminal
    assert any(f.status == "INVALIDATED" and f.setup_key == state.key for f in replay.facts)


def test_observational_never_claims_historical_long_ready(right):
    bundle, _ = right
    observed = replace(
        bundle,
        w1=replace(bundle.w1, mode="OBSERVATIONAL"),
        d1=replace(bundle.d1, mode="OBSERVATIONAL"),
        m30=replace(bundle.m30, mode="OBSERVATIONAL"),
    )
    result = run(observed, ROOT)
    assert result.status == "AVAILABLE" and not result.strict_confirmation
    assert any(f.status == "OBSERVATIONAL_LONG_QUALIFIED" for f in result.facts)
    assert not any(f.status == "LONG_READY" for f in result.facts)


def test_partial_w1_and_synthetic_open_on_provider_basis_block_qualification(right):
    bundle, _ = right
    observed = replace(
        bundle,
        w1=replace(bundle.w1, mode="OBSERVATIONAL", quality="PARTIAL"),
        d1=replace(bundle.d1, mode="OBSERVATIONAL"),
        m30=replace(bundle.m30, mode="OBSERVATIONAL"),
    )
    partial = run(observed, ROOT)
    assert partial.status == "AVAILABLE"
    assert not any(f.status == "OBSERVATIONAL_LONG_QUALIFIED" for f in partial.facts)
    assert any("W1_CONTEXT_QUALITY_INSUFFICIENT" in f.reasons for f in partial.facts)

    def provider_basis(data):
        return replace(
            data,
            mode="OBSERVATIONAL",
            bars=tuple(replace(bar, adjustment="PROVIDER_QFQ_CURRENT") for bar in data.bars),
        )

    provider = MultiInput(
        provider_basis(bundle.w1),
        provider_basis(bundle.d1),
        provider_basis(bundle.m30),
        tuple(replace(ref, adjustment="PROVIDER_QFQ_CURRENT") for ref in bundle.entry_references),
    )
    rejected = run(provider, ROOT)
    assert rejected.status == "AVAILABLE"
    assert not any(f.status == "OBSERVATIONAL_LONG_QUALIFIED" for f in rejected.facts)
    assert any("ENTRY_REFERENCE_PRICE_BASIS_CONFLICT" in f.reasons for f in rejected.facts)


def test_gap_over_frozen_target_and_near_target_does_not_shop_t2(right):
    bundle, normal = right
    ready = next(f for f in normal.facts if f.status == "LONG_READY")
    ref_time = ready.entry_reference_price_at
    barrier = D(ready.target1.upper)
    refs = tuple(
        replace(ref, price=barrier + 1) if ref.price_at == ref_time else ref
        for ref in bundle.entry_references
    )
    result = run(replace(bundle, entry_references=refs), ROOT)
    matching = [f for f in result.facts if f.candidate_key == ready.candidate_key]
    assert any(f.status == "NO_TRADE" and "ORIGINAL_T1_OVERRUN" in f.reasons for f in matching)
    assert not any(f.status == "LONG_READY" for f in matching)


def test_targets_complete_diameter_nearest_and_inside_block():
    from datetime import UTC, datetime

    known = datetime(2025, 1, 1, tzinfo=UTC)
    obstacles = (
        Obstacle("ZONE", "a" * 64, D("105"), D("106"), known),
        Obstacle("HIGH", "b" * 64, D("105.2"), D("105.2"), known),
        Obstacle("HIGH", "c" * 64, D("105.4"), D("105.4"), known),
        Obstacle("HIGH", "d" * 64, D("120"), D("120"), known),
    )
    t1, t2, _, inside = targets(obstacles, D("100"), D("1"))
    assert t1.effective_price == "105"
    assert set(t1.source_keys) == {"a" * 64, "b" * 64}
    assert t2.effective_price == "105.4"  # no chain merge via b
    assert not inside
    _, _, rejected, inside = targets(obstacles, D("105.5"), D("1"))
    assert inside and any("ENTRY_INSIDE_RESISTANCE" in item for item in rejected)


def test_regular_open_gap_uses_completed_m30_and_preserves_unfilled_interval(right):
    bundle, _ = right
    registry = load_event_registry(ROOT)
    structure = registry.structure(bundle.d1, CONTEXT_ID, "1.0.1")
    context = ContextEvidence.model_validate_json(
        FrozenJSON.of(structure.document()["evidence"]).data
    )
    original = bundle.m30.bars
    previous_close = original[12].close
    bar = original[13]
    shifted = replace(
        bar,
        open=previous_close - D("3"),
        high=previous_close - D("2.7"),
        low=previous_close - D("3.2"),
        close=previous_close - D("2.9"),
    )
    m30 = replace(bundle.m30, bars=(*original[:13], shifted, *original[14:]))
    cutoff = shifted.completed_at
    gaps, reasons = regular_open_gaps(bundle.d1, context, m30, cutoff)
    assert gaps and gaps[0].kind == "REGULAR_SESSION_OPEN_GAP"
    assert gaps[0].gap_original_upper == previous_close
    assert gaps[0].lower == shifted.high
    assert gaps[0].gap_status == "PARTIALLY_FILLED"
    assert not any("GAP_SESSION_COVERAGE_UNPROVEN" in x for x in reasons)
    before, _ = regular_open_gaps(bundle.d1, context, m30, shifted.start)
    assert not before


def _periods(bundle: MultiInput) -> dict[str, Period]:
    registry = load_event_registry(ROOT)
    output = {}
    for name, data in (("W1", bundle.w1), ("D1", bundle.d1), ("M30", bundle.m30)):
        structure = registry.structure(data, CONTEXT_ID, "1.0.1")
        event = registry.event(data, structure, EVENT_ID, "1.0.1")
        context = ContextEvidence.model_validate_json(
            FrozenJSON.of(structure.document()["evidence"]).data
        )
        facts = tuple(
            EventEvidence.model_validate_json(FrozenJSON.of(r["record"]["evidence"]).data)
            for r in event.document()["records"]
        )
        output[name] = Period(data, context, facts)
    return output


def test_age_15_inclusive_16_expired_and_no_missing_bar_clock():
    bundle = demo_bundle(
        daily_count=81, weekly_history=80, m30_count=221, offset=D("0"), range_failure=True
    )
    replay = Replay(bundle, _periods(bundle))
    created = bundle.d1.bars[80]
    state = State(
        "a" * 64,
        "RANGE_FAILED_BREAKDOWN_LONG",
        "RECLAIM",
        "b" * 64,
        None,
        D("98.8"),
        D("0.1"),
        80,
        created.completed_at,
    )
    assert replay._expired(state, bundle.d1.bars[95].start) is False
    assert replay._expired(state, bundle.d1.bars[96].start) is True
    missing = replace(bundle.d1, bars=bundle.d1.bars[:90] + bundle.d1.bars[91:])
    broken = Replay(
        replace(bundle, d1=missing),
        {**_periods(bundle), "D1": replace(_periods(bundle)["D1"], data=missing)},
    )
    assert broken._expired(state, bundle.d1.bars[96].start) is None
    assert "SETUP_CLOCK_CALENDAR_OR_D1_BAR_INSUFFICIENT" in broken.reasons


def test_future_append_preserves_old_facts(right):
    bundle, full = right
    cutoff = bundle.m30.bars[39].completed_at
    w1 = replace(
        bundle.w1, bars=tuple(b for b in bundle.w1.bars if b.completed_at <= cutoff), as_of=cutoff
    )
    d1 = replace(
        bundle.d1, bars=tuple(b for b in bundle.d1.bars if b.completed_at <= cutoff), as_of=cutoff
    )
    m30 = replace(bundle.m30, bars=bundle.m30.bars[:40], as_of=cutoff)
    refs = tuple(r for r in bundle.entry_references if r.price_at <= cutoff)
    short = run(MultiInput(w1, d1, m30, refs), ROOT)
    assert short.status == "AVAILABLE"
    old = [
        (
            f.setup_key,
            f.candidate_key,
            f.status,
            f.effective_at,
            f.reference_price,
            f.risk_reference_price,
            f.rr_t1,
        )
        for f in short.facts
    ]
    complete = [
        (
            f.setup_key,
            f.candidate_key,
            f.status,
            f.effective_at,
            f.reference_price,
            f.risk_reference_price,
            f.rr_t1,
        )
        for f in full.facts
        if f.effective_at <= cutoff
    ]
    assert old == complete


def test_manifest_and_core_import_boundary():
    assert verify(ROOT) == run(demo_bundle(), ROOT).code_hash
    assert any(p.endswith("setup_rules.py") for p in FILES)
    for name in ("setup_rules.py", "setup_targets.py"):
        tree = ast.parse((ROOT / "src/ai_infra_quant/core/strategy/paqs_q" / name).read_text())
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert not any(
            module.startswith(("tools", "ai_infra_quant.integrations")) for module in imports
        )


def test_offline_report_exact_json_and_links(right, tmp_path):
    bundle, result = right
    output = tmp_path / "setup"
    summary = write_bundle(bundle, output)
    raw = json.loads((output / "result.json").read_text(encoding="utf-8"))
    html = (output / "report.html").read_text(encoding="utf-8")
    assert summary["result_hash"] == raw["result_hash"] == result.canonical_result_hash
    assert len(raw["run"]["facts"]) == len(result.facts)
    assert raw["run"]["facts"][0]["fact_key"] == result.facts[0].fact_key
    first_ready = next(f for f in result.facts if f.status == "LONG_READY")
    exported = next(f for f in raw["run"]["facts"] if f["fact_key"] == first_ready.fact_key)
    assert exported["rr_t1"] == first_ready.rr_t1
    assert exported["entry_reference_source_ref"] == first_ready.entry_reference_source_ref
    assert "result.json" in html and "<canvas" in html
    assert "https://" not in html and "http://" not in html
    assert "__PAYLOAD__" not in html
