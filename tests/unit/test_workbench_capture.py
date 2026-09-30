"""Canonical source retention, derived membership and truthful observation timing."""

import hashlib
from dataclasses import fields, replace
from datetime import timedelta
from decimal import Decimal

import pytest

from ai_infra_quant.application.paqs_capture_evidence import (
    CapturedPaqsInputBundle,
    capture_payload,
)
from ai_infra_quant.application.paqs_q_product_input import adapt_snapshot
from ai_infra_quant.core.domain.market_data import MinuteBar
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from tests.unit.test_paqs_q_product_input import fixture_capture


def test_retained_raw_members_reproduce_derived_prices_and_do_not_create_pit():
    snapshot, source, _ = fixture_capture()
    derived = source.completed_30m_bars[0]
    minutes = tuple(
        MinuteBar(
            security=derived.security,
            interval_start=derived.interval_start + timedelta(minutes=i),
            interval_end=derived.interval_start + timedelta(minutes=i + 1),
            open=derived.open,
            high=derived.high,
            low=derived.low,
            close=derived.close,
            volume=derived.volume if i == 29 else Decimal(0),
            is_completed=True,
            retrieved_at=source.as_of_timestamp - timedelta(seconds=1),
        )
        for i in range(30)
    )
    retained = CapturedPaqsInputBundle(
        **{f.name: getattr(source, f.name) for f in fields(source)},
        source_minute_bars=minutes,
        daily_retrieved_at=source.as_of_timestamp,
        minute_retrieved_at=source.as_of_timestamp,
        minute_window_start=derived.interval_start,
    )
    adapted = adapt_snapshot(snapshot, retained)
    assert "DERIVED_BAR_SOURCE_RETRIEVAL_UNAVAILABLE" not in adapted.diagnostics
    assert "INDEPENDENT_M30_OPEN_REFERENCE_MISSING" in adapted.diagnostics
    assert adapted.multi_input.entry_references == ()
    bar = adapted.multi_input.m30.bars[0]
    assert bar.available_at is None and bar.retrieved_at == minutes[0].retrieved_at
    digest = hashlib.sha256(canonical_json(capture_payload(retained)).encode()).hexdigest()
    assert bar.source_ref.startswith(f"capture:{digest}:members:")
    assert len(capture_payload(retained)["source_minute_bars"]) == 30
    assert adapted.multi_input.m30.mode == "OBSERVATIONAL"
    with pytest.raises(ValueError, match="DERIVED_SOURCE_COVERAGE_INVALID"):
        adapt_snapshot(snapshot, replace(retained, source_minute_bars=minutes[1:]))
    with pytest.raises(ValueError, match="DERIVED_SOURCE_PRICES_MISMATCH"):
        adapt_snapshot(
            snapshot,
            replace(
                retained,
                source_minute_bars=(*minutes[:-1], replace(minutes[-1], volume=derived.volume + 1)),
            ),
        )
