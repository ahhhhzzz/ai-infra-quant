from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from ai_infra_quant.application.bootstrap import DatabaseNotReadyError
from ai_infra_quant.backend.main import create_app
from ai_infra_quant.config import Settings
from ai_infra_quant.database.session import create_database_engine
from ai_infra_quant.integrations.futu_quote import adapter as futu_adapter


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
    assert "READ ONLY · DECISION SUPPORT" in text
    assert 'ID="SECURITY-SELECTOR"' in text
    assert 'ID="DECISION-HISTORY"' in text
    assert "PORTFOLIO FACTS AND LOCAL ADMINISTRATION" not in text
    assert "BUY" not in text and "SELL" not in text


def test_unmigrated_database_refuses_startup(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "unmigrated.db")
    engine = create_database_engine(database_url)
    app = create_app(Settings(database_url=database_url), engine)
    with pytest.raises(DatabaseNotReadyError), TestClient(app):
        pass
    engine.dispose()


def test_futu_configuration_starts_without_importing_optional_sdk(
    database_url: str,
    migrated_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_sdk(_name: str) -> object:
        raise ImportError("futu intentionally unavailable in test")

    monkeypatch.setattr(futu_adapter, "import_module", missing_sdk)
    app = create_app(
        Settings(database_url=database_url, market_data_provider="futu"),
        migrated_engine,
    )
    with TestClient(app) as test_client:
        assert test_client.get("/health").status_code == 200
        security_id = test_client.get("/api/v1/watchlist").json()["items"][0]["security"]["id"]
        response = test_client.get(f"/api/v1/market-data/securities/{security_id}/state")
    assert response.status_code == 200
    assert response.json()["quote_status"] == "UNAVAILABLE"
    assert "optional dependency missing" in response.json()["reason"]
