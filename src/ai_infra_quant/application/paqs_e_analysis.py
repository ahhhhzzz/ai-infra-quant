from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from ai_infra_quant.application.paqs_e_runtime import (
    PaqsEReasoningRuntime,
    build_reasoning_request,
    load_prompt_package,
    load_strategy_package,
)
from ai_infra_quant.core.domain.common import canonical_uuid, utc_now
from ai_infra_quant.core.domain.paqs_e_ledger import PersistedAnalysis
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    PaqsERuntimeConfigV1,
    PromptPackage,
    StrategyPackage,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot, canonical_json
from ai_infra_quant.core.ports.paqs_e_ledger import PaqsELedger


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
    ) -> None:
        self._snapshot_queries = snapshot_queries
        self._runtime = runtime
        self._ledger = ledger
        self._strategy_loader = strategy_loader
        self._prompt_loader = prompt_loader
        self._runtime_config = runtime_config or PaqsERuntimeConfigV1()
        self._now = now

    def analyze(self, *, security_id: str, model_id: str, strategy_id: str) -> PersistedAnalysis:
        security_id = canonical_uuid(security_id)
        if not model_id.strip() or any(character.isspace() for character in model_id):
            raise ValueError("model_id must be a non-empty identifier without whitespace")
        strategy = self._strategy_loader(strategy_id)
        prompt = self._prompt_loader()
        snapshot = self._snapshot_queries.current_snapshot(security_id)
        if snapshot.security.security_id != security_id:
            raise ValueError("snapshot Security does not match requested Security")
        request = build_reasoning_request(
            snapshot=snapshot,
            model_id=model_id,
            runtime_config=self._runtime_config,
            strategy=strategy,
            prompt=prompt,
            auxiliary_context=(),
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
