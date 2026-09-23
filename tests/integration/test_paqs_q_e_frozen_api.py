"""Explicit E-from-Q uses the stored Q Snapshot, never a fresh market capture."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from test_paqs_e_analysis_api import AnalysisHarness
from test_paqs_e_analysis_api import analysis as analysis_fixture

from ai_infra_quant.application.paqs_e_narrative import NarrativeAnalysisService
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.paqs_e_narrative import NarrativeSuccess
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json

analysis = analysis_fixture
PROSE = "  # 原文\nEntry/Holder 字样不构成结构化结论。\n"


class FrozenProvider:
    def __init__(self) -> None:
        self.requests: list[Any] = []

    def reason_text(self, *, request: Any, strategy: Any, prompt: Any) -> NarrativeSuccess:
        self.requests.append(request)
        return NarrativeSuccess(PROSE, "synthetic-frozen")


def test_explicit_e_uses_q_snapshot_and_preserves_text(analysis: AnalysisHarness) -> None:
    frozen = analysis.snapshots.current_snapshot(analysis.security_id)
    q = analysis.container.paqs_q_analysis_ledger.record(
        security_id=analysis.security_id,
        snapshot_hash=frozen.snapshot_hash,
        status="INSUFFICIENT",
        payload={"market_snapshot": json.loads(canonical_json(frozen)), "status": "INSUFFICIENT"},
    )
    analysis.snapshots.snapshots.clear()
    analysis.snapshots.error = AssertionError("Frozen E must not acquire a new market Snapshot")
    provider = FrozenProvider()
    previous = analysis.container.narrative_analysis_service
    analysis.container.narrative_analysis_service = NarrativeAnalysisService(
        analysis.snapshots,
        provider,
        analysis.container.narrative_ledger,
        previous.models,
        previous.research,
    )
    payload = {
        "q_analysis_id": q["analysis_id"],
        "model_key": "gpt-5.6-luna",
        "strategy_id": "paqs-e-master",
        "web_research": False,
    }
    response = analysis.client.post("/api/v1/paqs-e/narrative-analyses/from-q", json=payload)
    assert response.status_code == 201, response.text
    e = response.json()
    assert e["response_text"] == PROSE and e["snapshot_hash"] == frozen.snapshot_hash
    assert len(provider.requests) == 1 and provider.requests[0].market_snapshot == frozen
    assert analysis.snapshots.snapshots == []
    compare = analysis.client.get(
        f"/api/v1/paqs-q/analyses/{q['analysis_id']}/compare/{e['narrative_result_id']}"
    )
    assert compare.status_code == 200, compare.text
    body = compare.json()
    assert body["same_snapshot"] is True
    assert body["e_narrative"]["response_text"] == PROSE
    assert body["structural_agreement"] == "UNDETERMINED_UNSTRUCTURED_E_NARRATIVE"
    assert len(provider.requests) == 1 and analysis.snapshots.snapshots == []


def test_e_from_unknown_q_does_not_call_provider(analysis: AnalysisHarness) -> None:
    provider = FrozenProvider()
    previous = analysis.container.narrative_analysis_service
    analysis.container.narrative_analysis_service = NarrativeAnalysisService(
        analysis.snapshots,
        provider,
        analysis.container.narrative_ledger,
        previous.models,
        previous.research,
    )
    response = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses/from-q",
        json={
            "q_analysis_id": str(uuid4()),
            "model_key": "gpt-5.6-luna",
            "strategy_id": "paqs-e-master",
            "web_research": False,
        },
    )
    assert response.status_code == 404
    assert provider.requests == []


def test_different_frozen_snapshots_are_not_directly_comparable(
    analysis: AnalysisHarness,
) -> None:
    original = analysis.snapshots.current_snapshot(analysis.security_id)
    analysis.market_provider.quote_status = DataAvailabilityStatus.UNAVAILABLE
    changed = analysis.snapshots.current_snapshot(analysis.security_id)
    assert original.snapshot_hash != changed.snapshot_hash
    store = analysis.container.paqs_q_analysis_ledger
    q_original = store.record(
        security_id=analysis.security_id,
        snapshot_hash=original.snapshot_hash,
        status="INSUFFICIENT",
        payload={"market_snapshot": json.loads(canonical_json(original))},
    )
    q_changed = store.record(
        security_id=analysis.security_id,
        snapshot_hash=changed.snapshot_hash,
        status="INSUFFICIENT",
        payload={"market_snapshot": json.loads(canonical_json(changed))},
    )
    provider = FrozenProvider()
    previous = analysis.container.narrative_analysis_service
    analysis.container.narrative_analysis_service = NarrativeAnalysisService(
        analysis.snapshots,
        provider,
        analysis.container.narrative_ledger,
        previous.models,
        previous.research,
    )
    e = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses/from-q",
        json={
            "q_analysis_id": q_changed["analysis_id"],
            "model_key": "gpt-5.6-luna",
            "strategy_id": "paqs-e-master",
            "web_research": False,
        },
    )
    assert e.status_code == 201, e.text
    comparison = analysis.client.get(
        f"/api/v1/paqs-q/analyses/{q_original['analysis_id']}/compare/"
        f"{e.json()['narrative_result_id']}"
    )
    assert comparison.status_code == 200, comparison.text
    body = comparison.json()
    assert body["same_snapshot"] is False
    assert body["reason"] == "DIFFERENT_SNAPSHOT_NOT_DIRECTLY_COMPARABLE"
    assert body["e_narrative"]["response_text"] == PROSE


def test_e_from_q_rejects_inconsistent_frozen_snapshot_before_provider(
    analysis: AnalysisHarness,
) -> None:
    frozen = analysis.snapshots.current_snapshot(analysis.security_id)
    q_id = str(uuid4())

    class CorruptQStore:
        def get(self, analysis_id: str) -> dict[str, Any]:
            assert analysis_id == q_id
            return {
                "analysis_id": q_id,
                "security_id": analysis.security_id,
                "snapshot_hash": "b" * 64,
                "payload": {"market_snapshot": json.loads(canonical_json(frozen))},
            }

    analysis.container.paqs_q_analysis_ledger = CorruptQStore()  # type: ignore[assignment]
    provider = FrozenProvider()
    previous = analysis.container.narrative_analysis_service
    analysis.container.narrative_analysis_service = NarrativeAnalysisService(
        analysis.snapshots,
        provider,
        analysis.container.narrative_ledger,
        previous.models,
        previous.research,
    )
    before = len(analysis.snapshots.snapshots)
    response = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses/from-q",
        json={
            "q_analysis_id": q_id,
            "model_key": "gpt-5.6-luna",
            "strategy_id": "paqs-e-master",
            "web_research": False,
        },
    )
    assert response.status_code == 500
    assert provider.requests == []
    assert len(analysis.snapshots.snapshots) == before
