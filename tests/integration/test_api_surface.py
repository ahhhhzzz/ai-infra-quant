from fastapi.testclient import TestClient

EXPECTED_PATHS = {
    "/health",
    "/api/v1/portfolio",
    "/api/v1/positions",
    "/api/v1/performance",
    "/api/v1/watchlist",
    "/api/v1/watchlist/{security_id}",
    "/api/v1/watchlist/supported-securities",
    "/api/v1/strategies/paqs/securities/{security_id}/input-status",
    "/api/v1/strategies/paqs/securities/{security_id}/structure",
    "/api/v1/paqs/securities/{security_id}/market-snapshot",
    "/api/v1/paqs-e/narrative-analyses",
    "/api/v1/paqs-e/narrative-analyses/{run_id}",
    "/api/v1/paqs-e/narrative-results/{result_id}",
    "/api/v1/paqs-e/securities/{security_id}/narrative-results",
    "/api/v1/paqs-e/configuration",
    "/api/v1/paqs-e/credentials/{model_key}",
    "/api/v1/paqs-e/analyses/{analysis_run_id}",
    "/api/v1/paqs-e/decisions/{decision_id}",
    "/api/v1/paqs-e/securities/{security_id}/decisions",
    "/api/v1/securities",
    "/api/v1/securities/{security_id}",
    "/api/v1/strategies",
    "/api/v1/brokers",
    "/api/v1/brokers/{broker}/status",
    "/api/v1/market-data/providers",
    "/api/v1/market-data/securities/{security_id}/state",
    "/api/v1/market-data/securities/{security_id}/daily-bars",
    "/api/v1/market-data/securities/{security_id}/minute-bars",
    "/api/v1/fundamental-data/providers",
    "/api/v1/event-data/providers",
}


def test_openapi_has_exact_approved_allowlist(client: TestClient) -> None:
    document = client.get("/openapi.json").json()
    assert set(document["paths"]) == EXPECTED_PATHS
    assert set(document["paths"]["/api/v1/paqs-e/configuration"]) == {"get"}
    assert set(document["paths"]["/api/v1/paqs-e/credentials/{model_key}"]) == {
        "get",
        "put",
        "delete",
    }
    serialized = str(document).lower()
    for forbidden in (
        "/live",
        "/paper",
        "deposit",
        "withdraw",
        "manual-fill",
        "orders",
        "fills",
        "backtest",
        "kill-switch",
        "strategies/run",
        "indicators",
        "signals",
        "score",
        "accounts",
    ):
        assert forbidden not in serialized


def test_response_headers_and_problem_shape(client: TestClient) -> None:
    response = client.get("/api/v1/securities/not-a-uuid")
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"] == response.json()["request_id"]
    assert response.headers["content-type"].startswith("application/problem+json")
