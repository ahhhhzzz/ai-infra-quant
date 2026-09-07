from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from ai_infra_quant.core.domain.paqs_e_ledger import AnalysisRun, Decision, PersistedAnalysis
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    PaqsEReasoningRequestV1,
    PaqsEValidationFailure,
    PromptPackage,
    StrategyPackage,
    ValidatedPaqsEResult,
)
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningProviderFailure

AnalysisOutcome = ValidatedPaqsEResult | PaqsEValidationFailure | ReasoningProviderFailure


class PaqsELedger(Protocol):
    """Each record call owns one atomic terminal-outcome transaction, then returns."""

    def record(
        self,
        *,
        request: PaqsEReasoningRequestV1,
        strategy: StrategyPackage,
        prompt: PromptPackage,
        outcome: AnalysisOutcome,
        request_payload_json: str,
        request_payload_sha256: str,
        started_at: datetime,
        completed_at: datetime,
    ) -> PersistedAnalysis: ...

    def get_analysis(self, analysis_run_id: UUID) -> AnalysisRun | None: ...

    def get_decision(self, decision_id: UUID) -> Decision | None: ...

    def list_decisions(
        self,
        security_id: UUID,
        *,
        limit: int = 20,
        strategy_id: str | None = None,
    ) -> tuple[Decision, ...]: ...
