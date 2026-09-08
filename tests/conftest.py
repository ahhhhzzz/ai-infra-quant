from __future__ import annotations

from argparse import Namespace
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from paqs_e_support import MemoryCredentials
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.backend.main import create_app
from ai_infra_quant.config import Settings
from ai_infra_quant.database.session import create_database_engine, create_session_factory


@pytest.fixture(autouse=True)
def isolated_os_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ai_infra_quant.backend.dependencies.WindowsCredentialStore", MemoryCredentials
    )


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def upgrade_database(database_url: str) -> None:
    config = Config("alembic.ini")
    config.cmd_opts = Namespace(x=[f"database_url={database_url}"])
    command.upgrade(config, "head")


@pytest.fixture
def database_url(tmp_path: Path) -> str:
    return sqlite_url(tmp_path / "phase1-test.db")


@pytest.fixture
def migrated_engine(database_url: str) -> Iterator[Engine]:
    upgrade_database(database_url)
    engine = create_database_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(migrated_engine: Engine) -> sessionmaker[Session]:
    return create_session_factory(migrated_engine)


@pytest.fixture
def settings(database_url: str) -> Settings:
    return Settings(database_url=database_url)


@pytest.fixture
def client(settings: Settings, migrated_engine: Engine) -> Iterator[TestClient]:
    with TestClient(create_app(settings, migrated_engine)) as test_client:
        yield test_client
