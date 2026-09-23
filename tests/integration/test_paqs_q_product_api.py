"""Real route through one provider capture, frozen Q history and no implicit rerun."""

from test_paqs_e_analysis_api import AnalysisHarness
from test_paqs_e_analysis_api import analysis as analysis_fixture

from ai_infra_quant.application.paqs_q_product_analysis import PaqsQProductAnalysisService

analysis = analysis_fixture


def test_q_route_freezes_one_capture_and_history_is_read_only(analysis: AnalysisHarness) -> None:
    container = analysis.container
    container.paqs_q_analysis_service = PaqsQProductAnalysisService(
        container.paqs_market_snapshot_queries, container.paqs_q_analysis_ledger
    )
    created = analysis.client.post(
        "/api/v1/paqs-q/analyses", json={"security_id": analysis.security_id}
    )
    assert created.status_code == 201, created.text
    saved = created.json()
    assert saved["security_id"] == analysis.security_id
    assert saved["status"] == "INSUFFICIENT"
    assert saved["payload"]["qualification_mode"] == "OBSERVATIONAL"
    assert saved["payload"]["entry_reference_count"] == 0
    assert "CLOSED_DAY_FACTS_UNAVAILABLE" in saved["payload"]["diagnostics"]
    assert saved["payload"]["market_snapshot"]["snapshot_hash"] == saved["snapshot_hash"]
    assert not any(fact["status"] == "LONG_READY" for fact in saved["payload"]["setup"]["facts"])
    q_id = saved["analysis_id"]
    detail = analysis.client.get(f"/api/v1/paqs-q/analyses/{q_id}")
    history = analysis.client.get(f"/api/v1/paqs-q/securities/{analysis.security_id}/analyses")
    assert detail.status_code == 200 and detail.json() == saved
    assert history.status_code == 200
    assert [item["analysis_id"] for item in history.json()["items"]] == [q_id]
    assert "payload" not in history.json()["items"][0]
    assert analysis.client.get(f"/api/v1/paqs-q/analyses/{q_id}").json() == saved
