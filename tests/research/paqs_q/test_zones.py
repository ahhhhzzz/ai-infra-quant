"""Independent numerical expectations for active zones and recent boxes."""

from dataclasses import replace
from decimal import Decimal

import pytest

from tools.research.paqs_q.engine import evaluate
from tools.research.paqs_q.fixtures import synthetic
from tools.research.paqs_q.types import Bar, Evidence, Parameters, Pivot, Zone
from tools.research.paqs_q.zones import (
    build_zones,
    geometry,
    independent,
    iou,
    ranges,
    select_zones,
)

D = Decimal
P = Parameters.default("D1")


def touch(price: str, index: int, kind: str = "LOW", atr: str = "2") -> Pivot:
    return Pivot(
        kind,
        D(price),
        index,
        index + 1,
        f"e{index}",
        f"c{index + 1}",
        D(atr),
        Evidence("QSTR-006", (), "synthetic oracle", None),
        f"{kind}:{index}:{price}",
    )


def test_touch_independence_dedup_and_exact_geometry():
    a, b, c = touch("100", 0), touch("100.2", 4), touch("100.2", 5)
    assert independent((c, b, a, a)) == (a, c)
    zone = geometry((a, c), "SUPPORT", P)
    assert (zone.center, zone.atr, zone.mad, zone.half_width) == (
        D("100.1"),
        D(2),
        D("0.1"),
        D("0.3"),
    )
    assert (zone.lower, zone.upper) == (D("99.8"), D("100.4"))
    wide = geometry((touch("80", 0), touch("120", 5)), "SUPPORT", P)
    assert wide.half_width == D("1.5")


def test_complete_link_does_not_transitively_chain_and_order_is_deterministic():
    ps = (touch("100", 0), touch("100.8", 5), touch("101.6", 10))
    zones = build_zones(ps, P, {})
    assert sorted(len(z.touches) for z in zones) == [1, 2]
    assert zones == build_zones(tuple(reversed(ps)), P, {})
    assert zones == build_zones((ps[1], ps[2], ps[0]), P, {})
    assert all(
        not {ps[0].identity, ps[2].identity} <= {p.identity for p in z.touches} for z in zones
    )


def test_iou_half_is_inclusive_and_age_counts_extreme_not_confirmation():
    zone = geometry((touch("100", 0), touch("100", 5)), "SUPPORT", P)
    shifted = replace(zone, lower=zone.lower + D("0.2"), upper=zone.upper + D("0.2"))
    assert iou(zone, shifted) == D("0.5")
    late = replace(zone, touches=(zone.touches[0], replace(zone.touches[1], confirmed=130)))
    assert select_zones((late,), 131, D(110), P)[1] == (late,)
    assert select_zones((late,), 132, D(110), P) == ((), ())
    assert select_zones((zone,), 10, D(90), P) == ((), ())  # no role flip.


def test_role_cap_and_candidate_rejection():
    zones = tuple(
        geometry((touch(str(price), 100, kind), touch(str(price), 105, kind)), role, P)
        for kind, role, prices in (
            ("LOW", "SUPPORT", (70, 80, 90)),
            ("HIGH", "RESISTANCE", (110, 120, 130)),
        )
        for price in prices
    )
    eligible, decision = select_zones(zones, 110, D(100), P)
    assert len(eligible) == 6 and len(decision) == 4
    assert [z.center for z in decision] == list(map(D, (90, 80, 110, 120)))
    single = geometry((touch("95", 100),), "SUPPORT", P)
    assert not select_zones((single,), 110, D(100), P)[1]


def range_fixture() -> tuple[tuple[Bar, ...], tuple[Decimal, ...], tuple[Zone, ...]]:
    bars = tuple(
        replace(b, open=D(105), high=D(106), low=D(104), close=D(105))
        for b in synthetic(count=80).bars
    )
    support = geometry((touch("100", 45), touch("100", 65)), "SUPPORT", P)
    resistance = geometry((touch("110", 55, "HIGH"), touch("110", 75, "HIGH")), "RESISTANCE", P)
    return bars, (D(2),) * 80, (support, resistance)


def test_range_recent_reactions_alternation_and_old_touches_rejected():
    bars, atr, zs = range_fixture()
    box = ranges(bars, atr, zs, P, {})
    assert len(box) == 1
    assert (box[0].inside_ratio, box[0].width_atr, box[0].recent_touches) == (D(1), D(5), 4)
    old = tuple(
        replace(
            z,
            touches=tuple(
                replace(t, extreme=t.extreme - 40, confirmed=t.confirmed - 40) for t in z.touches
            ),
        )
        for z in zs
    )
    assert ranges(bars, atr, old, P, {}) == ()
    grouped = (
        replace(zs[0], touches=(touch("100", 45), touch("100", 50))),
        replace(zs[1], touches=(touch("110", 65, "HIGH"), touch("110", 70, "HIGH"))),
    )
    assert ranges(bars, atr, grouped, P, {}) == ()
    same_time = (
        zs[0],
        replace(zs[1], touches=(touch("110", 45, "HIGH"), touch("110", 75, "HIGH"))),
    )
    assert ranges(bars, atr, same_time, P, {}) == ()


@pytest.mark.parametrize("outside,accepted", [(12, True), (13, False)])
def test_range_inside_ratio_exact_70_percent(outside, accepted):
    bars, atr, zs = range_fixture()
    changed = bars[:40] + tuple(
        replace(b, close=D(120)) if i < outside else b for i, b in enumerate(bars[40:])
    )
    result = ranges(changed, atr, zs, P, {})
    assert bool(result) is accepted
    if accepted:
        assert result[0].inside_ratio == D("0.7")


def test_range_latest_close_width_and_atr_guards():
    bars, atr, zs = range_fixture()
    assert not ranges((*bars[:-1], replace(bars[-1], close=D(120))), atr, zs, P, {})
    assert not ranges(bars, (*atr[:-1], None), zs, P, {})
    assert not ranges(bars, (D(0),) * 80, zs, P, {})
    assert ranges(bars, (D(5),) * 80, zs, P, {})[0].width_atr == D(2)
    assert not ranges(bars, (D("5.0000000001"),) * 80, zs, P, {})


@pytest.mark.parametrize("tf", ["W1", "M30"])
def test_no_non_d1_decision_zones_or_ranges(tf):
    data = synthetic(tf)
    decision = evaluate(data, data.bars[-1].completed_at).document()["decision"]
    assert decision["zones"] == [] and decision["range"] is None


def test_range_id_changes_do_not_imply_semantic_range_exit():
    bars, atr, zs = range_fixture()
    first = ranges(bars, atr, zs, P, {})[0]
    second = ranges((*bars[:-1], replace(bars[-1], volume=D(999))), atr, zs, P, {})[0]
    assert first.identity != second.identity
    assert (first.lower, first.upper) == (second.lower, second.upper)


def test_full_engine_range_precedence_and_all_touch_lineage_active():
    data = synthetic(pattern="tight_range")
    decision = evaluate(data, data.bars[-1].completed_at).document()["decision"]
    assert decision["regime"] == "RANGE"
    assert decision["reasons"] == ["CURRENT_RANGE"]
    assert decision["range"]["inside_ratio"] == "1"
    assert len(decision["zones"]) == 2
    assert all(p["extreme"] >= 60 for z in decision["zones"] for p in z["touches"])
