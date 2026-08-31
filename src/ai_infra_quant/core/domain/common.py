from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID


def canonical_uuid(value: UUID | str) -> str:
    return str(value if isinstance(value, UUID) else UUID(value))


def require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(UTC)


def utc_now() -> datetime:
    return datetime.now(UTC)
