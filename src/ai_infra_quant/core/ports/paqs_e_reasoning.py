from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from ai_infra_quant.core.domain.paqs_e_reasoning import (
    PaqsEReasoningRequestV1,
    PaqsEReasoningResultV1,
    PromptPackage,
    StrategyPackage,
)


class ReasoningFailureKind(StrEnum):
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_REFUSAL = "PROVIDER_REFUSAL"
    INVALID_STRUCTURED_OUTPUT = "INVALID_STRUCTURED_OUTPUT"


@dataclass(frozen=True, slots=True)
class ReasoningProviderSuccess:
    result: PaqsEReasoningResultV1
    provider_response_id: str | None


@dataclass(frozen=True, slots=True)
class ReasoningProviderFailure:
    kind: ReasoningFailureKind
    reason: str


ReasoningProviderOutcome = ReasoningProviderSuccess | ReasoningProviderFailure


class PaqsEReasoningProvider(Protocol):
    def reason(
        self,
        *,
        request: PaqsEReasoningRequestV1,
        strategy: StrategyPackage,
        prompt: PromptPackage,
    ) -> ReasoningProviderOutcome: ...
