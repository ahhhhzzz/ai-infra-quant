from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from ai_infra_quant.application.paqs_structure_queries import PaqsStructureQueries
from ai_infra_quant.backend.main import create_app
from ai_infra_quant.config import Settings
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus, SnapshotQualityStatus
from ai_infra_quant.core.domain.market_data import DailyBar
from ai_infra_quant.core.domain.paqs_input import (
    AdjustmentBasis,
    AdjustmentMetadata,
    CalendarMetadata,
    PaqsInputBundle,
    SourceCoverage,
)

NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)


class SyntheticInputSource:
    def __init__(self) -> None:
        self.quality = SnapshotQualityStatus.PARTIAL
        self.daily_count = 60
        self.as_of_timestamp = NOW
        self.events: list[str] = []

    def current_bundle(self, security_id: str) -> PaqsInputBundle:
        self.events.append("bundle")
        bars = tuple(
            DailyBar(
                security="US.AVGO",
                session_date=date(2026, 1, 1) + timedelta(days=index),
                provider_time=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=index),
                open=Decimal("100"),
                high=Decimal("102"),
                low=Decimal("99"),
                close=Decimal("101"),
                volume=Decimal("1000"),
                is_completed=True,
                retrieved_at=NOW,
            )
            for index in range(self.daily_count)
        )
        return PaqsInputBundle(
            security_id=security_id,
            market="US",
            symbol="AVGO",
            market_timezone="America/New_York",
            provider="synthetic_test_provider",
            as_of_timestamp=self.as_of_timestamp,
            completed_w1_bars=(),
            completed_d1_bars=bars,
            completed_30m_bars=(),
            calendar=CalendarMetadata(
                status=DataAvailabilityStatus.AVAILABLE,
                provider="synthetic_test_provider",
                retrieved_at=NOW,
                trading_days=(),
            ),
            adjustment=AdjustmentMetadata(
                basis=AdjustmentBasis.PROVIDER_QFQ_CURRENT,
                adjustment_as_of=NOW,
                historical_replay_safe=False,
            ),
            data_quality=self.quality,
            warnings=("SYNTHETIC_TEST_DATA",),
            source_coverage=SourceCoverage(
                d1_source_count=len(bars),
                w1_completed_count=0,
                w1_partial_count=0,
                minute_source_count=0,
                m30_completed_count=0,
                m30_partial_count=0,
            ),
        )


@pytest.fixture
def structure_source() -> SyntheticInputSource:
    return SyntheticInputSource()


@pytest.fixture
def structure_app(
    settings: Settings,
    migrated_engine: Engine,
    structure_source: SyntheticInputSource,
) -> FastAPI:
    application = create_app(settings, migrated_engine)
    application.state.container.paqs_structure_queries = PaqsStructureQueries(
        structure_source,
        now=lambda: NOW,
    )
    return application


@pytest.fixture
def structure_client(structure_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(structure_app) as client:
        yield client


def _avgo_id(client: TestClient) -> str:
    items = client.get("/api/v1/watchlist").json()["items"]
    return str(
        next(
            item["security"]["id"]
            for item in items
            if item["security"]["display_symbol"] == "US.AVGO"
        )
    )


def test_structure_endpoint_returns_current_explainable_snapshot(
    structure_client: TestClient,
) -> None:
    response = structure_client.get(
        f"/api/v1/strategies/paqs/securities/{_avgo_id(structure_client)}/structure"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["strategy_version"] == "PAQS-v0.3.1"
    assert body["structure_version"] == "TASK-006B-v1"
    assert len(body["config_hash"]) == 64
    assert body["config"]["atr_period"] == 14
    assert body["as_of_timestamp"] == "2026-09-02T12:00:00Z"
    assert body["calculated_at"] == "2026-09-02T12:00:00Z"
    assert body["input_quality"] == "PARTIAL"
    assert body["adjustment_metadata"] == {
        "basis": "PROVIDER_QFQ_CURRENT",
        "adjustment_as_of": "2026-09-02T12:00:00Z",
        "historical_replay_safe": False,
    }
    assert [item["timeframe"] for item in body["timeframes"]] == ["W1", "D1", "M30"]
    daily = body["timeframes"][1]
    assert daily["role"] == "SETUP"
    assert daily["bar_count"] == 60
    assert daily["atr_ready"] is True
    assert daily["latest_atr"] is not None
    assert daily["base_regime"] == "UNCERTAIN"
    serialized = str(body).upper()
    for forbidden in (
        "BREAKOUT",
        "RETEST",
        "FOLLOW_THROUGH",
        "LONG_READY",
        "HOLDER_ADVISORY",
        "COMPOSITE_SCORE",
        "RANKING",
    ):
        assert forbidden not in serialized


def test_invalid_input_returns_uncertain_without_fabricated_structure(
    structure_client: TestClient,
    structure_source: SyntheticInputSource,
) -> None:
    structure_source.quality = SnapshotQualityStatus.INVALID
    response = structure_client.get(
        f"/api/v1/strategies/paqs/securities/{_avgo_id(structure_client)}/structure"
    )

    assert response.status_code == 200
    for timeframe in response.json()["timeframes"]:
        assert timeframe["atr_ready"] is False
        assert timeframe["latest_atr"] is None
        assert timeframe["micro_pivots"] == []
        assert timeframe["major_pivots"] == []
        assert timeframe["zones"] == []
        assert timeframe["valid_ranges"] == []
        assert timeframe["base_regime"] == "UNCERTAIN"


def test_structure_endpoint_has_no_public_replay_or_config_parameters(
    structure_client: TestClient,
) -> None:
    operation = structure_client.get("/openapi.json").json()["paths"][
        "/api/v1/strategies/paqs/securities/{security_id}/structure"
    ]["get"]
    assert [(item["name"], item["in"]) for item in operation["parameters"]] == [
        ("security_id", "path")
    ]


@pytest.mark.parametrize(
    ("bundle_as_of", "query_clock", "expected"),
    [
        (NOW + timedelta(seconds=2), NOW, NOW + timedelta(seconds=2)),
        (NOW, NOW + timedelta(seconds=2), NOW + timedelta(seconds=2)),
    ],
)
def test_structure_query_retrieves_once_before_selecting_ordered_calculation_time(
    structure_source: SyntheticInputSource,
    bundle_as_of: datetime,
    query_clock: datetime,
    expected: datetime,
) -> None:
    structure_source.as_of_timestamp = bundle_as_of

    def clock() -> datetime:
        structure_source.events.append("clock")
        return query_clock

    snapshot = PaqsStructureQueries(structure_source, now=clock).current_snapshot(
        "00000000-0000-4000-8000-000000000001"
    )

    assert structure_source.events == ["bundle", "clock"]
    assert snapshot.as_of_timestamp == bundle_as_of
    assert snapshot.calculated_at == expected
    assert snapshot.calculated_at >= snapshot.as_of_timestamp


def test_unknown_security_remains_a_structured_not_found(client: TestClient) -> None:
    response = client.get(
        "/api/v1/strategies/paqs/securities/00000000-0000-4000-8000-000000000099/structure"
    )
    assert response.status_code == 404
    assert response.json()["code"] == "SECURITY_NOT_FOUND"
