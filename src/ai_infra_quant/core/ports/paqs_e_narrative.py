from __future__ import annotations

from datetime import datetime
from typing import Protocol

from ai_infra_quant.core.domain.paqs_e_narrative import (
    NarrativeFailure,
    NarrativeRequest,
    NarrativeResult,
    NarrativeRun,
    NarrativeSuccess,
    PersistedNarrative,
)
from ai_infra_quant.core.domain.paqs_e_reasoning import PromptPackage, StrategyPackage


class PaqsENarrativeProvider(Protocol):
    def reason_text(
        self, *, request: NarrativeRequest, strategy: StrategyPackage, prompt: PromptPackage
    ) -> NarrativeSuccess | NarrativeFailure: ...


class NarrativeLedger(Protocol):
    def record(
        self,
        *,
        request: NarrativeRequest,
        strategy: StrategyPackage,
        prompt: PromptPackage,
        outcome: NarrativeSuccess | NarrativeFailure,
        started_at: datetime,
        completed_at: datetime,
    ) -> PersistedNarrative: ...
    def get_run(self, run_id: str) -> NarrativeRun | None: ...
    def get_result(self, result_id: str) -> NarrativeResult | None: ...
    def history(
        self, security_id: str, strategy_id: str | None = None, limit: int = 20
    ) -> tuple[NarrativeResult, ...]: ...
