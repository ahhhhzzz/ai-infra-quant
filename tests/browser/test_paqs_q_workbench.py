"""Focused Q product actions and same-Snapshot comparison in real Chromium."""

from __future__ import annotations

from urllib.parse import urlparse

from playwright.sync_api import Browser, Route, expect

from .workbench_support import US, Workbench

Q_ID = "40000000-0000-4000-8000-000000000001"
E_ID = "50000000-0000-4000-8000-000000000001"
OTHER_E_ID = "50000000-0000-4000-8000-000000000002"
Q_HASH = "a" * 64
OTHER_HASH = "b" * 64
PROSE = "# 模型原文\n<script>window.qAttack=1</script>\nEntry/Holder 文字不是结构化事实。"


def q_record() -> dict[str, object]:
    return {
        "analysis_id": Q_ID,
        "security_id": US,
        "snapshot_hash": Q_HASH,
        "status": "INSUFFICIENT",
        "created_at": "2026-09-23T12:00:00Z",
        "payload": {
            "market_snapshot": {
                "snapshot_hash": Q_HASH,
                "as_of_timestamp": "2026-09-23T12:00:00Z",
                "security": {"security_id": US, "symbol": "AVGO"},
                "data_quality": "PARTIAL",
                "adjustment_metadata": {"basis": "PROVIDER_QFQ_CURRENT"},
                "timeframe_evidence_status": {"W1": {}, "D1": {}, "M30": {}},
            },
            "context": {"status": "INSUFFICIENT"},
            "event": {"status": "INSUFFICIENT"},
            "setup": {"entry_advisory": "DATA_UNAVAILABLE"},
            "holder": {"status": "UNDETERMINED"},
            "diagnostics": ["calendar facts missing"],
        },
    }


def test_q_history_refresh_and_explicit_e_same_snapshot_actions(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server, legacy_history=False)
    page = app.page
    q = q_record()
    e = {
        "narrative_result_id": E_ID,
        "snapshot_hash": Q_HASH,
        "response_text": PROSE,
        "model_id": "qwen3.8-max",
        "strategy_id": "fixture-alternative",
        "web_research": True,
        "market_snapshot": {
            "timeframe_evidence_status": {"d1": {"authoritative_bar_count": 80}},
            "source_coverage": {"d1_source_count": 80},
            "adjustment_metadata": {"basis": "PROVIDER_QFQ_CURRENT"},
            "data_quality": "PARTIAL",
        },
        "auxiliary_context": [{"provider": "fixture-research", "status": "UNAVAILABLE"}],
    }
    calls: list[tuple[str, str, object]] = []
    created = False

    def q_route(route: Route) -> None:
        nonlocal created
        request = route.request
        path = urlparse(request.url).path
        payload = request.post_data_json if request.method == "POST" else None
        calls.append((request.method, path, payload))
        if request.method == "POST" and path.endswith("/paqs-q/analyses"):
            assert payload == {"security_id": US}
            created = True
            return app.fulfill(route, q, 201)
        if "/paqs-q/securities/" in path and path.endswith("/analyses"):
            summary = {key: value for key, value in q.items() if key != "payload"}
            items = [summary] if created else []
            return app.fulfill(route, {"items": items})
        if path.endswith("/paqs-q/analyses/" + Q_ID):
            return app.fulfill(route, q)
        if "/compare/" in path:
            differing = path.endswith(OTHER_E_ID)
            other = (
                {**e, "narrative_result_id": OTHER_E_ID, "snapshot_hash": OTHER_HASH}
                if differing
                else e
            )
            return app.fulfill(
                route, {"same_snapshot": not differing, "q_analysis": q, "e_narrative": other}
            )
        raise AssertionError(path)

    def e_route(route: Route) -> None:
        request = route.request
        payload = request.post_data_json
        calls.append((request.method, urlparse(request.url).path, payload))
        assert payload["q_analysis_id"] == Q_ID
        assert payload["model_key"] == "qwen3.8-max"
        assert payload["strategy_id"] == "fixture-alternative"
        assert payload["web_research"] is True
        return app.fulfill(route, {**e, "status": "SUCCEEDED"}, 201)

    page.route("**/api/v1/paqs-q/**", q_route)
    page.route("**/api/v1/paqs-e/narrative-analyses/from-q", e_route)
    app.open()
    expect(page.locator("#q-analyze")).to_be_enabled()
    assert not any(method == "POST" for method, _, _ in calls)
    page.locator("#refresh-market").click()
    page.reload()
    expect(page.locator("#q-analyze")).to_be_enabled()
    assert not any(method == "POST" for method, _, _ in calls)
    page.locator("#q-analyze").click()
    expect(page.locator("#q-result")).to_contain_text(Q_ID)
    expect(page.locator("#q-e-analyze")).to_be_enabled()
    assert len([call for call in calls if call[0] == "POST"]) == 1
    page.locator("#model-id").select_option("qwen3.8-max")
    page.locator("#strategy-id").select_option("fixture-alternative")
    page.locator("#web-research").check()
    page.locator("#q-e-analyze").click()
    expect(page.locator("#q-e-status")).to_contain_text("快照身份一致")
    assert page.locator("#q-e-result .narrative-text").text_content() == PROSE
    expect(page.locator("#q-e-result")).to_contain_text("E 冻结输入覆盖与来源")
    expect(page.locator("#q-e-result")).to_contain_text("E 附加研究原始引用")
    assert page.locator("#q-e-result script").count() == 0
    assert page.evaluate("window.qAttack") is None
    assert len([call for call in calls if call[0] == "POST"]) == 2
    page.locator("#q-e-known-id").fill(OTHER_E_ID)
    page.locator("#q-e-known-form button").click()
    expect(page.locator("#q-e-status")).to_contain_text("快照身份不一致")
    assert "不可直接比较" in (page.locator("#q-e-result").text_content() or "")
    page.reload()
    expect(page.locator("#q-history .history-row")).to_have_count(1)
    assert len([call for call in calls if call[0] == "POST"]) == 2
    page.locator("#q-history .history-row").click()
    expect(page.locator("#q-result")).to_contain_text(Q_ID)
    assert len([call for call in calls if call[0] == "POST"]) == 2
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert app.posts == [] and app.errors == []
    app.close()
