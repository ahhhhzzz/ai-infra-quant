from decimal import Decimal

import pytest

from ai_infra_quant.core.strategy.paqs_q.event_rules import Replay

from .support import candle, controlled, select


@pytest.mark.parametrize("sign", [1, -1])
def test_attempt_break_equalities_cycles_and_activation(monkeypatch, sign):
    rows = [
        candle("99.9", h="100"),
        candle("100.15", h="100.2"),
        candle("100.1501"),
        candle("101"),
        candle("100"),
        candle("101"),
    ]
    _, _, engine, _ = controlled(monkeypatch, rows, sign=sign)
    facts, _ = engine.run()
    breaks = select(facts, "BREAKOUT" if sign == 1 else "BREAKDOWN")
    assert [e.bar_index for e in breaks] == [4, 7]
    assert 2 not in [e.bar_index for e in select(facts, "ATTEMPT")]
    assert 3 in [e.bar_index for e in select(facts, "ATTEMPT")]
    _, _, engine, _ = controlled(
        monkeypatch, [candle("102"), candle("100"), candle("101")], sign=sign, first="101"
    )
    facts, _ = engine.run()
    assert [e.bar_index for e in select(facts, "BREAKOUT" if sign == 1 else "BREAKDOWN")] == [4]


@pytest.mark.parametrize("sign", [1, -1])
def test_wick_reclaim_same_bar_equalities_and_original_deadline(monkeypatch, sign):
    _, _, engine, _ = controlled(
        monkeypatch,
        [
            candle("99.94", h="100.1"),
            candle("99.95", h="100.1001"),
            candle("100.02", h="100.4"),
            candle("100.03", h="100.6"),
            candle("99.9499", h="100.5"),
        ],
        sign=sign,
    )
    facts, _ = engine.run()
    starts = select(facts, "EXCURSION", "PENDING")
    reclaim = select(facts, "FAILED_BREAK")
    assert [e.bar_index for e in starts] == [3]
    assert [(e.bar_index, e.event_key) for e in reclaim] == [(6, starts[0].event_key)]
    assert Decimal(reclaim[0].excursion_extreme) == (
        Decimal("100.6") if sign == 1 else Decimal("99.4")
    )
    _, _, engine, _ = controlled(monkeypatch, [candle("99.9", h="100.2")], sign=sign)
    facts, _ = engine.run()
    assert select(facts, "FAILED_BREAK")[0].bar_index == 2
    _, _, engine, _ = controlled(
        monkeypatch, [candle("100", h="100.2")] * 4 + [candle("99.9", h="100")], sign=sign
    )
    facts, _ = engine.run()
    assert [e.bar_index for e in select(facts, "EXCURSION", "EXPIRED")] == [5]
    assert not select(facts, "FAILED_BREAK")


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("delay", [1, 3, 4])
def test_valid_break_failure_window_preserves_break_and_no_wick_relabel(monkeypatch, sign, delay):
    rows = [candle("101", o="99", h="101.1")] + [candle("100.5", h="102")] * (delay - 1)
    rows += [candle("99.94", h="103")]
    _, _, engine, _ = controlled(monkeypatch, rows, sign=sign)
    facts, _ = engine.run()
    original = select(facts, "BREAKOUT" if sign == 1 else "BREAKDOWN")[0]
    failed = select(facts, "BREAKOUT_FAILURE")
    assert bool(failed) == (delay <= 3)
    assert not select(facts, "FAILED_BREAK")
    if failed:
        assert failed[0].related_keys == (original.event_key,)
        assert failed[0].bar_index == 2 + delay
        assert failed[0].direction != original.direction


@pytest.mark.parametrize("sign", [1, -1])
def test_retest_later_hold_repeated_touch_departure_and_original_deadline(monkeypatch, sign):
    rows = [
        candle("101", o="99"),
        candle("101.1", o="100.2", low="100.25", h="101.2"),  # strong touch, no same-bar hold
        candle("100.5", low="100.1"),  # repeat touch
        candle("101.1", o="100.2", low="100.1", h="101.2"),  # later hold
        candle("100.25", low="100.1"),  # equality isn't departure
        candle("100.3", low="100.1"),  # departure, cannot start same bar
        candle("100.4", low="100.2"),  # start number 2
        candle("101.1", o="100.2", low="100.1", h="101.2"),
    ]
    _, _, engine, _ = controlled(monkeypatch, rows, sign=sign)
    facts, _ = engine.run()
    assert [(e.bar_index, e.retest_number) for e in select(facts, "RETEST", "START")] == [
        (3, 1),
        (8, 2),
    ]
    assert [(e.bar_index, e.retest_number) for e in select(facts, "RETEST", "HOLD")] == [
        (5, 1),
        (9, 2),
    ]
    for hold in select(facts, "RETEST", "HOLD"):
        candidate = next(e for e in facts if e.event_key == hold.related_keys[0])
        assert set(candidate.trigger_reasons) & {"MICRO", "STRONG"}


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("ending", ["hold", "expire", "failure", "untouched"])
def test_retest_inclusive_last_bar_precedence(monkeypatch, sign, ending):
    rows = [candle("101", o="99")] + [candle("101", low="100.5")] * 14
    if ending != "untouched":
        rows[13] = candle("100.5", low="100.25", h="100.7")
    rows += [
        candle("101.1", o="100.2", low="100.1", h="101.2")
        if ending == "hold"
        else candle("99.8499")
        if ending == "failure"
        else candle("100.9", low="100.5")
    ]
    rows += [candle("101", o="100.2", low="100.1", h="101.1")]
    _, _, engine, _ = controlled(monkeypatch, rows, sign=sign)
    facts, _ = engine.run()
    last = [e for e in select(facts, "RETEST") if e.bar_index == 17]
    assert [e.status for e in last] == [
        {"hold": "HOLD", "failure": "FAILURE"}.get(ending, "EXPIRED")
    ]
    assert not [e for e in select(facts, "RETEST") if e.bar_index > 17]
    if ending == "untouched":
        assert not select(facts, "RETEST", "START")


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("finish", ["confirmed", "none", "failed"])
def test_follow_window_equalities_failure_first_and_immutable_terminal(monkeypatch, sign, finish):
    rows = [
        candle("101", o="99", h="101.2"),
        candle("101.3"),
        candle("101.3"),
        candle("101.3001")
        if finish == "confirmed"
        else candle("99.8499")
        if finish == "failed"
        else candle("101.3"),
        candle("102"),
        candle("98"),
    ]
    _, _, engine, _ = controlled(monkeypatch, rows, sign=sign)
    facts, _ = engine.run()
    start = select(facts, "FOLLOW_THROUGH", "PENDING")[0]
    history = [e for e in facts if e.event_key == start.event_key]
    assert [(e.bar_index, e.status) for e in history] == [(2, "PENDING"), (5, finish.upper())]
    assert select(facts, "EVENT_INVALIDATED") or select(facts, "BREAKOUT_FAILURE")
    # A later extreme can never turn NONE/FAILED into CONFIRMED.
    assert len(history) == 2


@pytest.mark.parametrize("sign", [1, -1])
def test_strong_inclusive_ratios_and_no_anchor_guard(monkeypatch, sign):
    # All three inclusive thresholds exactly met: span=.8, body=.48, CLV=.75.
    rows = [
        candle("99.6", o="99.12", low="99", h="99.8"),
        candle("99.5999", o="99.12", low="99", h="99.8"),
        candle("99", h="99", low="99"),
    ]
    _, _, engine, _ = controlled(monkeypatch, rows, sign=sign)
    facts, _ = engine.run()
    patterns = select(facts, "PRICE_PATTERN")
    assert [(e.bar_index, e.trigger_reasons) for e in patterns] == [(2, ("STRONG",))]
    assert patterns[0].event_guard is None and patterns[0].anchor_key is None
    assert not select(facts, "FOLLOW_THROUGH")


def test_guard_exact_equality_and_missing_future_keeps_pending(monkeypatch):
    _, _, engine, _ = controlled(
        monkeypatch,
        [candle("101", o="99")] + [candle("100.1")] * 3 + [candle("99.85"), candle("99.8499")],
    )
    facts, _ = engine.run()
    assert [e.bar_index for e in select(facts, "EVENT_INVALIDATED")] == [7]
    _, _, engine, _ = controlled(monkeypatch, [candle("101", o="99")])
    facts, _ = engine.run()
    assert [e.status for e in select(facts, "FOLLOW_THROUGH")] == ["PENDING"]


def test_zero_atr_ratios_do_not_divide_by_zero(monkeypatch):
    data, context, _, _ = controlled(monkeypatch, [candle("99", h="99", low="99")])
    context = context.model_copy(
        update={"frames": tuple(f.model_copy(update={"atr": "0"}) for f in context.frames)}
    )
    facts, _ = Replay(data, context).run()
    assert not select(facts, "PRICE_PATTERN")


@pytest.mark.parametrize("sign", [1, -1])
def test_micro_equality_first_cross_and_merge_with_strong(monkeypatch, sign):
    from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, digest, primitive
    from ai_infra_quant.core.domain.paqs_q.event_reference import PivotEvidence

    data, context, engine, _ = controlled(
        monkeypatch,
        [
            candle("100.05"),
            candle("100.0501", o="99", low="98.9", h="100.1"),
            candle("100.06", o="99", low="98.9", h="100.1"),
        ],
        sign=sign,
    )
    pivots = []
    for kind, price, label in (("HIGH", "100", "LH"), ("LOW", "98", "LL")):
        if sign == -1:
            kind = "LOW" if kind == "HIGH" else "HIGH"
            price = str(200 - Decimal(price))
            label = {"LH": "HL", "LL": "HH"}[label]
        pivots.append(
            PivotEvidence.model_validate_json(
                FrozenJSON.of(
                    {
                        "key": digest("micro-unit", kind),
                        "hierarchy": "MICRO",
                        "kind": kind,
                        "price": price,
                        "label": label,
                        "previous_key": None,
                        "tolerance": None,
                        "extreme_index": 0,
                        "confirmation_index": 1,
                        "extreme_time": primitive(data.bars[0].completed_at),
                        "confirmation_time": primitive(data.bars[1].completed_at),
                        "support_refs": (data.bars[0].version_ref, data.bars[1].version_ref),
                    }
                ).data
            )
        )
    engine.pivots = {p.key: p for p in pivots}
    frames = tuple(
        f.model_copy(update={"micro": tuple(p.key for p in pivots) if f.index >= 1 else ()})
        for f in context.frames
    )
    engine.context = context.model_copy(update={"pivots": tuple(pivots), "frames": frames})
    facts, _ = engine.run()
    micro = [f for f in facts if "MICRO" in f.trigger_reasons]
    assert [(e.bar_index, e.trigger_reasons) for e in micro] == [(3, ("MICRO", "STRONG"))]
    assert len({(e.anchor_key, e.direction, e.bar_index) for e in micro}) == len(micro)


@pytest.mark.parametrize("sign", [1, -1])
def test_reclaim_guard_uses_frozen_excursion_and_current_atr(monkeypatch, sign):
    _, _, engine, _ = controlled(
        monkeypatch,
        [candle("99.9", h="100.2"), candle("100.30", h="100.4"), candle("100.3001", h="100.5")],
        sign=sign,
    )
    facts, _ = engine.run()
    reclaim = select(facts, "FAILED_BREAK")[0]
    invalid = [e for e in select(facts, "EVENT_INVALIDATED") if e.event_key == reclaim.event_key]
    assert [e.bar_index for e in invalid] == [4]
    assert invalid[0].event_guard == reclaim.event_guard


@pytest.mark.parametrize("removed", [False, True])
def test_opened_outside_cycle_keeps_range_source_when_activity_changes(monkeypatch, removed):
    data, context, engine, source = controlled(
        monkeypatch, [candle("100.02", h="100.04"), candle("101")]
    )
    original = source.model_copy(
        update={"source_type": "RANGE_BOUNDARY", "range_key": "a" * 64, "range_version": "b" * 64}
    )
    later = source.model_copy(update={"source_type": "ZONE", "version_key": "c" * 64})

    def available(c, frame):
        if frame.index < 1:
            return ()
        if frame.index == 1:
            return (original,)
        return () if removed else (later,)

    monkeypatch.setattr("ai_infra_quant.core.strategy.paqs_q.event_rules.sources", available)
    facts, _ = engine.run()
    breakout = select(facts, "BREAKOUT")[0]
    assert breakout.bar_index == 3
    assert breakout.source == original
    assert len(select(facts, "ATTEMPT")) == (1 if removed else 2)
