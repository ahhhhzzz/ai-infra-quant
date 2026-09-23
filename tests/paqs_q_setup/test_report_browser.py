"""One offline Chromium acceptance path; no product UI or remote resources."""

from playwright.sync_api import sync_playwright

from tools.research.setup_risk.__main__ import write_bundle
from tools.research.setup_risk.demo import demo_bundle


def test_offline_report_locates_trigger_and_keeps_exact_export(tmp_path):
    output = tmp_path / "offline"
    summary = write_bundle(demo_bundle(), output)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        requests = []
        page.on("request", lambda request: requests.append(request.url))
        page.goto((output / "report.html").as_uri())
        assert page.title() == "PAQS-Q Setup/Risk 1.0.0 — 离线复盘"
        assert page.locator("#facts tr").count() == summary["facts"]
        assert page.locator("#chart").is_visible()
        page.locator("#facts tr").filter(has_text="TRIGGER_PENDING").first.locator("button").click()
        assert "M30 #" in page.locator("#focus").inner_text()
        assert page.locator('a[href="result.json"]').count() == 1
        assert all(url.startswith("file:") for url in requests)
        browser.close()
