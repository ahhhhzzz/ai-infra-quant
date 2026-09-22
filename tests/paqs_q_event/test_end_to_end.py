from collections import Counter
from dataclasses import replace
from decimal import Decimal

import pytest

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON
from ai_infra_quant.core.strategy.paqs_q.event_context import compute_context, sources
from tools.research.event_engine.data import daily_input, demo_input

from .support import candle, prefix, replay, select


@pytest.mark.parametrize("mirror", [False, True])
def test_real_ohlc_context_all_six_families_and_transition_structure(mirror):
    data = demo_input(mirror=mirror)
    context, facts, _ = replay(data)
    assert len(context.pivots) > 20 and context.zones and context.ranges
    kinds = {e.kind for e in facts}
    assert {
        "ATTEMPT",
        "BREAKOUT",
        "BREAKDOWN",
        "FAILED_BREAK",
        "BREAKOUT_FAILURE",
        "RETEST",
        "TRANSITION",
        "PRICE_TRIGGER_CANDIDATE",
        "FOLLOW_THROUGH",
    } <= kinds
    assert {"PENDING", "CONFIRMED", "NONE", "FAILED"} == {
        e.status for e in select(facts, "FOLLOW_THROUGH")
    }
    assert {"START", "HOLD", "FAILURE"} <= {e.status for e in select(facts, "RETEST")}
    transitions = select(facts, "TRANSITION", "CONFIRMED")
    assert {"RANGE", "REVERSAL"} <= {e.reasons[-1] for e in transitions}
    pivots = {p.key: p for p in context.pivots}
    for event in facts:
        if event.source:
            assert event.source.confirmation_index < event.bar_index
    for done in transitions:
        started = next(e for e in facts if e.event_key == done.event_key and e.status == "PENDING")
        high, low = (pivots[k] for k in done.related_keys)
        assert min(high.extreme_index, low.extreme_index) > started.bar_index
        assert max(high.confirmation_index, low.confirmation_index) <= done.bar_index - 2
        assert (high.label, low.label) == (("HH", "HL") if done.direction == "UP" else ("LH", "LL"))
    # No Range/underlying Zone duplicate; repeated source versions stay on original anchors.
    for frame in context.frames:
        src = sources(context, frame)
        assert len({s.source_key for s in src}) == len(src)
    for start in select(facts, "RETEST", "START"):
        anchor = next(
            e
            for e in facts
            if e.event_key == start.anchor_key and e.kind in {"BREAKOUT", "BREAKDOWN"}
        )
        assert start.source == anchor.source
        holds = [e for e in facts if e.event_key == start.event_key and e.status == "HOLD"]
        assert all(e.bar_index > start.bar_index for e in holds)


def test_real_ohlc_full_mirror_and_determinism():
    data = demo_input()
    c, f, _ = replay(data)
    assert replay(data)[0].frozen() == c.frozen()
    assert replay(data)[1] == f
    _, mirrored, _ = replay(demo_input(mirror=True))

    def shape(e, flip=False):
        kind = (
            {"BREAKOUT": "BREAKDOWN", "BREAKDOWN": "BREAKOUT"}.get(e.kind, e.kind)
            if flip
            else e.kind
        )
        direction = {"UP": "DOWN", "DOWN": "UP"}[e.direction] if flip else e.direction
        return e.bar_index, kind, e.status, direction, e.retest_number, e.trigger_reasons

    assert Counter(shape(e) for e in f) == Counter(shape(e, True) for e in mirrored)


@pytest.mark.parametrize("count", [32, 54, 86, 89, 94, 101, 112])
def test_future_append_preserves_context_and_facts_not_f1_ids(count):
    data = demo_input()
    c, all_facts, _ = replay(data)
    old, prior_facts, _ = replay(prefix(data, count))
    assert old.frames == c.frames[:count]
    assert old.prefix_hashes == c.prefix_hashes[:count]
    assert old.pivots == tuple(p for p in c.pivots if p.confirmation_index < count)
    assert prior_facts == tuple(e for e in all_facts if e.bar_index < count)


def test_expiry_and_cancellation_through_actual_ohlc_context():
    original = demo_input()
    values = [
        tuple(str(getattr(b, k)) for k in ("open", "high", "low", "close"))
        for b in original.bars[:86]
    ]
    _, facts, _ = replay(daily_input(values + [candle("116", low="115.9")] * 16))
    expired = select(facts, "RETEST", "EXPIRED")
    assert expired and any(e.retest_number == 0 and e.bar_index == 100 for e in expired)
    # Cancel the real range transition during its original failure window.
    _, facts, _ = replay(daily_input([*values, candle("109")]))
    assert select(facts, "TRANSITION", "CANCELLED")
    assert select(facts, "BREAKOUT_FAILURE")


def test_history_revision_and_origin_are_new_sources():
    data = demo_input()
    first = compute_context(data)
    revised = replace(data, bars=(replace(data.bars[0], volume=Decimal(101)), *data.bars[1:]))
    assert compute_context(revised).prefix_hashes[0] != first.prefix_hashes[0]
    shortened = replace(data, bars=data.bars[1:], calendar=data.calendar[1:])
    assert compute_context(shortened).series_key != first.series_key


def test_atr_seed_initialization_wait_and_partial_readiness():
    # Flat prices: ATR zero, no pivots; no fake readiness or events.
    c, f, _ = replay(daily_input([candle("100", h="100", low="100")] * 20))
    assert not c.pivots and not f and not c.frames[-1].readiness.atr
    # Real directional OHLC before a confirmed Major/Zone still emits unanchored strong patterns.
    values = [
        candle(
            str(100 + i), o=str(99 + i), h=str(Decimal("100.1") + i), low=str(Decimal("98.9") + i)
        )
        for i in range(20)
    ]
    c, f, _ = replay(daily_input(values))
    assert all(x.atr is None for x in c.frames[:13])
    assert c.frames[13].atr == "1.2"
    assert not c.frames[-1].readiness.zone and select(f, "PRICE_PATTERN")
    assert all(e.event_guard is None for e in f)


def test_zone_age_blocks_new_sources_without_moving_open_event_guard():
    data = demo_input()
    c, f, _ = replay(data)
    frame = next(f for f in c.frames if any(s.source_type == "ZONE" for s in sources(c, f)))
    original = sources(c, frame)
    stale = frame.model_copy(update={"index": frame.index + 251, "active_range": None})
    assert all(s.source_type == "MAJOR_SWING" for s in sources(c, stale))
    assert any(s.source_type == "ZONE" for s in original)
    anchors = {
        e.event_key: e
        for e in f
        if e.kind in {"BREAKOUT", "BREAKDOWN", "FAILED_BREAK", "BREAKOUT_FAILURE"}
    }
    for fact in f:
        if fact.anchor_key:
            assert fact.source == anchors[fact.anchor_key].source
            assert fact.event_guard == anchors[fact.anchor_key].event_guard


def test_serialized_schema_is_recursively_immutable():
    context = compute_context(demo_input())
    frozen = context.frozen()
    copy = frozen.document()
    copy["frames"][13]["atr"] = "123"
    assert frozen == context.frozen()
    with pytest.raises(ValueError):
        context.frames[13].atr = "123"
    assert isinstance(context.frames, tuple)
    assert FrozenJSON.of(context.model_dump()) == frozen
