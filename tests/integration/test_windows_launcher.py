from __future__ import annotations

import re
from pathlib import Path

LAUNCHER = Path("start_dashboard.bat")


def _launcher_source() -> str:
    return LAUNCHER.read_text(encoding="utf-8")


def test_launcher_resolves_repository_runtime_and_opend_portably() -> None:
    source = _launcher_source()

    assert 'set "REPO_ROOT=%~dp0"' in source
    assert 'set "PYTHON_EXE=%REPO_ROOT%.venv\\Scripts\\python.exe"' in source
    assert "FUTU_OPEND_EXE" in source
    assert "%APPDATA%\\Futu_OpenD\\Futu_OpenD.exe" in source
    assert "%LOCALAPPDATA%\\Futu_OpenD\\Futu_OpenD.exe" in source
    assert "%ProgramFiles%\\Futu_OpenD\\Futu_OpenD.exe" in source
    assert not re.search(r"[A-Za-z]:\\Users\\", source, flags=re.IGNORECASE)


def test_launcher_checks_readiness_before_starting_components_or_browser() -> None:
    source = _launcher_source()

    opend_check = source.index("call :tcp_ready 127.0.0.1 11111")
    opend_start = source.index('start "Futu OpenD"')
    health_check = source.index("call :health_ready")
    port_check = source.index("call :tcp_ready 127.0.0.1 8000")
    fastapi_start = source.index('start "AI Infra Quant Dashboard"')
    health_wait = source.index("call :wait_health")
    browser_open = source.index('start "" "%DASHBOARD_URL%"')

    assert opend_check < opend_start
    assert health_check < port_check < fastapi_start < health_wait < browser_open
    assert "OPEND_TIMEOUT_SECONDS=60" in source
    assert "FASTAPI_TIMEOUT_SECONDS=45" in source
    assert "Port 8000 is occupied" in source


def test_launcher_uses_existing_quote_only_application_without_scope_expansion() -> None:
    source = _launcher_source()
    lowered = source.lower()

    assert 'set "market_data_provider=futu"' in lowered
    assert "-m uvicorn ai_infra_quant.backend.main:app --host 127.0.0.1 --port 8000" in source
    assert 'set "DASHBOARD_URL=http://127.0.0.1:8000"' in source
    assert 'set "HEALTH_URL=%DASHBOARD_URL%/health"' in source
    assert '"%ComSpec%" /k' in source

    for forbidden in (
        "git pull",
        "pip install",
        "python -m venv",
        "opensectradecontext",
        "openfuturetradecontext",
        "place_order",
        "cancel_order",
        "modify_order",
        "unlock_trade",
        "account id",
        "trade password",
    ):
        assert forbidden not in lowered
