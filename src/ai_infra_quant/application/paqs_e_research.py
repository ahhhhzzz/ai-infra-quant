"""Research is a precondition stage; an incomplete capsule has no fabricated Run ID."""

from typing import Protocol

from ai_infra_quant.application.paqs_e_models import ModelDescriptor
from ai_infra_quant.core.domain.paqs_e_reasoning import AuxiliaryContextItem
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningFailureKind


class ResearchFailure(RuntimeError):
    def __init__(self, kind: ReasoningFailureKind) -> None:
        self.kind = kind
        super().__init__("Requested web research could not produce a complete auditable capsule")


class WebResearch(Protocol):
    def research(
        self, model: ModelDescriptor, snapshot: PaqsMarketSnapshot
    ) -> tuple[AuxiliaryContextItem, ...]: ...
