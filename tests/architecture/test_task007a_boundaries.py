from __future__ import annotations

import ast
from pathlib import Path


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_core_and_application_do_not_import_openai_or_provider_adapter() -> None:
    paths = (
        Path("src/ai_infra_quant/core/domain/paqs_e_reasoning.py"),
        Path("src/ai_infra_quant/core/ports/paqs_e_reasoning.py"),
        Path("src/ai_infra_quant/application/paqs_e_runtime.py"),
    )
    forbidden = ("openai", "ai_infra_quant.integrations", "fastapi", "sqlalchemy")
    for path in paths:
        assert not any(module.startswith(forbidden) for module in _imports(path))


def test_task007a_adds_no_api_ui_persistence_migration_or_broker_capability() -> None:
    route_names = {path.name for path in Path("src/ai_infra_quant/backend/api/v1").glob("*.py")}
    assert "paqs_e.py" not in route_names
    migrations = Path("src/ai_infra_quant/database/migrations/versions").glob("*.py")
    assert sorted(path.name for path in migrations) == ["0001_phase1_foundation.py"]
    task_source = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (
            Path("src/ai_infra_quant/core/domain/paqs_e_reasoning.py"),
            Path("src/ai_infra_quant/core/ports/paqs_e_reasoning.py"),
            Path("src/ai_infra_quant/application/paqs_e_runtime.py"),
            Path("src/ai_infra_quant/integrations/openai_reasoning/adapter.py"),
        )
    )
    for forbidden in (
        "place_order",
        "cancel_order",
        "modify_order",
        "unlock_trade",
        "broker_account",
        "decision_ledger",
        "historical_replay_store",
        "paqs_q",
    ):
        assert forbidden not in task_source


def test_local_environment_files_remain_ignored_except_safe_example() -> None:
    patterns = Path(".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in patterns
    assert ".env.*" in patterns
    assert "!.env.example" in patterns
