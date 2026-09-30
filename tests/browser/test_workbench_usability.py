"""Windows Chromium operation paths with explicit synthetic provider responses."""
# ruff: noqa: RUF001 -- Exact Chinese UI text.

import copy
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import expect

from .test_dashboard_readability import choose, display_record, install
from .test_paqs_q_workbench import Q_ID
from .workbench_support import HK, US, Workbench

SHOTS = Path(__file__).resolve().parents[2] / "docs/evidence/TASK_V1_1"


def test_delete_cancel_restore_refresh_and_comparison_invalidation(browser, workbench_server):
    app = Workbench(browser, workbench_server, legacy_history=False)
    record = display_record()
    install(app, record)
    e = next(iter(app.narratives.values()))
    e_id = e["narrative_result_id"]
    removed = {"Q": False, "E": False}
    writes = []
    pending = []

    def visibility(route):
        payload = route.request.post_data_json
        kind = urlparse(route.request.url).path.split("/")[-3]
        writes.append(payload)
        removed[kind] = payload["deleted"]
        app.fulfill(route, {"deleted": payload["deleted"]})

    def q_history(route):
        deleted = parse_qs(urlparse(route.request.url).query).get("deleted") == ["true"]
        items = (
            [{k: v for k, v in record.items() if k != "payload"}] if deleted == removed["Q"] else []
        )
        app.fulfill(route, {"items": items})

    def e_history(route):
        deleted = parse_qs(urlparse(route.request.url).query).get("deleted") == ["true"]
        item = {**e, "preview": e["response_text"][:160]}
        app.fulfill(route, {"items": [item] if deleted == removed["E"] else []})

    app.page.route("**/api/v1/analysis-history/**", visibility)
    app.page.route(f"**/paqs-q/securities/{US}/analyses?*", q_history)
    app.page.route(f"**/paqs-e/securities/{US}/narrative-results?*", e_history)
    page = app.open()
    choose(app)
    page.locator("#tab-history").click()
    page.once("dialog", lambda d: d.dismiss())
    page.locator("#q-history .history-visibility").click()
    assert writes == []
    page.once("dialog", lambda d: (assert_confirmation(d.message), d.accept()))
    page.locator("#q-history .history-visibility").click()
    expect(page.locator("#q-history .history-row")).to_have_count(0)
    expect(page.locator("#q-result")).to_contain_text("尚未选择分析结果")
    page.locator("#q-history-deleted").check()
    expect(page.locator("#q-history .history-row")).to_be_disabled()
    page.reload()
    page.locator("#tab-history").click()
    page.locator("#q-history-deleted").check()
    expect(page.locator("#q-history .history-visibility")).to_have_text("恢复")
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / "after-deleted-synthetic.png"), full_page=True)
    page.locator("#q-history .history-visibility").click()
    expect(page.locator("#q-history .history-row")).to_have_count(0)
    page.locator("#q-history-deleted").uncheck()
    page.locator('[data-q-analysis-id="' + Q_ID + '"]').click()
    page.locator("#tab-compare").click()
    page.route("**/compare/*", lambda r: pending.append(r))
    page.locator("#q-e-read").click()
    page.wait_for_timeout(100)
    assert pending
    page.locator("#tab-history").click()
    page.once("dialog", lambda d: d.accept())
    page.locator("#decision-history .history-visibility").click()
    expect(page.locator("#decision-history .history-row")).to_have_count(0)
    # A response captured before deletion cannot resurrect a displayed comparison.
    for route in pending:
        app.fulfill(
            route,
            {
                "same_snapshot": True,
                "q_analysis": record,
                "e_narrative": {**e, "snapshot_hash": record["snapshot_hash"]},
            },
        )
    expect(page.locator("#q-e-result")).to_be_empty()
    page.locator("#e-history-deleted").check()
    expect(page.locator("#latest-decision")).to_be_disabled()
    page.locator("#decision-history .history-visibility").click()
    expect(page.locator("#decision-history .history-row")).to_have_count(0)
    page.locator("#e-history-deleted").uncheck()
    expect(page.locator(f'[data-narrative-result-id="{e_id}"]')).to_be_enabled()
    assert len(writes) == 4 and not app.posts and app.errors == []
    app.close()


def assert_confirmation(message):
    assert "US.AVGO" in message and "Q 分析" in message and "2026-" in message
    assert "可恢复" in message and "原始证据仍保留" in message


def test_name_refresh_chinese_html_text_and_switch(browser, workbench_server):
    app = Workbench(browser, workbench_server, legacy_history=False)
    page = app.open()
    page.locator(f'[data-security-id="{HK}"]').click()
    current = page.evaluate("selectedSecurity")
    updated = {**current, "display_name": '中文长名称 <img src=x onerror="window.nameAttack=1">'}
    calls = []

    def refresh(route):
        calls.append(route.request.method)
        app.fulfill(route, updated)

    page.route("**/refresh-name", refresh)
    page.locator("#refresh-security-name").click()
    expect(page.locator("#selected-name")).to_have_text(updated["display_name"])
    expect(page.locator("#q-security")).to_contain_text(updated["display_name"])
    expect(page.locator("#analysis-security")).to_contain_text(updated["display_name"])
    assert page.locator("#selected-name img").count() == 0
    assert page.evaluate("window.nameAttack") is None
    assert page.evaluate("selectedSecurity.id") == HK and calls == ["POST"]
    assert app.errors == []
    app.close()


def test_summary_states_stage_a_retained_and_no_false_failure(browser, workbench_server):
    app = Workbench(browser, workbench_server, legacy_history=False)
    q = display_record()
    p = q["payload"]
    p.update(qualification_mode="OBSERVATIONAL", strict_historical_as_of=False)
    a = copy.deepcopy(p["setup"]["facts"][0])
    p["setup"]["facts"] = [
        a,
        {
            **a,
            "status": "NO_TRADE",
            "fact_key": "missing-open",
            "effective_at": "2026-09-23T10:30:00Z",
            "reference_price": None,
            "risk_reference_price": None,
            "target1": None,
            "rr_t1": None,
            "reasons": ["ENTRY_REFERENCE_UNAVAILABLE_AT_OPEN"],
        },
    ]
    p["diagnostics"] = ["INDEPENDENT_M30_OPEN_REFERENCE_MISSING"]
    p["setup"]["reasons"] = ["D1_ATR_UNAVAILABLE"]
    for tf in ("W1", "D1", "M30"):
        p["context"][tf]["evidence"]["frames"] = [
            {"index": 0, "atr": None},
            {"index": 1, "atr": "2.123456789", "base_regime": "RANGE"},
        ]
    install(app, q)
    page = app.open()
    choose(app)
    expect(page.locator("#q-result .q-headline")).to_have_text("确认评估已保留，开盘证据尚未接入")
    expect(page.locator("#q-result")).to_contain_text("100.12")
    expect(page.locator("#q-result")).to_contain_text("93.12")
    expect(page.locator("#q-result")).to_contain_text("115.12")
    expect(page.locator("#q-result")).to_contain_text("独立开盘证据缺失，尚不能验证下一开盘资格")
    assert "规则未满足" not in page.locator("#q-result").inner_text()
    assert "日线 ATR 尚不可用" not in page.locator("#q-result").inner_text()
    assert page.locator('#q-result [title="精确原值：100.123456789012345678"]').count() == 1
    page.screenshot(path=str(SHOTS / "after-stage-a-synthetic.png"), full_page=True)
    page.locator(
        '#q-result [title="精确原值：100.123456789012345678"]'
    ).scroll_into_view_if_needed()
    page.screenshot(path=str(SHOTS / "after-stage-a-prices-synthetic.png"))
    variants = {}
    for name, status in [
        ("waiting", "FOLLOW_THROUGH_PENDING"),
        ("expired", "EXPIRED"),
        ("none", "FOLLOW_THROUGH_NONE"),
        ("poor", "VALID_SETUP_BUT_POOR_ENTRY"),
        ("qualified", "OBSERVATIONAL_LONG_QUALIFIED"),
    ]:
        sample = copy.deepcopy(q)
        sample["payload"]["setup"]["facts"] = [{**a, "status": status, "reasons": []}]
        variants[name] = page.evaluate("r => PaqsQView.headline(r)", sample)
    assert len(set(variants.values())) == len(variants)
    sample = display_record("insufficient")
    assert "证据不足" in page.evaluate("r => PaqsQView.headline(r)", sample)
    assert (
        "未获正式入场资格" in page.evaluate("r => PaqsQView.summary(r).textContent", q)
        or "不能据此获得正式入场资格" in page.locator("#q-result").inner_text()
    )
    assert app.errors == [] and not app.posts
    app.close()
