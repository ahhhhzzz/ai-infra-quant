"""Offline comparison renders exact export values; no product browser matrix."""

import csv
import json
from decimal import Decimal

from playwright.sync_api import sync_playwright

from tools.research.single_pattern.comparison import compare, display, write_comparison
from tools.research.single_pattern.integrations.local import demo, load
from tools.research.single_pattern.model import Config


def test_offline_comparison_exports_and_interaction(tmp_path):
    path, calendar = demo(tmp_path / "input")
    result = compare(load(path, calendar, "America/New_York", "USD"), Config(), Decimal(".01"))
    output = tmp_path / "comparison"
    write_comparison(result, output)
    with (output / "summary.csv").open(encoding="utf-8-sig", newline="") as stream:
        summaries = {row["mode"]: row for row in csv.DictReader(stream)}
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
        assert json.loads(page.locator("#payload").text_content()) == result
        assert "SYNTHETIC" in page.locator(".notice").inner_text()
        for name, mode in result["modes"].items():
            for field in ("final_equity", "total_return", "max_drawdown", "win_rate", "total_fees"):
                cell = page.locator(f'#summary [data-mode="{name}"] [data-field="{field}"]')
                value = mode["summary"][field]
                assert cell.inner_text() == display(
                    value, field in {"total_return", "max_drawdown", "win_rate"}
                )
                assert summaries[name][field] == value
            assert page.locator(f'table.trades[data-mode="{name}"] tbody tr').count() == 3
        page.locator("#benchmark").check()
        assert page.locator("#equity").evaluate("c => c.width > 0 && c.height > 0")
        page.locator("#equity").hover()
        assert "fixed-risk" in page.locator("#hover").inner_text()
        assert page.locator('a[href="decisions.csv"]').count() == 1
        assert not errors and not network
        browser.close()
