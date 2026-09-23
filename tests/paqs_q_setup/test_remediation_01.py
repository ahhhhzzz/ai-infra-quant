"""Focused regressions for Setup/Risk 1.0.1 remediation."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from ai_infra_quant.application.paqs_q_setup_artifacts import run
from ai_infra_quant.core.domain.paqs_q.setup_reference import MultiInput
from tools.research.setup_risk.demo import demo_bundle

ROOT = Path(__file__).resolve().parents[2]
D = Decimal


def test_late_entry_reference_preserves_complete_historical_facts() -> None:
    bundle = demo_bundle()
    baseline = run(bundle, ROOT)
    ready = next(f for f in baseline.facts if f.status == "LONG_READY")
    assert ready.m30_index is not None
    received_at = bundle.m30.bars[ready.m30_index + 26].completed_at
    cutoff = bundle.m30.bars[ready.m30_index + 10].completed_at
    refs = tuple(
        replace(ref, available_at=received_at)
        if ref.price_at == ready.entry_reference_price_at
        else ref
        for ref in bundle.entry_references
    )
    full = run(replace(bundle, entry_references=refs), ROOT)
    short = MultiInput(
        replace(
            bundle.w1,
            bars=tuple(b for b in bundle.w1.bars if b.completed_at <= cutoff),
            as_of=cutoff,
        ),
        replace(
            bundle.d1,
            bars=tuple(b for b in bundle.d1.bars if b.completed_at <= cutoff),
            as_of=cutoff,
        ),
        replace(
            bundle.m30,
            bars=tuple(b for b in bundle.m30.bars if b.completed_at <= cutoff),
            as_of=cutoff,
        ),
        tuple(ref for ref in refs if ref.available_at <= cutoff),
    )
    prefix = run(short, ROOT)
    assert full.status == prefix.status == "AVAILABLE"
    before = tuple(f for f in full.facts if f.effective_at <= cutoff)
    assert before == prefix.facts  # full SetupFact, including fact_key and evidence
    assert all(
        a.effective_at <= b.effective_at for a, b in zip(full.facts, full.facts[1:], strict=False)
    )
    assert len({f.fact_key for f in full.facts}) == len(full.facts)
    assert not any(
        f.status == "LONG_READY" and f.candidate_key == ready.candidate_key for f in full.facts
    )
    missed = [
        f
        for f in full.facts
        if "ENTRY_REFERENCE_UNAVAILABLE_AT_OPEN" in f.reasons
        and f.candidate_key == ready.candidate_key
    ]
    assert len(missed) == 1 and missed[0].effective_at == ready.entry_reference_price_at
    late = [
        f
        for f in full.facts
        if "LATE_OPEN_REFERENCE_NOT_OPEN_TIME_QUALIFICATION" in f.reasons
        and f.candidate_key == ready.candidate_key
    ]
    assert len(late) == 1
    assert late[0].effective_at == received_at
    at_receipt = [f for f in full.facts if f.effective_at == received_at]
    late_flags = [
        "LATE_OPEN_REFERENCE_NOT_OPEN_TIME_QUALIFICATION" in f.reasons for f in at_receipt
    ]
    assert late_flags == sorted(late_flags)  # equal-time market facts precede reference receipts
