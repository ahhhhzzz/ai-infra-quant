"""Real SQLite/API regression; all market and paid provider responses are synthetic."""

import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from test_paqs_e_analysis_api import AnalysisHarness
from test_paqs_e_analysis_api import analysis as analysis_fixture
from test_paqs_q_e_frozen_api import FrozenProvider

from ai_infra_quant.application.paqs_e_narrative import NarrativeAnalysisService
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.database.models.paqs_e_narrative import results, runs
from ai_infra_quant.database.models.paqs_q_analysis import paqs_q_analysis_runs
from ai_infra_quant.database.repositories.analysis_visibility import set_deleted
from ai_infra_quant.database.repositories.paqs_q_analysis import SQLAlchemyPaqsQAnalysisStore

analysis = analysis_fixture


def prepare(analysis: AnalysisHarness):
    snapshot = analysis.snapshots.current_snapshot(analysis.security_id)
    q = analysis.container.paqs_q_analysis_ledger.record(
        security_id=analysis.security_id,
        snapshot_hash=snapshot.snapshot_hash,
        status="INSUFFICIENT",
        payload={"market_snapshot": json.loads(canonical_json(snapshot))},
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
    return q, provider


def make_e(analysis: AnalysisHarness, q):
    response = analysis.client.post(
        "/api/v1/paqs-e/narrative-analyses/from-q",
        json={
            "q_analysis_id": q["analysis_id"],
            "model_key": "gpt-5.6-luna",
            "strategy_id": "paqs-e-master",
            "web_research": False,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_matching_filters_before_limit_and_never_analyzes(analysis: AnalysisHarness):
    q, provider = prepare(analysis)
    old = make_e(analysis, q)
    analysis.market_provider.quote_status = DataAvailabilityStatus.UNAVAILABLE
    other, _ = prepare(analysis)
    for _ in range(21):
        make_e(analysis, other)
    assert old["narrative_result_id"] not in {
        r.narrative_result_id
        for r in analysis.container.narrative_ledger.history(analysis.security_id)
    }
    found = analysis.client.get(f"/api/v1/paqs-q/analyses/{q['analysis_id']}/e-matches").json()
    assert found["state"] == "MATCHES_FOUND"
    assert [r["narrative_result_id"] for r in found["items"]] == [old["narrative_result_id"]]
    compare = analysis.client.get(
        f"/api/v1/paqs-q/analyses/{other['analysis_id']}/compare/{old['narrative_result_id']}"
    ).json()
    assert compare["same_snapshot"] is False
    assert len(provider.requests) == 1


def test_visibility_idempotence_restart_evidence_lineage_and_boundaries(analysis: AnalysisHarness):
    q, provider = prepare(analysis)
    first, second = make_e(analysis, q), make_e(analysis, q)
    sessions = analysis.container.session_factory
    with sessions() as session:
        before = {
            t.name: session.execute(select(t)).all() for t in (runs, results, paqs_q_analysis_runs)
        }
        triggers = session.execute(
            text("SELECT name,sql FROM sqlite_master WHERE type='trigger' ORDER BY name")
        ).all()
    local = TestClient(analysis.app, base_url="http://127.0.0.1", client=("127.0.0.1", 4321))

    def write(kind, id, deleted, **changes):
        return local.put(
            f"/api/v1/analysis-history/{kind}/{id}/visibility",
            headers={"Origin": "http://127.0.0.1"},
            json={"security_id": analysis.security_id, "deleted": deleted, **changes},
        )

    path = f"/api/v1/paqs-q/analyses/{q['analysis_id']}"
    # A mutation without same-origin proof is rejected.
    assert (
        local.put(
            f"/api/v1/analysis-history/Q/{q['analysis_id']}/visibility",
            json={"security_id": analysis.security_id, "deleted": True},
        ).status_code
        == 403
    )
    assert write("Q", str(uuid4()), True).status_code == 404
    assert write("Q", q["analysis_id"], True, security_id=str(uuid4())).status_code == 409
    assert write("Q", "invalid", True).status_code == 422
    a = write("Q", q["analysis_id"], True)
    assert a.status_code == 200, a.text
    assert write("Q", q["analysis_id"], True).json() == a.json()
    assert local.get(path).status_code == 410
    assert local.get(path + "/e-matches").status_code == 410
    assert local.get(path + f"/compare/{first['narrative_result_id']}").status_code == 410
    assert (
        local.get(f"/api/v1/paqs-q/securities/{analysis.security_id}/analyses").json()["items"]
        == []
    )
    deleted = local.get(
        f"/api/v1/paqs-q/securities/{analysis.security_id}/analyses?deleted=true"
    ).json()["items"]
    assert len(deleted) == 1
    # New store instance proves persistence independent of process memory.
    fresh = SQLAlchemyPaqsQAnalysisStore(sessions)
    assert fresh.history(analysis.security_id) == []
    assert len(fresh.history(analysis.security_id, deleted=True)) == 1
    assert write("Q", q["analysis_id"], False).status_code == 200
    assert local.get(path).json() == q
    for entry in (first, second):
        assert write("E", entry["narrative_result_id"], True).status_code == 200
        assert (
            local.get(
                "/api/v1/paqs-e/narrative-results/" + entry["narrative_result_id"]
            ).status_code
            == 410
        )
        assert (
            local.get("/api/v1/paqs-e/narrative-analyses/" + entry["narrative_run_id"]).status_code
            == 410
        )
    assert local.get(path + "/e-matches").json()["state"] == "MATCHES_DELETED"
    assert write("E", second["narrative_result_id"], False).status_code == 200
    # Hidden predecessor still verifies internally; visible revision chain isn't rewritten.
    assert (
        local.get("/api/v1/paqs-e/narrative-results/" + second["narrative_result_id"]).status_code
        == 200
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(
            pool.map(
                lambda _: set_deleted(
                    sessions, "E", first["narrative_result_id"], analysis.security_id, True
                ),
                range(2),
            )
        )
    assert outcomes[0] == outcomes[1]
    with sessions() as session:
        assert before == {
            t.name: session.execute(select(t)).all() for t in (runs, results, paqs_q_analysis_runs)
        }
        assert (
            triggers
            == session.execute(
                text("SELECT name,sql FROM sqlite_master WHERE type='trigger' ORDER BY name")
            ).all()
        )
    for table in (runs, results, paqs_q_analysis_runs):
        with pytest.raises(IntegrityError), sessions.begin() as session:
            session.execute(table.delete())
    assert len(provider.requests) == 2
    local.close()
