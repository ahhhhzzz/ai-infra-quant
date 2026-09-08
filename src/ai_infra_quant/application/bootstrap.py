from __future__ import annotations

EXPECTED_REVISION = "0003_task007c1_narrative_ledger"


class DatabaseNotReadyError(RuntimeError):
    pass


def ensure_database_ready(revision: str | None) -> str:
    if revision != EXPECTED_REVISION:
        raise DatabaseNotReadyError(
            f"database revision is {revision or 'missing'}; expected {EXPECTED_REVISION}"
        )
    return revision
