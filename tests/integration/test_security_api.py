import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.exc import DatabaseError

from ai_infra_quant.database.repositories.security import SQLAlchemySecurityRepository


def test_user_security_creation_is_forced_unverified(client: TestClient) -> None:
    response = client.post(
        "/api/v1/securities",
        json={
            "market": " us ",
            "symbol": " example ",
            "currency": "usd",
            "instrument_type": "equity",
            "display_name": "Local example",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["display_symbol"] == "US.EXAMPLE"
    assert body["record_source"] == "USER_SUPPLIED"
    assert body["verification_status"] == "USER_SUPPLIED_UNVERIFIED"
    assert body["tradability_status"] == "UNVERIFIED"
    assert body["exchange"] is None
    assert body["market_timezone"] is None
    assert body["trading_calendar"] is None
    assert body["provider_mappings"] == []
    assert body["trading_rules"]["status"] == "UNAVAILABLE"
    assert client.get(f"/api/v1/securities/{body['id']}").json() == body


def test_duplicate_security_returns_existing_id(client: TestClient) -> None:
    payload = {
        "market": "US",
        "symbol": "DUPLICATE",
        "currency": "USD",
        "instrument_type": "UNKNOWN",
    }
    created = client.post("/api/v1/securities", json=payload).json()
    conflict = client.post("/api/v1/securities", json=payload)
    assert conflict.status_code == 409
    assert conflict.headers["content-type"].startswith("application/problem+json")
    assert conflict.json()["code"] == "SECURITY_ALREADY_EXISTS"
    assert conflict.json()["security_id"] == created["id"]


@pytest.mark.parametrize("symbol", ["A/B", "<img>", "$BAD", "BAD SYMBOL", ""])
def test_us_security_rejects_invalid_symbols_with_stable_code(
    client: TestClient, symbol: str
) -> None:
    response = client.post(
        "/api/v1/securities",
        json={
            "market": "US",
            "symbol": symbol,
            "currency": "USD",
            "instrument_type": "EQUITY",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_SYMBOL"


def test_unsupported_market_is_rejected_fail_closed(client: TestClient) -> None:
    response = client.post(
        "/api/v1/securities",
        json={
            "market": "CN",
            "symbol": "600519",
            "currency": "CNY",
            "instrument_type": "EQUITY",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_MARKET"


@pytest.mark.parametrize("symbol", ["brk.b", "abc-def"])
def test_us_dot_and_hyphen_symbols_are_canonicalized(client: TestClient, symbol: str) -> None:
    response = client.post(
        "/api/v1/securities",
        json={
            "market": "us",
            "symbol": symbol,
            "currency": "usd",
            "instrument_type": "equity",
        },
    )
    assert response.status_code == 201
    assert response.json()["symbol"] == symbol.upper()


def test_hk_padding_conflicts_with_existing_canonical_identity(client: TestClient) -> None:
    existing = next(
        item["security"]
        for item in client.get("/api/v1/watchlist").json()["items"]
        if item["security"]["display_symbol"] == "HK.09698"
    )
    response = client.post(
        "/api/v1/securities",
        json={
            "market": "hk",
            "symbol": "9698",
            "currency": "HKD",
            "instrument_type": "EQUITY",
        },
    )
    assert response.status_code == 409
    assert response.json()["security_id"] == existing["id"]


def test_security_creation_rejects_privileged_fields(client: TestClient) -> None:
    response = client.post(
        "/api/v1/securities",
        json={
            "market": "US",
            "symbol": "EXTRA",
            "currency": "USD",
            "instrument_type": "EQUITY",
            "exchange": "NASDAQ",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_database_blocks_provider_mapping_for_user_supplied_security(
    client: TestClient, migrated_engine: Engine
) -> None:
    security = client.post(
        "/api/v1/securities",
        json={
            "market": "US",
            "symbol": "NO-MAPPING",
            "currency": "USD",
            "instrument_type": "EQUITY",
        },
    ).json()
    with migrated_engine.connect() as connection, pytest.raises(DatabaseError):
        connection.exec_driver_sql(
            """
            INSERT INTO provider_symbol_mappings
                (id, security_id, provider_type, provider_name, provider_symbol,
                 valid_from, valid_to, mapping_status, source, retrieved_at)
            VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?, NULL)
            """,
            (
                "00000000-0000-0000-0000-000000000099",
                security["id"],
                "MARKET_DATA",
                "synthetic-test",
                "US.NO-MAPPING",
                "AVAILABLE",
                "TEST_SYNTHETIC",
            ),
        )
        connection.commit()


def test_database_blocks_provider_mapping_update_to_user_security(
    client: TestClient, migrated_engine: Engine
) -> None:
    user_security = client.post(
        "/api/v1/securities",
        json={
            "market": "US",
            "symbol": "USER-MAP",
            "currency": "USD",
            "instrument_type": "EQUITY",
        },
    ).json()
    system_security = client.get("/api/v1/watchlist").json()["items"][0]["security"]
    mapping_id = "00000000-0000-0000-0000-000000000098"
    with migrated_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            INSERT INTO provider_symbol_mappings
                (id, security_id, provider_type, provider_name, provider_symbol,
                 valid_from, valid_to, mapping_status, source, retrieved_at)
            VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?, NULL)
            """,
            (
                mapping_id,
                system_security["id"],
                "MARKET_DATA",
                "synthetic-test",
                "US.SYSTEM",
                "UNVERIFIED",
                "TEST_SYNTHETIC",
            ),
        )
    with migrated_engine.begin() as connection, pytest.raises(DatabaseError):
        connection.exec_driver_sql(
            "UPDATE provider_symbol_mappings SET security_id = ? WHERE id = ?",
            (user_security["id"], mapping_id),
        )


def test_database_keeps_user_security_metadata_unavailable(
    client: TestClient, migrated_engine: Engine
) -> None:
    security = client.post(
        "/api/v1/securities",
        json={
            "market": "US",
            "symbol": "NO-METADATA",
            "currency": "USD",
            "instrument_type": "EQUITY",
        },
    ).json()
    with migrated_engine.begin() as connection, pytest.raises(DatabaseError):
        connection.exec_driver_sql(
            "UPDATE securities SET metadata_status = 'AVAILABLE' WHERE id = ?",
            (security["id"],),
        )


def test_normalized_security_integrity_race_returns_stable_conflict(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    existing = client.get("/api/v1/watchlist").json()["items"][0]["security"]
    original = SQLAlchemySecurityRepository.get_by_identity
    calls = 0

    def stale_then_current(
        repository: SQLAlchemySecurityRepository, market: str, symbol: str
    ) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            return None
        return original(repository, market, symbol)

    monkeypatch.setattr(SQLAlchemySecurityRepository, "get_by_identity", stale_then_current)
    response = client.post(
        "/api/v1/securities",
        json={
            "market": existing["market"].lower(),
            "symbol": existing["symbol"].lower(),
            "currency": existing["currency"],
            "instrument_type": existing["instrument_type"],
        },
    )
    assert response.status_code == 409
    assert response.json()["code"] == "SECURITY_ALREADY_EXISTS"
    assert response.json()["security_id"] == existing["id"]
