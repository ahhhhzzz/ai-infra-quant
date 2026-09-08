from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import Browser, expect

from .workbench_support import HK, MODEL, MODEL_NAME, STRATEGY, US, Workbench, fixture_pair


def test_actual_uvicorn_unconfigured_http_and_static_smoke(
    workbench_server: str, browser: Browser
) -> None:
    with httpx.Client(base_url=workbench_server, trust_env=False) as client:
        for path in (
            "/health",
            "/openapi.json",
            "/",
            "/api/v1/paqs-e/configuration",
            "/static/app.js",
            "/static/paqs-e.js",
            "/static/app.css",
            "/static/vendor/lightweight-charts.standalone.production.js",
        ):
            assert client.get(path).status_code == 200
        configuration = client.get("/api/v1/paqs-e/configuration").json()
        assert all(not item["credential_configured"] for item in configuration["models"])
        assert configuration["default_strategy_id"] == STRATEGY
    context = browser.new_context()
    page = context.new_page()
    calls: list[str] = []
    page.on("request", lambda request: calls.append(request.method + " " + request.url))
    page.goto(workbench_server)
    expect(page.locator("#configuration-status")).to_contain_text("API Key")
    expect(page.locator("#analyze-button")).to_be_disabled()
    expect(page.locator("#model-id")).to_have_value("deepseek-v4-flash")
    assert not any(call.startswith("POST") for call in calls)
    context.close()


def test_all_non_explicit_actions_have_zero_analyze_posts(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    expect(page.locator("#model-id")).to_have_value("deepseek-v4-flash")
    page.locator("#model-id").select_option("qwen3.8-max")
    page.locator("#strategy-id").select_option("fixture-alternative")
    page.locator("#theme-toggle").click()
    page.locator("#tab-minute").click()
    page.locator("#tab-daily").click()
    page.locator("#refresh-market").click()
    page.locator(f'#security-selector [data-security-id="{HK}"]').click()
    page.locator(f'#security-selector [data-security-id="{US}"]').click()
    page.locator("#history-strategy").select_option(STRATEGY)
    expect(page.locator(".history-row")).to_have_count(2)
    app.select(1)
    for frame in ("D1", "M30", "W1"):
        page.locator(f'[data-evidence-frame="{frame}"]').click()
    page.locator("#reload-history").click()
    page.locator("#latest-decision").click()
    page.locator(".known-run > summary").click()
    page.locator("#known-run-id").fill("10000000-0000-4000-8000-000000000001")
    page.locator("#known-run-form button").click()
    expect(page.locator("#known-run-status")).to_contain_text("SUCCEEDED")
    page.clock.install()
    page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    expect(page.locator("#refresh-market")).to_be_enabled()
    page.clock.run_for(61000)
    page.evaluate("""() => {
      Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'hidden'});
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    count = len([url for _, url in app.requests if "/market-data/securities/" in url])
    page.clock.run_for(61000)
    assert len([url for _, url in app.requests if "/market-data/securities/" in url]) == count
    page.evaluate("""() => {
      Object.defineProperty(document, 'visibilityState', {
        configurable: true, get: () => 'visible'});
    }""")
    page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    expect(page.locator("#model-id")).to_have_value("qwen3.8-max")
    assert app.posts == []
    assert app.errors == []
    assert all(url.startswith(workbench_server) for _, url in app.requests)
    app.close()


def test_explicit_capture_double_enter_guard_and_security_switch(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    app.hold = "/paqs-e/narrative-analyses"
    app.analyze()
    page.locator("#analyze-form").dispatch_event("submit")
    page.locator("#model-id").press("Enter")
    page.locator(f'#security-selector [data-security-id="{HK}"]').click()
    page.locator("#model-id").select_option("glm-5.2")
    page.locator("#strategy-id").select_option("fixture-alternative")
    page.locator("#analyze-form").dispatch_event("submit")
    expect(page.locator("#analysis-state")).to_contain_text(f"US.AVGO · {MODEL_NAME} · {STRATEGY}")
    assert app.posts == [
        {"security_id": US, "model_key": MODEL, "strategy_id": STRATEGY, "web_research": True}
    ]
    app.hold = None
    app.respond(app.pending.pop())
    expect(page.locator("#analysis-state")).to_contain_text("当前已切换证券")
    expect(page.locator("#decision-heading")).to_have_text("尚无选中的分析结果")
    expect(page.locator("#model-id")).to_have_value("glm-5.2")
    assert app.posts == [
        {"security_id": US, "model_key": MODEL, "strategy_id": STRATEGY, "web_research": True}
    ]
    app.close()


def test_history_selection_survives_pending_analyze_and_refresh(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    app.hold = "/paqs-e/narrative-analyses"
    app.analyze()
    app.hold = None
    app.select(1)
    selected = page.locator("#decision-heading").inner_text()
    app.respond(app.pending.pop())
    expect(page.locator("#analysis-state")).to_contain_text("已提交成功 Narrative")
    expect(page.locator("#decision-heading")).to_have_text(selected)
    page.locator("#reload-history").click()
    expect(page.locator(".history-row")).to_have_count(2)
    expect(page.locator("#decision-heading")).to_have_text(selected)
    app.close()


@pytest.mark.parametrize("kind", ["history", "filter", "decision", "evidence"])
def test_out_of_order_reads_do_not_overwrite_selection(
    kind: str, browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    if kind in ("history", "filter"):
        app.hold = f"securities/{US}/decisions"
        page.locator("#reload-history").click()
        app.hold = None
        if kind == "filter":
            page.locator("#history-strategy").select_option("fixture-alternative")
            expect(page.locator("#history-status")).to_contain_text("暂无成功")
        else:
            page.locator(f'#security-selector [data-security-id="{HK}"]').click()
            expect(page.locator(".history-row")).to_have_count(1)
        for route in app.pending:
            app.respond(route)
        expect(page.locator(".history-row")).to_have_count(0 if kind == "filter" else 1)
    else:
        suffix = "decisions/20000000" if kind == "decision" else "analyses/10000000"
        app.hold = suffix
        page.locator('[data-decision-id="20000000-0000-4000-8000-000000000001"]').click()
        page.wait_for_timeout(100)
        app.hold = None
        app.select(2)
        heading = page.locator("#decision-heading").inner_text()
        for route in app.pending:
            app.respond(route)
        expect(page.locator("#decision-heading")).to_have_text(heading)
        expect(page.locator("#evidence-identity")).to_contain_text("修订 2")
    assert app.posts == []
    app.close()


@pytest.mark.parametrize(
    "kind",
    [
        "CONFIGURATION_ERROR",
        "PROVIDER_UNAVAILABLE",
        "PROVIDER_REFUSAL",
        "INVALID_FINAL_TEXT",
        "PROVIDER_INCOMPLETE",
        "404",
        "409",
        "422",
        "500",
        "nonjson",
        "abort",
        "mismatched",
        "long_wait_connection_failure",
    ],
)
def test_typed_failures_unknown_no_retry_and_prior_decision_retention(
    kind: str, browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    app.select(1)
    if kind in ("nonjson", "abort"):
        app.post_mode = kind
    elif kind == "mismatched":
        app.post_body = {
            **app.decisions["20000000-0000-4000-8000-000000000002"],
            "model_id": "wrong",
            "status": "SUCCEEDED",
        }
    elif kind == "long_wait_connection_failure":
        page.clock.install()
        app.hold = "/paqs-e/narrative-analyses"
    elif kind.isdigit():
        app.post_status = int(kind)
        app.post_body = {
            "status": int(kind),
            "code": "SYNTHETIC_PRECONDITION_OR_LEDGER_ERROR",
            "detail": "synthetic safe failure",
        }
    else:
        run = app.narrative_runs["10000000-0000-4000-8000-000000000002"]
        run.update(
            status="PROVIDER_FAILED", failure_kind=kind, failure_reason="synthetic provider failure"
        )
        app.post_status = 503 if kind in ("CONFIGURATION_ERROR", "PROVIDER_UNAVAILABLE") else 502
        app.post_body = {
            "status": app.post_status,
            "analysis_status": "PROVIDER_FAILED",
            "narrative_run_id": run["narrative_run_id"],
            "failure_kind": kind,
        }
    app.analyze()
    if kind == "long_wait_connection_failure":
        page.clock.run_for(180001)
        expect(page.locator("#analysis-state")).to_contain_text("仍在分析")
        expect(page.locator("#analyze-button")).to_be_disabled()
        assert len(app.posts) == 1
        app.pending.pop().abort("connectionfailed")
    expected = (
        "结果未知"
        if kind in ("nonjson", "abort", "mismatched", "long_wait_connection_failure")
        else "失败"
        if kind in ("404", "409", "422")
        else "账本证据"
        if kind == "500"
        else "本次没有新 Narrative"
    )
    expect(page.locator("#analysis-state")).to_contain_text(expected)
    expect(page.locator("#decision-heading")).to_contain_text("较早成功结果")
    expect(page.locator("#decision-heading")).to_contain_text("修订 1")
    expect(page.locator(".history-row")).to_have_count(2)
    expect(page.locator("#analyze-button")).to_be_enabled()
    assert len(app.posts) == 1
    if kind in (
        "CONFIGURATION_ERROR",
        "PROVIDER_UNAVAILABLE",
        "PROVIDER_REFUSAL",
        "INVALID_FINAL_TEXT",
        "PROVIDER_INCOMPLETE",
    ):
        expect(page.locator("#known-run-status")).to_contain_text(kind)
    app.close()


def test_frozen_capsule_only_refresh_decimal_and_prose_overlay_boundary(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    app.select(1)
    before = page.evaluate("JSON.stringify(chartCaptures[0].series.map(item => item.bars))")
    lines = page.evaluate("chartCaptures[0].lines.map(item => item.options.price)")
    assert len(lines) == 2  # Only invalidation/T1; prose zone never becomes a line.
    assert 3 not in lines and 100 not in lines
    expect(page.locator("#overlay-labels")).to_contain_text("88.123456789012345678")
    expect(page.locator("#overlay-labels")).to_contain_text("125.987654321098765432")
    app.state_price = "222.987654321098765432"
    page.locator("#refresh-market").click()
    expect(page.locator("#latest-price")).to_have_text(app.state_price)
    assert page.evaluate("JSON.stringify(chartCaptures[0].series.map(item => item.bars))") == before
    page.locator("#mode-current").click()
    assert page.evaluate("chartCaptures[0].lines.length") == 0
    page.locator("#mode-frozen").click()
    assert page.evaluate("chartCaptures[0].lines.length") == 2
    assert app.errors == []
    app.close()


@pytest.mark.parametrize(
    "damage",
    [
        "unavailable",
        "malformed",
        "security",
        "hash",
        "asof",
        "microsecond",
        "model",
        "strategy",
        "runid",
        "empty",
        "nonfinite",
        "nullvolume",
    ],
)
def test_bad_evidence_never_reuses_other_or_current_bars(
    damage: str, browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    app.select(1)
    run = app.runs["10000000-0000-4000-8000-000000000002"]
    if damage == "unavailable":
        app.run_mode = damage
    elif damage == "malformed":
        run["request_payload_json"] = "{"
    elif damage == "microsecond":
        run["snapshot_as_of_timestamp"] = "2026-09-04T12:00:00.000001Z"
    elif damage in ("security", "hash", "asof", "model", "strategy", "runid"):
        key = {
            "security": "security_id",
            "hash": "snapshot_hash",
            "asof": "snapshot_as_of_timestamp",
            "model": "model_id",
            "strategy": "strategy_id",
            "runid": "analysis_run_id",
        }[damage]
        run[key] = HK if damage in ("security", "runid") else "invalid"
    else:
        request = json.loads(run["request_payload_json"])
        bars = request["market_snapshot"]["w1_bars"]
        if damage == "empty":
            bars.clear()
        elif damage == "nonfinite":
            bars[0]["open"] = "9" * 400
        else:
            bars[0]["volume"] = None
        run["request_payload_json"] = json.dumps(request)
    page.locator('[data-decision-id="20000000-0000-4000-8000-000000000002"]').click()
    expect(page.locator("#decision-heading")).to_contain_text("修订 2")
    if damage == "nullvolume":
        expect(page.locator("#evidence-status")).to_contain_text("冻结 W1")
        assert page.evaluate("chartCaptures[0].series[1].bars.length") == 79
    elif damage == "empty":
        expect(page.locator("#evidence-empty")).to_contain_text("没有已完成")
        assert page.evaluate("chartCaptures[0].series[0].bars.length") == 0
    else:
        expect(page.locator("#evidence-status")).to_contain_text("不可用")
        assert page.evaluate("chartCaptures[0].series[0].bars.length") == 0
        assert page.evaluate("chartCaptures[0].lines.length") == 0
        expect(page.locator("#overlay-labels")).to_have_text("")
    assert app.posts == []
    app.close()


def test_market_timezones_dst_daily_date_and_completed_week_end(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    run = app.runs["10000000-0000-4000-8000-000000000001"]
    request = json.loads(run["request_payload_json"])
    bars = request["market_snapshot"]["m30_bars"][-2:]
    bars[0].update(interval_start="2026-03-06T14:30:00Z", interval_end="2026-03-06T15:00:00Z")
    bars[1].update(interval_start="2026-03-09T13:30:00Z", interval_end="2026-03-09T14:00:00Z")
    request["market_snapshot"]["m30_bars"] = bars
    run["request_payload_json"] = json.dumps(request)
    page = app.open()
    app.select(1)
    assert page.evaluate("chartCaptures[0].series[0].bars.length") == 80
    page.locator('[data-evidence-frame="D1"]').click()
    assert page.evaluate("chartCaptures[0].series[0].bars.at(-1).time") == "2026-09-03"
    page.locator('[data-evidence-frame="M30"]').click()
    facts = page.locator(".exact-bars").text_content() or ""
    assert facts.count("09:30:00") == 2
    assert "America/New_York" in facts
    page.locator(f'#security-selector [data-security-id="{HK}"]').click()
    app.select(3)
    page.locator('[data-evidence-frame="M30"]').click()
    assert "Asia/Hong_Kong" in (page.locator(".exact-bars").text_content() or "")
    assert "Pacific/Honolulu" not in page.locator("#evidence-status").inner_text()
    app.close()


def test_xss_strings_are_inert_and_exact_values_stay_text(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    attack = (
        '<img id="injected" src="https://invalid.example/x" onerror="window.injected=true">'
        "<script>window.injected=true</script>"
    )
    app.securities[0]["display_name"] = attack
    decision = app.decisions["20000000-0000-4000-8000-000000000001"]
    decision["result"]["one_line_thesis"] = attack
    decision["result"]["key_levels"][0]["price_or_zone"] = attack + " 123.456"
    # Adversarial presentation fixture: exact server-supplied financial strings must
    # remain text; the browser must not calculate or reinterpret RR semantics.
    decision["result"]["risk_reward"]["rr_t1"] = "1.234567890123456789"
    decision["rr_t1"] = "1.234567890123456789"
    decision["one_line_thesis"] = attack
    page = app.open()
    app.select(1)
    expect(page.locator(".thesis")).to_have_text(attack)
    assert page.locator("#injected").count() == 0
    assert page.evaluate("window.injected === undefined")
    assert all(url.startswith(workbench_server) for _, url in app.requests)
    page.locator(".result-group").filter(has_text="风险回报 · 服务端精确值").locator(
        "summary"
    ).click()
    expect(page.locator("#decision-result")).to_contain_text("1.234567890123456789")
    assert app.errors == []
    app.close()


def test_empty_watchlist_removal_add_error_and_current_viewport(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    page.evaluate("chart.timeScale().setVisibleLogicalRange({from: 10, to: 30})")
    page.wait_for_function("chart.timeScale().getVisibleLogicalRange().from === 10")
    before = page.evaluate("chart.timeScale().getVisibleLogicalRange()")
    page.locator("#refresh-market").click()
    expect(page.locator("#refresh-market")).to_be_enabled()
    assert page.evaluate("chart.timeScale().getVisibleLogicalRange()") == before
    assert any("daily-bars?limit=5" in url for _, url in app.requests)
    assert any("minute-bars?lookback_days=2" in url for _, url in app.requests)
    app.select(1)
    app.hold = "/paqs-e/narrative-analyses"
    app.analyze()
    page.locator("#remove-selected").click()
    expect(page.locator("#analysis-security")).to_contain_text("HK.00700")
    page.locator("#remove-selected").click()
    expect(page.locator("#analysis-security")).to_have_text("请选择证券")
    app.hold = None
    app.respond(app.pending.pop())
    expect(page.locator("#analyze-button")).to_be_disabled()
    expect(page.locator("#decision-heading")).to_have_text("尚无选中的分析结果")
    assert page.evaluate("chartCaptures[0].series[0].bars.length") == 0
    app.add_error = True
    page.locator('#supported-security-form [name="symbol"]').fill("700")
    page.locator("#supported-security-form button").click()
    expect(page.locator("#supported-security-result")).to_contain_text("NOT_ENTITLED")
    app.add_error = False
    page.locator("#supported-security-form button").click()
    expect(page.locator("#analysis-security")).to_contain_text("HK.00700")
    assert len(app.posts) == 1
    app.close()


def test_strategy_series_bounded_history_and_known_failed_lookup(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    decision, run = fixture_pair(4, strategy="fixture-alternative")
    decision["revision_no"] = 1
    decision["supersedes_decision_id"] = None
    app.add_pair(decision, run)
    app.history_ids.append(decision["decision_id"])
    page = app.open()
    expect(page.locator(".history-row")).to_have_count(3)
    page.locator("#history-strategy").select_option("fixture-alternative")
    expect(page.locator(".history-row")).to_have_count(1)
    expect(page.locator(".history-row")).to_contain_text("修订 1")
    assert not any("cursor" in url or "offset" in url for _, url in app.requests)
    assert app.posts == []
    app.close()


def test_configuration_get_failure_and_invalid_models_never_dispatch(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    app.page.route(
        "**/paqs-e/configuration",
        lambda route: app.fulfill(route, {"detail": "synthetic invalid registry"}, 503),
    )
    page = app.open()
    expect(page.locator("#configuration-status")).to_contain_text("配置不可用")
    expect(page.locator("#strategy-id option")).to_have_count(0)
    expect(page.locator("#analyze-button")).to_be_disabled()
    page.locator("#analyze-form").dispatch_event("submit")
    assert app.posts == []
    app.close()
    app = Workbench(browser, workbench_server)
    page = app.open()
    for value in ("bad model", " model", "model\u0085id", "model\u001fid"):
        page.locator("#model-id").evaluate(
            "(select, value) => { const option = new Option(value, value); "
            "select.add(option); select.value = value; }",
            value,
        )
        page.locator("#analyze-form").dispatch_event("submit")
        expect(page.locator("#model-id")).to_have_value(value)
        expect(page.locator("#analysis-state")).to_contain_text("无法提交")
    assert app.posts == []
    app.close()


def test_changed_form_does_not_relabel_captured_success(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    app.hold = "/paqs-e/narrative-analyses"
    app.analyze()
    page.locator("#model-id").select_option("kimi-k3")
    page.locator("#strategy-id").select_option("fixture-alternative")
    app.hold = None
    app.respond(app.pending.pop())
    expect(page.locator("#decision-heading")).to_contain_text(MODEL_NAME)
    expect(page.locator("#decision-heading")).not_to_contain_text("kimi-k3")
    expect(page.locator("#model-id")).to_have_value("kimi-k3")
    assert len(app.posts) == 1
    app.close()


@pytest.mark.parametrize(
    "width,height,scenario,light",
    [
        (1440, 900, "unconfigured", False),
        (900, 900, "success", True),
        (1440, 900, "success", False),
        (1440, 900, "historical", True),
        (900, 900, "unknown", False),
        (390, 844, "success", True),
    ],
)
def test_visual_acceptance_artifacts(
    width: int,
    height: int,
    scenario: str,
    light: bool,
    browser: Browser,
    workbench_server: str,
    tmp_path: Path,
) -> None:
    output = Path(os.environ.get("TASK007C_SCREENSHOT_DIR", str(tmp_path)))
    output.mkdir(parents=True, exist_ok=True)
    app = Workbench(
        browser, workbench_server, width=width, height=height, configured=scenario != "unconfigured"
    )
    page = app.open()
    if scenario == "historical":
        app.select(1)
    elif scenario in ("success", "unknown"):
        app.analyze()
        expect(page.locator("#analysis-state")).to_contain_text("已提交成功 Narrative")
        expect(page.locator("#evidence-status")).to_contain_text("冻结 W1")
        if scenario == "unknown":
            app.post_mode = "nonjson"
            app.analyze()
            expect(page.locator("#analysis-state")).to_contain_text("结果未知")
    if light:
        page.locator("#theme-toggle").click()
    page.evaluate("window.scrollTo(0, 0)")
    expect(page.locator("#service-health")).to_contain_text("本地服务正常")
    page.wait_for_timeout(200)
    overflowing = page.evaluate("""() => [...document.querySelectorAll('body *')]
      .filter(item => item.getBoundingClientRect().right > innerWidth + 1)
      .map(item => ({tag: item.tagName, id: item.id,
        width: item.getBoundingClientRect().width}))""")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), overflowing
    assert app.errors == []
    filename = f"{width}x{height}-{scenario}-{'light' if light else 'dark'}.png"
    for control in (
        "#analyze-button",
        "#analysis-security",
        "#analysis-state",
        "#mode-frozen",
        "#latest-quote-at",
    ):
        bounds = page.locator(control).bounding_box()
        assert bounds is not None and bounds["y"] < height, (control, bounds)
    page.screenshot(path=str(output / filename.replace(".png", "-viewport.png")))
    page.screenshot(path=str(output / filename), full_page=True)
    (output / filename.replace(".png", ".json")).write_text(
        json.dumps(
            {
                "viewport": [width, height],
                "scenario": scenario,
                "theme": "light" if light else "dark",
                "source": "actual Uvicorn with synthetic API fixtures; not real market evidence",
                "screenshot": filename,
                "horizontal_overflow": False,
                "page_errors": app.errors,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    app.close()
