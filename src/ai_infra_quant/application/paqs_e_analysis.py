from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from ai_infra_quant.application.paqs_e_models import ModelRegistry
from ai_infra_quant.application.paqs_e_research import ResearchFailure, WebResearch
from ai_infra_quant.application.paqs_e_runtime import (
    PaqsEReasoningRuntime,
    build_reasoning_request,
    load_prompt_package,
    load_strategy_package,
)
from ai_infra_quant.core.domain.common import canonical_uuid, utc_now
from ai_infra_quant.core.domain.paqs_e_ledger import PersistedAnalysis
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    AuxiliaryContextItem,
    PaqsERuntimeConfigV1,
    PromptPackage,
    StrategyPackage,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot, canonical_json
from ai_infra_quant.core.ports.paqs_e_ledger import PaqsELedger
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningFailureKind


class CurrentSnapshotQueries(Protocol):
    def current_snapshot(self, security_id: str) -> PaqsMarketSnapshot: ...


class PaqsEAnalysisService:
    """One explicit current request, one runtime attempt, one committed ledger outcome."""

    def __init__(
        self,
        snapshot_queries: CurrentSnapshotQueries,
        runtime: PaqsEReasoningRuntime,
        ledger: PaqsELedger,
        *,
        strategy_loader: Callable[[str], StrategyPackage] = load_strategy_package,
        prompt_loader: Callable[[], PromptPackage] = load_prompt_package,
        runtime_config: PaqsERuntimeConfigV1 | None = None,
        now: Callable[[], datetime] = utc_now,
        models: ModelRegistry | None = None,
        research: WebResearch | None = None,
    ) -> None:
        self._snapshot_queries = snapshot_queries
        self._runtime = runtime
        self._ledger = ledger
        self._strategy_loader = strategy_loader
        self._prompt_loader = prompt_loader
        self._runtime_config = runtime_config or PaqsERuntimeConfigV1()
        self._now = now
        self._models = models or ModelRegistry()
        self._research = research

    def analyze(
        self, *, security_id: str, model_key: str, strategy_id: str, web_research: bool
    ) -> PersistedAnalysis:
        security_id = canonical_uuid(security_id)
        strategy = self._strategy_loader(strategy_id)
        prompt = self._prompt_loader()
        snapshot = self._snapshot_queries.current_snapshot(security_id)
        if snapshot.security.security_id != security_id:
            raise ValueError("snapshot Security does not match requested Security")
        model = self._models.resolve(model_key)
        context: tuple[AuxiliaryContextItem, ...] = ()
        if web_research:
            if not model.web_research_supported or self._research is None:
                raise ResearchFailure(ReasoningFailureKind.CONFIGURATION_ERROR)
            context = self._research.research(model, snapshot)
        request = build_reasoning_request(
            snapshot=snapshot,
            model_id=model.model_id,
            model_provider=model.provider_id,
            runtime_config=self._runtime_config,
            strategy=strategy,
            prompt=prompt,
            auxiliary_context=context,
        )
        payload = canonical_json(request)
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        started_at = self._now()
        outcome = self._runtime.reason(request=request, strategy=strategy, prompt=prompt)
        completed_at = self._now()
        # The adapter opens its transaction here, after the external runtime call ends.
        return self._ledger.record(
            request=request,
            strategy=strategy,
            prompt=prompt,
            outcome=outcome,
            request_payload_json=payload,
            request_payload_sha256=payload_hash,
            started_at=started_at,
            completed_at=completed_at,
        )
