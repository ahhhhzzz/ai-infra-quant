from __future__ import annotations

import ast
from pathlib import Path


def _source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_structure_core_is_provider_agnostic_decimal_only_and_environment_free() -> None:
    path = "src/ai_infra_quant/core/strategy/paqs_structure.py"
    source = _source(path)
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules = {
        (node.module or "") for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }

    assert "Decimal" in source
    assert "localcontext" in source
    assert "ROUND_HALF_EVEN" in source
    assert "float(" not in source
    assert "os" not in imported_roots
    assert all("integrations" not in module for module in imported_modules)
    assert all("database" not in module for module in imported_modules)
    assert all("backend" not in module for module in imported_modules)
    assert "OpenQuoteContext" not in source
    assert "DataFrame" not in source


def test_task006b_adds_no_later_event_decision_or_write_vocabulary() -> None:
    sources = "\n".join(
        _source(path)
        for path in (
            "src/ai_infra_quant/core/strategy/paqs_structure.py",
            "src/ai_infra_quant/application/paqs_structure_queries.py",
            "src/ai_infra_quant/backend/schemas/paqs_structure.py",
            "src/ai_infra_quant/backend/api/v1/strategies.py",
        )
    ).lower()
    for forbidden in (
        "break_attempt",
        "breakout",
        "breakdown",
        "failed_break",
        "retest",
        "role_flip",
        "follow_through",
        "long_ready",
        "entry_advisory",
        "holder_advisory",
        "quality_score",
        "composite_score",
        "ranking",
        "place_order",
        "cancel_order",
        "modify_order",
        "unlock_trade",
        "broker_account",
    ):
        assert forbidden not in sources


def test_task006b_adds_no_migration_or_persistence_model() -> None:
    revisions = sorted(
        path.name for path in Path("src/ai_infra_quant/database/migrations/versions").glob("*.py")
    )
    assert revisions == ["0001_phase1_foundation.py"]
    assert not Path("src/ai_infra_quant/database/models/paqs_structure.py").exists()
    assert not Path("src/ai_infra_quant/database/repositories/paqs_structure.py").exists()
