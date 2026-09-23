"""Conditional, evidence-bound Holder reading of Setup/Risk 1.0.1 results.

This module never infers a real position or changes the frozen Setup/Entry rules.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from ai_infra_quant.core.domain.paqs_q.inputs import QInput
from ai_infra_quant.core.domain.paqs_q.setup_reference import SetupFact, SetupRun

HOLDER_ID = "paqs-q-conditional-holder"
HOLDER_VERSION = "1.0.1"


def holder_code_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _newest(facts: list[SetupFact]) -> SetupFact:
    return max(enumerate(facts), key=lambda pair: (pair[1].effective_at, pair[0]))[1]


def _target_binding(facts: list[SetupFact]) -> tuple[SetupFact | None, str | None]:
    """Keep the first frozen candidate; only its qualified Stage B may revise T1.

    A geometry on NO_TRADE is not a Holder target. A later candidate cannot
    silently replace the hypothetical target of the first traceable candidate.
    Repeating the same target never moves its first binding time.
    """
    ordered = [
        fact for _, fact in sorted(enumerate(facts), key=lambda row: (row[1].effective_at, row[0]))
    ]
    stages_a = [
        fact
        for fact in ordered
        if fact.status == "ENTRY_PENDING_REVALIDATION"
        and fact.candidate_key is not None
        and fact.target1 is not None
    ]
    if not stages_a:
        return None, "FROZEN_TARGET_BINDING_UNAVAILABLE"
    first = stages_a[0]
    assert first.target1 is not None and first.candidate_key is not None
    if first.target1.known_at > first.effective_at:
        return None, "TARGET_STRUCTURE_NOT_KNOWN_AT_BINDING"
    if any(
        fact.candidate_key == first.candidate_key and fact.target1 != first.target1
        for fact in stages_a[1:]
    ):
        return None, "CONFLICTING_STAGE_A_TARGET_FOR_CANDIDATE"
    qualified = [
        fact
        for fact in ordered
        if fact.candidate_key == first.candidate_key
        and fact.status in {"LONG_READY", "OBSERVATIONAL_LONG_QUALIFIED"}
        and fact.target1 is not None
        and fact.effective_at >= first.effective_at
    ]
    selected = first
    if qualified:
        final = qualified[0]
        assert final.target1 is not None
        if final.target1.known_at > final.effective_at or any(
            fact.target1 != final.target1 for fact in qualified[1:]
        ):
            return None, "CONFLICTING_OR_FUTURE_STAGE_B_TARGET"
        if final.target1 != first.target1:
            selected = final
    if any(
        fact.candidate_key != first.candidate_key and fact.target1 != selected.target1
        for fact in stages_a[1:]
    ):
        return None, "MULTIPLE_CANDIDATE_TARGETS_AMBIGUOUS"
    return selected, None


def _complete_post_target_coverage(m30: QInput, binding_at: datetime) -> bool:
    """Prove every elapsed regular slot from target binding through as_of.

    OBSERVATIONAL Event qualification does not certify unlisted calendar dates.
    Negative target evidence therefore needs each intervening OPEN/CLOSED day and
    every completed regular M30 bucket, including the current partial session.
    """
    zone = ZoneInfo(m30.market_timezone)
    first = binding_at.astimezone(zone).date()
    last = m30.as_of.astimezone(zone).date()
    span = (last - first).days
    if not 0 <= span <= 10000 or m30.problem() is not None:
        return False
    days = {fact.day: fact for fact in m30.calendar}
    expected: list[tuple[datetime, datetime]] = []
    step = timedelta(minutes=30)
    for offset in range(span + 1):
        fact = days.get(first + timedelta(days=offset))
        if fact is None or not fact.complete or fact.kind not in {"OPEN", "CLOSED"}:
            return False
        if fact.available_at is not None and fact.available_at > m30.as_of:
            return False
        if fact.kind == "CLOSED":
            if fact.segments:
                return False
            continue
        if not fact.segments:
            return False
        for start, end in fact.segments:
            if start >= end or (end - start) % step:
                return False
            point = start
            while point < end:
                if point >= binding_at and point + step <= m30.as_of:
                    expected.append((point, point + step))
                point += step
    actual = [
        (bar.start, bar.end) for bar in m30.bars if bar.start >= binding_at and bar.end <= m30.as_of
    ]
    return (
        bool(expected)
        and expected == actual
        and all(
            bar.completed
            and bar.coverage == "COMPLETE"
            and bar.session == "REGULAR"
            and bar.completed_at <= m30.as_of
            and bar.retrieved_at <= m30.as_of
            and (bar.available_at is not None or m30.mode != "AS_OF")
            and (bar.available_at is None or bar.available_at <= m30.as_of)
            for bar in m30.bars
            if bar.start >= binding_at and bar.end <= m30.as_of
        )
    )


def conditional_holder(setup: SetupRun, m30: QInput | None) -> dict[str, Any]:
    """Assess only a hypothetical holder of each traceable Setup.

    Target touches use completed M30 bars whose entire interval follows the
    candidate's frozen target binding; structural known_at is not that binding.
    """

    identity = {
        "holder_id": HOLDER_ID,
        "holder_version": HOLDER_VERSION,
        "code_hash": holder_code_hash(),
        "setup_result_hash": setup.canonical_result_hash,
        "entry_is_not_position": True,
    }
    if setup.status != "AVAILABLE":
        return {
            **identity,
            "status": "UNDETERMINED",
            "reasons": ["SETUP_RESULT_" + setup.status, *setup.reasons],
            "items": [],
        }
    grouped: dict[str, list[SetupFact]] = defaultdict(list)
    for fact in setup.facts:
        grouped[fact.setup_key].append(fact)
    if not grouped:
        return {
            **identity,
            "status": "UNDETERMINED",
            "reasons": ["NO_TRACEABLE_SETUP"],
            "items": [],
        }
    items: list[dict[str, Any]] = []
    for setup_key, facts in sorted(grouped.items()):
        latest = _newest(facts)
        binding, binding_problem = _target_binding(facts)
        frozen_target = binding.target1 if binding is not None else None
        state = "UNDETERMINED"
        reasons: list[str] = []
        evidence_keys = [latest.fact_key]
        touch: dict[str, Any] | None = None
        if binding is not None and binding.fact_key not in evidence_keys:
            evidence_keys.append(binding.fact_key)
        hard_invalidation = next(
            (
                fact
                for fact in facts
                if fact.status == "INVALIDATED" and "D1_CLOSE_BELOW_FROZEN_ANCHOR" in fact.reasons
            ),
            None,
        )
        context_invalidation = next(
            (
                fact
                for fact in facts
                if fact.status == "INVALIDATED" and "W1_CONTEXT_NO_LONGER_ALLOWED" in fact.reasons
            ),
            None,
        )
        if hard_invalidation is not None:
            state = "EXIT_IF_HELD"
            reasons = ["FROZEN_SETUP_D1_CLOSE_HARD_INVALIDATION"]
            evidence_keys = [hard_invalidation.fact_key]
        elif context_invalidation is not None:
            reasons = ["W1_CONTEXT_NO_LONGER_ALLOWED_HOLDER_UNDETERMINED"]
            evidence_keys = [context_invalidation.fact_key]
        elif latest.status == "EXPIRED":
            reasons = ["SETUP_EXPIRED_NO_CURRENT_THESIS"]
        elif binding is None or frozen_target is None:
            reasons = [binding_problem or "FROZEN_TARGET_UNAVAILABLE"]
        elif m30 is None or m30.quality != "COMPLETE":
            reasons = ["COMPLETE_M30_TARGET_EVIDENCE_MISSING"]
        elif m30.problem() is not None or binding.effective_at > m30.as_of:
            reasons = ["M30_OR_TARGET_BINDING_NOT_AVAILABLE_AS_OF"]
        else:
            observed = [
                bar
                for bar in m30.bars
                if bar.completed
                and bar.coverage == "COMPLETE"
                and bar.session == "REGULAR"
                and bar.start >= binding.effective_at
                and bar.end <= m30.as_of
                and bar.completed_at <= m30.as_of
                and bar.retrieved_at <= m30.as_of
                and (bar.available_at is not None or m30.mode != "AS_OF")
                and (bar.available_at is None or bar.available_at <= m30.as_of)
            ]
            if not observed:
                reasons = ["POST_TARGET_COMPLETE_M30_EVIDENCE_MISSING"]
            elif touched := next(
                (bar for bar in observed if bar.high >= Decimal(frozen_target.effective_price)),
                None,
            ):
                state = "TARGET_REACHED_REVIEW"
                reasons = ["FROZEN_T1_TOUCHED_AFTER_SETUP_BINDING"]
                touch = {
                    "bar_version_ref": touched.version_ref,
                    "source_ref": touched.source_ref,
                    "start": touched.start,
                    "completed_at": touched.completed_at,
                    "high": str(touched.high),
                }
            elif not _complete_post_target_coverage(m30, binding.effective_at):
                reasons = ["POST_TARGET_M30_CALENDAR_OR_BUCKET_COVERAGE_UNPROVEN"]
            elif latest.status == "FOLLOW_THROUGH_FAILED":
                state = "HOLD_WITH_WARNING"
                reasons = ["SETUP_FOLLOW_THROUGH_FAILED_WITHOUT_HARD_INVALIDATION"]
            elif latest.status in {
                "CREATED",
                "OBSERVED",
                "TRIGGER_PENDING",
                "FOLLOW_THROUGH_PENDING",
                "FOLLOW_THROUGH_CONFIRMED",
                "FOLLOW_THROUGH_NONE",
                "ENTRY_PENDING_REVALIDATION",
                "LONG_READY",
                "OBSERVATIONAL_LONG_QUALIFIED",
                "VALID_SETUP_BUT_POOR_ENTRY",
            }:
                state = "THESIS_VALID"
                reasons = ["TRACEABLE_SETUP_NO_HARD_INVALIDATION_OR_T1_TOUCH"]
            else:
                reasons = ["LATEST_SETUP_STATUS_NOT_HOLDER_THESIS_EVIDENCE"]
        items.append(
            {
                "setup_key": setup_key,
                "family": latest.family,
                "variant": latest.variant,
                "status": state,
                "reasons": reasons,
                "evidence_fact_keys": evidence_keys,
                "as_of": m30.as_of if m30 is not None else latest.effective_at,
                "anchor_price": latest.anchor_price,
                "target1": frozen_target.effective_price if frozen_target else None,
                "target_binding": (
                    {
                        "setup_key": setup_key,
                        "candidate_key": binding.candidate_key,
                        "fact_key": binding.fact_key,
                        "fact_status": binding.status,
                        "effective_at": binding.effective_at,
                        "structural_known_at": frozen_target.known_at,
                        "source_keys": frozen_target.source_keys,
                        "sources": frozen_target.sources,
                    }
                    if binding is not None and frozen_target is not None
                    else None
                ),
                "target_touch": touch,
                "hypothetical_position_only": True,
            }
        )
    priority = {
        "EXIT_IF_HELD": 4,
        "TARGET_REACHED_REVIEW": 3,
        "HOLD_WITH_WARNING": 2,
        "THESIS_VALID": 1,
        "UNDETERMINED": 0,
    }
    # Several unrelated Setups have no shared thesis: report per-Setup items and
    # keep the aggregate undecided rather than presenting a combined trade call.
    overall = items[0]["status"] if len(items) == 1 else "UNDETERMINED"
    if len(items) == 1:
        assert overall in priority
    return {
        **identity,
        "status": overall,
        "reasons": [] if len(items) == 1 else ["MULTIPLE_INDEPENDENT_SETUPS"],
        "items": items,
    }
