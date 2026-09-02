from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from ai_infra_quant.core.domain.common import utc_now
from ai_infra_quant.core.domain.paqs_input import PaqsInputBundle
from ai_infra_quant.core.strategy.paqs_structure import (
    PaqsStructureConfig,
    PaqsStructureSnapshot,
    build_structure_snapshot,
)


class PaqsInputSource(Protocol):
    def current_bundle(self, security_id: str) -> PaqsInputBundle: ...


class PaqsStructureQueries:
    """Build current read-only PAQS structure from the TASK-006A input bundle."""

    def __init__(
        self,
        input_queries: PaqsInputSource,
        *,
        config: PaqsStructureConfig | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._input_queries = input_queries
        self._config = config or PaqsStructureConfig()
        self._now = now or utc_now

    def current_snapshot(self, security_id: str) -> PaqsStructureSnapshot:
        bundle = self._input_queries.current_bundle(security_id)
        calculated_at = max(self._now(), bundle.as_of_timestamp)
        return build_structure_snapshot(
            bundle,
            config=self._config,
            calculated_at=calculated_at,
        )
