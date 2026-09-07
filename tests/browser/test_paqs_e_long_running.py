from __future__ import annotations

import pytest
from playwright.sync_api import Browser, expect

from .workbench_support import Workbench


@pytest.mark.parametrize("terminal", ["SUCCEEDED", "PROVIDER_FAILED", "VALIDATION_FAILED"])
def test_analyze_remains_guarded_after_180_seconds_until_terminal_response(
    browser: Browser, workbench_server: str, terminal: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    app.select(1)
    page.clock.install()
    app.hold = "/paqs-e/analyses"
    app.analyze()
    page.clock.run_for(180001)
    expect(page.locator("#analysis-state")).to_contain_text("仍在分析")
    expect(page.locator("#analysis-state")).to_contain_text("请勿重复提交")
    expect(page.locator("#analyze-button")).to_be_disabled()
    page.locator("#analyze-form").dispatch_event("submit")
    page.clock.run_for(61000)
    assert len(app.posts) == 1 and len(app.pending) == 1
    expect(page.locator("#analyze-button")).to_be_disabled()
    if terminal != "SUCCEEDED":
        run = app.runs["10000000-0000-4000-8000-000000000002"]
        validation = terminal == "VALIDATION_FAILED"
        run.update(
            status=terminal,
            failure_kind=None if validation else "PROVIDER_UNAVAILABLE",
            failure_reason=None if validation else "Synthetic failure",
            validator_version="paqs-e-validator-v1" if validation else None,
            validation_issues=[
                {"code": "SYNTHETIC_ISSUE", "field": "entry", "message": "Synthetic semantic issue"}
            ]
            if validation
            else [],
        )
        app.post_status = 502 if validation else 503
        context = {
            key: run[key]
            for key in (
                "analysis_run_id",
                "status",
                "failure_kind",
                "validator_version",
                "validation_issues",
            )
        }
        app.post_body = {
            **context,
            "status": app.post_status,
            "analysis_status": terminal,
            "analysis_run": context,
        }
    app.hold = None
    app.respond(app.pending.pop())
    expected = (
        "已提交成功 Decision"
        if terminal == "SUCCEEDED"
        else "确定性校验失败"
        if terminal == "VALIDATION_FAILED"
        else "推理提供方不可用"
    )
    expect(page.locator("#analysis-state")).to_contain_text(expected)
    expect(page.locator("#analyze-button")).to_be_enabled()
    page.clock.run_for(180001)
    expect(page.locator("#analysis-state")).to_contain_text(expected)
    assert len(app.posts) == 1 and app.errors == []
    app.close()
