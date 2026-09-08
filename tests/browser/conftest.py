from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import Browser, sync_playwright


@pytest.fixture(scope="session")
def workbench_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Actual normal Uvicorn entrypoint, fresh migrated DB, no configured providers."""
    root = Path(__file__).resolve().parents[2]
    temporary = tmp_path_factory.mktemp("007c-real-startup")
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env.update(
        DATABASE_URL=f"sqlite:///{(temporary / 'app.db').as_posix()}",
        MARKET_DATA_PROVIDER="none",
        FUNDAMENTAL_DATA_PROVIDER="none",
        EVENT_DATA_PROVIDER="none",
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-x",
            f"database_url={env['DATABASE_URL']}",
            "upgrade",
            "head",
        ],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    address = f"http://127.0.0.1:{port}"
    with (temporary / "uvicorn.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "ai_infra_quant.backend.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=root,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            for _ in range(200):
                if process.poll() is not None:
                    raise AssertionError("Task Uvicorn process exited during startup")
                try:
                    health = httpx.get(address + "/health", timeout=1, trust_env=False)
                    if health.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.1)
            else:
                raise AssertionError("Actual Uvicorn startup timed out")
            assert health.json()["migration_revision"] == "0003_task007c1_narrative_ledger"
            yield address
        finally:
            # Only the subprocess created above belongs to this fixture.
            process.terminate()
            process.wait(timeout=15)


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        launched = playwright.chromium.launch(
            channel=os.environ.get("TASK007C_BROWSER_CHANNEL", "chrome"), headless=True
        )
        yield launched
        launched.close()
