from __future__ import annotations

import ast
from pathlib import Path

CORE_SNAPSHOT = Path("src/ai_infra_quant/core/domain/paqs_market_snapshot.py")
TASK_MODULES = (
    CORE_SNAPSHOT,
    Path("src/ai_infra_quant/application/paqs_market_snapshot_queries.py"),
    Path("src/ai_infra_quant/backend/schemas/paqs_market_snapshot.py"),
    Path("src/ai_infra_quant/backend/api/v1/paqs_market_snapshot.py"),
)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
    return imports


def test_core_snapshot_is_provider_neutral_and_has_no_runtime_or_storage_dependency() -> None:
    forbidden = ("fastapi", "sqlalchemy", "futu", "openai", "ai_infra_quant.backend")
    assert not any(module.startswith(forbidden) for module in _imports(CORE_SNAPSHOT))
    source = CORE_SNAPSHOT.read_text(encoding="utf-8")
    assert "os.environ" not in source
    assert "core.strategy" not in source
    assert "float(" not in source


def test_task006b2_adds_no_model_provider_strategy_or_write_capability() -> None:
    product_source = "\n".join(path.read_text(encoding="utf-8") for path in TASK_MODULES).lower()
    for forbidden in (
        "openai_api_key",
        "openai client",
        "place_order",
        "cancel_order",
        "modify_order",
        "unlock_trade",
        "broker_account",
        "executable_entry_reference",
        "quote_freshness_policy",
    ):
        assert forbidden not in product_source
    # TASK-007A adds an OpenAI reasoning adapter, but the accepted TASK-006B2
    # snapshot modules themselves remain provider- and strategy-neutral.


def test_snapshot_public_schema_has_no_strategy_conclusion_fields() -> None:
    from ai_infra_quant.backend.schemas.paqs_market_snapshot import PaqsMarketSnapshotRead

    fields = set(PaqsMarketSnapshotRead.model_fields)
    assert fields.isdisjoint(
        {
            "pivots",
            "zones",
            "ranges",
            "regime",
            "events",
            "setup",
            "trigger",
            "advisory",
            "risk_reward",
            "score",
            "ranking",
        }
    )


def test_snapshot_has_no_separate_market_data_storage_migration() -> None:
    migrations = Path("src/ai_infra_quant/database/migrations/versions").glob("*.py")
    assert sorted(path.name for path in migrations) == [
        "0001_phase1_foundation.py",
        "0002_task007b_paqs_e_decision_ledger.py",
        "0003_task007c1_narrative_ledger.py",
    ]
    assert not Path("src/ai_infra_quant/database/models/paqs_market_snapshot.py").exists()
