from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from playwright.sync_api import expect


@pytest.fixture(scope="module")
def archive_server(tmp_path_factory: Any) -> Iterator[str]:
    root = Path(__file__).resolve().parents[2]
    folder = tmp_path_factory.mktemp("archive-browser")
    env = os.environ.copy()
    env.update(
        DATABASE_URL=f"sqlite:///{(folder / 'archive.sqlite').as_posix()}",
        MARKET_DATA_PROVIDER="none",
        PYTHONPATH=f"{root / 'src'}{os.pathsep}{root}",
    )
    env.pop("OPENAI_API_KEY", None)
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
    )
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    address = f"http://127.0.0.1:{port}"
    with (folder / "uvicorn.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "tests.browser.archive_server:create_archive_test_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=root,
            env=env,
            stdout=log,
            stderr=log,
        )
        try:
            with httpx.Client(base_url=address, trust_env=False) as client:
                for _ in range(100):
                    try:
                        response = client.get("/health")
                        if response.status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.1)
                else:
                    raise AssertionError((folder / "uvicorn.log").read_text(encoding="utf-8"))
                assert response.json()["migration_revision"] == "0004_task006b1_market_archive"
            yield address
        finally:
            process.terminate()
            process.wait(timeout=10)


def configure(server: str, **kwargs: Any) -> None:
    with httpx.Client(base_url=server, trust_env=False) as client:
        assert client.post("/_fixture/configure", json=kwargs).status_code == 200


def normal_seed_details(server: str) -> dict[str, Any]:
    with httpx.Client(base_url=server, trust_env=False) as client:
        details = {
            item["security"]["display_symbol"]: client.get(
                f"/api/v1/securities/{item['security']['id']}"
            ).json()
            for item in client.get("/api/v1/watchlist").json()["items"]
        }
    assert set(details) == {"US.AVGO", "US.VRT", "HK.09698"}
    for security in details.values():
        assert security["verification_status"] == "SYSTEM_SEED_UNVERIFIED"
        assert security["tradability_status"] == "UNVERIFIED"
        assert security["metadata_status"] == "UNAVAILABLE"
    return details


@pytest.mark.parametrize("width", [390, 900, 1440])
@pytest.mark.parametrize("theme", ["dark", "light"])
def test_real_capture_offline_pages_layout_keyboard(
    browser: Any, archive_server: str, width: int, theme: str
) -> None:
    before = normal_seed_details(archive_server)
    configure(archive_server)
    assert normal_seed_details(archive_server) == before
    context = browser.new_context(viewport={"width": width, "height": 1000})
    page = context.new_page()
    errors: list[str] = []
    calls: list[tuple[str, str]] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console", lambda message: errors.append(message.text) if message.type == "error" else None
    )
    page.on("request", lambda request: calls.append((request.method, request.url)))
    page.goto(archive_server)
    expect(page.locator("#archive-save")).to_be_enabled()
    assert not page.locator("#market-archive").evaluate("element => element.open")
    if theme == "light":
        page.locator("#theme-toggle").click()
    summary = page.locator("#market-archive > summary")
    summary.focus()
    page.keyboard.press("Enter")
    expect(page.locator("#archive-status")).to_contain_text("本地")
    assert not [url for method, url in calls if method == "POST"]
    page.locator("#archive-save").click()
    expect(page.locator("#archive-detail h3")).to_contain_text("PARTIAL")
    expect(page.locator("#archive-bars tbody tr")).to_have_count(1)
    assert "12345678901234567890.123456789012345678" in page.locator("#archive-bars").inner_text()
    capture_id = page.locator("#archive-known-id").input_value()
    with httpx.Client(base_url=archive_server, trust_env=False) as client:
        assert client.get("/_fixture/calls").json()["calls"] == ["enter", "D1", "M1", "calendar"]
        for path in (
            "/health",
            "/",
            "/static/market-data-archive.js",
            "/static/app.css",
            "/openapi.json",
        ):
            assert client.get(path).status_code == 200
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/market-data/archive/captures/{capture_id}/bars" in paths
    configure(archive_server, offline=True)
    # Reload with live initialization unavailable: known-ID control remains independently usable.
    page.reload()
    page.locator("#market-archive > summary").click()
    page.locator("#archive-known-id").fill(capture_id)
    page.locator("#archive-known-form button").click()
    expect(page.locator("#archive-bars tbody tr")).to_have_count(1)
    page.locator("#archive-timeframe").select_option("M1")
    expect(page.locator("#archive-bars tbody tr")).to_have_count(500)
    first = page.locator("#archive-bars tbody tr").first.inner_text()
    page.locator("#archive-bars-next").click()
    expect(page.locator("#archive-bars tbody tr")).to_have_count(101)
    assert page.locator("#archive-bars tbody tr").first.inner_text() != first
    expect(page.locator("#archive-bars-next")).to_be_disabled()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    for selector in ("#archive-save", "#archive-known-id", "#archive-timeframe"):
        box = page.locator(selector).bounding_box()
        assert box and box["x"] >= 0 and box["x"] + box["width"] <= width
    scroll = page.locator(".archive-table-scroll")
    scroll.focus()
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(120)
    assert scroll.evaluate("element => element.scrollLeft") > 0
    scroll.evaluate("element => element.scrollLeft = 0")
    evidence = os.environ.get("TASK006B1_EVIDENCE_DIR")
    if evidence:
        folder = Path(evidence)
        folder.mkdir(parents=True, exist_ok=True)
        page.locator("#market-archive").screenshot(
            path=str(folder / f"archive-{width}-{theme}.png")
        )
    assert (
        len([url for method, url in calls if method == "POST" and "/archive/captures" in url]) == 1
    )
    assert not [url for method, url in calls if method == "POST" and "analyses" in url]
    with httpx.Client(base_url=archive_server, trust_env=False) as client:
        assert client.get("/_fixture/calls").json()["calls"] == []
    assert normal_seed_details(archive_server) == before
    assert errors == []
    context.close()


def test_pending_duplicate_guard_and_late_security_result(
    browser: Any, archive_server: str
) -> None:
    configure(archive_server, delay=0.3)
    context = browser.new_context()
    page = context.new_page()
    page.goto(archive_server)
    expect(page.locator("#archive-save")).to_be_enabled()
    page.locator("#market-archive > summary").click()
    page.locator("#archive-save").click()
    expect(page.locator("#archive-save")).to_be_disabled()
    page.locator("#archive-save").evaluate("button => button.click()")
    page.evaluate("document.dispatchEvent(new CustomEvent('security-selected', {detail: null}))")
    expect(page.locator("#archive-status")).to_contain_text("执行中")
    page.wait_for_timeout(1500)
    expect(page.locator("#archive-detail")).to_be_empty()
    expect(page.locator("#archive-save")).to_be_disabled()
    with httpx.Client(base_url=archive_server, trust_env=False) as client:
        assert client.get("/_fixture/calls").json()["calls"] == ["enter", "D1", "M1", "calendar"]
    context.close()


def test_capture_failure_is_recoverable_without_retry(browser: Any, archive_server: str) -> None:
    configure(archive_server, fail=["D1", "M1", "calendar"])
    context = browser.new_context()
    page = context.new_page()
    page.goto(archive_server)
    expect(page.locator("#archive-save")).to_be_enabled()
    page.locator("#market-archive > summary").click()
    page.locator("#archive-save").click()
    expect(page.locator("#archive-status")).to_contain_text("HTTP 503")
    expect(page.locator("#archive-save")).to_be_enabled()
    expect(page.locator("#archive-detail")).to_be_empty()
    configure(archive_server)
    page.locator("#archive-save").click()
    expect(page.locator("#archive-detail h3")).to_contain_text("PARTIAL")
    context.close()
