from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path

SOURCE_ROOT = Path("src/ai_infra_quant")
LEDGER_MODULES = (
    SOURCE_ROOT / "core/domain/paqs_e_ledger.py",
    SOURCE_ROOT / "core/ports/paqs_e_ledger.py",
    SOURCE_ROOT / "application/paqs_e_analysis.py",
    SOURCE_ROOT / "database/models/paqs_e_ledger.py",
    SOURCE_ROOT / "database/repositories/paqs_e_ledger.py",
    SOURCE_ROOT / "backend/api/v1/paqs_e.py",
    SOURCE_ROOT / "backend/schemas/paqs_e.py",
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


def test_ledger_domain_and_port_remain_independent_of_frameworks_and_adapters() -> None:
    forbidden = (
        "fastapi",
        "sqlalchemy",
        "sqlite3",
        "openai",
        "ai_infra_quant.backend",
        "ai_infra_quant.database",
        "ai_infra_quant.integrations",
    )
    for path in LEDGER_MODULES[:2]:
        assert not any(module.startswith(forbidden) for module in _imports(path))


def test_analyze_uses_core_ports_without_sdk_storage_or_internal_http_dependencies() -> None:
    path = SOURCE_ROOT / "application/paqs_e_analysis.py"
    forbidden = (
        "openai",
        "sqlalchemy",
        "sqlite3",
        "requests",
        "httpx",
        "urllib",
        "ai_infra_quant.backend",
        "ai_infra_quant.database",
        "ai_infra_quant.integrations",
    )
    assert not any(module.startswith(forbidden) for module in _imports(path))
    source = path.read_text(encoding="utf-8").lower()
    for forbidden_text in ("sqlite:///", ".sqlite", "market-snapshot", "float("):
        assert forbidden_text not in source


def test_openai_sdk_behavior_stays_in_the_reasoning_integration() -> None:
    for path in SOURCE_ROOT.rglob("*.py"):
        if any(module == "openai" or module.startswith("openai.") for module in _imports(path)):
            assert path.is_relative_to(SOURCE_ROOT / "integrations/openai_reasoning")


def test_database_adapter_keeps_strategy_loading_and_reasoning_outside_persistence() -> None:
    path = SOURCE_ROOT / "database/repositories/paqs_e_ledger.py"
    imports = _imports(path)
    assert not any(
        module.startswith(("ai_infra_quant.integrations", "ai_infra_quant.application"))
        for module in imports
    )
    source = path.read_text(encoding="utf-8")
    for forbidden in (
        "load_strategy",
        "load_prompt",
        ".read_text(",
        ".read_bytes(",
        "PaqsEReasoningRuntime(",
        "PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md",
    ):
        assert forbidden not in source


def test_task007b_adds_only_analysis_evidence_tables() -> None:
    path = SOURCE_ROOT / "database/models/paqs_e_ledger.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    table_names = {
        node.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__tablename__" for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
    }
    assert table_names == {
        "paqs_e_runtime_artifacts",
        "paqs_e_analysis_runs",
        "paqs_e_decisions",
    }
    model_names = {path.name for path in (SOURCE_ROOT / "database/models").glob("*.py")}
    assert model_names == {
        "__init__.py",
        "accounting.py",
        "paqs_e_ledger.py",
        "paqs_e_narrative.py",
        "portfolio.py",
        "security.py",
        "settings.py",
        "strategy.py",
    }


def test_market_refresh_has_no_analyze_action_or_hidden_dispatch() -> None:
    # TASK-007C explicitly adopts a user form; the backend refresh ban remains intact.
    # Real browser non-action/POST-count coverage lives in tests/browser/test_paqs_e_workbench.py.
    paths = [
        SOURCE_ROOT / path
        for path in (
            "application/market_data_queries.py",
            "application/paqs_market_snapshot_queries.py",
            "backend/api/v1/market_data.py",
        )
    ]
    for path in paths:
        source = path.read_text(encoding="utf-8").lower()
        assert "paqs-e" not in source
        assert "paqs_e" not in source


def test_frontend_analyze_post_is_owned_only_by_explicit_form() -> None:
    owned = list((SOURCE_ROOT / "frontend/static").glob("*.js"))
    sources = {path.name: path.read_text(encoding="utf-8") for path in owned}
    assert "/paqs-e/analyses" not in sources["app.js"]
    assert (
        sum(
            source.count('fetch("/api/v1/paqs-e/narrative-analyses",')
            for source in sources.values()
        )
        == 1
    )
    source = sources["paqs-e.js"]
    form = source.index('$("analyze-form").addEventListener("submit"')
    guard = source.index("inFlight = attempt;", form)
    dispatch = source.index('await fetch("/api/v1/paqs-e/narrative-analyses",', guard)
    assert form < guard < dispatch


def test_no_later_strategy_execution_or_broker_state_is_added_to_the_ledger() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in LEDGER_MODULES).lower()
    for forbidden in (
        "paqs_q",
        "paperfill",
        "paper_portfolio",
        "place_order",
        "cancel_order",
        "modify_order",
        "unlock_trade",
        "broker_order_id",
        "broker_account_id",
        "order_id",
        "position_id",
        "fill_id",
        "executed_quantity",
        "execution_status",
        "backgroundtasks",
        "create_task(",
    ):
        assert forbidden not in source
    assert not list(SOURCE_ROOT.rglob("*paqs_q*"))


def test_no_background_scheduler_or_worker_dependency_is_added() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
    requirements = project["dependencies"] + [
        requirement for group in project["optional-dependencies"].values() for requirement in group
    ]
    names = {
        re.split(r"[<>=!~\[]", requirement, maxsplit=1)[0].lower() for requirement in requirements
    }
    assert names.isdisjoint({"celery", "redis", "rq", "dramatiq", "apscheduler", "schedule"})
