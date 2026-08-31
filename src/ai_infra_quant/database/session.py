from __future__ import annotations

from pathlib import Path
from typing import Any

from alembic.migration import MigrationContext
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker


def ensure_sqlite_database_parent(database_url: str) -> None:
    """Create the parent for a file-backed SQLite database URL."""
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite":
        return
    database = url.database
    if (
        not database
        or database == ":memory:"
        or database.startswith("file::memory:")
        or url.query.get("mode") == "memory"
    ):
        return
    Path(database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def create_database_engine(database_url: str) -> Engine:
    url = make_url(database_url)
    if url.drivername != "sqlite":
        raise ValueError("Phase 1 runtime supports SQLite only")
    ensure_sqlite_database_parent(database_url)
    engine = create_engine(database_url, future=True, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False, future=True)


def current_migration_revision(engine: Engine) -> str | None:
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()
