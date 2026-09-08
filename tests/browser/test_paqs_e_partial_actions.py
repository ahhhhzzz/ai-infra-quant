from __future__ import annotations

from typing import Any

import pytest
from playwright.sync_api import Browser, expect

from .test_paqs_e_narrative import make_app, select
from .workbench_support import MODEL


@pytest.mark.parametrize(
    "value,code",
    [
        (13, "ACTION_STATUS"),
        (None, "UNKNOWN"),
        (True, True),
        (-1, None),
        (1025, "private-boundary"),
        ("private-query-text", {"raw": "private-body"}),
        ({"raw": "private-body"}, ["ACTION_STATUS"]),
    ],
)
def test_exact_boundary_and_partial_status_diagnostics_are_safe(
    browser: Browser, workbench_server: str, value: Any, code: Any
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
            "web_search_call_count": 16,
            "search_action_count": 7,
            "message_count": 0,
            "research_http_request_count": 1,
            "boundary_code": code,
            "completed_action_count": value,
            "in_progress_action_count": 1,
            "incomplete_action_count": 1,
            "failed_action_count": 1,
            "cancelled_action_count": 0,
            "completed_search_count": 6,
            "non_completed_search_count": 1,
            "missing_or_unknown_status_count": value,
            "invalid_query_value_count": value,
            "malformed_action_count": value,
            "unexpected_output_item_count": value,
            "provider_exposed_query_count": 24,
            "raw_source_record_count": 0,
            "unknown_action_count": 0,
            "queries": ["private-query-text"],
            "sources": [{"url": "https://private.example"}],
            "reasoning": "private-reasoning",
            "provider_response_id": "private-response-id",
        },
    }
    page.locator("#analyze-button").click()
    expect(page.locator("#analysis-state")).to_contain_text("来源记录 0")
    rendered = page.locator("#analysis-state").text_content() or ""
    assert ("边界 ACTION_STATUS" in rendered) is (code == "ACTION_STATUS")
    assert ("动作 completed 13" in rendered) is (type(value) is int and value == 13)
    assert ("无效查询值 13" in rendered) is (type(value) is int and value == 13)
    for expected in [
        "动作 in_progress 1",
        "动作 incomplete 1",
        "动作 failed 1",
        "动作 cancelled 0",
        "完成搜索 6",
        "未完成搜索 1",
        "查询 24",
    ]:
        assert expected in rendered
    assert "未知动作 0" in rendered and "搜索 7" in rendered
    assert all(v not in rendered for v in ["private-", "private.example", "{", "}"])
    expect(page.locator("#decision-heading")).to_contain_text("较早成功结果")
    assert page.locator(".narrative-text").text_content() == before
    page.get_by_role("button", name="原文", exact=True).click()
    assert page.locator(".narrative-text").text_content() == before
    page.get_by_role("button", name="格式化", exact=True).click()
    assert len(app.posts) == 1 and app.posts[0]["web_research"] is True
    assert app.errors == []
    app.close()
