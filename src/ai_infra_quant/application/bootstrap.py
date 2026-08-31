from __future__ import annotations

EXPECTED_REVISION = "0001_phase1_foundation"


class DatabaseNotReadyError(RuntimeError):
    pass


def ensure_database_ready(revision: str | None) -> str:
    if revision != EXPECTED_REVISION:
        raise DatabaseNotReadyError(
            f"database revision is {revision or 'missing'}; expected {EXPECTED_REVISION}"
        )
    return revision
