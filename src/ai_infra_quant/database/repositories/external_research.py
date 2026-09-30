from __future__ import annotations

import json
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.core.domain.common import canonical_uuid, utc_now
from ai_infra_quant.core.domain.paqs_e_ledger import (
    LedgerIntegrityError,
    LedgerPersistenceError,
    payload_sha256,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot, canonical_json
from ai_infra_quant.database.models.external_research import searches


class SQLAlchemySearchEvidence:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.sessions = sessions

    def record(
        self,
        research_id: str,
        snapshot: PaqsMarketSnapshot,
        status: str,
        payload: dict[str, object],
    ) -> None:
        raw = canonical_json(payload)
        try:
            with self.sessions.begin() as session:
                session.execute(
                    insert(searches).values(
                        research_id=research_id,
                        security_id=snapshot.security.security_id,
                        snapshot_hash=snapshot.snapshot_hash,
                        snapshot_as_of=snapshot.as_of_timestamp,
                        status=status,
                        payload_json=raw,
                        payload_sha256=payload_sha256(raw),
                        created_at=utc_now(),
                    )
                )
        except SQLAlchemyError:
            raise LedgerPersistenceError("External research evidence unavailable") from None

    def get(self, research_id: str) -> dict[str, Any] | None:
        canonical_uuid(research_id)
        try:
            with self.sessions() as session:
                row = (
                    session.execute(select(searches).where(searches.c.research_id == research_id))
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                return None
            if payload_sha256(row["payload_json"]) != row["payload_sha256"]:
                raise LedgerIntegrityError("External research evidence digest mismatch")
            return {**dict(row), "payload": json.loads(row["payload_json"])}
        except SQLAlchemyError:
            raise LedgerPersistenceError("External research evidence unavailable") from None
