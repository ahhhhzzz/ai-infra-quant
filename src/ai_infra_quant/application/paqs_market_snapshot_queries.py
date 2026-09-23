from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from ai_infra_quant.application.market_data_queries import MarketDataQueries
from ai_infra_quant.application.paqs_input_queries import PaqsInputQueries
from ai_infra_quant.core.domain.common import utc_now
from ai_infra_quant.core.domain.paqs_input import PaqsInputBundle
from ai_infra_quant.core.domain.paqs_market_snapshot import (
    PaqsMarketSnapshot,
    build_paqs_market_snapshot,
)


class PaqsMarketSnapshotQueries:
    """Freeze one current provider-neutral factual snapshot per request."""

    def __init__(
        self,
        input_queries: PaqsInputQueries,
        market_data_queries: MarketDataQueries,
        *,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._input_queries = input_queries
        self._market_data_queries = market_data_queries
        self._now = now

    def current_snapshot(self, security_id: str) -> PaqsMarketSnapshot:
        return self.current_capture(security_id)[0]

    def current_capture(self, security_id: str) -> tuple[PaqsMarketSnapshot, PaqsInputBundle]:
        """Return the frozen display snapshot and its source facts from one acquisition."""
        acquisition = self._input_queries.current_acquisition(security_id)
        market_state = self._market_data_queries.state(security_id)
        snapshot = build_paqs_market_snapshot(
            bundle=acquisition.bundle,
            security=market_state.security,
            quote_result=market_state.quote,
            market_state_result=market_state.market_status,
            d1_source_status=acquisition.d1_source_status,
            minute_source_status=acquisition.minute_source_status,
            created_at=self._now(),
        )
        return snapshot, acquisition.bundle
