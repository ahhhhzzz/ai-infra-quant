from __future__ import annotations

import pytest
from playwright.sync_api import Browser, expect

from .test_paqs_e_narrative import make_app, select
from .workbench_support import MODEL


@pytest.mark.parametrize("stage", ["SEARCH", "SYNTHESIS", "unsafe"])
def test_explicit_research_cost_and_bounded_failure_detail_preserve_narrative(
    browser: Browser, workbench_server: str, stage: str
) -> None:
    app = make_app(browser, workbench_server)
    page = app.open()
    expect(page.locator("#web-research")).not_to_be_checked()
    disclosure = page.locator("#research-status").text_content() or ""
    assert all(
        value in disclosure for value in ["默认关闭", "最多 2 次", "最终分析前", "耗时", "API 成本"]
    )
    assert all(value not in disclosure for value in ["web_search_call", "Responses", "pass-back"])
    select(app)
    before = page.locator(".narrative-text").text_content()
    page.locator("#model-id").select_option(MODEL)
    expect(page.locator("#web-research")).not_to_be_checked()
    page.locator("#web-research").check()
    assert app.posts == []
    diagnostic = {
        "detail_version": "paqs-e-research-diagnostic-v1",
        "stage": stage,
        "failure_class": "INVALID_RESPONSE",
        "web_search_call_count": 11,
        "search_action_count": 4,
        "message_count": 0,
        "research_http_request_count": 2 if stage == "SYNTHESIS" else 1,
        "raw_body": "synthetic-private-provider-body",
        "reasoning": "synthetic-hidden-reasoning",
        "provider_response_id": "synthetic-do-not-render-id",
    }
    app.post_status = 422
    app.post_body = dict(
        status=422,
        code="PAQS_E_RESEARCH_PRECONDITION_FAILED",
        detail="synthetic-private-provider-body",
        research_diagnostic=diagnostic,
    )
    page.locator("#analyze-button").click()
    expect(page.locator("#analysis-state")).to_contain_text("联网研究未完成")
    expect(page.locator("#decision-heading")).to_contain_text("较早成功结果")
    rendered = page.locator("#analysis-state").text_content() or ""
    if stage != "unsafe":
        assert f"{stage} / INVALID_RESPONSE" in rendered
        assert all(value in rendered for value in ["研究动作 11", "搜索 4", "消息 0"])
    else:
        assert "研究诊断" not in rendered
    assert all(
        value not in rendered
        for value in ["raw_body", "synthetic-", "research_diagnostic", "{", "}"]
    )
    assert page.locator(".narrative-text").text_content() == before
    page.get_by_role("button", name="原文", exact=True).click()
    assert page.locator(".narrative-text").text_content() == before
    page.get_by_role("button", name="格式化", exact=True).click()
    assert len(app.posts) == 1 and app.posts[0]["web_research"] is True
    assert app.errors == []
    app.close()
