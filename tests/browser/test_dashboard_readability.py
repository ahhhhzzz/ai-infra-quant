"""Presentation fixtures only: intercepted HTTP, no market/model calls or user DB writes."""

# ruff: noqa: RUF001 -- Exact Chinese UI punctuation.
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Browser, Route, expect

from .test_paqs_q_workbench import E_ID, PROSE, Q_HASH, Q_ID, q_record
from .workbench_support import HK, US, Workbench, narrative_pair

SHOTS = Path(__file__).resolve().parents[2] / "data/dashboard-ui-review"


def display_record(kind: str = "ready") -> dict[str, Any]:
    """Explicit synthetic view-contract data, not a natural market LONG_READY."""
    record = cast(dict[str, Any], q_record())
    p = record["payload"]
    p["market_snapshot"] = json.loads(narrative_pair()[1]["request_payload_json"])[
        "market_snapshot"
    ]
    p["market_snapshot"]["snapshot_hash"] = Q_HASH
    p["market_snapshot"]["as_of_timestamp"] = record["created_at"]
    p["market_snapshot"]["data_quality"] = "COMPLETE" if kind == "ready" else "PARTIAL"
    p["market_snapshot"]["security"]["display_symbol"] = "US.AVGO · 合成展示样本"
    p["market_snapshot"]["warnings"] = ["仅供展示验收；不代表真实行情结论。"]
    p.update(qualification_mode="AS_OF", strict_historical_as_of=True)
    p["diagnostics"] = []
    p["evidence_guidance"] = []
    for layer in ("context", "event"):
        p[layer] = {
            tf: {"status": "AVAILABLE", "reason_codes": [], "records": [], "evidence": {}}
            for tf in ("W1", "D1", "M30")
        }
    a = {
        "setup_key": "setup-1",
        "candidate_key": "candidate-1",
        "fact_key": "stage-a-1",
        "family": "TREND_PULLBACK_LONG",
        "status": "ENTRY_PENDING_REVALIDATION",
        "effective_at": "2026-09-23T10:00:00Z",
        "anchor_price": "94",
        "reference_price": "100.123456789012345678",
        "risk_reference_price": "93.123456789012345678",
        "target1": {"effective_price": "115.123456789012345678"},
        "rr_t1": "2.142857142857142857",
        "reasons": ["ALL_ENTRY_GATES_PASS"],
    }
    b = {
        **a,
        "fact_key": "stage-b-1",
        "status": "LONG_READY",
        "effective_at": "2026-09-23T10:30:00Z",
        "entry_reference_price_at": "2026-09-23T10:30:00Z",
    }
    p["setup"] = {
        "status": "AVAILABLE",
        "strict_confirmation": True,
        "reasons": [],
        "facts": [a, b],
    }
    p["holder"] = {
        "status": "UNDETERMINED",
        "items": [],
        "reasons": ["POST_TARGET_COMPLETE_M30_EVIDENCE_MISSING"],
    }
    record["status"] = "AVAILABLE"
    if kind == "insufficient":
        record["status"] = "INSUFFICIENT"
        p.update(qualification_mode="OBSERVATIONAL", strict_historical_as_of=False)
        p["setup"] = {
            "status": "INSUFFICIENT",
            "reasons": ["W1_INPUT_MISSING", "M30_COVERAGE_INCOMPLETE"],
            "facts": [],
        }
        p["diagnostics"] = [
            "HISTORICAL_PRICE_AVAILABILITY_UNKNOWN",
            "INDEPENDENT_M30_OPEN_REFERENCE_MISSING",
            "CLOSED_DAY_FACTS_UNAVAILABLE",
        ]
    if kind == "no_trade":
        p["setup"]["facts"] = [{**b, "status": "NO_TRADE", "reasons": ["RR_T1_BELOW_2"]}]
    return record


def install(
    app: Workbench, record: dict[str, Any], *, empty: bool = False
) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []

    def route_q(route: Route) -> None:
        path = urlparse(route.request.url).path
        calls.append((route.request.method, path))
        if route.request.method == "POST":
            return app.fulfill(route, {"detail": "合成请求失败，未保存新分析"}, 503)
        if "/securities/" in path:
            items = (
                [] if empty or HK in path else [{k: v for k, v in record.items() if k != "payload"}]
            )
            return app.fulfill(route, {"items": items})
        if "/compare/" in path:
            return app.fulfill(
                route,
                {
                    "same_snapshot": True,
                    "q_analysis": record,
                    "e_narrative": {
                        "narrative_result_id": E_ID,
                        "snapshot_hash": Q_HASH,
                        "response_text": PROSE,
                        "model_id": "synthetic-model",
                        "strategy_id": "fixture",
                        "web_research": False,
                    },
                },
            )
        return app.fulfill(route, record)

    app.page.route("**/api/v1/paqs-q/**", route_q)
    result, _ = narrative_pair()
    result.update(narrative_result_id=E_ID, snapshot_hash=Q_HASH)
    app.narratives[E_ID] = result
    app.narrative_history_ids = [E_ID]
    return calls


def choose(app: Workbench) -> None:
    app.page.locator("#tab-history").click()
    app.page.locator(f'[data-q-analysis-id="{Q_ID}"]').click()
    expect(app.page.locator("#q-result .q-headline")).to_be_visible()
    expect(app.page.locator("#tab-details")).to_have_attribute("aria-selected", "true")
    # Clicking a bottom tab must not leave the top summary outside the viewport.


@pytest.mark.parametrize(
    "width,height,kind",
    [
        (1920, 1080, "ready"),
        (1920, 1080, "insufficient"),
        (1366, 768, "ready"),
        (1366, 768, "insufficient"),
        (390, 844, "insufficient"),
    ],
)
def test_readable_first_screen_and_passive_history(
    browser: Browser,
    workbench_server: str,
    width: int,
    height: int,
    kind: str,
) -> None:
    app = Workbench(browser, workbench_server, width=width, height=height, legacy_history=False)
    calls = install(app, display_record(kind))
    page = app.open()
    choose(app)
    title = "符合入场规则" if kind == "ready" else "证据不足，暂无法判断"
    expect(page.locator("#q-result .q-headline")).to_have_text(title)
    assert page.locator("#q-result .q-headline").evaluate(
        "n => n.getBoundingClientRect().bottom < innerHeight"
    )
    assert page.locator("#q-basis pre:visible").count() == 0
    assert page.locator("#q-result pre").count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if width > 1150:
        box = page.locator("#chart-stage").bounding_box()
        assert box is not None and box["width"] > 700
    if kind == "ready":
        expect(page.locator("#q-result")).to_contain_text("不代表已成交")
    else:
        expect(page.locator("#q-result")).to_contain_text("这不表示看空")
    SHOTS.mkdir(exist_ok=True)
    page.screenshot(path=str(SHOTS / f"workbench-{width}x{height}-{kind}.png"))
    if width == 1920:
        page.locator("#theme-toggle").click()
        page.screenshot(path=str(SHOTS / "workbench-1920-light.png"))
    before = copy.deepcopy(calls)
    page.locator("#tab-history").click()
    history_box = page.locator("#q-history").bounding_box()
    assert history_box is not None and history_box["height"] < 160
    page.locator("#tab-compare").click()
    expect(page.locator("#q-e-read")).to_be_enabled()
    page.locator("#q-e-read").click()
    expect(page.locator("#q-e-status")).to_contain_text("快照身份一致")
    assert page.locator("#q-e-result .narrative-text").text_content() == PROSE
    assert page.evaluate("window.qAttack") is None
    page.locator("#refresh-market").click()
    page.reload()
    expect(page.locator("#q-result")).to_contain_text("尚未选择分析结果")
    assert before and all(method == "GET" for method, _ in calls)
    assert app.posts == [] and app.errors == []
    app.close()


def test_candidate_geometry_stages_limits_and_unknown_codes(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server, legacy_history=False)
    record = display_record()
    first = record["payload"]["setup"]["facts"][0]
    other = {
        **first,
        "candidate_key": "candidate-2",
        "fact_key": "stage-a-2",
        "reference_price": "202",
        "target1": {"effective_price": "250"},
        "risk_reference_price": None,
        "rr_t1": None,
    }
    record["payload"]["setup"]["facts"] += [
        other,
        {
            **other,
            "fact_key": "bad-stage-b",
            "status": "NO_TRADE",
            "reference_price": "203",
            "target1": {"effective_price": "999"},
            "effective_at": "2026-09-23T11:00:00Z",
            "entry_reference_price_at": None,
            "reasons": ["UNRECOGNIZED_TEST_REASON", "ENTRY_REFERENCE_UNAVAILABLE_AT_OPEN"],
        },
    ]
    record["payload"]["diagnostics"] = ["CLOSED_DAY_FACTS_UNAVAILABLE"]
    install(app, record)
    page = app.open()
    choose(app)
    root = page.locator('#q-basis [data-candidate-key="candidate-2"]')
    expect(root).to_contain_text("202")
    expect(root).to_contain_text("250")
    expect(root).to_contain_text("下一常规 M30 开盘验证")
    # Invalid new geometry remains only in folded exact audit, never a valid displayed target.
    assert "999" not in root.inner_text()
    assert "115.123456789012345678" not in root.inner_text()
    expect(root).to_contain_text("未识别的原因：UNRECOGNIZED_TEST_REASON")
    expect(root).to_contain_text("开盘时尚无可用的独立价格证据")
    assert "尚无此候选的下一开盘验证事实" not in root.inner_text()
    expect(root).to_contain_text("未形成 / 无法评估")
    # An independent limitation cannot be promoted to the headline's direct reason.
    assert "缺少闭市日期的事实" not in page.locator("#q-result").inner_text()
    expect(page.locator("#q-basis")).to_contain_text("以下为输入限制与诊断集合")
    page.evaluate(
        "Object.defineProperty(navigator, 'clipboard', {value: "
        "{writeText: async text => {window.copiedQ = text;}}})"
    )
    audit = page.locator("#q-basis .q-technical").filter(
        has=page.get_by_text("技术详情 · 原始枚举、身份、manifest、输入及完整 JSON", exact=True)
    )
    audit.locator("summary").click()
    audit.locator("button").click()
    assert page.evaluate("JSON.parse(window.copiedQ)") == record
    # A terminal Setup fact overrides the historical candidate's ready status.
    record["payload"]["setup"]["facts"].append(
        {
            **first,
            "candidate_key": None,
            "status": "INVALIDATED",
            "effective_at": "2026-09-23T12:00:00Z",
        }
    )
    assert page.evaluate("r => PaqsQView.headline(r)", record) == "规则未满足，尚无入场资格"
    record["payload"]["setup"]["facts"].pop()
    record["payload"]["qualification_mode"] = "OBSERVATIONAL"
    assert "未认证" in page.evaluate("r => PaqsQView.headline(r)", record)
    assert app.errors == []
    app.close()


def test_empty_failure_and_late_history_never_cross_security(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server, legacy_history=False)
    record = display_record("no_trade")
    calls = install(app, record)
    pending: list[Route] = []
    app.page.route("**/paqs-q/analyses/" + Q_ID, lambda route: pending.append(route))
    page = app.open()
    page.locator("#tab-history").click()
    page.locator("#q-history .history-row").click()
    page.locator(f'[data-security-id="{HK}"]').click()
    expect(page.locator("#q-security")).to_contain_text("HK.")
    for route in pending:
        app.fulfill(route, record)
    expect(page.locator("#q-result")).to_contain_text("尚未选择分析结果")
    expect(page.locator("#q-history-status")).to_contain_text("尚无 Q 历史")
    page.locator("#q-analyze").click()
    expect(page.locator("#q-status")).to_contain_text("请求失败")
    expect(page.locator("#q-status")).to_have_attribute("data-error", "true")
    expect(page.locator("#q-analyze")).to_be_enabled()
    assert sum(method == "POST" for method, _ in calls) == 1
    page.screenshot(path=str(SHOTS / "workbench-request-failure.png"))
    page.unroute("**/paqs-q/analyses/" + Q_ID)
    page.locator(f'[data-security-id="{US}"]').click()
    choose(app)
    expect(page.locator("#q-result .q-headline")).to_have_text("规则未满足，尚无入场资格")
    assert app.errors == [] and not app.posts
    app.close()


def test_existing_e_narrative_and_chart_controls_still_read_only(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server, legacy_history=False)
    e, run = narrative_pair(prose=PROSE)
    app.narratives[e["narrative_result_id"]] = e
    app.narrative_runs[run["narrative_run_id"]] = run
    app.narrative_history_ids = [e["narrative_result_id"]]
    page = app.open()
    page.locator("#branch-e").click()
    expect(page.locator("#analyze-button")).to_be_enabled()
    page.locator("#tab-history").click()
    page.locator("#decision-history .history-row").click()
    expect(page.locator("#decision-result .narrative-text")).to_have_text(PROSE)
    expect(page.locator("#evidence-status")).to_contain_text("冻结 W1")
    for frame in ("M30", "D1", "W1"):
        page.locator(f'[data-evidence-frame="{frame}"]').click()
        expect(page.locator("#evidence-status")).to_contain_text(f"冻结 {frame}")
    page.locator("#mode-current").click()
    page.locator("#tab-minute").click()
    page.locator("#refresh-market").click()
    page.locator("#mode-frozen").click()
    assert page.locator("#decision-result .narrative-text").text_content() == PROSE
    assert all(method == "GET" for method, _ in app.requests)
    assert not app.errors and not app.posts
    app.close()


def test_replay_diagnostic_is_not_current_missing_data(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server, legacy_history=False)
    record = display_record()
    p = record["payload"]
    p["setup"]["reasons"] = ["D1_ATR_UNAVAILABLE"]
    p["diagnostics"] = ["D1_ATR_UNAVAILABLE"]
    p["evidence_guidance"] = [{"code": "D1_ATR_UNAVAILABLE", "action": "历史集合"}]
    p["context"]["D1"]["evidence"]["frames"] = [
        {"index": 0, "atr": None},
        {"index": 1, "atr": "11.58133628411984225", "base_regime": "BEAR_TREND"},
    ]
    p["q_inputs"] = {"D1": {"payload": {"bars": [
        {"completed_at": "2024-09-25T20:00:00Z"},
        {"completed_at": "2026-09-23T20:00:00Z"},
    ]}}}
    # This diagnostic predates discovery; no candidate carries it.
    base = p["setup"]["facts"][0]
    p["setup"]["facts"] = [
        {**base, "candidate_key": None, "status": "CREATED", "reasons": ["FROZEN_SETUP_SOURCE"]},
        {**base, "candidate_key": None, "fact_key": "terminal", "status": "EXPIRED",
         "effective_at": "2026-09-23T11:00:00Z", "reasons": ["SETUP_D1_CLOCK_EXPIRED"]},
    ]
    original = copy.deepcopy(record)
    calls = install(app, record)
    page = app.open()
    choose(app)
    summary = page.locator("#q-result")
    assert "日线 ATR 尚不可用" not in summary.inner_text()
    expect(summary).to_contain_text("本记录各模块未报告输入阻断")
    expect(summary).to_contain_text("没有未结束的入场候选")
    expect(summary).to_contain_text("1 个已失效或过期")
    expect(page.locator("#q-basis")).to_contain_text("11.581336")
    diagnostics = page.locator(".q-run-diagnostics")
    diagnostics.locator(":scope > summary").click()
    expect(diagnostics).to_contain_text("未保存候选、阶段或发生时间关联")
    expect(diagnostics).to_contain_text("日线 ATR 尚不可用")
    expect(diagnostics).to_contain_text("2024/09/26 04:00 UTC+8")
    history = page.locator('.q-setup-history[data-setup-key="setup-1"]')
    history.locator("summary").click()
    terminal = history.locator('section[data-fact-key="terminal"]')
    expect(terminal).to_contain_text("2026/09/23 19:00 UTC+8")
    expect(terminal).to_contain_text("形态的日线有效窗口已结束")
    # Projection never rewrites the frozen payload; history causes GETs only.
    assert record == original
    assert all(method == "GET" for method, _ in calls) and not app.posts
    # The same code remains visible when the latest frame really lacks ATR.
    current_missing = copy.deepcopy(record)
    current_missing["payload"]["context"]["D1"]["evidence"]["frames"][-1]["atr"] = None
    current_text = page.evaluate("r => PaqsQView.summary(r).textContent", current_missing)
    assert "日线最新完成行情 · ATR 字段未形成" in current_text
    assert "日线 ATR 尚不可用" in current_text
    assert not app.errors
    app.close()


def test_candidate_reason_keeps_its_own_stage_time_and_identity(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server, legacy_history=False)
    record = display_record()
    facts = record["payload"]["setup"]["facts"]
    old = {**facts[0], "fact_key": "early-failure", "status": "NO_TRADE",
           "effective_at": "2026-09-23T09:00:00Z", "reasons": ["D1_ATR_UNAVAILABLE"]}
    current = {**facts[1], "status": "NO_TRADE", "reasons": ["RR_T1_BELOW_2"]}
    record["payload"]["setup"]["facts"] = [old, facts[0], current]
    install(app, record)
    page = app.open()
    choose(app)
    summary = page.locator('#q-result [data-candidate-key="candidate-1"]')
    detail = page.locator('#q-basis [data-candidate-key="candidate-1"]')
    for root in (summary, detail):
        label = root.locator(":scope > [data-fact-key]")
        expect(label).to_have_attribute("data-fact-key", current["fact_key"])
        expect(label).to_have_attribute("data-effective-at", current["effective_at"])
        expect(label).to_contain_text("Stage B")
        expect(root).to_contain_text("第一目标盈亏比低于规则要求")
    assert "日线 ATR 尚不可用" not in summary.inner_text()
    history = detail.locator(".q-candidate-history")
    history.locator("summary").click()
    early = history.locator('section[data-fact-key="early-failure"]')
    expect(early).to_contain_text("日线 ATR 尚不可用")
    expect(early).to_contain_text("2026/09/23 17:00 UTC+8")
    expect(early).to_contain_text("阶段以原始记录为准")
    assert not app.errors and not app.posts
    app.close()
