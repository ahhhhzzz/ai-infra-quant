"""Research is a precondition stage; an incomplete capsule has no fabricated Run ID."""

import re
from dataclasses import asdict, dataclass
from typing import Literal, Protocol

from ai_infra_quant.application.paqs_e_models import ModelDescriptor
from ai_infra_quant.core.domain.paqs_e_reasoning import AuxiliaryContextItem
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningFailureKind


@dataclass(frozen=True)
class ResearchDiagnostic:
    """Allowlisted metadata only, never provider bodies or exception messages."""

    stage: Literal["SEARCH", "SYNTHESIS"]
    failure_class: Literal["TRANSPORT_ERROR", "INVALID_RESPONSE", "UNSAFE_RESPONSE", "REFUSAL"]
    provider_id: str
    model_id: str
    synthesis_attempted: bool
    research_http_request_count: int
    provider_status: str | None = None
    provider_response_id: str | None = None
    web_search_call_count: int = 0
    search_action_count: int = 0
    message_count: int = 0
    incomplete_reason: str | None = None
    detail_version: str = "paqs-e-research-diagnostic-v1"

    def __post_init__(self) -> None:
        if (
            self.stage not in {"SEARCH", "SYNTHESIS"}
            or self.failure_class
            not in {"TRANSPORT_ERROR", "INVALID_RESPONSE", "UNSAFE_RESPONSE", "REFUSAL"}
            or self.detail_version != "paqs-e-research-diagnostic-v1"
            or self.provider_status not in {None, "completed", "incomplete", "failed", "cancelled"}
            or self.incomplete_reason not in {None, "max_output_tokens", "content_filter"}
            or type(self.synthesis_attempted) is not bool
            or type(self.research_http_request_count) is not int
            or self.research_http_request_count not in {1, 2}
        ):
            raise ValueError("Unsafe research diagnostic")
        for value in (self.provider_id, self.model_id):
            if re.fullmatch(r"[a-z0-9_.-]{1,100}", value) is None:
                raise ValueError("Unsafe research identity")
        if (
            self.provider_response_id is not None
            and re.fullmatch(r"[A-Za-z0-9_.:-]{1,200}", self.provider_response_id) is None
        ):
            raise ValueError("Unsafe research response identity")
        for count in (self.web_search_call_count, self.search_action_count, self.message_count):
            if type(count) is not int or not 0 <= count <= 129:
                raise ValueError("Unsafe research count")

    def as_dict(self) -> dict[str, object]:
        return {key: value for key, value in asdict(self).items() if value is not None}


class ResearchFailure(RuntimeError):
    def __init__(
        self, kind: ReasoningFailureKind, diagnostic: ResearchDiagnostic | None = None
    ) -> None:
        self.kind = kind
        self.diagnostic = diagnostic
        super().__init__("Requested web research could not produce a complete auditable capsule")


class WebResearch(Protocol):
    def research(
        self, model: ModelDescriptor, snapshot: PaqsMarketSnapshot
    ) -> tuple[AuxiliaryContextItem, ...]: ...
