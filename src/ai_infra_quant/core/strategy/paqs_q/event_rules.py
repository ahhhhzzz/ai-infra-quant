"""Six symmetric price-event families. Mutable state is local to one pure replay."""

from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from typing import Any, Literal, cast

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, decimal_text, digest
from ai_infra_quant.core.domain.paqs_q.event_reference import (
    ContextEvidence,
    Direction,
    EventEvidence,
    Frame,
    Guard,
    Regime,
    Source,
)
from ai_infra_quant.core.domain.paqs_q.inputs import CONTEXT, Bar, QInput
from ai_infra_quant.core.domain.paqs_q.results import Config

from .event_context import sources

D = Decimal
ZERO = D(0)


def event_config() -> Config:
    return Config(
        "paqs-q-event-reference-config-v1",
        FrozenJSON.of(
            {
                "breakout": D(".15"),
                "excursion": D(".10"),
                "reclaim": D(".05"),
                "failure_window": 3,
                "retest_window": 15,
                "retest_outer": D(".25"),
                "retest_inner": D(".20"),
                "retest_guard": D(".15"),
                "reclaim_guard": D(".10"),
                "micro": D(".05"),
                "body": D(".60"),
                "clv": D(".75"),
                "bar_range": D(".80"),
                "followthrough_window": 3,
                "extension": D(".10"),
                "regime_confirmation": 2,
            }
        ),
    )


def direction(sign: int) -> Direction:
    return "UP" if sign == 1 else "DOWN"


def edge(source: Source, sign: int) -> Decimal:
    return D(source.upper if sign == 1 else source.lower)


def outside(close: Decimal, boundary: Decimal, sign: int, buffer: Decimal = ZERO) -> bool:
    return sign * (close - boundary) > buffer


def wick(bar: Bar, sign: int) -> Decimal:
    return bar.high if sign == 1 else bar.low


def extreme(left: Decimal, right: Decimal, sign: int) -> Decimal:
    return max(left, right) if sign == 1 else min(left, right)


@dataclass
class Excursion:
    key: str
    source: Source
    start: int
    extreme: Decimal


@dataclass
class Episode:
    armed: bool
    excursion: Excursion | None = None
    excursion_consumed: bool = False
    cycle_source: Source | None = None


@dataclass
class Anchor:
    key: str
    source: Source
    sign: int
    start: int
    kind: Literal["BREAKOUT", "RECLAIM"]
    guard: Guard
    extreme: Decimal
    invalid: int | None = None
    confirmation_candidate: str | None = None
    retest_start: int | None = None
    retest_number: int = 0
    retest_key: str | None = None
    retest_done: bool = False
    holds: list[int] = field(default_factory=list)
    departed: int | None = None


@dataclass
class Follow:
    key: str
    candidate: str
    anchor: str
    start: int
    boundary: Decimal
    terminal: str | None = None


@dataclass
class Transition:
    key: str
    anchor: str
    path: Literal["RANGE", "REVERSAL"]
    consecutive: int = 0
    continuation: bool = False


class Replay:
    def __init__(self, data: QInput, context: ContextEvidence) -> None:
        self.data, self.context = data, context
        self.facts: list[EventEvidence] = []
        self.episodes: dict[tuple[str, int], Episode] = {}
        self.anchors: dict[str, Anchor] = {}
        self.follows: dict[str, Follow] = {}
        self.consumed_micro: set[str] = set()
        self.transition: Transition | None = None
        self.regime: Regime = "UNCERTAIN"
        self.pivots = {p.key: p for p in context.pivots}
        self.ranges = {r.version_key: r for r in context.ranges}
        self.i = 0
        self.atr = D(0)

    def key(self, family: str, *parts: Any) -> str:
        return digest(
            "paqs-q/event-key/v1",
            (
                self.context.series_key,
                event_config().config_hash,
                family,
                parts,
                self.context.prefix_hashes[self.i],
            ),
        )

    def emit(
        self,
        kind: str,
        status: str,
        key: str,
        sign: int,
        source: Source | None = None,
        anchor: Anchor | None = None,
        **fields: Any,
    ) -> EventEvidence:
        evidence = EventEvidence.model_validate_json(
            FrozenJSON.of(
                {
                    "schema_version": "paqs-q-price-event-evidence-v1",
                    "event_key": key,
                    "kind": kind,
                    "bar_index": self.i,
                    "direction": direction(sign),
                    "status": status,
                    "source": source.model_dump() if source else None,
                    "anchor_key": anchor.key if anchor else None,
                    "related_keys": (),
                    "reasons": (kind + "_" + status,),
                    "event_guard": anchor.guard.model_dump() if anchor else None,
                    "atr": self.atr,
                    "trigger_reasons": (),
                    "retest_number": None,
                    "regime": None,
                    "excursion_extreme": None,
                    **fields,
                }
            ).data
        )
        self.facts.append(evidence)
        return evidence

    def add_anchor(
        self,
        source: Source,
        sign: int,
        kind: Literal["BREAKOUT", "RECLAIM"],
        key: str,
        price_extreme: Decimal,
    ) -> Anchor:
        boundary = (
            D(source.lower if sign == 1 else source.upper) if kind == "BREAKOUT" else price_extreme
        )
        guard = Guard(
            kind=kind,
            direction=direction(sign),
            boundary=decimal_text(boundary),
            atr_buffer="0.15" if kind == "BREAKOUT" else "0.1",
        )
        a = Anchor(key, source, sign, self.i, kind, guard, price_extreme)
        self.anchors[key] = a
        return a

    def invalidate(self, a: Anchor, reason: str) -> None:
        a.invalid = self.i
        if reason != "PARENT_BREAKOUT_FAILURE":
            self.emit("EVENT_INVALIDATED", "FAILED", a.key, a.sign, a.source, a, reasons=(reason,))
        if (
            a.kind == "BREAKOUT"
            and not a.retest_done
            and self.i <= a.start + 15
            and (a.retest_start is not None or a.retest_number == 0)
        ):
            self.emit(
                "RETEST",
                "FAILURE",
                a.retest_key or self.key("RETEST_WINDOW", a.key),
                a.sign,
                a.source,
                a,
                retest_number=a.retest_number,
                reasons=(reason,),
            )
        a.retest_done = True

    def closing_regime(self, frame: Frame, bar: Bar) -> Regime:
        """Revalue only structure known before this bar at its completed close."""
        if self.atr <= 0:
            return "UNCERTAIN"
        active = self.ranges.get(frame.active_range or "")
        if active and D(active.lower) <= bar.close <= D(active.upper):
            return "RANGE"
        high = next(
            (
                self.pivots[k]
                for k in reversed(frame.major)
                if self.pivots[k].kind == "HIGH" and self.pivots[k].label is not None
            ),
            None,
        )
        low = next(
            (
                self.pivots[k]
                for k in reversed(frame.major)
                if self.pivots[k].kind == "LOW" and self.pivots[k].label is not None
            ),
            None,
        )
        if high and low:
            if high.label == "HH" and low.label == "HL" and bar.close >= D(low.price):
                return "BULL_TREND"
            if high.label == "LH" and low.label == "LL" and bar.close <= D(high.price):
                return "BEAR_TREND"
        return "UNCERTAIN"

    def invalidations(self, bar: Bar, frame: Frame) -> set[str]:
        confirmed: set[str] = set()
        for a in list(self.anchors.values()):
            if a.invalid is not None:
                continue
            if a.kind == "BREAKOUT" and self.i <= a.start + 3:
                a.extreme = extreme(a.extreme, wick(bar, a.sign), a.sign)
                if self.i > a.start and outside(
                    bar.close, edge(a.source, a.sign), -a.sign, D(".05") * self.atr
                ):
                    key = self.key("BREAKOUT_FAILURE", a.key)
                    reversal = self.add_anchor(a.source, -a.sign, "RECLAIM", key, a.extreme)
                    self.emit(
                        "BREAKOUT_FAILURE",
                        "CONFIRMED",
                        key,
                        -a.sign,
                        a.source,
                        reversal,
                        related_keys=(a.key,),
                        excursion_extreme=a.extreme,
                        reasons=("VALID_CLOSE_BREAK_THEN_RECLAIM",),
                    )
                    confirmed.add(key)
                    self.invalidate(a, "PARENT_BREAKOUT_FAILURE")
                    continue
            if outside(bar.close, D(a.guard.boundary), -a.sign, D(a.guard.atr_buffer) * self.atr):
                self.invalidate(a, "CLOSE_CROSSED_FROZEN_EVENT_GUARD")
        if self.transition and self.anchors[self.transition.anchor].invalid is not None:
            t, a = self.transition, self.anchors[self.transition.anchor]
            current = self.context.frames[self.i]
            original = self.ranges.get(a.source.range_version or "")
            active = self.ranges.get(current.active_range or "")
            self.regime = (
                "RANGE"
                if (
                    original
                    and active
                    and original.key == active.key
                    and D(original.lower) <= bar.close <= D(original.upper)
                )
                else self.closing_regime(frame, bar)
            )
            self.emit(
                "TRANSITION",
                "CANCELLED",
                t.key,
                a.sign,
                a.source,
                a,
                reasons=("EVENT_INVALIDATED_BEFORE_TRANSITION_CONFIRMATION",),
                regime=self.regime,
            )
            self.transition = None
        return confirmed

    def open_transition(self, a: Anchor, frame: Frame) -> None:
        if self.transition is not None:
            return
        path: Literal["RANGE", "REVERSAL"] | None = None
        if a.source.source_type == "RANGE_BOUNDARY":
            path = "RANGE"
        elif a.source.source_type == "MAJOR_SWING":
            pivot = self.pivots[a.source.source_key]
            if (a.sign == 1 and self.regime == "BEAR_TREND" and pivot.label == "LH") or (
                a.sign == -1 and self.regime == "BULL_TREND" and pivot.label == "HL"
            ):
                path = "REVERSAL"
        if path is not None:
            key = self.key("TRANSITION", a.key)
            self.transition = Transition(key, a.key, path)
            self.regime = "BULL_TRANSITION" if a.sign == 1 else "BEAR_TRANSITION"
            self.emit(
                "TRANSITION",
                "PENDING",
                key,
                a.sign,
                a.source,
                a,
                reasons=(path + "_BREAK", "POST_BREAK_MAJOR_STRUCTURE_REQUIRED"),
                regime=self.regime,
            )

    def breaks(self, bar: Bar, frame: Frame) -> set[str]:
        active = {
            (s.source_key, 1 if s.role == "RESISTANCE" else -1): s
            for s in sources(self.context, frame)
        }
        previous = self.data.bars[self.i - 1]
        confirmed: set[str] = set()
        for pair, initial_source in active.items():
            if pair not in self.episodes:
                self.episodes[pair] = Episode(
                    not outside(previous.close, edge(initial_source, pair[1]), pair[1])
                )
        for pair, state in sorted(self.episodes.items()):
            sign, current = pair[1], active.get(pair)
            if current is not None and outside(wick(bar, sign), edge(current, sign), sign):
                self.emit(
                    "ATTEMPT",
                    "OBSERVED",
                    self.key("ATTEMPT", current.version_key, sign),
                    sign,
                    current,
                )
                if state.armed and state.cycle_source is None:
                    state.cycle_source = current
            # A shallow outside close can change Range activity before a valid Breakout.
            # Continue the opened cycle on its frozen source, including expired Zones.
            source = state.cycle_source or current
            made_break = False
            if source is not None:
                boundary = edge(source, sign)
                if state.armed and outside(bar.close, boundary, sign, D(".15") * self.atr):
                    key = self.key("BREAK", source.version_key, sign)
                    peak = wick(bar, sign)
                    if state.excursion is not None:
                        peak = extreme(peak, state.excursion.extreme, sign)
                        self.emit(
                            "EXCURSION",
                            "CANCELLED",
                            state.excursion.key,
                            sign,
                            state.excursion.source,
                            reasons=("VALID_CLOSE_BREAK_SUPERSEDES_WICK",),
                        )
                    a = self.add_anchor(source, sign, "BREAKOUT", key, peak)
                    self.emit(
                        "BREAKOUT" if sign == 1 else "BREAKDOWN",
                        "CONFIRMED",
                        key,
                        sign,
                        source,
                        a,
                        reasons=("CLOSE_OUTSIDE_0_15_ATR",),
                    )
                    self.open_transition(a, frame)
                    confirmed.add(key)
                    state.armed, state.excursion, made_break = False, None, True
                if (
                    not made_break
                    and state.armed
                    and not state.excursion_consumed
                    and state.excursion is None
                    and outside(wick(bar, sign), boundary, sign, D(".10") * self.atr)
                ):
                    state.excursion = Excursion(
                        self.key("EXCURSION", source.version_key, sign),
                        source,
                        self.i,
                        wick(bar, sign),
                    )
                    state.excursion_consumed = True
                    self.emit(
                        "EXCURSION",
                        "PENDING",
                        state.excursion.key,
                        sign,
                        source,
                        excursion_extreme=state.excursion.extreme,
                    )
            e = state.excursion
            if e is not None:
                e.extreme = extreme(e.extreme, wick(bar, sign), sign)
                if self.i <= e.start + 3 and outside(
                    bar.close, edge(e.source, sign), -sign, D(".05") * self.atr
                ):
                    a = self.add_anchor(e.source, -sign, "RECLAIM", e.key, e.extreme)
                    self.emit(
                        "FAILED_BREAK",
                        "CONFIRMED",
                        e.key,
                        -sign,
                        e.source,
                        a,
                        excursion_extreme=e.extreme,
                        reasons=("EXCURSION_THEN_RECLAIM_NO_VALID_CLOSE_BREAK",),
                    )
                    confirmed.add(e.key)
                    state.excursion = None
                elif self.i == e.start + 3:
                    self.emit(
                        "EXCURSION", "EXPIRED", e.key, sign, e.source, excursion_extreme=e.extreme
                    )
                    state.excursion = None
            if source is not None and not outside(bar.close, edge(source, sign), sign):
                state.armed = True  # first usable again on the next completed bar
                if state.excursion is None:
                    state.excursion_consumed = False
                    state.cycle_source = None
        return confirmed

    def patterns(self, bar: Bar, frame: Frame) -> dict[int, tuple[str, ...]]:
        result: dict[int, tuple[str, ...]] = {}
        for sign in (1, -1):
            reasons = []
            span = bar.high - bar.low
            if (
                span > 0
                and self.atr > 0
                and sign * (bar.close - bar.open) > 0
                and abs(bar.close - bar.open) / span >= D(".60")
                and (bar.close - bar.low if sign == 1 else bar.high - bar.close) / span >= D(".75")
                and span / self.atr >= D(".80")
            ):
                reasons.append("STRONG")
            high = next(
                (self.pivots[k] for k in reversed(frame.micro) if self.pivots[k].kind == "HIGH"),
                None,
            )
            low = next(
                (self.pivots[k] for k in reversed(frame.micro) if self.pivots[k].kind == "LOW"),
                None,
            )
            pivot = high if sign == 1 else low
            if (
                high
                and low
                and pivot
                and pivot.key not in self.consumed_micro
                and (high.label, low.label) == (("LH", "LL") if sign == 1 else ("HH", "HL"))
                and outside(bar.close, D(pivot.price), sign, D(".05") * self.atr)
            ):
                reasons.append("MICRO")
                self.consumed_micro.add(pivot.key)
            result[sign] = tuple(sorted(reasons))
        return result

    def candidates(
        self, bar: Bar, raw: dict[int, tuple[str, ...]], confirmations: set[str]
    ) -> dict[str, str]:
        candidates = {}
        for sign in (1, -1):
            anchors = [a for a in self.anchors.values() if a.sign == sign and a.invalid is None]
            if raw[sign] and not anchors:
                self.emit(
                    "PRICE_PATTERN",
                    "OBSERVED",
                    self.key("PATTERN", sign),
                    sign,
                    trigger_reasons=raw[sign],
                    reasons=("NO_EVENT_ANCHOR_NO_EVENT_GUARD",),
                )
            for a in anchors:
                reasons = tuple(
                    sorted(
                        (*raw[sign], *(("EVENT_CONFIRMATION",) if a.key in confirmations else ()))
                    )
                )
                if not reasons:
                    continue
                key = self.key("CANDIDATE", a.key, sign)
                self.emit(
                    "PRICE_TRIGGER_CANDIDATE",
                    "CONFIRMED",
                    key,
                    sign,
                    a.source,
                    a,
                    trigger_reasons=reasons,
                    reasons=("PRICE_CANDIDATE_NOT_TRADE_QUALIFICATION",),
                )
                candidates[a.key] = key
                follow_key = self.key("FOLLOW_THROUGH", key)
                self.follows[follow_key] = Follow(follow_key, key, a.key, self.i, wick(bar, sign))
                self.emit(
                    "FOLLOW_THROUGH", "PENDING", follow_key, sign, a.source, a, related_keys=(key,)
                )
                if a.key in confirmations:
                    a.confirmation_candidate = follow_key
        return candidates

    def retests(
        self, bar: Bar, raw: dict[int, tuple[str, ...]], candidates: dict[str, str]
    ) -> None:
        for a in self.anchors.values():
            if a.kind != "BREAKOUT" or a.invalid is not None or a.retest_done or self.i <= a.start:
                continue
            if self.i > a.start + 15:
                continue
            sign = a.sign
            touched = (
                (
                    bar.low <= D(a.source.upper) + D(".25") * self.atr
                    and bar.high >= D(a.source.lower) - D(".20") * self.atr
                )
                if sign == 1
                else (
                    bar.high >= D(a.source.lower) - D(".25") * self.atr
                    and bar.low <= D(a.source.upper) + D(".20") * self.atr
                )
            )
            eligible_start = not a.holds or (a.departed is not None and self.i > a.departed)
            if a.retest_start is None and eligible_start and touched:
                a.retest_start = self.i
                a.retest_number += 1
                a.retest_key = self.key("RETEST", a.key, a.retest_number)
                a.departed = None
                self.emit(
                    "RETEST",
                    "START",
                    a.retest_key,
                    sign,
                    a.source,
                    a,
                    retest_number=a.retest_number,
                )
            if (
                a.retest_start is not None
                and self.i > a.retest_start
                and raw[sign]
                and outside(bar.close, edge(a.source, sign), sign)
            ):
                self.emit(
                    "RETEST",
                    "HOLD",
                    cast(str, a.retest_key),
                    sign,
                    a.source,
                    a,
                    retest_number=a.retest_number,
                    related_keys=(candidates[a.key],),
                    reasons=("LATER_MICRO_OR_STRONG_AND_CLOSE_OUTSIDE",),
                )
                a.holds.append(self.i)
                a.retest_start = None
            if (
                a.holds
                and a.retest_start is None
                and self.i > a.holds[-1]
                and outside(bar.close, edge(a.source, sign), sign, D(".25") * self.atr)
            ):
                a.departed = self.i
            if self.i == a.start + 15:
                if a.retest_start is not None or not a.holds:
                    self.emit(
                        "RETEST",
                        "EXPIRED",
                        a.retest_key or self.key("RETEST_WINDOW", a.key),
                        sign,
                        a.source,
                        a,
                        retest_number=a.retest_number,
                        reasons=("ORIGINAL_BREAKOUT_DEADLINE",),
                    )
                a.retest_done = True

    def followthrough(self, bar: Bar) -> None:
        for ft in self.follows.values():
            if ft.terminal is not None or self.i <= ft.start or self.i > ft.start + 3:
                continue
            a = self.anchors[ft.anchor]
            if a.invalid is not None:
                ft.terminal = "FAILED"
            elif outside(bar.close, ft.boundary, a.sign, D(".10") * self.atr):
                ft.terminal = "CONFIRMED"
            elif self.i == ft.start + 3:
                ft.terminal = "NONE"
            if ft.terminal is not None:
                self.emit(
                    "FOLLOW_THROUGH",
                    ft.terminal,
                    ft.key,
                    a.sign,
                    a.source,
                    a,
                    related_keys=(ft.candidate,),
                )

    def transitions(self, bar: Bar, frame: Frame) -> None:
        t = self.transition
        if t is None:
            return
        a = self.anchors[t.anchor]
        high = next(
            (self.pivots[k] for k in reversed(frame.major) if self.pivots[k].kind == "HIGH"), None
        )
        low = next(
            (self.pivots[k] for k in reversed(frame.major) if self.pivots[k].kind == "LOW"), None
        )
        if any(self.i > hold for hold in a.holds) and outside(
            bar.close, wick(self.data.bars[a.start], a.sign), a.sign, D(".10") * self.atr
        ):
            t.continuation = True
        ft = self.follows.get(a.confirmation_candidate or "")
        price_path = (
            t.path == "REVERSAL"
            or (ft is not None and ft.terminal == "CONFIRMED")
            or t.continuation
        )
        structure = bool(
            high
            and low
            and high.extreme_index > a.start
            and low.extreme_index > a.start
            and (
                (
                    a.sign == 1
                    and low.label == "HL"
                    and high.label == "HH"
                    and low.extreme_index < high.extreme_index
                    and bar.close >= D(low.price)
                )
                or (
                    a.sign == -1
                    and high.label == "LH"
                    and low.label == "LL"
                    and high.extreme_index < low.extreme_index
                    and bar.close <= D(high.price)
                )
            )
        )
        t.consecutive = t.consecutive + 1 if structure and price_path else 0
        if t.consecutive >= 2:
            self.regime = "BULL_TREND" if a.sign == 1 else "BEAR_TREND"
            self.emit(
                "TRANSITION",
                "CONFIRMED",
                t.key,
                a.sign,
                a.source,
                a,
                regime=self.regime,
                related_keys=(cast(Any, high).key, cast(Any, low).key),
                reasons=("POST_BREAK_MAJOR_STRUCTURE", "TWO_CONSECUTIVE_VALID_BARS", t.path),
            )
            self.transition = None

    def run(self) -> tuple[tuple[EventEvidence, ...], Regime]:
        with localcontext(CONTEXT):
            for i, bar in enumerate(self.data.bars):
                self.i = i
                atr = self.context.frames[i].atr
                if i == 0 or atr is None:
                    continue
                self.atr = D(atr)
                frame = self.context.frames[i - 1]
                if self.transition is None:
                    self.regime = frame.base_regime
                started_in_transition = self.transition is not None
                confirmations = self.invalidations(bar, frame)
                confirmations |= self.breaks(bar, frame)
                raw = self.patterns(bar, frame)
                candidates = self.candidates(bar, raw, confirmations)
                self.retests(bar, raw, candidates)
                self.followthrough(bar)
                self.transitions(bar, frame)
                if self.transition is None and not started_in_transition:
                    # Break/transition decisions above use the prior completed
                    # structure. Only the closing output revalues that same
                    # structure with this bar's now-known price.
                    self.regime = self.closing_regime(frame, bar)
        return tuple(self.facts), self.regime
