from fastapi.testclient import TestClient


def test_opening_portfolio_and_positions(client: TestClient) -> None:
    response = client.get("/api/v1/portfolio")
    assert response.status_code == 200
    body = response.json()
    assert body["base_currency"] == "HKD"
    assert body["total_equity"] == "20000.000000000000000000"
    assert body["cash_value"] == "20000.000000000000000000"
    assert body["units_outstanding"] == "200.000000000000000000"
    assert body["nav"] == "100.000000000000000000"
    assert body["unrealized_pnl"] == "0.000000000000000000"
    assert body["quality_status"] == "COMPLETE"
    for field in (
        "market_value",
        "cost_basis",
        "realized_pnl",
        "unrealized_pnl",
        "fees",
        "taxes",
        "equity_pnl",
        "fx_pnl",
        "invested_ratio",
    ):
        assert not body[field].startswith("-")
    assert body["capabilities"]["market_data"] == "UNAVAILABLE"
    positions = client.get("/api/v1/positions").json()
    assert positions == {"items": [], "next_cursor": None, "has_more": False}


def test_inception_only_performance_is_truthful(client: TestClient) -> None:
    response = client.get("/api/v1/performance")
    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary["daily_return"]["status"] == "UNAVAILABLE"
    assert summary["weekly_return"]["status"] == "UNAVAILABLE"
    assert summary["monthly_return"]["status"] == "UNAVAILABLE"
    assert summary["since_inception_return"] == "0.000000000000"
    assert summary["maximum_drawdown"] == "0.000000000000"
    assert len(response.json()["points"]) == 1
    assert response.json()["points"][0]["quality_status"] == "COMPLETE"
