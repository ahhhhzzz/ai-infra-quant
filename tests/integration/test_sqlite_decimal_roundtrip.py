from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import Column, Engine, MetaData, Table, insert, select
from sqlalchemy.exc import StatementError

from ai_infra_quant.database.types import ExactDecimal, UTCDateTime

VECTORS = (
    Decimal("100.000000000000000001"),
    Decimal("12345678901234567890.123456789012345678"),
    Decimal("0.123456789012345678"),
)


def test_sqlite_exact_decimal_round_trip_and_typeof(migrated_engine: Engine) -> None:
    metadata = MetaData()
    probe = Table(
        "decimal_probe",
        metadata,
        Column("id", ExactDecimal(), primary_key=True),
    )
    metadata.create_all(migrated_engine)
    with migrated_engine.begin() as connection:
        connection.execute(insert(probe), [{"id": value} for value in VECTORS])
    with migrated_engine.connect() as connection:
        returned = connection.execute(select(probe.c.id)).scalars().all()
        raw = connection.exec_driver_sql(
            "SELECT id, typeof(id) FROM decimal_probe ORDER BY rowid"
        ).all()
    assert [value.as_tuple() for value in returned] == [value.as_tuple() for value in VECTORS]
    assert all(storage_type == "text" for _, storage_type in raw)
    assert all(len(stored.removeprefix("-")) == 39 for stored, _ in raw)


def test_float_over_scale_and_overflow_are_rejected(migrated_engine: Engine) -> None:
    metadata = MetaData()
    probe = Table("decimal_rejection_probe", metadata, Column("value", ExactDecimal()))
    metadata.create_all(migrated_engine)
    with migrated_engine.connect() as connection:
        for invalid in (
            1.5,
            "0.1234567890123456789",
            "100000000000000000000.000000000000000000",
        ):
            with pytest.raises(StatementError):
                connection.execute(insert(probe).values(value=invalid))


def test_decimal_ordering_is_done_in_python_not_lexically(migrated_engine: Engine) -> None:
    metadata = MetaData()
    probe = Table("decimal_order_probe", metadata, Column("value", ExactDecimal()))
    metadata.create_all(migrated_engine)
    values = [Decimal("2"), Decimal("-10"), Decimal("0"), Decimal("100")]
    with migrated_engine.begin() as connection:
        connection.execute(insert(probe), [{"value": value} for value in values])
    with migrated_engine.connect() as connection:
        returned = connection.execute(select(probe.c.value)).scalars().all()
    assert sorted(returned) == [Decimal("-10"), Decimal("0"), Decimal("2"), Decimal("100")]


@pytest.mark.parametrize(
    "zero",
    [Decimal("-0"), Decimal("-0.00"), Decimal("0.000000000000000000")],
)
def test_sqlite_signed_zero_is_stored_and_loaded_positive(
    migrated_engine: Engine, zero: Decimal
) -> None:
    metadata = MetaData()
    probe = Table("signed_zero_probe", metadata, Column("value", ExactDecimal()))
    metadata.create_all(migrated_engine)
    with migrated_engine.begin() as connection:
        connection.execute(insert(probe).values(value=zero))
    with migrated_engine.connect() as connection:
        returned = connection.execute(select(probe.c.value)).scalar_one()
        stored = connection.exec_driver_sql("SELECT value FROM signed_zero_probe").scalar_one()
    assert returned == Decimal(0)
    assert not returned.is_signed()
    assert not stored.startswith("-")


def test_aware_datetime_round_trips_as_the_same_utc_instant(migrated_engine: Engine) -> None:
    metadata = MetaData()
    probe = Table(
        "utc_datetime_probe",
        metadata,
        Column("id", ExactDecimal(), primary_key=True),
        Column("occurred_at", UTCDateTime(), nullable=False),
    )
    metadata.create_all(migrated_engine)
    source = datetime(2026, 8, 31, 12, 0, tzinfo=timezone(timedelta(hours=8)))
    with migrated_engine.begin() as connection:
        connection.execute(insert(probe).values(id=Decimal("1"), occurred_at=source))
    with migrated_engine.connect() as connection:
        returned = connection.execute(select(probe.c.occurred_at)).scalar_one()
        stored = connection.exec_driver_sql(
            "SELECT occurred_at FROM utc_datetime_probe"
        ).scalar_one()
    assert returned == datetime(2026, 8, 31, 4, 0, tzinfo=UTC)
    assert returned.tzinfo is UTC
    assert stored == "2026-08-31T04:00:00.000000Z"


def test_naive_datetime_is_rejected_at_persistence_boundary(migrated_engine: Engine) -> None:
    metadata = MetaData()
    probe = Table("naive_datetime_probe", metadata, Column("occurred_at", UTCDateTime()))
    metadata.create_all(migrated_engine)
    with migrated_engine.connect() as connection, pytest.raises(StatementError):
        connection.execute(insert(probe).values(occurred_at=datetime(2026, 8, 31, 4, 0)))
