"""Real Chromium layout and interactions with synthetic, intercepted evidence only."""

# ruff: noqa: RUF001 -- Chinese UI assertions retain application punctuation.
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Browser, Page, Route, expect

from .test_paqs_e_narrative import make_app, select
from .workbench_support import HK, Workbench

RETIRED = (
    "/portfolio",
    "/performance",
    "/brokers",
    "/fundamental-data/providers",
    "/event-data/providers",
    "/market-data/providers",
)


def observe(app: Workbench) -> list[str]:
    errors: list[str] = []
    app.page.on(
        "console", lambda message: errors.append(message.text) if message.type == "error" else None
    )
    return errors


def passive_only(app: Workbench, errors: list[str]) -> None:
    assert not app.posts and not app.errors and not errors
    assert not any(urlparse(url).path.endswith(RETIRED) for _, url in app.requests)
    assert all(urlparse(url).netloc == urlparse(app.address).netloc for _, url in app.requests)
    assert not any(method == "POST" and "/paqs-e/" in url for method, url in app.requests)


def screenshot(page: Page, name: str) -> None:
    directory = os.environ.get("TASK007C2_SCREENSHOT_DIR")
    if directory:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path / f"{name}.png"), full_page=True)


def check_geometry(page: Page) -> None:
    result = page.evaluate("""() => {
      const dialog = document.querySelector('#credential-dialog');
      const form = document.querySelector('#credential-form');
      const box = dialog.getBoundingClientRect();
      const nodes = [...form.children];
      const boxes = nodes.map(node => node.getBoundingClientRect());
      const input = document.querySelector('#credential-secret').getBoundingClientRect();
      const actions = [...document.querySelectorAll('.credential-actions button')];
      const actionBoxes = actions.map(node => node.getBoundingClientRect());
      return {
        contained: box.left >= 15 && box.right <= innerWidth - 15 &&
          box.top >= 15 && box.bottom <= innerHeight - 15,
        centered: Math.abs(box.left + box.width / 2 - innerWidth / 2) <= 1 &&
          Math.abs(box.top + box.height / 2 - innerHeight / 2) <= 1,
        oneColumn: getComputedStyle(form).gridTemplateColumns.split(' ').length === 1,
        ordered: boxes.every((value, i) => i === 0 || value.top >= boxes[i - 1].bottom),
        fullWidth: Math.abs(input.width - form.getBoundingClientRect().width) <= 1,
        noOverflow: dialog.scrollWidth <= dialog.clientWidth &&
          document.documentElement.scrollWidth <= innerWidth,
        childWidths: boxes.every(value => value.left >= box.left && value.right <= box.right),
        actionsOrdered: actionBoxes.every((value, i) => i === 0 ||
          value.top >= actionBoxes[i - 1].bottom),
        primaryDistinct: getComputedStyle(actions[0]).backgroundColor !==
          getComputedStyle(actions[1]).backgroundColor,
      };
    }""")
    assert all(result.values()), result
    for selector in ("#credential-save", "#credential-delete", "#credential-close"):
        button = page.locator(selector)
        button.scroll_into_view_if_needed()
        assert button.evaluate("""node => {
          const a = node.getBoundingClientRect();
          const b = document.querySelector('#credential-dialog').getBoundingClientRect();
          return a.top >= b.top && a.bottom <= b.bottom && a.height >= 32;
        }""")
    page.locator("#credential-dialog").evaluate("(node) => node.scrollTop = 0")


@pytest.mark.parametrize("width,height", [(1440, 900), (900, 900), (390, 844)])
@pytest.mark.parametrize("light", [False, True])
def test_open_modal_geometry_themes_and_keyboard(
    browser: Browser,
    workbench_server: str,
    width: int,
    height: int,
    light: bool,
) -> None:
    app = Workbench(browser, workbench_server, width=width, height=height, legacy_history=False)
    errors = observe(app)
    app.page.route(
        "**/paqs-e/credentials/*",
        lambda route: app.fulfill(
            route,
            {
                "credential_source": "missing",
                "credential_configured": False,
                "secure_storage_available": True,
            },
        ),
    )
    page = app.open()
    if light:
        page.locator("#theme-toggle").click()
    page.locator("#configure-credential").click()
    expect(page.locator("#credential-secret")).to_be_focused()
    expect(page.locator("#credential-status")).not_to_be_empty()
    page.locator("#credential-service").evaluate(
        "(node, value) => node.textContent = value",
        "SyntheticLongRegisteredModelDescription" * 5 + " · 合成服务说明，非真实模型或凭据。" * 4,
    )
    page.locator("#credential-status").evaluate(
        "(node, value) => node.textContent = value",
        "合成错误：操作未能确认；请检查安全存储状态后手动重试。" * 7,
    )
    check_geometry(page)
    if width == 390:
        assert page.locator("#credential-dialog").evaluate("(n) => n.scrollHeight > n.clientHeight")
    screenshot(page, f"modal-{width}x{height}-{'light' if light else 'dark'}")
    if width == 390:
        page.locator("#credential-close").scroll_into_view_if_needed()
        screenshot(page, f"modal-390x844-{'light' if light else 'dark'}-actions")
    page.locator("#credential-secret").fill("synthetic-unsaved-only")
    page.keyboard.press("Tab")
    expect(page.locator("#credential-save")).to_be_focused()
    page.keyboard.press("Escape")
    expect(page.locator("#credential-dialog")).not_to_be_visible()
    expect(page.locator("#credential-secret")).to_have_value("")
    expect(page.locator("#configure-credential")).to_be_focused()
    page.locator("#configure-credential").press("Enter")
    expect(page.locator("#credential-secret")).to_be_focused()
    page.locator("#credential-close").click()
    expect(page.locator("#configure-credential")).to_be_focused()
    passive_only(app, errors)
    app.close()


def test_modal_at_equivalent_200_percent_text_enlargement(
    browser: Browser,
    workbench_server: str,
) -> None:
    app = Workbench(browser, workbench_server, legacy_history=False)
    errors = observe(app)
    app.page.route(
        "**/paqs-e/credentials/*",
        lambda route: app.fulfill(
            route,
            {
                "credential_source": "missing",
                "credential_configured": False,
            },
        ),
    )
    page = app.open()
    page.locator("#configure-credential").click()
    expect(page.locator("#credential-status")).not_to_be_empty()
    # Actual computed modal text doubles from 16px to 32px. This is text enlargement,
    # not a claim of browser page zoom or a pinch/visual-viewport emulation.
    before = page.locator("#credential-dialog").evaluate("(n) => getComputedStyle(n).fontSize")
    page.evaluate("document.documentElement.style.fontSize = '32px'")
    assert before == "16px"
    assert (
        page.locator("#credential-dialog").evaluate("(n) => getComputedStyle(n).fontSize") == "32px"
    )
    check_geometry(page)
    screenshot(page, "modal-1440x900-text-200-percent")
    page.locator("#credential-close").click()
    expect(page.locator("#configure-credential")).to_be_focused()
    passive_only(app, errors)
    app.close()


def test_credentials_update_failure_clear_and_no_automatic_analysis(
    browser: Browser,
    workbench_server: str,
) -> None:
    app = Workbench(browser, workbench_server, legacy_history=False)
    errors = observe(app)
    values: list[str] = []
    deleted: list[bool] = []

    def credentials(route: Route) -> None:
        if route.request.method == "PUT":
            payload = route.request.post_data_json
            assert isinstance(payload, dict)
            values.append(payload["secret"])
        elif route.request.method == "DELETE":
            deleted.append(True)
        app.fulfill(route, {"credential_source": "secure_store", "credential_configured": True})

    app.page.route("**/paqs-e/credentials/*", credentials)
    page = app.open()
    page.locator("#configure-credential").click()
    for value in ("synthetic-save-only", "synthetic-update-only"):
        page.locator("#credential-secret").fill(value)
        page.locator("#credential-save").click()
        expect(page.locator("#credential-status")).to_contain_text("已安全保存")
        expect(page.locator("#credential-secret")).to_have_value("")
    page.locator("#credential-delete").click()
    expect(page.locator("#credential-status")).to_contain_text("已删除")
    # A malformed confirmation read produces the real catch-path without generating
    # an expected HTTP-resource console error; no backend secret store is touched.
    page.route(
        "**/paqs-e/configuration",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body="synthetic-invalid-json",
        ),
    )
    page.locator("#credential-secret").fill("synthetic-unconfirmed-only")
    page.locator("#credential-save").click()
    expect(page.locator("#credential-status")).to_contain_text("操作未能确认")
    expect(page.locator("#credential-secret")).to_have_value("")
    expect(page.locator("#credential-save")).to_be_enabled()
    page.locator("#credential-secret").fill("synthetic-unsaved-only")
    page.locator("#credential-close").click()
    expect(page.locator("#credential-secret")).to_have_value("")
    expect(page.locator("#configure-credential")).to_be_focused()
    assert values == ["synthetic-save-only", "synthetic-update-only", "synthetic-unconfirmed-only"]
    assert deleted == [True]
    passive_only(app, errors)
    app.close()


@pytest.mark.parametrize("width,light", [(1440, False), (900, True), (390, False)])
def test_clean_workbench_watchlist_market_and_both_histories(
    browser: Browser,
    workbench_server: str,
    width: int,
    light: bool,
) -> None:
    app = make_app(browser, workbench_server, width=width, height=844 if width == 390 else 900)
    errors = observe(app)
    page = app.open()
    if light:
        page.locator("#theme-toggle").click()
    expect(
        page.locator(
            ".local-admin, #equity, #cash, #nav, #units, #invested, "
            "#return, #watchlist-admin, #providers"
        )
    ).to_have_count(0)
    assert "Portfolio facts and local administration" not in page.content()
    expect(page.locator("#web-research")).not_to_be_checked()
    expect(page.locator("#model-id option")).to_have_count(11)
    if width == 390:
        page.locator("#watchlist-toggle").click()
    page.locator(f'[data-security-id="{HK}"]').click()
    expect(page.locator("#selected-title")).to_contain_text("00700")
    expect(page.locator("#market-watchlist-status")).to_contain_text("2 securities")
    expect(page.locator("#latest-price")).not_to_have_text("—")
    page.locator("#remove-selected").click()
    expect(page.locator("#security-selector button")).to_have_count(1)
    page.locator("#remove-selected").click()
    expect(page.locator("#security-selector button")).to_have_count(0)
    page.locator("#supported-security-form select").select_option("HK")
    page.locator("#supported-security-form input").fill("700")
    page.locator("#supported-security-form button").click()
    expect(page.locator("#security-selector button")).to_have_count(1)
    expect(page.locator("#supported-security-result")).to_contain_text("validated")
    select(app, 3)
    facts = page.locator("#evidence-facts").text_content()
    assert len(page.evaluate("window.chartCaptures[0].series[0].bars")) == 80
    page.locator("#mode-current").click()
    app.state_price = "999.123456789012345678"
    page.locator("#refresh-market").click()
    expect(page.locator("#latest-price")).to_contain_text("999")
    expect(page.locator("#provider-mode")).to_contain_text("synthetic-browser-fixture")
    expect(page.locator("#quote-status")).to_have_text("AVAILABLE")
    page.locator("#reload-history").click()
    expect(page.locator("#decision-history .history-row")).to_have_count(1)
    page.locator("#mode-frozen").click()
    assert page.locator("#evidence-facts").text_content() == facts
    page.locator("#legacy-history-section > summary").click()
    app.select(3)
    expect(page.locator("#decision-heading")).to_contain_text("Legacy")
    expect(page.locator("#evidence-status")).to_contain_text("冻结 W1")
    page.locator(".known-run > summary").click()
    page.locator("#known-run-kind").select_option("legacy")
    page.locator("#known-run-id").fill("10000000-0000-4000-8000-000000000003")
    page.locator("#known-run-form button").click()
    expect(page.locator("#known-run-detail")).to_contain_text("SUCCEEDED")
    page.locator(".known-run > summary").click()
    select(app, 3)
    screenshot(page, f"workbench-{width}-{'light' if light else 'dark'}")
    passive_only(app, errors)
    app.close()
