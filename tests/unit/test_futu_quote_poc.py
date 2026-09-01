from __future__ import annotations

from datetime import UTC, datetime
from types import TracebackType

import pytest

from ai_infra_quant.config import Settings
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import (
    MarketDataSecurity,
    ProviderResult,
    ProviderStatus,
)
from ai_infra_quant.integrations.futu_quote import poc

FIXED_NOW = datetime(2026, 9, 1, 14, 35, 30, tzinfo=UTC)


class FakeAdapter:
    def __init__(self) -> None:
        self.closed = False

    def __enter__(self) -> FakeAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.closed = True

    def provider_status(self) -> ProviderResult[ProviderStatus]:
        return ProviderResult(
            status=DataAvailabilityStatus.AVAILABLE,
            retrieved_at=FIXED_NOW,
            data=ProviderStatus(quote_context_open=True, sdk_version="test-sdk"),
        )

    def get_latest_quote(self, security: MarketDataSecurity) -> ProviderResult[str]:
        if security.display_symbol == "US.VRT":
            return ProviderResult(
                status=DataAvailabilityStatus.NOT_ENTITLED,
                retrieved_at=FIXED_NOW,
                reason="quote permission unavailable",
            )
        return _available(security)

    def get_market_status(self, security: MarketDataSecurity) -> ProviderResult[str]:
        return _available(security)

    def get_daily_bars(self, security: MarketDataSecurity) -> ProviderResult[str]:
        return _available(security)

    def get_recent_minute_bars(
        self, security: MarketDataSecurity, lookback_days: int
    ) -> ProviderResult[str]:
        assert lookback_days == 30
        return _available(security)


def _available(security: MarketDataSecurity) -> ProviderResult[str]:
    return ProviderResult(
        status=DataAvailabilityStatus.AVAILABLE,
        retrieved_at=FIXED_NOW,
        data=security.display_symbol,
    )


def test_smoke_runner_preserves_partial_results_and_closes_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeAdapter()
    monkeypatch.setattr(poc, "opend_reachable", lambda *_args: (True, None))
    monkeypatch.setattr(poc, "FutuQuoteAdapter", lambda *_args: fake)

    report = poc.run_live_poc(Settings())

    assert report["result"] == "LIVE_POC_PARTIAL"
    securities = report["securities"]
    assert isinstance(securities, dict)
    assert list(securities) == ["US.AVGO", "US.VRT", "HK.09698"]
    vrt = securities["US.VRT"]
    assert isinstance(vrt, dict)
    assert vrt["latest"].status is DataAvailabilityStatus.NOT_ENTITLED
    assert fake.closed is True
