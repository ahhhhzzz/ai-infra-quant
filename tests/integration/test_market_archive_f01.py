"""F01: normal product identities, real routes/storage, synthetic market facts only."""

from collections.abc import Iterator
from dataclasses import replace
from importlib import import_module
from typing import Any
from uuid import uuid4

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from ai_infra_quant.application.market_data_archive import MarketDataArchiveService
from ai_infra_quant.application.supported_security_service import SupportedSecurityService
from ai_infra_quant.backend.main import create_app
from ai_infra_quant.config import Settings
from ai_infra_quant.core.domain.market_data import PROVIDER_FUTU_QUOTE
from ai_infra_quant.database.models.market_data_archive import captures
from ai_infra_quant.database.models.security import SecurityModel
from ai_infra_quant.database.repositories.market_data_archive import SQLAlchemyMarketDataArchive
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork

support = import_module("tests.browser.archive_support")
validation = import_module("tests.integration.test_supported_security_api")
PREFIX = "/api/v1/market-data/archive"
STATUS_FIELDS = ("verification_status", "tradability_status", "metadata_status")


@pytest.fixture
def normal_archive(settings: Settings, migrated_engine: Engine) -> Iterator[Any]:
    app = create_app(settings, migrated_engine)
    with TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        container = app.state.container
        provider = support.SyntheticArchiveProvider()
        # Deliberately no install helper or Security UPDATE: also reproduces on reviewed code.
        container.market_data_archive = MarketDataArchiveService(
            container.market_data_queries,
            SQLAlchemyMarketDataArchive(container.session_factory),
            provider_name=PROVIDER_FUTU_QUOTE,
            provider_factory=lambda: provider,
            now=lambda: provider.now,
        )
        validator = validation.SupportedFakeProvider()
        container.supported_security_service = SupportedSecurityService(
            lambda: SQLAlchemyUnitOfWork(container.session_factory),
            provider_name=validation.PROVIDER,
            provider_factory=lambda: validator,
        )
        client.headers["Origin"] = "http://127.0.0.1"
        yield client, container, provider, validator


def security_details(client: TestClient) -> dict[str, Any]:
    return {
        item["security"]["display_symbol"]: client.get(
            f"/api/v1/securities/{item['security']['id']}"
        ).json()
        for item in client.get("/api/v1/watchlist").json()["items"]
    }


def assert_status(security: dict[str, Any], verification: str) -> None:
    assert tuple(security[field] for field in STATUS_FIELDS) == (
        verification,
        "UNVERIFIED",
        "UNAVAILABLE",
    )


def save_and_read_offline(client: TestClient, container: Any, security_id: str) -> None:
    response = client.post(PREFIX + "/captures", json={"security_id": security_id})
    assert response.status_code == 201, response.text
    capture = response.json()
    assert capture["status"] == "PARTIAL"
    capture_id = capture["capture_id"]
    service = container.market_data_archive
    factory = service.provider_factory

    def forbidden() -> Any:
        raise AssertionError("offline reads must not construct a provider")

    service.provider_factory = forbidden
    try:
        assert client.get(f"{PREFIX}/captures/{capture_id}").json() == capture
        assert (
            client.get(f"{PREFIX}/securities/{security_id}/captures").json()["items"][0][
                "capture_id"
            ]
            == capture_id
        )
        for timeframe, count in (("D1", 1), ("M1", 601)):
            result = client.get(
                f"{PREFIX}/captures/{capture_id}/bars?timeframe={timeframe}&limit=1000"
            )
            assert result.status_code == 200
            rows = result.json()["items"]
            assert len(rows) == count
            assert all(row["open"] == str(support.PRICE) for row in rows)
            assert all(row["security_id"] == security_id for row in rows)
    finally:
        service.provider_factory = factory


@pytest.mark.parametrize("symbol", ["US.AVGO", "US.VRT", "HK.09698"])
def test_normal_seed_capture_and_offline_read_without_status_upgrade(
    normal_archive: Any, symbol: str
) -> None:
    client, container, provider, validator = normal_archive
    before = security_details(client)
    for security in before.values():
        assert_status(security, "SYSTEM_SEED_UNVERIFIED")
    save_and_read_offline(client, container, before[symbol]["id"])
    assert security_details(client) == before
    assert provider.calls == ["enter", "D1", "M1", "calendar"]
    assert provider.closed == 1
    assert validator.seen == []


@pytest.mark.parametrize(
    "market,symbol,canonical", [("us", "nvda", "US.NVDA"), ("hk", "700", "HK.00700")]
)
def test_validated_add_then_capture_without_status_upgrade(
    normal_archive: Any, market: str, symbol: str, canonical: str
) -> None:
    client, container, provider, validator = normal_archive
    seeds = security_details(client)
    added = client.post(
        "/api/v1/watchlist/supported-securities", json={"market": market, "symbol": symbol}
    )
    assert added.status_code == 201, added.text
    assert added.json()["provider_validation"]["status"] == "AVAILABLE"
    before = security_details(client)
    assert {key: before[key] for key in seeds} == seeds
    assert_status(before[canonical], "USER_SUPPLIED_UNVERIFIED")
    save_and_read_offline(client, container, before[canonical]["id"])
    assert security_details(client) == before
    assert provider.calls == ["enter", "D1", "M1", "calendar"]
    assert provider.closed == 1
    # Only the existing explicit supported-add validation called quote, never capture/read.
    assert validator.seen == [canonical]


@pytest.mark.parametrize(
    "change,http_status",
    [
        ({"unknown": True}, 404),
        ({"enabled": False}, 422),
        ({"instrument_type": "ETF"}, 422),
        ({"currency": "HKD"}, 409),
        ({"market_timezone": "Asia/Hong_Kong"}, 409),
        ({"provider": "unsupported"}, 422),
    ],
)
def test_identity_conflicts_still_rejected_before_provider(
    normal_archive: Any, change: dict[str, Any], http_status: int
) -> None:
    client, container, provider, validator = normal_archive
    security_id = security_details(client)["US.AVGO"]["id"]
    if "unknown" in change:
        security_id = str(uuid4())
    elif "provider" in change:
        container.market_data_archive.provider_name = change["provider"]
    else:
        # Negative corruption fixture only; never upgrades verification/trading metadata.
        with container.session_factory.begin() as session:
            session.execute(
                sa.update(SecurityModel).where(SecurityModel.id == security_id).values(**change)
            )
    response = client.post(PREFIX + "/captures", json={"security_id": security_id})
    assert response.status_code == http_status, response.text
    assert provider.calls == validator.seen == []
    with container.engine.connect() as connection:
        assert connection.scalar(sa.select(sa.func.count()).select_from(captures)) == 0


@pytest.mark.parametrize("mismatch", ["security", "provider"])
def test_returned_identity_mismatch_is_not_archived(normal_archive: Any, mismatch: str) -> None:
    client, container, provider, _ = normal_archive
    before = security_details(client)
    original = provider.result

    def wrong(kind: str, rows: Any) -> Any:
        result = original(kind, rows)
        if kind not in {"D1", "M1"}:
            return result
        if mismatch == "provider":
            return replace(result, provider="wrong_provider")
        return replace(result, data=tuple(replace(row, security="US.WRONG") for row in rows))

    provider.result = wrong
    response = client.post(PREFIX + "/captures", json={"security_id": before["US.AVGO"]["id"]})
    assert response.status_code == 503, response.text
    assert response.json()["code"] == "ARCHIVE_UNAVAILABLE"
    assert all(response.json()["batches"][tf]["count"] == 0 for tf in ("D1", "M1"))
    assert provider.calls == ["enter", "D1", "M1", "calendar"]
    assert provider.closed == 1
    assert security_details(client) == before
    with container.engine.connect() as connection:
        assert connection.scalar(sa.select(sa.func.count()).select_from(captures)) == 0
