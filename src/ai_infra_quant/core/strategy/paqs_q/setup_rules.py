"""Long-only Setup, frozen risk geometry and two-stage entry reference replay."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, localcontext
from typing import Literal, cast
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, decimal_text, digest
from ai_infra_quant.core.domain.paqs_q.event_reference import ContextEvidence, EventEvidence, Regime
from ai_infra_quant.core.domain.paqs_q.inputs import CONTEXT, QInput
from ai_infra_quant.core.domain.paqs_q.results import Config
from ai_infra_quant.core.domain.paqs_q.setup_reference import (
    EntryReference,
    FactStatus,
    MultiInput,
    SetupFact,
    TargetEvidence,
)

from .setup_targets import (
    Obstacle,
    latest_index,
    next_regular_open,
    structural_obstacles,
    targets,
    trading_days,
)

D = Decimal
LiteralFamily = Literal[
    "TREND_PULLBACK_LONG", "RANGE_FAILED_BREAKDOWN_LONG", "RIGHT_SIDE_BREAKOUT_LONG"
]
FAMILY_TREND = "TREND_PULLBACK_LONG"
FAMILY_RANGE = "RANGE_FAILED_BREAKDOWN_LONG"
FAMILY_BREAKOUT = "RIGHT_SIDE_BREAKOUT_LONG"


def setup_config() -> Config:
    return Config(
        "paqs-q-setup-risk-config-v1",
        FrozenJSON.of(
            {
                "minimum_rr": D("2.0"),
                "setup_max_age_d1_bars": 15,
                "invalidation_buffer_atr": D("0.15"),
                "failed_breakdown_buffer_atr": D("0.10"),
                "target_confluence_tolerance_atr": D("0.25"),
                "gap_min_size_atr": D("0.25"),
                "followthrough_window_m30": 3,
                "followthrough_extension_atr": D("0.10"),
                "history": "FIXED_START",
            }
        ),
    )


@dataclass(frozen=True, slots=True)
class Period:
    data: QInput
    context: ContextEvidence
    events: tuple[EventEvidence, ...]


@dataclass(slots=True)
class Trigger:
    key: str
    event_key: str
    index: int
    high: Decimal


@dataclass(slots=True)
class PendingEntry:
    key: str
    stage_a_at: datetime
    m30_index: int
    frozen_t1: TargetEvidence


@dataclass(slots=True)
class State:
    key: str
    family: str
    variant: str
    source_key: str
    origin_event_key: str | None
    anchor: Decimal
    buffer: Decimal
    created_index: int
    created_at: datetime
    expiry_origin: int | None = None
    terminal: bool = False
    trigger: Trigger | None = None
    pending_entry: PendingEntry | None = None
    seen_triggers: set[str] = field(default_factory=set)
    observed: bool = False


class Replay:
    def __init__(self, bundle: MultiInput, periods: dict[str, Period]) -> None:
        self.bundle, self.periods = bundle, periods
        self.w1, self.d1, self.m30 = (periods[name] for name in ("W1", "D1", "M30"))
        self.facts: list[SetupFact] = []
        self.reasons: set[str] = set()
        self.states: list[State] = []
        self.by_d1: dict[int, list[EventEvidence]] = defaultdict(list)
        self.by_m30: dict[int, list[EventEvidence]] = defaultdict(list)
        self.d1_events = {e.event_key: e for e in self.d1.events if e.kind == "BREAKOUT"}
        self.d1_candidates = {
            e.event_key: e for e in self.d1.events if e.kind == "PRICE_TRIGGER_CANDIDATE"
        }
        for event in self.d1.events:
            self.by_d1[event.bar_index].append(event)
        for event in self.m30.events:
            self.by_m30[event.bar_index].append(event)
        self.refs = {r.price_at: r for r in bundle.entry_references}
        self.zone = ZoneInfo(self.m30.data.market_timezone)

    def regime(self, period: Period, when: datetime) -> Regime | None:
        index = latest_index(period.data, when)
        if index is None:
            return None
        if period.data.timeframe == "W1" and when >= period.data.bars[index].end + timedelta(
            days=7
        ):
            return None
        base = period.context.frames[index].base_regime
        transitions = [e for e in period.events if e.kind == "TRANSITION" and e.bar_index <= index]
        if transitions:
            last = transitions[-1]
            if last.status == "PENDING" or last.bar_index == index:
                return last.regime
        return base

    def _allowed_w1(self, state: State, when: datetime) -> bool:
        index = latest_index(self.w1.data, when)
        if index is None or when >= self.w1.data.bars[index].end + timedelta(days=7):
            self.reasons.add("W1_COMPLETED_CONTEXT_STALE_OR_MISSING")
            return False
        regime = self.regime(self.w1, when)
        allowed = (
            {"BULL_TREND"}
            if state.family == FAMILY_TREND
            else {"RANGE"}
            if state.family == FAMILY_RANGE
            else {"BULL_TREND", "RANGE", "BULL_TRANSITION"}
        )
        return regime in allowed

    def _emit(
        self,
        state: State,
        status: str,
        when: datetime,
        reasons: tuple[str, ...],
        *,
        m30_index: int | None = None,
        candidate_key: str | None = None,
        atr: Decimal | None = None,
        risk: Decimal | None = None,
        price: Decimal | None = None,
        target1: TargetEvidence | None = None,
        target2: TargetEvidence | None = None,
        rr1: Decimal | None = None,
        rr2: Decimal | None = None,
        entry_ref: EntryReference | None = None,
        rejected: tuple[str, ...] = (),
        related: tuple[str, ...] = (),
    ) -> None:
        fact = SetupFact(
            fact_key=digest(
                "paqs-q/setup-fact/v1",
                (state.key, candidate_key, status, when, m30_index, len(self.facts)),
            ),
            setup_key=state.key,
            candidate_key=candidate_key,
            family=cast("LiteralFamily", state.family),
            variant=state.variant,
            status=cast(FactStatus, status),
            entry_advisory=(
                "NO_TRADE"
                if status in {"NO_TRADE", "INVALIDATED", "EXPIRED", "FOLLOW_THROUGH_FAILED"}
                else cast(
                    Literal[
                        "ENTRY_PENDING_REVALIDATION",
                        "LONG_READY",
                        "OBSERVATIONAL_LONG_QUALIFIED",
                        "VALID_SETUP_BUT_POOR_ENTRY",
                    ],
                    status,
                )
                if status
                in {
                    "ENTRY_PENDING_REVALIDATION",
                    "LONG_READY",
                    "OBSERVATIONAL_LONG_QUALIFIED",
                    "VALID_SETUP_BUT_POOR_ENTRY",
                }
                else "WATCH_LONG"
            ),
            effective_at=when,
            d1_index=state.created_index,
            m30_index=m30_index,
            source_key=state.source_key,
            origin_event_key=state.origin_event_key,
            anchor_price=decimal_text(state.anchor),
            invalidation_buffer_atr=decimal_text(state.buffer),
            atr=decimal_text(atr) if atr is not None else None,
            risk_reference_price=decimal_text(risk) if risk is not None else None,
            reference_price=decimal_text(price) if price is not None else None,
            target1=target1,
            target2=target2,
            rr_t1=decimal_text(rr1) if rr1 is not None else None,
            rr_t2=decimal_text(rr2) if rr2 is not None else None,
            entry_reference_source=entry_ref.source if entry_ref else None,
            entry_reference_source_ref=entry_ref.source_ref if entry_ref else None,
            entry_reference_adjustment=entry_ref.adjustment if entry_ref else None,
            entry_reference_price_at=entry_ref.price_at if entry_ref else None,
            entry_reference_available_at=entry_ref.available_at if entry_ref else None,
            rejected_targets=rejected,
            reasons=reasons,
            related_keys=related,
        )
        self.facts.append(fact)

    def _create(
        self,
        family: str,
        variant: str,
        index: int,
        source_key: str,
        anchor: Decimal,
        buffer: Decimal,
        origin: str | None,
        *,
        expiry_origin: int | None = None,
    ) -> None:
        bar = self.d1.data.bars[index]
        atr_text = self.d1.context.frames[index].atr
        if atr_text is None or bar.close < anchor - buffer * D(atr_text):
            self.reasons.add("SETUP_CREATION_BAR_ALREADY_INVALIDATED")
            return
        key = digest(
            "paqs-q/setup-key/v1",
            (
                self.d1.context.series_key,
                family,
                variant,
                source_key,
                origin,
                bar.version_ref,
            ),
        )
        if any(s.key == key for s in self.states):
            return
        if any(
            not s.terminal
            and s.family == family
            and s.variant == variant
            and s.source_key == source_key
            and s.origin_event_key == origin
            for s in self.states
        ):
            return
        state = State(
            key, family, variant, source_key, origin, anchor, buffer, index, bar.completed_at
        )
        state.expiry_origin = expiry_origin
        self.states.append(state)
        self._emit(state, "CREATED", bar.completed_at, ("FROZEN_SETUP_SOURCE",))

    def _discover(self, i: int) -> None:
        bar = self.d1.data.bars[i]
        frame = self.d1.context.frames[i]
        w1_regime = self.regime(self.w1, bar.completed_at)
        d1_regime = self.regime(self.d1, bar.completed_at)
        if w1_regime is None:
            self.reasons.add("W1_CONTEXT_UNAVAILABLE")
            return
        if frame.atr is None or D(frame.atr) <= 0:
            self.reasons.add("D1_ATR_UNAVAILABLE")
            return
        if (
            i > 0
            and w1_regime == "BULL_TREND"
            and d1_regime
            not in {
                "BEAR_TREND",
                "BEAR_TRANSITION",
            }
        ):
            previous = self.d1.data.bars[i - 1]
            if bar.close < previous.close:
                zones = {z.key: z for z in self.d1.context.zones}
                for key in self.d1.context.frames[i - 1].zones:
                    zone = zones[key]
                    if (
                        zone.role == "SUPPORT"
                        and zone.status == "CONFIRMED"
                        and zone.confirmation_index < i
                        and bar.low <= D(zone.upper)
                        and bar.high >= D(zone.lower)
                    ):
                        self._create(
                            FAMILY_TREND,
                            "SUPPORT_ZONE",
                            i,
                            key,
                            D(zone.lower),
                            D("0.15"),
                            None,
                        )
                for event in self.by_d1[i]:
                    if (
                        event.kind == "RETEST"
                        and event.status == "HOLD"
                        and event.direction == "UP"
                        and event.source is not None
                        and event.source.source_type != "MAJOR_SWING"
                        and bar.low <= D(event.source.upper)
                        and bar.high >= D(event.source.lower)
                    ):
                        self._create(
                            FAMILY_TREND,
                            "OLD_RESISTANCE_RETEST",
                            i,
                            event.source.version_key,
                            D(event.source.lower),
                            D("0.15"),
                            event.event_key,
                        )
        for event in self.by_d1[i]:
            source = event.source
            if event.direction != "UP" or source is None:
                continue
            if event.kind in {"FAILED_BREAK", "BREAKOUT_FAILURE"} and event.status == "CONFIRMED":
                range_known = any(
                    item.version_key == source.range_version and item.calculation_index < i
                    for item in self.d1.context.ranges
                )
                original_breakdown = any(
                    prior.kind == "BREAKDOWN"
                    and prior.source == source
                    and prior.anchor_key == event.anchor_key
                    and prior.bar_index < i
                    for prior in self.d1.events
                )
                if (
                    w1_regime == "RANGE"
                    and source.source_type == "RANGE_BOUNDARY"
                    and source.role == "SUPPORT"
                    and event.excursion_extreme is not None
                    and range_known
                    and (event.kind == "FAILED_BREAK" or original_breakdown)
                ):
                    self._create(
                        FAMILY_RANGE,
                        "RECLAIM",
                        i,
                        source.version_key,
                        D(event.excursion_extreme),
                        D("0.10"),
                        event.event_key,
                    )
                else:
                    self.reasons.add("RANGE_RECLAIM_SOURCE_OR_W1_BLOCKED")
            if w1_regime not in {"BULL_TREND", "RANGE", "BULL_TRANSITION"}:
                continue
            if event.kind == "FOLLOW_THROUGH" and event.status == "CONFIRMED":
                candidate = (
                    self.d1_candidates.get(event.related_keys[0]) if event.related_keys else None
                )
                parent = self.d1_events.get(candidate.anchor_key or "") if candidate else None
                if (
                    parent is not None
                    and candidate is not None
                    and candidate.bar_index == parent.bar_index
                    and "EVENT_CONFIRMATION" in candidate.trigger_reasons
                    and parent.direction == "UP"
                    and parent.source is not None
                    and parent.source.source_type in {"ZONE", "RANGE_BOUNDARY"}
                    and parent.source.role == "RESISTANCE"
                ):
                    self._create(
                        FAMILY_BREAKOUT,
                        "FOLLOW_THROUGH",
                        i,
                        parent.source.version_key,
                        D(parent.source.lower),
                        D("0.15"),
                        parent.event_key,
                    )
            if event.kind == "RETEST" and event.status == "HOLD":
                parent = self.d1_events.get(event.anchor_key or "")
                if (
                    parent is not None
                    and parent.direction == "UP"
                    and parent.source is not None
                    and parent.source.source_type in {"ZONE", "RANGE_BOUNDARY"}
                    and parent.source.role == "RESISTANCE"
                    and event.source == parent.source
                ):
                    self._create(
                        FAMILY_BREAKOUT,
                        "RETEST",
                        i,
                        parent.source.version_key,
                        D(parent.source.lower),
                        D("0.15"),
                        parent.event_key,
                        expiry_origin=parent.bar_index,
                    )

    def _clock_age(self, first: datetime, when: datetime) -> int | None:
        day = when.astimezone(self.zone).date()
        start = first.astimezone(self.zone).date()
        facts = {fact.day: fact for fact in self.d1.data.calendar}
        completed = {
            bar.start.astimezone(self.zone).date()
            for bar in self.d1.data.bars
            if bar.completed_at <= when and (bar.available_at is None or bar.available_at <= when)
        }
        for offset in range((day - start).days + 1):
            current = start + timedelta(days=offset)
            fact = facts.get(current)
            if (
                fact is None
                or (
                    self.d1.data.mode == "AS_OF"
                    and (fact.available_at is None or fact.available_at > when)
                )
                or (current < day and fact.kind == "OPEN" and current not in completed)
            ):
                self.reasons.add("SETUP_CLOCK_CALENDAR_OR_D1_BAR_INSUFFICIENT")
                return None
        return trading_days(self.d1.data, start, day)

    def _expired(self, state: State, when: datetime) -> bool | None:
        age = self._clock_age(state.created_at, when)
        if age is None:
            return None
        if age > 15:
            return True
        if state.expiry_origin is not None:
            original_at = self.d1.data.bars[state.expiry_origin].start
            original_age = self._clock_age(original_at, when)
            return None if original_age is None else original_age > 15
        return False

    def _terminate(self, state: State, status: str, when: datetime, reason: str) -> None:
        if state.trigger is not None:
            self._emit(
                state,
                "FOLLOW_THROUGH_FAILED",
                when,
                (reason,),
                candidate_key=state.trigger.key,
                related=(state.trigger.event_key,),
            )
            state.trigger = None
        state.pending_entry = None
        state.terminal = True
        self._emit(state, status, when, (reason,))

    def _on_d1_close(self, i: int) -> None:
        bar = self.d1.data.bars[i]
        atr_text = self.d1.context.frames[i].atr
        for state in self.states:
            if state.terminal or i < state.created_index or atr_text is None:
                continue
            threshold = state.anchor - state.buffer * D(atr_text)
            if bar.close < threshold:
                self._terminate(
                    state, "INVALIDATED", bar.completed_at, "D1_CLOSE_BELOW_FROZEN_ANCHOR"
                )
        self._discover(i)

    def _geometry(
        self, state: State, when: datetime, entry: Decimal
    ) -> tuple[
        Decimal | None,
        Decimal | None,
        TargetEvidence | None,
        TargetEvidence | None,
        Decimal | None,
        Decimal | None,
        tuple[str, ...],
        tuple[str, ...],
    ]:
        index = latest_index(self.d1.data, when)
        if index is None:
            return None, None, None, None, None, None, (), ("D1_CONTEXT_UNAVAILABLE",)
        atr_text = self.d1.context.frames[index].atr
        if atr_text is None or D(atr_text) <= 0:
            return None, None, None, None, None, None, (), ("D1_ATR_UNAVAILABLE",)
        atr = D(atr_text)
        risk = state.anchor - state.buffer * atr
        per_unit = entry - risk
        errors = []
        if risk <= 0 or per_unit <= 0:
            errors.append("RISK_GEOMETRY_INVALID")
        obstacles, gap_reasons, coverage = structural_obstacles(
            self.d1.data, self.d1.context, self.m30.data, when
        )
        if state.family == FAMILY_RANGE and state.origin_event_key is not None:
            origin = next(
                (e for e in self.d1.events if e.event_key == state.origin_event_key), None
            )
            version = origin.source.range_version if origin and origin.source else None
            original_range = next(
                (r for r in self.d1.context.ranges if r.version_key == version), None
            )
            if (
                original_range is not None
                and original_range.calculation_index <= index
                and not any(item.key == original_range.version_key for item in obstacles)
            ):
                obstacles = (
                    *obstacles,
                    Obstacle(
                        "FROZEN_RANGE_OPPOSITE_BOUNDARY",
                        original_range.version_key,
                        D(original_range.upper),
                        D(original_range.upper),
                        self.d1.data.bars[original_range.calculation_index].completed_at,
                    ),
                )
        t1, t2, rejected, inside = targets(obstacles, entry, atr)
        if inside:
            errors.append("ENTRY_INSIDE_RESISTANCE")
        if self.w1.data.quality != "COMPLETE":
            errors.append("W1_CONTEXT_QUALITY_INSUFFICIENT")
        if not coverage:
            errors.append("TARGET_COVERAGE_INSUFFICIENT")
        if t1 is None:
            errors.append("TARGET_UNAVAILABLE")
        rr1 = (D(t1.effective_price) - entry) / per_unit if t1 and per_unit > 0 else None
        rr2 = (D(t2.effective_price) - entry) / per_unit if t2 and per_unit > 0 else None
        return atr, risk, t1, t2, rr1, rr2, (*gap_reasons, *rejected), tuple(errors)

    def _on_m30_open(self, j: int, at: datetime, adjustment: str) -> None:
        for state in self.states:
            if state.terminal or state.created_at > at:
                continue
            expired = self._expired(state, at)
            if expired is None:
                continue
            if expired:
                self._terminate(state, "EXPIRED", at, "SETUP_D1_CLOCK_EXPIRED")
                continue
            pending = state.pending_entry
            if pending is None or j <= pending.m30_index:
                continue
            if j != pending.m30_index + 1:
                self._terminate(state, "EXPIRED", at, "NEXT_M30_BAR_MISSING")
                continue
            ref = self.refs.get(at)
            if ref is None:
                self.reasons.add("ENTRY_REFERENCE_UNAVAILABLE_AT_OPEN")
                state.pending_entry = None
                continue
            if (
                ref.security != self.m30.data.security
                or ref.adjustment != adjustment
                or (ref.source == "SYNTHETIC_OPEN" and adjustment != "SYNTHETIC")
            ):
                self._emit(
                    state,
                    "NO_TRADE",
                    ref.available_at,
                    ("ENTRY_REFERENCE_PRICE_BASIS_CONFLICT",),
                    m30_index=j,
                    candidate_key=pending.key,
                    price=ref.price,
                    entry_ref=ref,
                )
                state.pending_entry = None
                continue
            if ref.available_at > ref.price_at:
                self._emit(
                    state,
                    "NO_TRADE",
                    ref.available_at,
                    ("LATE_OPEN_REFERENCE_NOT_OPEN_TIME_QUALIFICATION",),
                    m30_index=j,
                    candidate_key=pending.key,
                    price=ref.price,
                    entry_ref=ref,
                )
                state.pending_entry = None
                continue
            if not self._allowed_w1(state, ref.price_at):
                self._emit(
                    state,
                    "NO_TRADE",
                    ref.price_at,
                    ("W1_CONTEXT_BLOCKED_AT_ENTRY",),
                    m30_index=j,
                    candidate_key=pending.key,
                    price=ref.price,
                    entry_ref=ref,
                )
                state.pending_entry = None
                continue
            d1_regime = self.regime(self.d1, ref.price_at)
            if d1_regime in {"BEAR_TREND", "BEAR_TRANSITION"}:
                self._emit(
                    state,
                    "NO_TRADE",
                    ref.price_at,
                    ("D1_BEAR_CONTEXT_AT_ENTRY",),
                    m30_index=j,
                    candidate_key=pending.key,
                    price=ref.price,
                    entry_ref=ref,
                )
                state.pending_entry = None
                continue
            atr, risk, fresh_t1, t2, rr1, rr2, rejected, errors = self._geometry(
                state, ref.price_at, ref.price
            )
            frozen = pending.frozen_t1
            if D(frozen.lower) <= ref.price <= D(frozen.upper):
                errors = (*errors, "ENTRY_INSIDE_ORIGINAL_T1")
            elif ref.price > D(frozen.upper):
                errors = (*errors, "ORIGINAL_T1_OVERRUN")
            if fresh_t1 is not None and D(fresh_t1.effective_price) < D(frozen.effective_price):
                chosen = fresh_t1
            else:
                chosen = frozen
                if risk is not None and ref.price > risk:
                    rr1 = (D(chosen.effective_price) - ref.price) / (ref.price - risk)
            if chosen and ref.price >= D(chosen.effective_price):
                errors = (*errors, "T1_NOT_ABOVE_ENTRY")
            if errors:
                status, reasons = "NO_TRADE", tuple(dict.fromkeys(errors))
            elif rr1 is None or rr1 < D("2.0"):
                status, reasons = "VALID_SETUP_BUT_POOR_ENTRY", ("WAIT_RETEST", "RR_T1_BELOW_2")
            else:
                status = (
                    "LONG_READY" if self.d1.data.mode == "AS_OF" else "OBSERVATIONAL_LONG_QUALIFIED"
                )
                reasons = ("ALL_ENTRY_GATES_PASS",)
            self._emit(
                state,
                status,
                ref.price_at,
                reasons,
                m30_index=j,
                candidate_key=pending.key,
                atr=atr,
                risk=risk,
                price=ref.price,
                target1=chosen,
                target2=t2,
                rr1=rr1,
                rr2=rr2,
                rejected=rejected,
                entry_ref=ref,
            )
            state.pending_entry = None

    def _stage_a(self, state: State, j: int, trigger: Trigger) -> None:
        bar = self.m30.data.bars[j]
        atr, risk, t1, t2, rr1, rr2, rejected, errors = self._geometry(
            state, bar.completed_at, bar.close
        )
        if errors or t1 is None:
            self._emit(
                state,
                "NO_TRADE",
                bar.completed_at,
                tuple(dict.fromkeys(errors)) or ("TARGET_UNAVAILABLE",),
                m30_index=j,
                candidate_key=trigger.key,
                atr=atr,
                risk=risk,
                price=bar.close,
                target1=t1,
                target2=t2,
                rr1=rr1,
                rr2=rr2,
                rejected=rejected,
            )
            return
        state.pending_entry = PendingEntry(trigger.key, bar.completed_at, j, t1)
        self._emit(
            state,
            "ENTRY_PENDING_REVALIDATION",
            bar.completed_at,
            ("NEXT_REGULAR_M30_OPEN_UNKNOWN",),
            m30_index=j,
            candidate_key=trigger.key,
            atr=atr,
            risk=risk,
            price=bar.close,
            target1=t1,
            target2=t2,
            rr1=rr1,
            rr2=rr2,
            rejected=rejected,
        )

    def _on_m30_close(self, j: int) -> None:
        bar = self.m30.data.bars[j]
        atr_text = self.m30.context.frames[j].atr
        if atr_text is None:
            return
        for state in self.states:
            if state.terminal or state.created_at > bar.start:
                continue
            expired = self._expired(state, bar.completed_at)
            if expired is None:
                continue
            if expired:
                self._terminate(state, "EXPIRED", bar.completed_at, "SETUP_D1_CLOCK_EXPIRED")
                continue
            if not self._allowed_w1(state, bar.completed_at):
                self._terminate(
                    state, "INVALIDATED", bar.completed_at, "W1_CONTEXT_NO_LONGER_ALLOWED"
                )
                continue
            trigger = state.trigger
            if trigger is not None and j > trigger.index:
                if j > trigger.index + 3:
                    self._emit(
                        state,
                        "FOLLOW_THROUGH_NONE",
                        bar.completed_at,
                        ("M30_FT_WINDOW_END",),
                        m30_index=j,
                        candidate_key=trigger.key,
                    )
                    state.trigger = None
                elif bar.close > trigger.high + D("0.10") * D(atr_text):
                    self._emit(
                        state,
                        "FOLLOW_THROUGH_CONFIRMED",
                        bar.completed_at,
                        ("M30_CLOSE_ABOVE_TRIGGER_HIGH_PLUS_0_10_ATR",),
                        m30_index=j,
                        candidate_key=trigger.key,
                        related=(trigger.event_key,),
                    )
                    state.trigger = None
                    self._stage_a(state, j, trigger)
                elif j == trigger.index + 3:
                    self._emit(
                        state,
                        "FOLLOW_THROUGH_NONE",
                        bar.completed_at,
                        ("M30_FT_WINDOW_END",),
                        m30_index=j,
                        candidate_key=trigger.key,
                    )
                    state.trigger = None
            if state.trigger is not None or state.pending_entry is not None:
                continue
            candidates = [
                e
                for e in self.by_m30[j]
                if e.kind in {"PRICE_PATTERN", "PRICE_TRIGGER_CANDIDATE"}
                and e.direction == "UP"
                and ("MICRO" in e.trigger_reasons or "STRONG" in e.trigger_reasons)
                and (state.family != FAMILY_TREND or "MICRO" in e.trigger_reasons)
                and e.event_key not in state.seen_triggers
            ]
            if not candidates:
                if not state.observed:
                    self._emit(
                        state, "OBSERVED", bar.completed_at, ("WAIT_M30_TRIGGER",), m30_index=j
                    )
                    state.observed = True
                continue
            event = min(candidates, key=lambda e: e.event_key)
            key = digest("paqs-q/setup-trigger/v1", (state.key, event.event_key, bar.version_ref))
            state.seen_triggers.add(event.event_key)
            state.trigger = Trigger(key, event.event_key, j, bar.high)
            self._emit(
                state,
                "TRIGGER_PENDING",
                bar.completed_at,
                (
                    "SETUP_BOUND_M30_MICRO"
                    if "MICRO" in event.trigger_reasons
                    else "SETUP_BOUND_M30_STRONG",
                ),
                m30_index=j,
                candidate_key=key,
                related=(event.event_key,),
            )
            self._emit(
                state,
                "FOLLOW_THROUGH_PENDING",
                bar.completed_at,
                ("M30_Q_PLUS_1_TO_Q_PLUS_3",),
                m30_index=j,
                candidate_key=key,
                related=(event.event_key,),
            )

    def run(self) -> tuple[tuple[SetupFact, ...], tuple[str, ...]]:
        events: list[tuple[datetime, int, str, int]] = []
        for i, bar in enumerate(self.d1.data.bars):
            events.append((bar.completed_at, 0, "D1_CLOSE", i))
        for j, bar in enumerate(self.m30.data.bars):
            if bar.session != "REGULAR":
                continue
            events.append((bar.start, 2, "M30_OPEN", j))
            events.append((bar.completed_at, 1, "M30_CLOSE", j))
        if self.m30.data.bars:
            last = self.m30.data.bars[-1]
            next_open = next_regular_open(self.m30.data, last.completed_at)
            if next_open is not None and next_open <= self.m30.data.as_of:
                events.append((next_open, 2, "M30_OPEN_ONLY", len(self.m30.data.bars)))
        with localcontext(CONTEXT):
            for instant, _, kind, index in sorted(events):
                if kind == "D1_CLOSE":
                    self._on_d1_close(index)
                elif kind in {"M30_OPEN", "M30_OPEN_ONLY"}:
                    at = self.m30.data.bars[index].start if kind == "M30_OPEN" else instant
                    adjustment = (
                        self.m30.data.bars[index].adjustment
                        if kind == "M30_OPEN"
                        else self.m30.data.bars[-1].adjustment
                    )
                    self._on_m30_open(index, at, adjustment)
                else:
                    self._on_m30_close(index)
        if not self.states:
            self.reasons.add("NO_QUALIFIED_SETUP")
        return tuple(self.facts), tuple(sorted(self.reasons))
