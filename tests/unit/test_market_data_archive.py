from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, localcontext
from typing import Any

import pytest

from ai_infra_quant.core.domain.market_data import DailyBar, MarketDataSecurity, MinuteBar
from ai_infra_quant.core.domain.market_data_archive import freeze_bars

SECURITY = MarketDataSecurity("US", "AVGO", "USD", "America/New_York")
ID = "10000000-0000-4000-8000-000000000001"


def freeze(rows: Any, tf: str = "M1", security: Any = SECURITY, now: Any = None) -> Any:
    return freeze_bars(
        tuple(rows),
        security_id=ID,
        security=security,
        provider="futu_opend_quote",
        timeframe=tf,
        observed_at=now or rows[0].retrieved_at,
    )


def minute(start: datetime) -> MinuteBar:
    return MinuteBar(
        "US.AVGO",
        start,
        start + timedelta(minutes=1),
        Decimal("1.123456789012345678"),
        Decimal("2"),
        Decimal("1"),
        Decimal("1.5"),
        Decimal("0.000000000000000001"),
        True,
        start + timedelta(days=1),
    )


@pytest.mark.parametrize(
    "start,day",
    [
        (datetime(2026, 3, 8, 6, 59, tzinfo=UTC), "2026-03-08"),
        (datetime(2026, 3, 8, 7, tzinfo=UTC), "2026-03-08"),
        (datetime(2026, 11, 1, 5, 30, tzinfo=UTC), "2026-11-01"),
        (datetime(2026, 11, 1, 6, 30, tzinfo=UTC), "2026-11-01"),
        (datetime(2026, 9, 8, 1, 30, tzinfo=UTC), "2026-09-07"),
    ],
)
def test_dst_and_cross_utc_date_preserve_exact_identity(start: datetime, day: str) -> None:
    frozen = freeze([minute(start)])[0]
    assert frozen.payload["session_date"] == day
    assert frozen.payload["interval_start"].startswith(start.isoformat()[:19])


def test_decimal_hash_stable_independent_of_context_scale_and_observation() -> None:
    bar = minute(datetime(2026, 9, 7, 14, tzinfo=UTC))
    first = freeze([bar])[0]
    with localcontext() as context:
        context.prec = 6
        second = freeze(
            [
                replace(
                    bar,
                    high=Decimal("2.0000"),
                    retrieved_at=bar.retrieved_at + timedelta(seconds=1),
                )
            ]
        )[0]
    assert first.version_hash == second.version_hash
    assert first.retrieved_at != second.retrieved_at
    assert second.payload["open"] == "1.123456789012345678"


@pytest.mark.parametrize(
    "field,value",
    [
        ("is_completed", False),
        ("security", "US.NVDA"),
        ("open", 1.5),
        ("volume", Decimal("-1")),
        ("close", Decimal("3")),
        ("low", Decimal("NaN")),
        ("volume", Decimal("0.0000000000000000001")),
    ],
)
def test_malformed_domain_objects_rejected_at_archive_boundary(field: str, value: Any) -> None:
    bar = minute(datetime(2026, 9, 7, 14, tzinfo=UTC))
    object.__setattr__(bar, field, value)
    with pytest.raises((ValueError, TypeError)):
        freeze([bar])


def test_minute_duration_window_and_duplicate_conflict() -> None:
    bar = minute(datetime(2026, 9, 7, 14, tzinfo=UTC))
    for invalid in (
        replace(bar, interval_end=bar.interval_end + timedelta(seconds=1)),
        replace(bar, retrieved_at=bar.interval_start),
        replace(bar, retrieved_at=bar.retrieved_at + timedelta(days=31)),
    ):
        with pytest.raises(ValueError):
            freeze([invalid])
    assert len(freeze([bar, bar])) == 1
    with pytest.raises(ValueError, match="CONFLICTING_DUPLICATE"):
        freeze([bar, replace(bar, volume=Decimal("5"))])
    with pytest.raises(ValueError, match="ROW_BOUND"):
        freeze([bar] * 50001)


def test_daily_provider_session_and_future_dates_checked() -> None:
    now = datetime(2026, 9, 8, 22, tzinfo=UTC)
    bar = DailyBar(
        "US.AVGO",
        date(2026, 9, 7),
        datetime(2026, 9, 7, 4, tzinfo=UTC),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("0"),
        True,
        now,
    )
    assert freeze([bar], "D1")[0].payload["provider_time"] == "2026-09-07T04:00:00.000000Z"
    with pytest.raises(ValueError):
        freeze([replace(bar, session_date=date(2026, 9, 8))], "D1")
