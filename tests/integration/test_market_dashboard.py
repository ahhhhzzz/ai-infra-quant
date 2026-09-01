from __future__ import annotations

import hashlib
import re
from pathlib import Path

from fastapi.testclient import TestClient

STATIC_ROOT = Path("src/ai_infra_quant/frontend/static")
TEMPLATE = Path("src/ai_infra_quant/frontend/templates/index.html")
APP_JS = STATIC_ROOT / "app.js"
APP_CSS = STATIC_ROOT / "app.css"
CHART_ASSET = STATIC_ROOT / "vendor/lightweight-charts.standalone.production.js"
CHART_LICENSE = STATIC_ROOT / "vendor/LIGHTWEIGHT_CHARTS_LICENSE.txt"
CHART_NOTICE = STATIC_ROOT / "vendor/LIGHTWEIGHT_CHARTS_NOTICE.txt"
CHART_SHA256 = "e21cc5caa0226ef30bd8549c50b9ef926615f2a4ee6b4e486353477a55f598cf"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_homepage_renders_market_first_read_only_dashboard(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    page = response.text
    for required in (
        'aria-label="Market data Dashboard"',
        'id="security-selector"',
        'id="latest-price"',
        'id="market-state"',
        'id="market-chart"',
        'id="refresh-market"',
        'id="refresh-countdown"',
        "READ ONLY · DECISION SUPPORT",
    ):
        assert required in page
    assert page.index('aria-label="Market data Dashboard"') < page.index(
        "Portfolio facts and local administration"
    )


def test_dashboard_uses_canonical_watchlist_security_ids(client: TestClient) -> None:
    symbols = [
        item["security"]["display_symbol"]
        for item in client.get("/api/v1/watchlist").json()["items"]
    ]
    assert symbols == ["US.AVGO", "US.VRT", "HK.09698"]

    source = _source(APP_JS)
    assert "security.id" in source
    assert "selectedSecurity.id" in source
    assert "/market-data/securities/${securityId}" in source
    assert 'display_symbol === "US.AVGO"' in source


def test_lightweight_charts_5_2_1_is_vendored_and_attributed(client: TestClient) -> None:
    asset = client.get("/static/vendor/lightweight-charts.standalone.production.js")
    license_response = client.get("/static/vendor/LIGHTWEIGHT_CHARTS_LICENSE.txt")
    notice_response = client.get("/static/vendor/LIGHTWEIGHT_CHARTS_NOTICE.txt")

    assert asset.status_code == license_response.status_code == notice_response.status_code == 200
    assert hashlib.sha256(asset.content).hexdigest() == CHART_SHA256
    assert "Apache License" in license_response.text
    assert "TradingView Lightweight Charts" in notice_response.text
    page = client.get("/").text
    assert "/static/vendor/lightweight-charts.standalone.production.js" in page
    assert 'href="https://www.tradingview.com/"' in page
    assert "attributionLogo: true" in _source(APP_JS)


def test_dashboard_has_no_runtime_cdn_or_unapproved_route_dependency() -> None:
    sources = "\n".join((_source(TEMPLATE), _source(APP_JS), _source(APP_CSS))).lower()
    for runtime_cdn in ("unpkg.com", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"):
        assert runtime_cdn not in sources
    for unapproved_route in ("/dashboard", "/refresh", "/terminal"):
        assert f'api("{unapproved_route}' not in sources


def test_daily_and_minute_modes_are_distinct_with_separate_volume_pane() -> None:
    page = _source(TEMPLATE)
    source = _source(APP_JS)

    assert page.count('data-timeframe="daily"') == 1
    assert page.count('data-timeframe="minute"') == 1
    assert ">日 K<" in page
    assert ">1 分钟<" in page
    assert "CandlestickSeries" in source
    assert "HistogramSeries" in source
    assert "volumeSeries" in source
    assert 'activeTimeframe === "daily"' in source
    assert "bar.session_date" in source
    assert "Date.parse(bar.interval_start)" in source
    assert "barsByInterval.set(bar.interval_start, bar)" in source


def test_refresh_visibility_and_security_race_guards_are_explicit() -> None:
    source = _source(APP_JS)

    assert "const REFRESH_INTERVAL_SECONDS = 60" in source
    assert "window.setTimeout" in source
    assert "activeRequest" in source
    assert "if (!selectedSecurity || activeRequest" in source
    assert "AbortController" in source
    assert "requestGeneration" in source
    assert "request.generation !== requestGeneration" in source
    assert "selectedSecurity?.id !== request.securityId" in source
    assert 'document.addEventListener("visibilitychange"' in source
    assert 'document.visibilityState === "hidden"' in source
    assert 'refreshSelectedSecurity("visibility-restored")' in source
    assert "已暂停" in source


def test_dashboard_exposes_truthful_capability_and_empty_states() -> None:
    page = _source(TEMPLATE)
    source = _source(APP_JS)
    css = _source(APP_CSS)

    for status_id in ("quote-status", "market-status", "daily-status", "minute-status"):
        assert f'id="{status_id}"' in page
    assert "1分钟行情暂不可用" in source
    assert 'dailySnapshot = data.status === "AVAILABLE" ? data : { ...data, bars: [] }' in source
    assert "minuteCache.barsByInterval.clear()" in source
    assert ".status-not-entitled" in css
    assert ".status-provider-error" in css
    assert "safeErrorMessage" in source


def test_frontend_has_no_fake_market_values_or_forbidden_controls() -> None:
    owned_sources = "\n".join((_source(TEMPLATE), _source(APP_JS), _source(APP_CSS)))
    lowered = owned_sources.lower()

    assert not re.search(r"\b(buy|sell)\b", lowered)
    assert not re.search(r"\border\s+(submission|control)\b", lowered)
    assert "composite score" not in lowered
    assert "score calculation" not in lowered
    assert "latest price" in lowered
    assert "closing price" not in lowered
    assert "today's close" not in lowered
    assert not re.search(r'latest_price\s*:\s*["\']?\d', owned_sources)
