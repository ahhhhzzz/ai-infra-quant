from __future__ import annotations

from typing import Any

import pytest
from playwright.sync_api import Browser, expect

from .test_paqs_e_narrative import make_app, select
from .workbench_support import MODEL


@pytest.mark.parametrize(
    "value", [6, None, True, -1, 1025, "private-query-text", {"raw": "private-body"}]
)
def test_optional_numeric_diagnostics_never_render_untrusted_data(
    browser: Browser, workbench_server: str, value: Any
) -> None:
    app = make_app(browser, workbench_server)
    page = app.open()
    expect(page.locator("#web-research")).not_to_be_checked()
    select(app)
    before = page.locator(".narrative-text").text_content()
    page.locator("#model-id").select_option(MODEL)
    expect(page.locator("#web-research")).not_to_be_checked()
    page.locator("#web-research").check()
    assert app.posts == []
    app.post_status = 422
    app.post_body = {
        "status": 422,
        "code": "PAQS_E_RESEARCH_PRECONDITION_FAILED",
        "detail": "private-body",
        "research_diagnostic": {
            "detail_version": "paqs-e-research-diagnostic-v1",
            "stage": "SEARCH",
            "failure_class": "INVALID_RESPONSE",
            "web_search_call_count": 20,
            "search_action_count": 6,
            "message_count": 0,
            "research_http_request_count": 1,
            "provider_exposed_query_count": value,
            "raw_source_record_count": 24,
            "unknown_action_count": 0,
            "queries": ["private-query-text"],
            "sources": [{"url": "https://private.example"}],
            "reasoning": "private-reasoning",
            "provider_response_id": "private-response-id",
        },
    }
    page.locator("#analyze-button").click()
    expect(page.locator("#analysis-state")).to_contain_text("来源记录 24")
    rendered = page.locator("#analysis-state").text_content() or ""
    assert ("查询 6" in rendered) is (type(value) is int and value == 6)
    assert "未知动作 0" in rendered and "搜索 6" in rendered
    assert all(v not in rendered for v in ["private-", "private.example", "{", "}"])
    expect(page.locator("#decision-heading")).to_contain_text("较早成功结果")
    assert page.locator(".narrative-text").text_content() == before
    page.get_by_role("button", name="原文", exact=True).click()
    assert page.locator(".narrative-text").text_content() == before
    page.get_by_role("button", name="格式化", exact=True).click()
    assert len(app.posts) == 1 and app.posts[0]["web_research"] is True
    assert app.errors == []
    app.close()
