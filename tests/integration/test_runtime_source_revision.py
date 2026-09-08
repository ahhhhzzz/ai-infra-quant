from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from ai_infra_quant.backend.main import create_app
from ai_infra_quant.backend.runtime_identity import capture_source_revision
from ai_infra_quant.config import Settings

SHA = "b7316e83f7fd377f4c628db90dee8e3d7b4a5335"


@pytest.mark.parametrize(
    "value", ["", "unknown", "a" * 39, "A" * 40, "a" * 40 + "\n", "private/path"]
)
def test_invalid_startup_revision_is_bounded_unknown(
    value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AI_INFRA_SOURCE_REVISION", value)
    assert capture_source_revision() == "unknown"


def test_health_revision_is_frozen_despite_checkout_environment_change(
    monkeypatch: pytest.MonkeyPatch, settings: Settings, migrated_engine: Engine
) -> None:
    monkeypatch.setenv("AI_INFRA_SOURCE_REVISION", SHA)
    app = create_app(settings, migrated_engine)
    with TestClient(app) as client:
        assert client.get("/health").json()["source_revision"] == SHA
        monkeypatch.setenv("AI_INFRA_SOURCE_REVISION", "f" * 40)
        assert client.get("/health").json()["source_revision"] == SHA


@pytest.mark.parametrize(
    "revision,code",
    [(SHA, 0), ("f" * 40, 2), (None, 2), ("A" * 40, 2), ("private/path", 2), (123, 2)],
)
def test_actual_powershell_health_handshake(revision: object, code: int) -> None:
    powershell = shutil.which("powershell.exe") or shutil.which("pwsh")
    if powershell is None:
        pytest.skip("PowerShell is required to execute the Windows launcher handshake")
    health = json.dumps({"status": "OK", "database": "READY", "source_revision": revision})
    script = Path("scripts/dashboard_runtime.ps1").resolve().as_posix().replace("'", "''")
    # Synthetic HTTP boundary; execute the exact production helper in a child shell.
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"function Invoke-RestMethod {{ '{health}' | ConvertFrom-Json }}; "
            f"& '{script}'; exit $LASTEXITCODE",
        ],
        env={**os.environ, "AI_INFRA_SOURCE_REVISION": SHA},
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == code, result.stdout + result.stderr
    if code == 2:
        assert "Stale backend/version mismatch" in result.stdout
        assert "Close/restart" in result.stdout
        assert "private/path" not in result.stdout


def test_launcher_resolves_before_check_and_never_terminates_processes() -> None:
    source = Path("start_dashboard.bat").read_text(encoding="utf-8")
    helper = Path("scripts/dashboard_runtime.ps1").read_text(encoding="utf-8")
    assert source.index("-Mode Resolve") < source.index("call :health_ready")
    assert "call :health_ready\nif errorlevel 2 goto fail" in source
    assert "call :wait_health %FASTAPI_TIMEOUT_SECONDS%\nif errorlevel 2 goto fail" in source
    for forbidden in ("taskkill", "stop-process", "terminateprocess"):
        assert forbidden not in (source + helper).lower()
