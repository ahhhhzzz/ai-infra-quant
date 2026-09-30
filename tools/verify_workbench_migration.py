"""Back up an explicit local SQLite file, migrate, verify all pre-existing business bytes."""

import hashlib
import json
import sqlite3
from argparse import Namespace
from contextlib import closing
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config


def inventory(db: sqlite3.Connection) -> dict:
    tables = {}
    names = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    for (name,) in names:
        if name == "alembic_version":
            continue
        quoted = '"' + name.replace('"', '""') + '"'
        hashes = sorted(
            hashlib.sha256(repr(row).encode()).hexdigest()
            for row in db.execute(f"SELECT * FROM {quoted}")
        )
        tables[name] = {
            "count": len(hashes),
            "sha256": hashlib.sha256("".join(hashes).encode()).hexdigest(),
        }
    triggers = db.execute(
        "SELECT name,sql FROM sqlite_master WHERE type='trigger' ORDER BY name"
    ).fetchall()
    return {"tables": tables, "triggers": triggers}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "data" / "ai_infra_quant.db"
    backup = (
        source.parent
        / "backups"
        / ("before_issue2_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".db")
    )
    backup.parent.mkdir(parents=True, exist_ok=True)
    with (
        closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as src,
        closing(sqlite3.connect(backup)) as dst,
    ):
        src.backup(dst)
        assert dst.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        before = inventory(dst)
        revision_before = dst.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    assert revision_before == "0006_external_research", (
        "Unexpected migration baseline; backup retained"
    )
    config = Config(str(root / "alembic.ini"))
    config.cmd_opts = Namespace(x=[f"database_url=sqlite:///{source.as_posix()}"])
    command.upgrade(config, "head")
    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as db:
        after = inventory(db)
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert (
            db.execute("SELECT version_num FROM alembic_version").fetchone()[0]
            == "0007_analysis_visibility"
        )
    assert all(after["tables"][k] == v for k, v in before["tables"].items())
    assert before["triggers"] == after["triggers"]
    assert set(after["tables"]) - set(before["tables"]) == {"analysis_visibility"}
    report = {
        "backup_file": backup.name,
        "from": revision_before,
        "to": "0007_analysis_visibility",
        "existing_tables": before["tables"],
        "preserved_trigger_count": len(before["triggers"]),
        "business_bytes_unchanged": True,
        "integrity_check": "ok",
        "foreign_key_check": [],
    }
    target = root / "docs/evidence/TASK_V1_1/migration.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "backup": str(backup),
                "business_bytes_unchanged": True,
                "tables_verified": len(before["tables"]),
                "report": str(target),
            }
        )
    )


if __name__ == "__main__":
    main()
