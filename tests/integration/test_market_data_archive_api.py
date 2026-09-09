from __future__ import annotations

import importlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Any, cast
from uuid import uuid4

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from ai_infra_quant.application.market_data_archive import ArchiveUnavailable
from ai_infra_quant.core.ports.market_data_archive import ArchivePersistenceError
from ai_infra_quant.database.models.market_data_archive import captures, memberships, versions
from ai_infra_quant.database.repositories.market_data_archive import SQLAlchemyMarketDataArchive
from ai_infra_quant.database.session import create_database_engine, create_session_factory

_support = importlib.import_module("tests.browser.archive_support")
PRICE = _support.PRICE
SyntheticArchiveProvider = _support.SyntheticArchiveProvider
install = _support.install


@pytest.fixture
def archive(client: TestClient) -> Any:
    provider = SyntheticArchiveProvider()
    container = cast(Any, client.app).state.container
    service = install(container, provider)
    items = client.get("/api/v1/watchlist").json()["items"]
    ids = {item["security"]["display_symbol"]: item["security"]["id"] for item in items}
    return service, provider, ids["US.AVGO"], container


def counts(container: Any) -> tuple[int, ...]:
    with container.engine.connect() as connection:
        return tuple(
            connection.scalar(sa.select(sa.func.count()).select_from(table))
            for table in (captures, versions, memberships)
        )


def test_same_content_dedup_a_b_a_and_restart_offline(archive: Any, database_url: str) -> None:
    service, provider, security_id, container = archive
    first = service.capture(security_id)
    provider.now += timedelta(seconds=1)
    second = service.capture(security_id)
    assert counts(container) == (2, 602, 1204)
    provider.price = (
        PRICE - 1
    )  # exactness below is separately checked; revision deliberately differs
    changed = service.capture(security_id)
    provider.price = PRICE
    again = service.capture(security_id)
    assert counts(container) == (4, 1204, 2408)
    assert provider.calls == ["enter", "D1", "M1", "calendar"] * 4
    assert provider.closed == 4
    assert first["batches"]["M1"]["actual_end"] == "2026-09-07T18:01:00.000000Z"
    container.engine.dispose()
    engine = create_database_engine(database_url)
    try:
        local = SQLAlchemyMarketDataArchive(create_session_factory(engine))
        provider.fail.update(("D1", "M1", "calendar"))
        a = local.read_bars(first["capture_id"], "D1")["items"][0]
        b = local.read_bars(changed["capture_id"], "D1")["items"][0]
        assert a["version_hash"] != b["version_hash"]
        assert (
            local.read_bars(again["capture_id"], "D1")["items"][0]["version_hash"]
            == a["version_hash"]
        )
        assert (
            local.read_bars(second["capture_id"], "D1")["items"][0]["retrieved_at"]
            != a["retrieved_at"]
        )
        assert a["open"] == str(PRICE)
        assert local.detail(first["capture_id"]) == first
        assert len(local.list_captures(security_id)["items"]) == 4
        assert len(provider.calls) == 16
        with engine.connect() as connection:
            assert (
                connection.exec_driver_sql(
                    "SELECT typeof(open) FROM market_archive_bar_versions LIMIT 1"
                ).scalar()
                == "text"
            )
    finally:
        engine.dispose()


def test_pagination_binding_limits_and_explicit_membership(archive: Any) -> None:
    service, provider, security_id, _ = archive
    first = service.capture(security_id)
    provider.daily_offset = 1
    second = service.capture(security_id)
    store = service.repository
    page = store.read_bars(first["capture_id"], "M1")
    assert len(page["items"]) == 500
    last = store.read_bars(first["capture_id"], "M1", 500, page["next_cursor"])
    assert [r["ordinal"] for r in page["items"] + last["items"]] == list(range(601))
    assert last["next_cursor"] is None
    for owner, tf in ((second["capture_id"], "M1"), (first["capture_id"], "D1")):
        with pytest.raises(ValueError):
            store.read_bars(owner, tf, 500, page["next_cursor"])
    assert store.read_bars(first["capture_id"], "D1")["items"][0]["session_date"] == "2026-09-07"
    assert store.read_bars(second["capture_id"], "D1")["items"][0]["session_date"] == "2026-09-08"
    page = store.list_captures(security_id, 1, None)
    tail = store.list_captures(security_id, 1, page["next_cursor"])
    assert {r["capture_id"] for r in page["items"] + tail["items"]} == {
        first["capture_id"],
        second["capture_id"],
    }
    assert tail["next_cursor"] is None
    for cursor in ("bad", "A" * 513, "e30"):
        with pytest.raises(ValueError):
            store.list_captures(security_id, 20, cursor)


@pytest.mark.parametrize("failure", [("M1",), ("calendar",), ("D1",), ("D1", "M1", "calendar")])
def test_partial_and_total_failures_never_fabricate(archive: Any, failure: tuple[str, ...]) -> None:
    service, provider, security_id, container = archive
    provider.fail.update(failure)
    if len(failure) == 3:
        with pytest.raises(ArchiveUnavailable) as caught:
            service.capture(security_id)
        assert "synthetic-private" not in str(caught.value.batches)
        assert counts(container) == (0, 0, 0)
    else:
        capture = service.capture(security_id)
        assert capture["status"] == "PARTIAL"
        for name in failure:
            assert capture["batches"][name]["status"] == "ERROR"
            assert capture["batches"][name]["count"] == 0
        assert not capture["batches"]["D1"]["coverage_complete"]
    assert provider.closed == 1


def test_duplicates_conflicts_rollback_and_immutable_tables(archive: Any) -> None:
    service, provider, security_id, container = archive
    provider.duplicate = True
    first = service.capture(security_id)
    assert first["batches"]["D1"]["duplicate_count"] == 1
    provider.conflict = True
    partial = service.capture(security_id)
    assert partial["batches"]["D1"]["status"] == "ERROR"
    assert service.repository.read_bars(partial["capture_id"], "D1")["items"] == []
    before = counts(container)

    def fail_members(
        connection: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: Any,
    ) -> None:
        if statement.startswith("INSERT INTO market_archive_memberships"):
            raise sa.exc.OperationalError(statement, parameters, RuntimeError("injected"))

    sa.event.listen(container.engine, "before_cursor_execute", fail_members)
    try:
        with pytest.raises(ArchivePersistenceError):
            service.capture(security_id)
    finally:
        sa.event.remove(container.engine, "before_cursor_execute", fail_members)
    assert counts(container) == before
    for table in (captures, versions, memberships):
        with pytest.raises(sa.exc.IntegrityError), container.engine.begin() as connection:
            connection.execute(table.delete())
        with pytest.raises(sa.exc.IntegrityError), container.engine.begin() as connection:
            column = next(iter(table.primary_key.columns))
            connection.execute(table.update().values({column.name: column}))


def test_concurrent_requests_dedup_transactionally(archive: Any) -> None:
    service, _, security_id, container = archive
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(service.capture, [security_id, security_id]))
    assert results[0]["capture_id"] != results[1]["capture_id"]
    assert counts(container) == (2, 602, 1204)


def test_sealed_membership_and_other_security_never_alias(archive: Any, client: TestClient) -> None:
    service, provider, security_id, container = archive
    a = service.capture(security_id)
    items = client.get("/api/v1/watchlist").json()["items"]
    other_id = next(
        item["security"]["id"] for item in items if item["security"]["id"] != security_id
    )
    b = service.capture(other_id)
    assert (
        service.repository.read_bars(a["capture_id"], "D1")["items"][0]["version_hash"]
        != service.repository.read_bars(b["capture_id"], "D1")["items"][0]["version_hash"]
    )
    with container.engine.connect() as connection:
        member = dict(
            connection.execute(
                sa.select(memberships).where(
                    memberships.c.capture_id == a["capture_id"], memberships.c.timeframe == "D1"
                )
            )
            .mappings()
            .one()
        )
    member["ordinal"] = 1
    with (
        pytest.raises(sa.exc.IntegrityError, match="sealed"),
        container.engine.begin() as connection,
    ):
        connection.execute(memberships.insert().values(**member))
    assert counts(container) == (2, 1204, 1204)


def test_hk_half_day_lunch_calendar_and_unknown_quality(archive: Any, client: TestClient) -> None:
    from dataclasses import replace
    from datetime import time

    from ai_infra_quant.core.domain.market_data import TradingDayType, TradingSessionSegment

    service, provider, _, _ = archive
    items = client.get("/api/v1/watchlist").json()["items"]
    security_id = next(
        item["security"]["id"] for item in items if item["security"]["market"] == "HK"
    )
    full = service.capture(security_id)
    assert full["calendar"][0]["session_segments"] == [
        {"start": "09:30:00", "end": "12:00:00"},
        {"start": "13:00:00", "end": "16:00:00"},
    ]
    original = provider.get_trading_days

    def half(market: str, start: Any, end: Any) -> Any:
        result = original(market, start, end)
        day = replace(
            result.data[0],
            day_type=TradingDayType.MORNING_ONLY,
            provider_day_type="SYNTHETIC_HALF",
            session_segments=(TradingSessionSegment(time(9, 30), time(12)),),
        )
        return replace(result, data=(day,))

    provider.get_trading_days = half
    partial = service.capture(security_id)
    assert partial["calendar"][0]["day_type"] == "MORNING_ONLY"
    assert partial["batches"]["M1"]["expected_regular_count"] == 150
    assert service.repository.detail(full["capture_id"])["calendar"] == full["calendar"]

    def unknown(market: str, start: Any, end: Any) -> Any:
        result = original(market, start, end)
        return replace(
            result,
            data=(replace(result.data[0], day_type=TradingDayType.UNKNOWN, session_segments=()),),
        )

    provider.get_trading_days = unknown
    unknown_capture = service.capture(security_id)
    assert unknown_capture["batches"]["calendar"]["status"] == "PARTIAL"
    assert unknown_capture["batches"]["M1"]["missing_count"] is None


def test_conflicting_metadata_and_context_failure(archive: Any) -> None:
    from ai_infra_quant.application.market_data_queries import MarketDataSecurityMetadataConflict
    from ai_infra_quant.database.models.security import SecurityModel

    service, provider, security_id, container = archive
    with container.session_factory.begin() as session:
        session.execute(
            sa.update(SecurityModel).where(SecurityModel.id == security_id).values(currency="HKD")
        )
    with pytest.raises(MarketDataSecurityMetadataConflict):
        service.capture(security_id)
    assert provider.calls == []
    with container.session_factory.begin() as session:
        session.execute(
            sa.update(SecurityModel).where(SecurityModel.id == security_id).values(currency="USD")
        )

    def unavailable() -> Any:
        raise RuntimeError("synthetic-private-exception")

    service.provider_factory = unavailable
    with pytest.raises(ArchiveUnavailable) as caught:
        service.capture(security_id)
    assert "synthetic-private" not in str(caught.value.batches)
    assert counts(container) == (0, 0, 0)


def test_http_offline_reads_write_boundary_and_errors(archive: Any, client: TestClient) -> None:
    service, provider, security_id, container = archive
    capture = service.capture(security_id)

    def forbidden() -> Any:
        raise AssertionError("GET must never construct provider")

    service.provider_factory = forbidden
    prefix = "/api/v1/market-data/archive"
    for path in (
        f"/captures/{capture['capture_id']}",
        f"/captures/{capture['capture_id']}/bars?timeframe=M1",
        f"/securities/{security_id}/captures",
    ):
        assert client.get(prefix + path).status_code == 200
    assert provider.calls == ["enter", "D1", "M1", "calendar"]
    for suffix in ("?timeframe=W1", "?timeframe=D1&limit=1001", "?timeframe=M1&cursor=bad"):
        assert (
            client.get(f"{prefix}/captures/{capture['capture_id']}/bars{suffix}").status_code == 422
        )
    assert client.get(f"{prefix}/captures/{uuid4()}").status_code == 404
    assert client.get(f"{prefix}/captures/not-a-uuid").status_code == 422
    assert client.post(prefix + "/captures", json={"security_id": security_id}).status_code == 403
    with TestClient(client.app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as local:
        service.provider_factory = lambda: provider
        headers = {"Origin": "http://127.0.0.1"}
        assert (
            local.post(
                prefix + "/captures", headers=headers, json={"security_id": security_id, "limit": 2}
            ).status_code
            == 422
        )
        assert (
            local.post(
                prefix + "/captures", headers=headers, json={"security_id": security_id}
            ).status_code
            == 201
        )
        provider.fail.update(("D1", "M1", "calendar"))
        response = local.post(
            prefix + "/captures", headers=headers, json={"security_id": security_id}
        )
        assert response.status_code == 503
        assert "synthetic-private" not in response.text
