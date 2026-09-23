"""The Q store binds the actual accepted Snapshot canonical content hash."""

from __future__ import annotations

import json

import pytest
from test_paqs_market_snapshot import SECURITY_ID, _snapshot

from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.database.repositories.paqs_q_analysis import (
    PaqsQAnalysisIntegrityError,
    _verify_payload,
)


def test_actual_snapshot_content_hash_is_verified_before_persistence() -> None:
    snapshot = _snapshot()
    payload = {"market_snapshot": json.loads(canonical_json(snapshot))}
    assert _verify_payload(
        payload,
        security_id=SECURITY_ID,
        snapshot_hash=snapshot.snapshot_hash,
        status="INSUFFICIENT",
    ) == canonical_json(payload)
    payload["market_snapshot"]["d1_bars"][0]["close"] = "999.00"
    with pytest.raises(PaqsQAnalysisIntegrityError, match="content hash"):
        _verify_payload(
            payload,
            security_id=SECURITY_ID,
            snapshot_hash=snapshot.snapshot_hash,
            status="INSUFFICIENT",
        )
