from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from importlib.resources import files

from ai_infra_quant.application.paqs_e_analysis import CurrentSnapshotQueries
from ai_infra_quant.application.paqs_e_models import ModelRegistry
from ai_infra_quant.application.paqs_e_research import ResearchFailure, WebResearch
from ai_infra_quant.application.paqs_e_runtime import RuntimePackageError, load_strategy_package
from ai_infra_quant.core.domain.common import canonical_uuid, utc_now
from ai_infra_quant.core.domain.paqs_e_ledger import payload_sha256
from ai_infra_quant.core.domain.paqs_e_narrative import (
    NARRATIVE_PROMPT_VERSION,
    NarrativeRequest,
    PersistedNarrative,
)
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    AuxiliaryContextItem,
    PaqsERuntimeConfigV1,
    PromptPackage,
    StrategyPackage,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot
from ai_infra_quant.core.ports.paqs_e_narrative import NarrativeLedger, PaqsENarrativeProvider
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningFailureKind


def load_narrative_prompt() -> PromptPackage:
    name = "runtime_prompt_narrative_v1.md"
    try:
        content = (
            files("ai_infra_quant.resources.paqs_e").joinpath(name).read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError):
        raise RuntimePackageError("Narrative prompt unavailable") from None
    return PromptPackage(
        NARRATIVE_PROMPT_VERSION,
        "src/ai_infra_quant/resources/paqs_e/" + name,
        payload_sha256(content),
        content,
    )


def build_narrative_request(
    *,
    snapshot: PaqsMarketSnapshot,
    model_provider: str,
    model_id: str,
    strategy: StrategyPackage,
    prompt: PromptPackage,
    auxiliary_context: tuple[AuxiliaryContextItem, ...] = (),
    web_research: bool = False,
) -> NarrativeRequest:
    config = PaqsERuntimeConfigV1()
    return NarrativeRequest(
        security_id=snapshot.security.security_id,
        symbol=snapshot.security.symbol,
        market=snapshot.security.market,
        instrument_type=snapshot.security.instrument_type,
        snapshot_hash=snapshot.snapshot_hash,
        snapshot_as_of_timestamp=snapshot.as_of_timestamp,
        model_provider=model_provider,
        model_id=model_id,
        primary_strategy_id=strategy.strategy_id,
        primary_strategy_content_sha256=strategy.content_sha256,
        prompt_version=prompt.prompt_version,
        prompt_content_sha256=prompt.content_sha256,
        runtime_config=config,
        runtime_config_version=config.runtime_config_version,
        market_snapshot=snapshot,
        auxiliary_context=auxiliary_context,
        web_research=web_research,
    )


class NarrativeAnalysisService:
    def __init__(
        self,
        snapshots: CurrentSnapshotQueries,
        provider: PaqsENarrativeProvider,
        ledger: NarrativeLedger,
        models: ModelRegistry,
        research: WebResearch,
        *,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.snapshots, self.provider, self.ledger = snapshots, provider, ledger
        self.models, self.research, self.now = models, research, now

    def analyze(
        self, *, security_id: str, model_key: str, strategy_id: str, web_research: bool
    ) -> PersistedNarrative:
        canonical_uuid(security_id)
        strategy, prompt = load_strategy_package(strategy_id), load_narrative_prompt()
        snapshot = self.snapshots.current_snapshot(security_id)
        if snapshot.security.security_id != security_id:
            raise ValueError("Snapshot Security mismatch")
        model = self.models.resolve(model_key)
        if web_research and not model.web_research_supported:
            raise ResearchFailure(ReasoningFailureKind.CONFIGURATION_ERROR)
        context = self.research.research(model, snapshot) if web_research else ()
        request = build_narrative_request(
            snapshot=snapshot,
            model_provider=model.provider_id,
            model_id=model.model_id,
            strategy=strategy,
            prompt=prompt,
            auxiliary_context=context,
            web_research=web_research,
        )
        started = self.now()
        outcome = self.provider.reason_text(request=request, strategy=strategy, prompt=prompt)
        return self.ledger.record(
            request=request,
            strategy=strategy,
            prompt=prompt,
            outcome=outcome,
            started_at=started,
            completed_at=self.now(),
        )
