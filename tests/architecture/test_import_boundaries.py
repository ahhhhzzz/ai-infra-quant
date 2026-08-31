from __future__ import annotations

import ast
from pathlib import Path

CORE = Path("src/ai_infra_quant/core")
APPLICATION = Path("src/ai_infra_quant/application")
FORBIDDEN_PREFIXES = (
    "ai_infra_quant.backend",
    "ai_infra_quant.database",
    "ai_infra_quant.integrations",
    "fastapi",
    "sqlalchemy",
    "futu",
)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_core_import_boundaries() -> None:
    violations: list[str] = []
    for path in CORE.rglob("*.py"):
        for module in imported_modules(path):
            if module.startswith(FORBIDDEN_PREFIXES):
                violations.append(f"{path}: {module}")
    assert violations == []


def test_application_depends_only_on_core_and_standard_library() -> None:
    forbidden = (
        "ai_infra_quant.backend",
        "ai_infra_quant.database",
        "ai_infra_quant.integrations",
        "fastapi",
        "sqlalchemy",
    )
    violations: list[str] = []
    for path in APPLICATION.rglob("*.py"):
        for module in imported_modules(path):
            if module.startswith(forbidden):
                violations.append(f"{path}: {module}")
    assert violations == []


def test_forbidden_future_route_modules_are_absent() -> None:
    route_dir = Path("src/ai_infra_quant/backend/api/v1")
    forbidden = {
        "orders.py",
        "paper.py",
        "live.py",
        "accounts.py",
        "signals.py",
        "indicators.py",
        "strategy_run.py",
        "backtest.py",
    }
    assert forbidden.isdisjoint({path.name for path in route_dir.glob("*.py")})
