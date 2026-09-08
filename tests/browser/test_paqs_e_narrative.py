from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Browser, expect

from .workbench_support import HK, MODEL_NAME, US, Workbench, narrative_pair

PROSE = (
    "  # 模型生成的最终分析\n"
    "<script>window.attack=1</script>\n"
    '<img src=x onerror="window.attack=2">\n'
    "[链接](javascript:alert(1))\n"
    "Context → Structure → Location\n"
    "Trigger 与 Followthrough 分开;没有持仓事实。{不是结构化字段}\n"
)


def make_app(browser: Browser, address: str, **kwargs: Any) -> Workbench:
    app = Workbench(browser, address, legacy_history=False, **kwargs)
    for revision, market in [(1, "US"), (2, "US"), (3, "HK")]:
        result, run = narrative_pair(revision, market=market, prose=PROSE + str(revision))
        app.narratives[result["narrative_result_id"]] = result
        app.narrative_runs[run["narrative_run_id"]] = run
    app.narrative_history_ids = list(app.narratives)
    return app


def select(app: Workbench, revision: int = 1) -> None:
    app.page.locator(
        f'[data-narrative-result-id="20000000-0000-4000-8000-{revision:012d}"]'
    ).click()
    expect(app.page.locator("#evidence-status")).to_contain_text("冻结 W1")


@pytest.mark.parametrize("width,light", [(1440, False), (900, True), (390, False), (390, True)])
def test_primary_narrative_is_exact_inert_multiline_and_frozen_across_refresh(
    browser: Browser,
    workbench_server: str,
    width: int,
    light: bool,
    tmp_path: Path,
) -> None:
    app = make_app(browser, workbench_server, width=width)
    page = app.open()
    expect(page.locator("#decision-history .history-row")).to_have_count(2)
    assert not page.locator("#legacy-history-section").evaluate("(item) => item.open")
    select(app)
    expected = app.narratives["20000000-0000-4000-8000-000000000001"]["response_text"]
    assert page.locator(".narrative-text").text_content() == expected
    assert (
        page.locator(".narrative-text").evaluate("(item) => getComputedStyle(item).whiteSpace")
        == "pre-wrap"
    )
    assert (
        page.locator("#decision-result script, #decision-result img, #decision-result a").count()
        == 0
    )
    assert page.evaluate("window.attack") is None
    expect(page.locator("#decision-heading")).to_contain_text("Narrative")
    expect(page.locator("#decision-heading")).to_contain_text(MODEL_NAME)
    before = page.locator("#evidence-facts").text_content()
    chart = page.evaluate("window.chartCaptures[0].series")
    assert len(chart[0]["bars"]) == 80 and page.evaluate("window.chartCaptures[0].lines") == []
    page.locator("#mode-current").click()
    app.state_price = "999.123456789012345678"
    page.locator("#refresh-market").click()
    page.locator("#mode-frozen").click()
    assert page.locator("#evidence-facts").text_content() == before
    assert page.locator(".narrative-text").text_content() == expected
    for frame in ("D1", "M30", "W1"):
        page.locator(f'[data-evidence-frame="{frame}"]').click()
        expect(page.locator("#evidence-status")).to_contain_text(f"冻结 {frame}")
    if light:
        page.locator("#theme-toggle").click()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(tmp_path / f"narrative-{width}-{light}.png"), full_page=True)
    page.locator("#legacy-history-section > summary").click()
    app.select(1)
    expect(page.locator("#decision-heading")).to_contain_text("Legacy 结构化历史")
    assert page.locator(".narrative-text").count() == 0
    assert app.posts == [] and app.errors == []
    app.close()


@pytest.mark.parametrize("kind", ["history", "result", "evidence"])
def test_narrative_read_races_never_overwrite_new_selection(
    browser: Browser, workbench_server: str, kind: str
) -> None:
    app = make_app(browser, workbench_server)
    page = app.open()
    if kind == "history":
        app.hold = f"securities/{US}/narrative-results"
        page.locator("#reload-history").click()
        app.hold = None
        page.locator(f'#security-selector [data-security-id="{HK}"]').click()
        expect(page.locator("#decision-history .history-row")).to_have_count(1)
    else:
        app.hold = (
            "narrative-results/20000000" if kind == "result" else "narrative-analyses/10000000"
        )
        page.locator('[data-narrative-result-id="20000000-0000-4000-8000-000000000001"]').click()
        page.wait_for_timeout(100)
        app.hold = None
        select(app, 2)
    before = page.locator("#decision-heading").text_content()
    for route in app.pending:
        app.respond(route)
    expect(page.locator("#decision-heading")).to_have_text(before or "")
    assert app.posts == [] and app.errors == []
    app.close()


@pytest.mark.parametrize("kind", ["provider", "research", "unknown"])
def test_failed_new_attempt_retains_prior_narrative_without_retry(
    browser: Browser, workbench_server: str, kind: str
) -> None:
    app = make_app(browser, workbench_server)
    page = app.open()
    select(app, 1)
    before = page.locator(".narrative-text").text_content()
    if kind == "provider":
        app.post_status = 502
        run = app.narrative_runs["10000000-0000-4000-8000-000000000002"]
        run.update(
            status="PROVIDER_FAILED", failure_kind="PROVIDER_REFUSAL", failure_reason="synthetic"
        )
        app.post_body = dict(
            status=502,
            analysis_status="PROVIDER_FAILED",
            failure_kind="PROVIDER_REFUSAL",
            narrative_run_id=run["narrative_run_id"],
        )
    elif kind == "research":
        app.post_status = 422
        app.post_body = dict(
            status=422, code="PAQS_E_RESEARCH_PRECONDITION_FAILED", detail="synthetic"
        )
    else:
        app.post_mode = "nonjson"
    app.analyze()
    expect(page.locator("#analysis-state")).to_contain_text(
        {"provider": "本次没有新 Narrative", "research": "分析前提失败", "unknown": "结果未知"}[
            kind
        ]
    )
    expect(page.locator("#decision-heading")).to_contain_text("较早成功结果")
    assert page.locator(".narrative-text").text_content() == before
    assert len(app.posts) == 1 and app.errors == []
    assert all("/narrative-analyses" in url for method, url in app.requests if method == "POST")
    app.close()


def test_explicit_narrative_success_and_frozen_research_are_not_prose_extraction(
    browser: Browser, workbench_server: str
) -> None:
    app = make_app(browser, workbench_server)
    result = app.narratives["20000000-0000-4000-8000-000000000002"]
    run = app.narrative_runs[result["narrative_run_id"]]
    capsule = json.loads(run["request_payload_json"])
    evidence = [
        {
            "context_id": "synthetic-source",
            "category": "web_research",
            "content": "source-specific context",
            "provenance": "https://example.org/frozen",
        }
    ]
    capsule.update(auxiliary_context=evidence, web_research=True)
    from ai_infra_quant.core.domain.paqs_e_ledger import payload_sha256
    from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json

    run.update(
        web_research=True,
        request_payload_json=canonical_json(capsule),
        request_payload_sha256=payload_sha256(canonical_json(capsule)),
    )
    result["web_research"] = True
    page = app.open()
    app.hold = "/paqs-e/narrative-analyses"
    app.analyze()
    page.clock.install()
    page.clock.run_for(180001)
    expect(page.locator("#analyze-button")).to_be_disabled()
    page.locator("#analyze-form").dispatch_event("submit")
    app.hold = None  # Only the already captured POST stays pending.
    select(app, 1)
    selected = page.locator(".narrative-text").text_content()
    app.hold = None
    app.respond(app.pending.pop())
    expect(page.locator("#analysis-state")).to_contain_text("已提交成功 Narrative")
    assert page.locator(".narrative-text").text_content() == selected
    select(app, 2)
    assert page.locator(".narrative-text").text_content() == result["response_text"]
    assert json.loads(page.locator("#research-evidence").text_content() or "") == evidence
    assert page.evaluate("window.chartCaptures[0].lines") == []
    assert len(app.posts) == 1 and app.errors == []
    app.close()
