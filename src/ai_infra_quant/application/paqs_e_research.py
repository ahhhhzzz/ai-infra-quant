"""Research is a precondition stage; an incomplete capsule has no fabricated Run ID."""

import re
from dataclasses import asdict, dataclass
from typing import Literal, Protocol

from ai_infra_quant.application.paqs_e_models import ModelDescriptor
from ai_infra_quant.core.domain.paqs_e_reasoning import AuxiliaryContextItem
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningFailureKind

RESEARCH_BOUNDARY_CODES = frozenset(
    {
        "SEARCH_ENVELOPE",
        "SEARCH_OUTPUT_SHAPE",
        "ACTION_SHAPE",
        "ACTION_TYPE",
        "ACTION_STATUS",
        "ACTION_BOUND",
        "NO_COMPLETED_SEARCH",
        "QUERY_STRUCTURE",
        "QUERY_INTEGRITY",
        "QUERY_STRUCTURAL_BOUND",
        "SOURCE_STRUCTURE",
        "SOURCE_BOUND",
        "SOURCE_URL",
        "MESSAGE_SHAPE",
        "MESSAGE_INTEGRITY",
        "PASSBACK_BOUND",
        "PROVENANCE_BOUND",
        "SYNTHESIS_ENVELOPE",
        "SYNTHESIS_OUTPUT_SHAPE",
        "SYNTHESIS_MESSAGE",
        "SYNTHESIS_MEMO_INTEGRITY",
    }
)


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
    provider_exposed_query_count: int | None = None
    raw_source_record_count: int | None = None
    unknown_action_count: int | None = None
    boundary_code: str | None = None
    completed_action_count: int | None = None
    in_progress_action_count: int | None = None
    incomplete_action_count: int | None = None
    failed_action_count: int | None = None
    cancelled_action_count: int | None = None
    completed_search_count: int | None = None
    non_completed_search_count: int | None = None
    missing_or_unknown_status_count: int | None = None
    invalid_query_value_count: int | None = None
    malformed_action_count: int | None = None
    unexpected_output_item_count: int | None = None

    def __post_init__(self) -> None:
        if self.boundary_code is not None and (
            not isinstance(self.boundary_code, str)
            or self.boundary_code not in RESEARCH_BOUNDARY_CODES
        ):
            raise ValueError("Unsafe research boundary")
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
        for optional_count in (
            self.provider_exposed_query_count,
            self.raw_source_record_count,
            self.unknown_action_count,
            self.completed_action_count,
            self.in_progress_action_count,
            self.incomplete_action_count,
            self.failed_action_count,
            self.cancelled_action_count,
            self.completed_search_count,
            self.non_completed_search_count,
            self.missing_or_unknown_status_count,
            self.invalid_query_value_count,
            self.malformed_action_count,
            self.unexpected_output_item_count,
        ):
            if optional_count is not None and (
                type(optional_count) is not int or not 0 <= optional_count <= 1024
            ):
                raise ValueError("Unsafe research diagnostic count")

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
