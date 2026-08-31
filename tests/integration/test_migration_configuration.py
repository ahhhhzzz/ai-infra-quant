from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"
MIGRATION_SCRIPTS = PROJECT_ROOT / "src/ai_infra_quant/database/migrations"


def _clean_environment() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key.upper() != "DATABASE_URL"}


def _isolated_alembic_directory(tmp_path: Path) -> Path:
    configuration = SOURCE_ALEMBIC_INI.read_text(encoding="utf-8")
    configuration = re.sub(
        r"(?m)^script_location\s*=.*$",
        f"script_location = {MIGRATION_SCRIPTS.resolve().as_posix()}",
        configuration,
    )
    (tmp_path / "alembic.ini").write_text(configuration, encoding="utf-8")
    return tmp_path


def _run_alembic(cwd: Path, *arguments: str, env: dict[str, str]) -> str:
    completed = subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    return output


def _assert_at_head(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    assert revision == ("0001_phase1_foundation",)


def test_default_command_creates_pristine_nested_sqlite_parent(tmp_path: Path) -> None:
    cwd = _isolated_alembic_directory(tmp_path)
    database_path = cwd / "data/ai_infra_quant.db"

    _run_alembic(cwd, "upgrade", "head", env=_clean_environment())

    assert database_path.is_file()
    _assert_at_head(database_path)


def test_database_url_environment_is_honored_without_creating_default(tmp_path: Path) -> None:
    cwd = _isolated_alembic_directory(tmp_path)
    database_path = cwd / "configured/nested/environment.db"
    env = _clean_environment()
    env["DATABASE_URL"] = "sqlite:///./configured/nested/environment.db"

    _run_alembic(cwd, "upgrade", "head", env=env)

    assert database_path.is_file()
    assert not (cwd / "data/ai_infra_quant.db").exists()
    _assert_at_head(database_path)


def test_database_url_dotenv_is_honored_without_creating_default(tmp_path: Path) -> None:
    cwd = _isolated_alembic_directory(tmp_path)
    database_path = cwd / "configured/nested/dotenv.db"
    (cwd / ".env").write_text(
        "DATABASE_URL=sqlite:///./configured/nested/dotenv.db\n",
        encoding="utf-8",
    )

    _run_alembic(cwd, "upgrade", "head", env=_clean_environment())

    assert database_path.is_file()
    assert not (cwd / "data/ai_infra_quant.db").exists()
    _assert_at_head(database_path)


def test_explicit_database_url_overrides_settings_environment(tmp_path: Path) -> None:
    cwd = _isolated_alembic_directory(tmp_path)
    override_path = cwd / "override/nested/explicit.db"
    env = _clean_environment()
    env["DATABASE_URL"] = "sqlite:///./configured/environment.db"

    _run_alembic(
        cwd,
        "-x",
        "database_url=sqlite:///./override/nested/explicit.db",
        "upgrade",
        "head",
        env=env,
    )

    assert override_path.is_file()
    assert not (cwd / "configured/environment.db").exists()
    assert not (cwd / "data/ai_infra_quant.db").exists()
    _assert_at_head(override_path)


def test_postgresql_offline_ddl_has_portable_globally_unique_names() -> None:
    ddl = _run_alembic(
        PROJECT_ROOT,
        "-x",
        "database_url=postgresql://phase1:phase1@localhost/phase1",
        "upgrade",
        "head",
        "--sql",
        env=_clean_environment(),
    )
    constraint_names = re.findall(r"\bCONSTRAINT\s+([a-zA-Z0-9_]+)", ddl)
    table_names = re.findall(r"\bCREATE TABLE\s+([a-zA-Z0-9_]+)", ddl)
    index_names = re.findall(r"\bCREATE(?: UNIQUE)? INDEX\s+([a-zA-Z0-9_]+)", ddl)
    backing_index_names = re.findall(
        r"\bCONSTRAINT\s+([a-zA-Z0-9_]+)\s+(?:PRIMARY KEY|UNIQUE)", ddl
    )

    assert not [name for name, count in Counter(constraint_names).items() if count > 1]
    relation_names = table_names + index_names + backing_index_names
    assert not [name for name, count in Counter(relation_names).items() if count > 1]
    assert all(len(name) <= 63 for name in constraint_names + table_names + index_names)
    assert {
        "uq_securities_market_symbol",
        "uq_strategy_definitions_name_version",
        "uq_broker_profiles_name",
        "uq_portfolios_name",
        "uq_ledger_transactions_sequence_no",
        "uq_ledger_transactions_portfolio_idempotency_key",
        "uq_cash_flows_portfolio_idempotency_key",
    }.issubset(constraint_names)
    assert "WHERE is_default IS TRUE" in ddl
    assert "WHERE is_default = 1" not in ddl
