"""One explicit product capture, truthful refusal and bounded Holder evidence."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from ai_infra_quant.application.paqs_q_holder import conditional_holder
from ai_infra_quant.application.paqs_q_product_analysis import (
    PaqsQProductAnalysisService,
    _latest_entry,
)
from ai_infra_quant.application.paqs_q_setup_artifacts import run as run_setup
from tests.unit.test_paqs_q_product_input import SECURITY_ID, fixture_capture
from tools.research.setup_risk.demo import demo_bundle


def test_product_analyze_is_one_capture_and_observational_insufficient() -> None:
    snapshot, source, _ = fixture_capture()
    calls = {"capture": 0, "record": 0}

    def current_capture(security_id: str):
        assert security_id == SECURITY_ID
        calls["capture"] += 1
        return snapshot, source

    def record(**kwargs):
        calls["record"] += 1
        return {"analysis_id": "test", **kwargs}

    service = PaqsQProductAnalysisService(
        SimpleNamespace(current_capture=current_capture), SimpleNamespace(record=record)
    )
    saved = service.analyze(SECURITY_ID)
    assert calls == {"capture": 1, "record": 1}
    payload = saved["payload"]
    assert saved["snapshot_hash"] == snapshot.snapshot_hash
    assert saved["status"] == "INSUFFICIENT"
    assert payload["qualification_mode"] == "OBSERVATIONAL"
    assert not payload["strict_historical_as_of"]
    assert payload["entry_reference_count"] == 0
    assert "CLOSED_DAY_FACTS_UNAVAILABLE" in payload["diagnostics"]
    assert payload["setup"]["status"] == "INSUFFICIENT"
    assert payload["holder"]["status"] == "UNDETERMINED"
    assert all(
        row["payload"]["snapshot_identity"] == snapshot.snapshot_hash
        for row in payload["q_inputs"].values()
    )
    assert all(row["qualification_mode"] == "OBSERVATIONAL" for row in payload["context"].values())
    assert all(row["qualification_mode"] == "OBSERVATIONAL" for row in payload["event"].values())


def test_synthetic_holder_is_setup_specific_and_never_infers_position() -> None:
    bundle = demo_bundle()
    result = run_setup(bundle, Path(__file__).resolve().parents[2])
    holder = conditional_holder(result, bundle.m30)
    assert result.status == "AVAILABLE"
    assert holder["status"] == "UNDETERMINED"  # two independent setups
    assert holder["entry_is_not_position"]
    assert len(holder["items"]) >= 2
    assert all(item["hypothetical_position_only"] for item in holder["items"])
    assert all(item["evidence_fact_keys"] for item in holder["items"])
    assert any(item["status"] == "TARGET_REACHED_REVIEW" for item in holder["items"])
    # Remove all post-target completed M30 evidence: a target is not inferred from
    # the confirmation bar's final high or an unknown later interval.
    first_target_time = min(f.target1.known_at for f in result.facts if f.target1 is not None)
    assert bundle.m30 is not None
    earlier = replace(
        bundle.m30,
        bars=tuple(bar for bar in bundle.m30.bars if bar.start < first_target_time),
    )
    earlier_holder = conditional_holder(result, earlier)
    assert all(item["status"] != "TARGET_REACHED_REVIEW" for item in earlier_holder["items"])


def test_holder_entry_disqualification_is_not_hard_exit() -> None:
    bundle = demo_bundle()
    result = run_setup(bundle, Path(__file__).resolve().parents[2])
    assert bundle.m30 is not None
    failed_entry = next(
        (fact for fact in result.facts if fact.status == "VALID_SETUP_BUT_POOR_ENTRY"), None
    )
    if failed_entry is None:
        # The deterministic demo may not include a poor-entry outcome. Construct
        # an isolated fact variation; the Setup identity remains otherwise intact.
        failed_entry = result.facts[-1].model_copy(
            update={
                "status": "VALID_SETUP_BUT_POOR_ENTRY",
                "entry_advisory": "VALID_SETUP_BUT_POOR_ENTRY",
                "effective_at": result.facts[-1].effective_at + timedelta(minutes=1),
            }
        )
    narrowed = result.model_copy(update={"facts": (failed_entry,)})
    outcome = conditional_holder(narrowed, bundle.m30)
    assert outcome["status"] != "EXIT_IF_HELD"
    assert all(item["status"] != "EXIT_IF_HELD" for item in outcome["items"])
    assert Decimal(outcome["items"][0]["anchor_price"]) > 0


def test_holder_requires_actual_hard_reason_and_full_negative_target_coverage() -> None:
    bundle = demo_bundle()
    result = run_setup(bundle, Path(__file__).resolve().parents[2])
    assert bundle.m30 is not None
    original = next(f for f in result.facts if f.target1 is not None)
    assert original.target1 is not None
    raised_target = original.target1.model_copy(
        update={"effective_price": "1000000", "lower": "1000000", "upper": "1000000"}
    )
    base = original.model_copy(
        update={
            "target1": raised_target,
            "status": "OBSERVED",
            "reasons": ("SYNTHETIC_OBSERVATION",),
        }
    )
    isolated = result.model_copy(update={"facts": (base,)})
    assert conditional_holder(isolated, bundle.m30)["status"] == "THESIS_VALID"
    after_target = next(bar for bar in bundle.m30.bars if bar.start >= raised_target.known_at)
    missing_bucket = replace(
        bundle.m30, bars=tuple(bar for bar in bundle.m30.bars if bar != after_target)
    )
    assert conditional_holder(isolated, missing_bucket)["status"] == "UNDETERMINED"
    closed = next(
        fact
        for fact in bundle.m30.calendar
        if fact.kind == "CLOSED" and fact.day >= raised_target.known_at.date()
    )
    missing_closed_day = replace(
        bundle.m30, calendar=tuple(f for f in bundle.m30.calendar if f != closed)
    )
    assert conditional_holder(isolated, missing_closed_day)["status"] == "UNDETERMINED"
    w1 = base.model_copy(
        update={
            "fact_key": "a" * 64,
            "status": "INVALIDATED",
            "effective_at": base.effective_at + timedelta(minutes=1),
            "reasons": ("W1_CONTEXT_NO_LONGER_ALLOWED",),
        }
    )
    w1_holder = conditional_holder(result.model_copy(update={"facts": (base, w1)}), bundle.m30)
    assert w1_holder["status"] == "UNDETERMINED"
    assert "W1_CONTEXT_NO_LONGER_ALLOWED_HOLDER_UNDETERMINED" in w1_holder["items"][0]["reasons"]
    hard = w1.model_copy(
        update={"fact_key": "b" * 64, "reasons": ("D1_CLOSE_BELOW_FROZEN_ANCHOR",)}
    )
    assert (
        conditional_holder(result.model_copy(update={"facts": (base, hard)}), bundle.m30)["status"]
        == "EXIT_IF_HELD"
    )
    no_trade = w1.model_copy(update={"status": "NO_TRADE", "reasons": ("RR_T1_BELOW_2",)})
    assert (
        conditional_holder(result.model_copy(update={"facts": (base, no_trade)}), bundle.m30)[
            "status"
        ]
        == "UNDETERMINED"
    )


def test_entry_stage_b_stays_bound_to_its_trigger_and_late_receipt_is_not_open_evidence() -> None:
    result = run_setup(demo_bundle(), Path(__file__).resolve().parents[2])
    prior_b = next(f for f in result.facts if f.status == "LONG_READY")
    prior_a = next(
        f
        for f in result.facts
        if f.setup_key == prior_b.setup_key
        and f.candidate_key == prior_b.candidate_key
        and f.status == "ENTRY_PENDING_REVALIDATION"
    )
    next_a = next(
        f
        for f in result.facts
        if f.setup_key == prior_b.setup_key
        and f.candidate_key != prior_b.candidate_key
        and f.status == "ENTRY_PENDING_REVALIDATION"
        and f.effective_at > prior_b.effective_at
    )
    mixed = result.model_copy(update={"facts": (prior_a, prior_b, next_a)})
    entry = _latest_entry(mixed)[0]
    assert entry["confirmation_candidate_key"] == next_a.candidate_key
    assert entry["next_open_stage_b"] is None
    assert not entry["independent_open_observed"]
    assert prior_b.entry_reference_price_at is not None
    late = prior_b.model_copy(
        update={
            "status": "NO_TRADE",
            "entry_advisory": "NO_TRADE",
            "effective_at": prior_b.entry_reference_price_at + timedelta(minutes=1),
            "entry_reference_available_at": prior_b.entry_reference_price_at + timedelta(minutes=1),
            "reasons": ("LATE_OPEN_REFERENCE_NOT_OPEN_TIME_QUALIFICATION",),
        }
    )
    late_entry = _latest_entry(result.model_copy(update={"facts": (prior_a, late)}))[0]
    assert late_entry["next_open_candidate_key"] == prior_a.candidate_key
    assert late_entry["next_open_qualification"]["status"] == "NO_TRADE"
    assert not late_entry["next_open_qualification"]["timely_open_reference"]
    assert not late_entry["independent_open_observed"]
