from pathlib import Path
from typing import Any, cast

from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateTable

from ai_infra_quant.database.models.market_data_archive import captures, memberships, versions


def test_archive_dependency_and_action_boundaries() -> None:
    root = Path(__file__).resolve().parents[2] / "src/ai_infra_quant"
    service = (root / "application/market_data_archive.py").read_text(encoding="utf-8")
    repository = (root / "database/repositories/market_data_archive.py").read_text(encoding="utf-8")
    javascript = (root / "frontend/static/market-data-archive.js").read_text(encoding="utf-8")
    for forbidden in (
        "NarrativeGateway",
        "get_latest_quote",
        "get_market_status",
        "analyze(",
        "integrations.",
    ):
        assert forbidden not in service
    for forbidden in ("provider_factory", "integrations.", "httpx", "requests"):
        assert forbidden not in repository
    assert javascript.count('method: "POST"') == 1
    assert "innerHTML" not in javascript
    assert "narrative-analyses" not in javascript
    assert "setInterval" not in javascript


def test_archive_dialect_ddl_exact_types_and_fk_membership() -> None:
    sqlite_ddl = str(CreateTable(versions).compile(dialect=cast(Any, sqlite).dialect()))
    pg_ddl = str(CreateTable(versions).compile(dialect=cast(Any, postgresql).dialect()))
    assert "open TEXT NOT NULL" in sqlite_ddl
    assert "open NUMERIC(38,18) NOT NULL" in pg_ddl
    for dialect in (cast(Any, sqlite).dialect(), cast(Any, postgresql).dialect()):
        for table in (captures, memberships):
            ddl = str(CreateTable(table).compile(dialect=dialect))
            assert "FOREIGN KEY" in ddl
    assert len(memberships.foreign_key_constraints) == 2
