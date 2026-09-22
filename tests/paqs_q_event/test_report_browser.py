"""One desktop/offline smoke, not the product or Linux browser matrix."""

import json

from playwright.sync_api import sync_playwright

from tools.research.event_engine.__main__ import run
from tools.research.event_engine.data import demo_input


def test_offline_event_report_filter_and_candle_location(tmp_path):
    folder = tmp_path / "offline-event"
    summary = run(demo_input(), folder)
    errors = []
    external = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on(
            "request",
            lambda r: external.append(r.url) if r.url.startswith(("http:", "https:")) else None,
        )
        page.context.set_offline(True)
        page.goto((folder / "report.html").as_uri())
        assert page.locator("#rows tr").count() == sum(summary["counts"].values())
        page.locator("#kind").select_option("RETEST")
        page.locator("#status").select_option("HOLD")
        assert page.locator("#rows tr").count() == summary["counts"]["RETEST/HOLD"]
        page.locator("#rows tr").first.click()
        detail = json.loads(page.locator("#detail").inner_text())
        assert detail["kind"] == "RETEST" and detail["status"] == "HOLD"
        assert f"bar {detail['bar_index']}" in page.locator("#candle").inner_text()
        assert page.locator("#chart").evaluate("(c) => c.width > 0 && c.height > 0")
        assert (
            page.locator("#payload").evaluate("(e) => JSON.parse(e.textContent).summary.event_hash")
            == summary["event_hash"]
        )
        page.screenshot(path=str(tmp_path / "event-report.png"), full_page=True)
        browser.close()
    assert not errors and not external
