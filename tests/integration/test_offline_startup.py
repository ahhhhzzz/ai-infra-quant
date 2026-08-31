from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_infra_quant.application.bootstrap import DatabaseNotReadyError
from ai_infra_quant.backend.main import create_app
from ai_infra_quant.config import Settings
from ai_infra_quant.database.session import create_database_engine


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def test_migrated_app_starts_offline_and_renders_dashboard(client: TestClient) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["database"] == "READY"
    dashboard = client.get("/")
    assert dashboard.status_code == 200
    text = dashboard.text.upper()
    assert "AI INFRA QUANT" in text
    assert "PAPER BROKER: NOT IMPLEMENTED" in text
    assert "LIVE ROUTES: ABSENT" in text
    assert "BUY" not in text and "SELL" not in text


def test_unmigrated_database_refuses_startup(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "unmigrated.db")
    engine = create_database_engine(database_url)
    app = create_app(Settings(database_url=database_url), engine)
    with pytest.raises(DatabaseNotReadyError), TestClient(app):
        pass
    engine.dispose()
