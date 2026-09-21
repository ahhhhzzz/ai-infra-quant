"""One offline report smoke, not the product browser matrix."""

from playwright.sync_api import sync_playwright

from tools.research.single_pattern.integrations.local import demo, load
from tools.research.single_pattern.model import Config
from tools.research.single_pattern.report import run, write_report


def test_offline_report_can_locate_trade_without_network(tmp_path):
    path, calendar = demo(tmp_path / "input")
    result = run(load(path, calendar, "America/New_York", "USD"), Config())
    output = tmp_path / "report"
    write_report(result, output)
    errors, network = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda request: network.append(request.url)
            if request.url.startswith(("http:", "https:"))
            else None,
        )
        page.goto((output / "report.html").as_uri())
        assert page.locator("#cards .card").count() == 8
        assert "SYNTHETIC" in page.locator(".warning").inner_text()
        page.locator('button[data-index="50"]').first.click()
        assert page.locator("#range").input_value() == "30"
        assert page.locator("#candles").evaluate("c => c.width > 0 && c.height > 0")
        assert "STOP" in page.locator("body").inner_text()
        assert errors == [] and network == []
        browser.close()
