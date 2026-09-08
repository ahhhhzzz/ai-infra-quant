from __future__ import annotations

import pytest
from playwright.sync_api import Browser, expect

from .workbench_support import Workbench


@pytest.mark.parametrize("terminal", ["SUCCEEDED", "PROVIDER_FAILED", "PROVIDER_INCOMPLETE"])
def test_analyze_remains_guarded_after_180_seconds_until_terminal_response(
    browser: Browser, workbench_server: str, terminal: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    app.select(1)
    page.clock.install()
    app.hold = "/paqs-e/narrative-analyses"
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
        run = app.narrative_runs["10000000-0000-4000-8000-000000000002"]
        kind = (
            "PROVIDER_INCOMPLETE" if terminal == "PROVIDER_INCOMPLETE" else "PROVIDER_UNAVAILABLE"
        )
        run.update(status="PROVIDER_FAILED", failure_kind=kind, failure_reason="Synthetic failure")
        app.post_status = 502 if terminal == "PROVIDER_INCOMPLETE" else 503
        app.post_body = {
            "status": app.post_status,
            "analysis_status": "PROVIDER_FAILED",
            "narrative_run_id": run["narrative_run_id"],
            "failure_kind": kind,
        }
    app.hold = None
    app.respond(app.pending.pop())
    expected = (
        "已提交成功 Narrative"
        if terminal == "SUCCEEDED"
        else "提供方回答未完成"
        if terminal == "PROVIDER_INCOMPLETE"
        else "推理提供方不可用"
    )
    expect(page.locator("#analysis-state")).to_contain_text(expected)
    expect(page.locator("#analyze-button")).to_be_enabled()
    page.clock.run_for(180001)
    expect(page.locator("#analysis-state")).to_contain_text(expected)
    assert len(app.posts) == 1 and app.errors == []
    app.close()
