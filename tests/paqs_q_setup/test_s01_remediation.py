"""Real Event 1.0.1 parentage for a failed range-support breakdown."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from ai_infra_quant.application.paqs_q_event_artifacts import load_event_registry
from ai_infra_quant.application.paqs_q_setup_artifacts import run
from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON
from ai_infra_quant.core.domain.paqs_q.event_reference import ContextEvidence, EventEvidence
from ai_infra_quant.core.domain.paqs_q.setup_reference import MultiInput
from ai_infra_quant.core.strategy.paqs_q.event_context import CONTEXT_ID, EVENT_ID
from ai_infra_quant.core.strategy.paqs_q.setup_rules import FAMILY_RANGE, Period, Replay
from tools.research.setup_risk.demo import demo_bundle

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def breakdown_failure():
    bundle = demo_bundle(daily_count=82, offset=Decimal("0"))
    d1_bars = list(bundle.d1.bars)
    d1_bars[80] = replace(d1_bars[80], close=Decimal("98.8"), low=Decimal("98.6"))
    bundle = MultiInput(
        bundle.w1, replace(bundle.d1, bars=tuple(d1_bars)), bundle.m30, bundle.entry_references
    )
    registry = load_event_registry(ROOT)
    periods = {}
    for name, data in (("W1", bundle.w1), ("D1", bundle.d1), ("M30", bundle.m30)):
        context = registry.structure(data, CONTEXT_ID, "1.0.1")
        event = registry.event(data, context, EVENT_ID, "1.0.1")
        assert context.status == event.status == "AVAILABLE"
        context_evidence = ContextEvidence.model_validate_json(
            FrozenJSON.of(context.document()["evidence"]).data
        )
        event_evidence = tuple(
            EventEvidence.model_validate_json(FrozenJSON.of(row["record"]["evidence"]).data)
            for row in event.document()["records"]
        )
        periods[name] = Period(data, context_evidence, event_evidence)
    d1_events = periods["D1"].events
    parent = next(
        e
        for e in d1_events
        if e.bar_index == 80
        and e.kind == "BREAKDOWN"
        and e.direction == "DOWN"
        and e.source is not None
        and e.source.source_type == "RANGE_BOUNDARY"
        and e.source.role == "SUPPORT"
    )
    failure = next(
        e
        for e in d1_events
        if e.bar_index == 81
        and e.kind == "BREAKOUT_FAILURE"
        and e.direction == "UP"
        and e.source == parent.source
    )
    return bundle, periods, parent, failure


def test_real_ohlc_breakdown_failure_creates_range_reclaim(breakdown_failure):
    bundle, periods, parent, failure = breakdown_failure
    assert parent.status == failure.status == "CONFIRMED"
    assert parent.event_key == parent.anchor_key
    assert failure.anchor_key != parent.anchor_key
    assert failure.related_keys == (parent.event_key,)
    assert Replay(bundle, periods).regime(periods["W1"], bundle.d1.bars[81].completed_at) == "RANGE"
    replay_facts, _ = Replay(bundle, periods).run()
    assert any(
        fact.family == FAMILY_RANGE
        and fact.variant == "RECLAIM"
        and fact.status == "CREATED"
        and fact.d1_index == 81
        and fact.origin_event_key == failure.event_key
        and fact.source_key == parent.source.version_key
        for fact in replay_facts
    )
    result = run(bundle, ROOT)
    assert result.status == "AVAILABLE" and tuple(result.facts) == replay_facts


@pytest.mark.parametrize("bad_link", ["wrong_type", "wrong_source_parent", "same_bar_parent"])
def test_breakout_failure_rejects_wrong_parent_reference(breakdown_failure, bad_link):
    bundle, periods, parent, failure = breakdown_failure
    d1_events = periods["D1"].events
    if bad_link == "wrong_type":
        wrong = next(
            e
            for e in d1_events
            if e.bar_index == 80 and e.source == parent.source and e.kind == "ATTEMPT"
        )
        replacement = failure.model_copy(update={"related_keys": (wrong.event_key,)})
    elif bad_link == "wrong_source_parent":
        wrong = next(
            e
            for e in d1_events
            if e.bar_index == 80 and e.kind == "BREAKDOWN" and e.source != parent.source
        )
        replacement = failure.model_copy(update={"related_keys": (wrong.event_key,)})
    else:
        replacement = failure.model_copy(update={"related_keys": (failure.event_key,)})
    edited = tuple(replacement if e is failure else e for e in d1_events)
    edited_periods = {**periods, "D1": replace(periods["D1"], events=edited)}
    facts, _ = Replay(bundle, edited_periods).run()
    assert not any(
        f.family == FAMILY_RANGE
        and f.status == "CREATED"
        and f.origin_event_key == failure.event_key
        for f in facts
    )


def test_breakout_failure_rejects_wrong_frozen_source(breakdown_failure):
    bundle, periods, _, failure = breakdown_failure
    assert failure.source is not None
    altered_source = failure.source.model_copy(update={"version_key": "0" * 64})
    replacement = failure.model_copy(update={"source": altered_source})
    edited = tuple(replacement if e is failure else e for e in periods["D1"].events)
    edited_periods = {**periods, "D1": replace(periods["D1"], events=edited)}
    facts, _ = Replay(bundle, edited_periods).run()
    assert not any(
        f.family == FAMILY_RANGE
        and f.status == "CREATED"
        and f.origin_event_key == failure.event_key
        for f in facts
    )


@pytest.mark.parametrize("corruption", ["wrong_direction", "same_bar"])
def test_breakout_failure_requires_prior_down_breakdown(breakdown_failure, corruption):
    bundle, periods, parent, failure = breakdown_failure
    if corruption == "wrong_direction":
        assert parent.event_guard is not None
        changed = parent.model_copy(
            update={
                "direction": "UP",
                "event_guard": parent.event_guard.model_copy(update={"direction": "UP"}),
            }
        )
    else:
        changed = parent.model_copy(update={"bar_index": failure.bar_index})
    changed = EventEvidence.model_validate(changed.model_dump())
    edited = tuple(changed if e is parent else e for e in periods["D1"].events)
    edited_periods = {**periods, "D1": replace(periods["D1"], events=edited)}
    facts, _ = Replay(bundle, edited_periods).run()
    assert not any(
        f.family == FAMILY_RANGE
        and f.status == "CREATED"
        and f.origin_event_key == failure.event_key
        for f in facts
    )
