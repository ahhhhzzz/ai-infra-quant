"""Immutable PAQS-Q product analysis storage; reads never invoke strategy code."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import fields
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.core.domain.common import canonical_uuid, require_utc
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot, canonical_json
from ai_infra_quant.database.models.paqs_q_analysis import paqs_q_analysis_runs


class PaqsQAnalysisIntegrityError(ValueError):
    """Supplied or stored Q analysis identity/evidence is inconsistent."""


class PaqsQAnalysisPersistenceError(RuntimeError):
    """A Q analysis could not be committed."""


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _verify_payload(
    payload: dict[str, Any], *, security_id: str, snapshot_hash: str, status: str
) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", snapshot_hash):
        raise PaqsQAnalysisIntegrityError("Invalid Q Snapshot hash")
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,39}", status):
        raise PaqsQAnalysisIntegrityError("Invalid Q analysis status")
    if type(payload) is not dict:
        raise PaqsQAnalysisIntegrityError("Q analysis payload must be an object")
    snapshot = payload.get("market_snapshot")
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("security"), dict):
        raise PaqsQAnalysisIntegrityError("Frozen Q Snapshot is missing")
    if (
        snapshot.get("snapshot_hash") != snapshot_hash
        or snapshot["security"].get("security_id") != security_id
    ):
        raise PaqsQAnalysisIntegrityError("Q Snapshot identity differs from analysis")
    if set(snapshot) != {field.name for field in fields(PaqsMarketSnapshot)}:
        raise PaqsQAnalysisIntegrityError("Frozen Q Snapshot is incomplete")
    timeframe_evidence = snapshot.get("timeframe_evidence_status")
    if not isinstance(timeframe_evidence, dict) or set(timeframe_evidence) != {
        "w1",
        "d1",
        "m30",
    }:
        raise PaqsQAnalysisIntegrityError("Frozen Q Snapshot timeframe evidence is incomplete")
    hash_payload = {
        key: value for key, value in snapshot.items() if key not in {"snapshot_hash", "created_at"}
    }
    hash_payload["timeframe_evidence_status"] = {
        key.upper(): value for key, value in timeframe_evidence.items()
    }
    try:
        computed_snapshot_hash = _digest(canonical_json(hash_payload))
    except (TypeError, ValueError) as exc:
        raise PaqsQAnalysisIntegrityError("Frozen Q Snapshot content is invalid") from exc
    if computed_snapshot_hash != snapshot_hash:
        raise PaqsQAnalysisIntegrityError("Frozen Q Snapshot content hash mismatch")
    if "status" in payload and payload["status"] != status:
        raise PaqsQAnalysisIntegrityError("Q analysis status differs from payload")
    try:
        return canonical_json(payload)
    except (TypeError, ValueError) as exc:
        raise PaqsQAnalysisIntegrityError("Q analysis payload is not canonical JSON") from exc


def _read_row(row: Any, *, include_payload: bool) -> dict[str, Any]:
    values = dict(row)
    try:
        payload_text = values["payload_json"]
        if _digest(payload_text) != values["payload_sha256"]:
            raise PaqsQAnalysisIntegrityError("Q analysis payload digest mismatch")
        payload = json.loads(payload_text)
        if (
            _verify_payload(
                payload,
                security_id=canonical_uuid(values["security_id"]),
                snapshot_hash=values["snapshot_hash"],
                status=values["status"],
            )
            != payload_text
        ):
            raise PaqsQAnalysisIntegrityError("Q analysis JSON is noncanonical")
        created_at = require_utc(values["created_at"])
        canonical_uuid(values["analysis_id"])
    except PaqsQAnalysisIntegrityError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise PaqsQAnalysisIntegrityError("Stored Q analysis evidence is invalid") from exc
    result = {
        "analysis_id": values["analysis_id"],
        "security_id": values["security_id"],
        "snapshot_hash": values["snapshot_hash"],
        "status": values["status"],
        "created_at": created_at.isoformat().replace("+00:00", "Z"),
        "payload_sha256": values["payload_sha256"],
    }
    if include_payload:
        result["payload"] = payload
    return result


class SQLAlchemyPaqsQAnalysisStore:
    """One explicit analysis inserts one immutable full payload and its digest."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        *,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._sessions = session_factory
        self._now = now

    def record(
        self,
        *,
        security_id: str,
        snapshot_hash: str,
        status: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        security_id = canonical_uuid(security_id)
        payload_text = _verify_payload(
            payload, security_id=security_id, snapshot_hash=snapshot_hash, status=status
        )
        analysis_id = str(uuid4())
        values = {
            "analysis_id": analysis_id,
            "security_id": security_id,
            "snapshot_hash": snapshot_hash,
            "status": status,
            "created_at": require_utc(self._now()),
            "payload_json": payload_text,
            "payload_sha256": _digest(payload_text),
        }
        try:
            with self._sessions.begin() as session:
                session.execute(sa.insert(paqs_q_analysis_runs).values(**values))
        except SQLAlchemyError as exc:
            raise PaqsQAnalysisPersistenceError("Q analysis could not be committed") from exc
        return _read_row(values, include_payload=True)

    def get(self, analysis_id: str) -> dict[str, Any] | None:
        analysis_id = canonical_uuid(analysis_id)
        try:
            with self._sessions() as session:
                row = (
                    session.execute(
                        sa.select(paqs_q_analysis_runs).where(
                            paqs_q_analysis_runs.c.analysis_id == analysis_id
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                return _read_row(row, include_payload=True) if row else None
        except SQLAlchemyError as exc:
            raise PaqsQAnalysisIntegrityError("Q analysis could not be read") from exc

    def history(self, security_id: str, limit: int = 20) -> list[dict[str, Any]]:
        security_id = canonical_uuid(security_id)
        if isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("Q analysis history limit must be 1..100")
        try:
            with self._sessions() as session:
                rows = (
                    session.execute(
                        sa.select(paqs_q_analysis_runs)
                        .where(paqs_q_analysis_runs.c.security_id == security_id)
                        .order_by(
                            paqs_q_analysis_runs.c.created_at.desc(),
                            paqs_q_analysis_runs.c.analysis_id.desc(),
                        )
                        .limit(limit)
                    )
                    .mappings()
                    .all()
                )
                return [_read_row(row, include_payload=False) for row in rows]
        except SQLAlchemyError as exc:
            raise PaqsQAnalysisIntegrityError("Q analysis history could not be read") from exc


# The ledger name is also valid for callers that use the existing E naming convention.
SQLAlchemyPaqsQAnalysisLedger = SQLAlchemyPaqsQAnalysisStore
