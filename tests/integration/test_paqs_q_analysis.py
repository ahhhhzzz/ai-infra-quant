"""Focused append-only Q analysis persistence and migration checks."""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields
from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, sessionmaker
from test_migrations import _alembic_config

from ai_infra_quant.config import Settings
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot, canonical_json
from ai_infra_quant.database.repositories.paqs_q_analysis import (
    PaqsQAnalysisIntegrityError,
    SQLAlchemyPaqsQAnalysisStore,
)
from ai_infra_quant.database.seed import bootstrap_phase_one
from ai_infra_quant.database.session import current_migration_revision


def _payload(security_id: str, *, reason: str) -> dict:
    snapshot = {field.name: None for field in fields(PaqsMarketSnapshot)}
    snapshot.update(
        snapshot_schema_version="paqs-market-snapshot-v1",
        security={"security_id": security_id},
        as_of_timestamp="2026-09-23T13:00:00Z",
        created_at="2026-09-23T13:01:00Z",
        w1_bars=[],
        d1_bars=[],
        m30_bars=[],
        timeframe_evidence_status={"w1": {}, "d1": {}, "m30": {}},
    )
    hash_payload = {
        key: value for key, value in snapshot.items() if key not in {"snapshot_hash", "created_at"}
    }
    hash_payload["timeframe_evidence_status"] = {"W1": {}, "D1": {}, "M30": {}}
    snapshot["snapshot_hash"] = hashlib.sha256(canonical_json(hash_payload).encode()).hexdigest()
    return {
        "market_snapshot": snapshot,
        "q_inputs": {"mode": "OBSERVATIONAL"},
        "context": {"status": "INSUFFICIENT"},
        "event": {"status": "INSUFFICIENT"},
        "setup": {"status": "INSUFFICIENT", "reason": reason},
        "holder": {"status": "UNDETERMINED"},
        "diagnostics": [reason],
    }


def test_q_analysis_create_reopen_history_and_database_immutability(
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    settings: Settings,
) -> None:
    security_id = bootstrap_phase_one(session_factory, settings).security_ids[0]
    first_payload = _payload(security_id, reason="CALENDAR_MISSING")
    snapshot_hash = first_payload["market_snapshot"]["snapshot_hash"]
    instants = iter(
        (
            datetime(2026, 9, 23, 13, tzinfo=UTC),
            datetime(2026, 9, 23, 13, tzinfo=UTC) + timedelta(minutes=1),
        )
    )
    store = SQLAlchemyPaqsQAnalysisStore(session_factory, now=lambda: next(instants))
    first = store.record(
        security_id=security_id,
        snapshot_hash=snapshot_hash,
        status="INSUFFICIENT",
        payload=first_payload,
    )
    first_payload["setup"]["reason"] = "MUTATED_AFTER_RECORD"
    second = store.record(
        security_id=security_id,
        snapshot_hash=snapshot_hash,
        status="INSUFFICIENT",
        payload=_payload(security_id, reason="ENTRY_REFERENCE_MISSING"),
    )
    assert first["analysis_id"] != second["analysis_id"]
    assert first["payload"]["setup"]["reason"] == "CALENDAR_MISSING"
    assert store.get(first["analysis_id"]) == first
    assert store.history(security_id, limit=1) == [
        {key: value for key, value in second.items() if key != "payload"}
    ]
    assert store.history(security_id) == [
        {key: value for key, value in item.items() if key != "payload"} for item in (second, first)
    ]
    assert store.get("00000000-0000-4000-8000-000000000000") is None
    with migrated_engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT payload_json,payload_sha256 FROM paqs_q_analysis_runs WHERE analysis_id=:id"
            ),
            {"id": first["analysis_id"]},
        ).one()
    assert row.payload_json == canonical_json(first["payload"])
    assert row.payload_sha256 == hashlib.sha256(row.payload_json.encode()).hexdigest()
    for statement in (
        "UPDATE paqs_q_analysis_runs SET status='AVAILABLE' WHERE analysis_id=:id",
        "DELETE FROM paqs_q_analysis_runs WHERE analysis_id=:id",
    ):
        with pytest.raises(DatabaseError), migrated_engine.begin() as connection:
            connection.execute(text(statement), {"id": first["analysis_id"]})
    assert store.get(first["analysis_id"]) == first


def test_q_analysis_rejects_identity_and_digest_corruption(
    migrated_engine: Engine,
    session_factory: sessionmaker[Session],
    settings: Settings,
) -> None:
    security_id = bootstrap_phase_one(session_factory, settings).security_ids[0]
    store = SQLAlchemyPaqsQAnalysisStore(session_factory)
    payload = _payload(security_id, reason="W1_MISSING")
    snapshot_hash = payload["market_snapshot"]["snapshot_hash"]
    with pytest.raises(PaqsQAnalysisIntegrityError, match="identity"):
        store.record(
            security_id=security_id,
            snapshot_hash="c" * 64,
            status="INSUFFICIENT",
            payload=payload,
        )
    corrupted_snapshot = json.loads(canonical_json(payload))
    corrupted_snapshot["market_snapshot"]["d1_bars"] = [{"invented": True}]
    with pytest.raises(PaqsQAnalysisIntegrityError, match="content hash"):
        store.record(
            security_id=security_id,
            snapshot_hash=snapshot_hash,
            status="INSUFFICIENT",
            payload=corrupted_snapshot,
        )
    with pytest.raises(PaqsQAnalysisIntegrityError, match="status"):
        store.record(
            security_id=security_id,
            snapshot_hash=snapshot_hash,
            status="lowercase",
            payload=payload,
        )
    recorded = store.record(
        security_id=security_id,
        snapshot_hash=snapshot_hash,
        status="INSUFFICIENT",
        payload=payload,
    )
    with migrated_engine.begin() as connection:
        connection.execute(text("DROP TRIGGER paqs_q_analysis_runs_immutable_update"))
        connection.execute(
            text("UPDATE paqs_q_analysis_runs SET payload_json=:payload WHERE analysis_id=:id"),
            {"id": recorded["analysis_id"], "payload": json.dumps({"tampered": True})},
        )
    with pytest.raises(PaqsQAnalysisIntegrityError, match="digest"):
        store.get(recorded["analysis_id"])
    with pytest.raises(PaqsQAnalysisIntegrityError, match="digest"):
        store.history(security_id)


def test_additive_0005_migration_does_not_change_0004_tables(database_url: str) -> None:
    config = _alembic_config(database_url)
    command.upgrade(config, "0004_task006b1_market_archive")
    from ai_infra_quant.database.session import create_database_engine

    engine = create_database_engine(database_url)
    try:
        original = set(inspect(engine).get_table_names())
        command.upgrade(config, "head")
        assert current_migration_revision(engine) == "0005_task006e_q_analysis"
        assert set(inspect(engine).get_table_names()) == original | {"paqs_q_analysis_runs"}
        with engine.connect() as connection:
            triggers = set(
                connection.execute(
                    text("SELECT name FROM sqlite_master WHERE type='trigger'")
                ).scalars()
            )
        assert {
            "paqs_q_analysis_runs_immutable_update",
            "paqs_q_analysis_runs_immutable_delete",
        } <= triggers
        command.downgrade(config, "0004_task006b1_market_archive")
        assert set(inspect(engine).get_table_names()) == original
        assert current_migration_revision(engine) == "0004_task006b1_market_archive"
    finally:
        engine.dispose()
