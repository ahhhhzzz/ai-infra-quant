from __future__ import annotations

EXPECTED_REVISION = "0004_task006b1_market_archive"


class DatabaseNotReadyError(RuntimeError):
    pass


def ensure_database_ready(revision: str | None) -> str:
    if revision != EXPECTED_REVISION:
        raise DatabaseNotReadyError(
            f"database revision is {revision or 'missing'}; expected {EXPECTED_REVISION}"
        )
    return revision
