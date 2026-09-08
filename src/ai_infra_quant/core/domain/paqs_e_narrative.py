"""Narrative evidence identities; no semantic interpretation of model prose."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from ai_infra_quant.core.domain.common import canonical_uuid, require_utc
from ai_infra_quant.core.domain.enums import InstrumentType
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    AnalysisMode,
    AuxiliaryContextItem,
    PaqsERuntimeConfigV1,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot

NARRATIVE_REQUEST_VERSION = "paqs-e-narrative-request-v1"
NARRATIVE_OUTPUT_VERSION = "paqs-e-narrative-markdown-v1"
NARRATIVE_PROMPT_VERSION = "paqs-e-narrative-prompt-v1"
MAX_NARRATIVE_CHARACTERS = 100_000


def check_final_text(text: str) -> None:
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_NARRATIVE_CHARACTERS:
        raise ValueError("Invalid final text length")
    text.encode("utf-8", errors="strict")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in text):
        raise ValueError("Invalid text control character")


class NarrativeFailureKind(StrEnum):
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_REFUSAL = "PROVIDER_REFUSAL"
    PROVIDER_INCOMPLETE = "PROVIDER_INCOMPLETE"
    INVALID_FINAL_TEXT = "INVALID_FINAL_TEXT"


@dataclass(frozen=True, slots=True)
class NarrativeSuccess:
    text: str
    provider_response_id: str | None = None

    def __post_init__(self) -> None:
        check_final_text(self.text)
        if self.provider_response_id is not None and not re.fullmatch(
            r"[A-Za-z0-9_.:-]{1,256}", self.provider_response_id
        ):
            raise ValueError("Invalid provider response id")


@dataclass(frozen=True, slots=True)
class NarrativeFailure:
    kind: NarrativeFailureKind

    @property
    def reason(self) -> str:
        return {
            NarrativeFailureKind.CONFIGURATION_ERROR: (
                "Selected model or runtime credential unavailable"
            ),
            NarrativeFailureKind.PROVIDER_UNAVAILABLE: "Selected provider request unavailable",
            NarrativeFailureKind.PROVIDER_REFUSAL: "Selected provider refused the request",
            NarrativeFailureKind.PROVIDER_INCOMPLETE: (
                "Selected provider did not complete its answer"
            ),
            NarrativeFailureKind.INVALID_FINAL_TEXT: "Provider final text failed integrity checks",
        }[self.kind]


@dataclass(frozen=True, slots=True, kw_only=True)
class NarrativeRequest:
    security_id: str
    symbol: str
    market: str
    instrument_type: InstrumentType
    snapshot_hash: str
    snapshot_as_of_timestamp: datetime
    model_provider: str
    model_id: str
    primary_strategy_id: str
    primary_strategy_content_sha256: str
    prompt_version: str
    prompt_content_sha256: str
    runtime_config: PaqsERuntimeConfigV1
    runtime_config_version: str
    market_snapshot: PaqsMarketSnapshot
    auxiliary_context: tuple[AuxiliaryContextItem, ...]
    web_research: bool
    request_schema_version: str = NARRATIVE_REQUEST_VERSION
    output_format_version: str = NARRATIVE_OUTPUT_VERSION
    analysis_mode: AnalysisMode = AnalysisMode.CURRENT_ANALYSIS

    def __post_init__(self) -> None:
        canonical_uuid(self.security_id)
        require_utc(self.snapshot_as_of_timestamp)
        snapshot = self.market_snapshot
        if (
            self.security_id,
            self.symbol,
            self.market,
            self.instrument_type,
            self.snapshot_hash,
            self.snapshot_as_of_timestamp,
        ) != (
            snapshot.security.security_id,
            snapshot.security.symbol,
            snapshot.security.market,
            snapshot.security.instrument_type,
            snapshot.snapshot_hash,
            snapshot.as_of_timestamp,
        ):
            raise ValueError("Narrative Snapshot identity mismatch")
        if (
            self.request_schema_version != NARRATIVE_REQUEST_VERSION
            or self.output_format_version != NARRATIVE_OUTPUT_VERSION
            or self.prompt_version != NARRATIVE_PROMPT_VERSION
            or self.analysis_mode is not AnalysisMode.CURRENT_ANALYSIS
        ):
            raise ValueError("Unsupported narrative version or mode")
        if (
            self.runtime_config_version != self.runtime_config.runtime_config_version
            or self.market not in self.runtime_config.supported_market_scope
            or self.instrument_type not in self.runtime_config.supported_instrument_scope
        ):
            raise ValueError("Narrative runtime scope mismatch")
        for value in (self.prompt_content_sha256, self.primary_strategy_content_sha256):
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ValueError("Invalid narrative artifact hash")
        for value in (self.model_provider, self.model_id, self.primary_strategy_id):
            if not re.fullmatch(r"[A-Za-z0-9_.-]{1,120}", value):
                raise ValueError("Invalid narrative identity")
        if type(self.web_research) is not bool or self.web_research != bool(self.auxiliary_context):
            raise ValueError("Narrative research outcome mismatch")
        ids = [item.context_id for item in self.auxiliary_context]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate auxiliary identity")
        for item in self.auxiliary_context:
            if (
                item.category != "web_research"
                or not item.as_of_compatible
                or (
                    item.source_timestamp is not None
                    and item.source_timestamp > self.snapshot_as_of_timestamp
                )
            ):
                raise ValueError("Narrative auxiliary evidence violates As-Of")


@dataclass(frozen=True, slots=True, kw_only=True)
class NarrativeIdentity:
    security_id: str
    symbol: str
    market: str
    instrument_type: str
    snapshot_hash: str
    snapshot_as_of_timestamp: datetime
    analysis_mode: str
    request_schema_version: str
    output_format_version: str
    runtime_config_version: str
    model_provider: str
    model_id: str
    strategy_id: str
    strategy_content_sha256: str
    strategy_artifact_id: str
    prompt_version: str
    prompt_content_sha256: str
    prompt_artifact_id: str
    web_research: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class NarrativeRun(NarrativeIdentity):
    narrative_run_id: str
    request_payload_json: str
    request_payload_sha256: str
    status: str
    provider_response_id: str | None
    failure_kind: str | None
    failure_reason: str | None
    started_at: datetime
    completed_at: datetime
    created_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class NarrativeResult(NarrativeIdentity):
    narrative_result_id: str
    narrative_run_id: str
    revision_no: int
    supersedes_narrative_result_id: str | None
    response_text: str
    response_text_sha256: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PersistedNarrative:
    run: NarrativeRun
    result: NarrativeResult | None
