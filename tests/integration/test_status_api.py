from fastapi.testclient import TestClient
from sqlalchemy import Engine, inspect


def test_broker_and_provider_statuses_are_truthful(client: TestClient) -> None:
    brokers = client.get("/api/v1/brokers")
    assert brokers.status_code == 200
    by_name = {item["name"]: item for item in brokers.json()["items"]}
    assert by_name["paper"]["implementation_status"] == "NOT_IMPLEMENTED"
    assert by_name["futu"]["connection_status"] == "UNAVAILABLE"
    assert by_name["eastmoney"]["implementation_status"] == "NOT_IMPLEMENTED"
    market_data = client.get("/api/v1/market-data/providers").json()["items"]
    market_data_by_name = {item["name"]: item for item in market_data}
    assert market_data_by_name["futu"]["implementation_status"] == "SUPPORTED"
    assert market_data_by_name["futu"]["connection_status"] == "UNKNOWN"
    assert market_data_by_name["none"]["implementation_status"] == "UNAVAILABLE"
    for path in ("/api/v1/fundamental-data/providers", "/api/v1/event-data/providers"):
        item = client.get(path).json()["items"][0]
        assert item["name"] == "none"
        assert item["implementation_status"] == "UNAVAILABLE"
        assert item["connection_status"] == "UNAVAILABLE"


def test_status_reads_do_not_record_a_connection_attempt(client: TestClient) -> None:
    first = client.get("/api/v1/brokers/futu/status").json()
    second = client.get("/api/v1/brokers/futu/status").json()
    assert first == second
    assert first["last_checked_at"] is None
    assert first["capabilities"] == []


def test_unknown_broker_is_problem(client: TestClient) -> None:
    response = client.get("/api/v1/brokers/unknown/status")
    assert response.status_code == 404
    assert response.json()["code"] == "BROKER_NOT_FOUND"


def test_strategy_status_sources_cannot_drift(client: TestClient, migrated_engine: Engine) -> None:
    columns = {
        column["name"] for column in inspect(migrated_engine).get_columns("strategy_definitions")
    }
    assert "implementation_status" not in columns
    assert "implementation_key" in columns
    response = client.get("/api/v1/strategies")
    assert response.status_code == 200
    strategy = response.json()["items"][0]
    assert strategy == {
        "id": strategy["id"],
        "name": "AIInfraStrategy",
        "version": "1.0.0",
        "implementation_status": "NOT_IMPLEMENTED",
        "research_status": "RESEARCH_UNVALIDATED",
        "enabled": False,
        "required_data_status": "UNAVAILABLE",
    }
