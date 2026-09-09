"""Short atomic inserts and keyset local reads. No provider import or mutable latest pointer."""

from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.core.domain.market_data_archive import (
    ArchivedBar,
    canonical_json,
    digest,
    instant,
)
from ai_infra_quant.core.domain.money import canonical_decimal_string, parse_decimal
from ai_infra_quant.core.ports.market_data_archive import ArchiveNotFound, ArchivePersistenceError
from ai_infra_quant.database.models.market_data_archive import captures, memberships, versions
from ai_infra_quant.database.models.security import SecurityModel


def _cursor(scope: str, position: Any) -> str:
    return (
        base64.urlsafe_b64encode(canonical_json([1, scope, position]).encode()).decode().rstrip("=")
    )


def _position(cursor: str | None, scope: str) -> Any:
    if cursor is None:
        return None
    try:
        if not 1 <= len(cursor) <= 512:
            raise ValueError
        version, actual_scope, value = json.loads(
            base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True)
        )
        if version != 1 or actual_scope != scope or _cursor(scope, value) != cursor:
            raise ValueError
        return value
    except (ValueError, TypeError, UnicodeError, binascii.Error) as exc:
        raise ValueError("Invalid archive cursor") from exc


def _payload(row: Any) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(row.payload_json)
    if (
        digest(value) != row.payload_hash
        or value["capture_id"] != row.capture_id
        or value["security_id"] != row.security_id
    ):
        raise ArchivePersistenceError("Archive integrity failure")
    return value


class SQLAlchemyMarketDataArchive:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    @contextmanager
    def _read_session(self) -> Iterator[Session]:
        try:
            with self.session_factory() as session:
                yield session
        except (SQLAlchemyError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ArchivePersistenceError("Local archive read failed") from exc

    def record(self, capture: dict[str, Any], bars: tuple[ArchivedBar, ...]) -> None:
        try:
            with self.session_factory() as session:
                # Serialize writers in SQLite; PostgreSQL serializes this Security's captures.
                if session.get_bind().dialect.name == "sqlite":
                    session.execute(sa.text("BEGIN IMMEDIATE"))
                else:
                    session.execute(
                        sa.select(SecurityModel.id)
                        .where(SecurityModel.id == capture["security_id"])
                        .with_for_update()
                    )
                session.execute(
                    captures.insert().values(
                        capture_id=capture["capture_id"],
                        security_id=capture["security_id"],
                        recorded_at=datetime.fromisoformat(capture["recorded_at"]),
                        payload_json=canonical_json(capture),
                        payload_hash=digest(capture),
                    )
                )
                counts = {"D1": 0, "M1": 0}
                existing: dict[str, str] = {}
                hashes = [bar.version_hash for bar in bars]
                for offset in range(0, len(hashes), 400):
                    existing.update(
                        session.execute(
                            sa.select(versions.c.version_hash, versions.c.payload_json).where(
                                versions.c.version_hash.in_(hashes[offset : offset + 400])
                            )
                        )
                        .tuples()
                        .all()
                    )
                inserts, members = [], []
                for bar in bars:
                    serialized = canonical_json(bar.payload)
                    if bar.version_hash in existing:
                        if existing[bar.version_hash] != serialized:
                            raise ArchivePersistenceError("Archive version collision")
                    else:
                        inserts.append(
                            {
                                "version_hash": bar.version_hash,
                                "identity_hash": bar.identity_hash,
                                "security_id": capture["security_id"],
                                "timeframe": bar.timeframe,
                                "sort_key": bar.sort_key,
                                "payload_json": serialized,
                                **{
                                    name: parse_decimal(bar.payload[name])
                                    for name in ("open", "high", "low", "close", "volume")
                                },
                            }
                        )
                        existing[bar.version_hash] = serialized
                    members.append(
                        {
                            "capture_id": capture["capture_id"],
                            "security_id": capture["security_id"],
                            "timeframe": bar.timeframe,
                            "ordinal": counts[bar.timeframe],
                            "version_hash": bar.version_hash,
                            "retrieved_at": datetime.fromisoformat(bar.retrieved_at),
                        }
                    )
                    counts[bar.timeframe] += 1
                if inserts:
                    session.execute(versions.insert(), inserts)
                session.execute(memberships.insert(), members)
                session.commit()
        except SQLAlchemyError as exc:
            raise ArchivePersistenceError(
                "Archive persistence failed; transaction rolled back"
            ) from exc

    def detail(self, capture_id: str) -> dict[str, Any]:
        with self._read_session() as session:
            row = session.execute(
                sa.select(captures).where(captures.c.capture_id == capture_id)
            ).first()
            if row is None:
                raise ArchiveNotFound("Capture not found")
            value = _payload(row)
            sizes = dict(
                session.execute(
                    sa.select(memberships.c.timeframe, sa.func.count())
                    .where(memberships.c.capture_id == capture_id)
                    .group_by(memberships.c.timeframe)
                )
                .tuples()
                .all()
            )
            if any(sizes.get(tf, 0) != value["batches"][tf]["count"] for tf in ("D1", "M1")):
                raise ArchivePersistenceError("Capture membership integrity failure")
            return value

    def list_captures(
        self, security_id: str, limit: int = 20, cursor: str | None = None
    ) -> dict[str, Any]:
        if not 1 <= limit <= 50:
            raise ValueError("Capture page limit must be 1..50")
        scope = f"captures:{security_id}"
        position = _position(cursor, scope)
        query = sa.select(captures).where(captures.c.security_id == security_id)
        with self._read_session() as session:
            if session.get(SecurityModel, security_id) is None:
                raise ArchiveNotFound("Security not found")
            if position is not None:
                if not isinstance(position, str):
                    raise ValueError("Invalid archive cursor")
                anchor = session.execute(
                    sa.select(captures).where(
                        captures.c.capture_id == position, captures.c.security_id == security_id
                    )
                ).first()
                if anchor is None:
                    raise ValueError("Invalid archive cursor")
                query = query.where(
                    sa.or_(
                        captures.c.recorded_at < anchor.recorded_at,
                        sa.and_(
                            captures.c.recorded_at == anchor.recorded_at,
                            captures.c.capture_id < anchor.capture_id,
                        ),
                    )
                )
            rows = session.execute(
                query.order_by(captures.c.recorded_at.desc(), captures.c.capture_id.desc()).limit(
                    limit + 1
                )
            ).all()
            items = [_payload(row) for row in rows[:limit]]
            for item in items:
                item.pop("calendar")
            return {
                "items": items,
                "next_cursor": _cursor(scope, rows[limit - 1].capture_id)
                if len(rows) > limit
                else None,
            }

    def read_bars(
        self, capture_id: str, timeframe: str, limit: int = 500, cursor: str | None = None
    ) -> dict[str, Any]:
        if timeframe not in {"D1", "M1"} or not 1 <= limit <= 1000:
            raise ValueError("Invalid timeframe or page limit")
        capture = self.detail(capture_id)
        scope = f"bars:{capture_id}:{timeframe}"
        position = _position(cursor, scope)
        if position is not None and (
            type(position) is not int or not 0 <= position < capture["batches"][timeframe]["count"]
        ):
            raise ValueError("Invalid archive cursor")
        with self._read_session() as session:
            query = (
                sa.select(versions, memberships.c.ordinal, memberships.c.retrieved_at)
                .join(memberships, memberships.c.version_hash == versions.c.version_hash)
                .where(
                    memberships.c.capture_id == capture_id,
                    memberships.c.timeframe == timeframe,
                    memberships.c.ordinal > (-1 if position is None else position),
                )
            )
            rows = session.execute(query.order_by(memberships.c.ordinal).limit(limit + 1)).all()
            items = []
            for row in rows[:limit]:
                payload = json.loads(row.payload_json)
                if digest(payload) != row.version_hash or any(
                    canonical_decimal_string(getattr(row, name)) != payload[name]
                    for name in ("open", "high", "low", "close", "volume")
                ):
                    raise ArchivePersistenceError("Archive bar integrity failure")
                items.append(
                    payload
                    | {
                        "version_hash": row.version_hash,
                        "ordinal": row.ordinal,
                        "retrieved_at": instant(row.retrieved_at),
                    }
                )
            return {
                "capture_id": capture_id,
                "timeframe": timeframe,
                "items": items,
                "next_cursor": _cursor(scope, rows[limit - 1].ordinal)
                if len(rows) > limit
                else None,
            }
