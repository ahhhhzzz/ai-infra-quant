import pytest
from fastapi.testclient import TestClient

from ai_infra_quant.database.repositories.watchlist import SQLAlchemyWatchlistRepository


def test_watchlist_seed_and_idempotent_add_remove(client: TestClient) -> None:
    watchlist = client.get("/api/v1/watchlist").json()
    assert [item["security"]["display_symbol"] for item in watchlist["items"]] == [
        "US.AVGO",
        "US.VRT",
        "HK.09698",
    ]
    created = client.post(
        "/api/v1/securities",
        json={
            "market": "US",
            "symbol": "WATCH",
            "currency": "USD",
            "instrument_type": "EQUITY",
        },
    ).json()
    first = client.post("/api/v1/watchlist", json={"security_id": created["id"]})
    second = client.post("/api/v1/watchlist", json={"security_id": created["id"]})
    assert first.status_code == 201 and first.json()["created"] is True
    assert second.status_code == 200 and second.json()["created"] is False
    assert client.delete(f"/api/v1/watchlist/{created['id']}").status_code == 204
    assert client.delete(f"/api/v1/watchlist/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/securities/{created['id']}").status_code == 200


def test_unknown_watchlist_security_is_problem(client: TestClient) -> None:
    response = client.post(
        "/api/v1/watchlist", json={"security_id": "00000000-0000-4000-8000-000000000000"}
    )
    assert response.status_code == 404
    assert response.json()["code"] == "SECURITY_NOT_FOUND"


def test_watchlist_integrity_race_remains_idempotent(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    security_id = client.post(
        "/api/v1/securities",
        json={
            "market": "US",
            "symbol": "WATCH-RACE",
            "currency": "USD",
            "instrument_type": "EQUITY",
        },
    ).json()["id"]
    assert client.post("/api/v1/watchlist", json={"security_id": security_id}).status_code == 201
    original = SQLAlchemyWatchlistRepository._active_item
    calls = 0

    def stale_then_current(
        repository: SQLAlchemyWatchlistRepository, watchlist_id: str, candidate_id: str
    ) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            return None
        return original(repository, watchlist_id, candidate_id)

    monkeypatch.setattr(SQLAlchemyWatchlistRepository, "_active_item", stale_then_current)
    response = client.post("/api/v1/watchlist", json={"security_id": security_id})
    assert response.status_code == 200, response.text
    assert response.json()["created"] is False
