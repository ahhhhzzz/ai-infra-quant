from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, SecretStr, StrictBool, field_serializer, field_validator

from ai_infra_quant.application.paqs_e_models import ModelRegistry
from ai_infra_quant.backend.schemas.common import Problem, StrictSchema
from ai_infra_quant.core.domain.enums import InstrumentType
from ai_infra_quant.core.domain.money import canonical_decimal_string
from ai_infra_quant.core.domain.paqs_e_ledger import (
    AnalysisRun,
    AnalysisStatus,
    Decision,
    PersistedAnalysis,
)
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    AnalysisMode,
    EntryAdvisory,
    HolderAdvisory,
    HolderAdvisoryBasis,
    MarketBias,
    PaqsEReasoningResultV1,
    RRStatus,
    SetupDirection,
    SetupFamily,
    SetupStage,
    UncertaintyLevel,
    ValidationIssue,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.core.ports.paqs_e_reasoning import ReasoningFailureKind


class StrategyOptionRead(StrictSchema):
    strategy_id: str
    display_name: str
    content_sha256: str


class ModelOptionRead(StrictSchema):
    model_key: str
    display_name: str
    credential_label: str
    credential_configured: bool
    web_research_supported: bool


class CredentialStatusRead(StrictSchema):
    credential_configured: bool
    credential_source: str
    secure_storage_available: bool


class CredentialSave(StrictSchema):
    secret: SecretStr = Field(min_length=1, max_length=1024)


class CredentialDelete(StrictSchema):
    pass


class ConfigurationRead(StrictSchema):
    default_model_key: str
    models: list[ModelOptionRead]
    default_strategy_id: str
    strategies: tuple[StrategyOptionRead, ...]


class AnalyzeCreate(StrictSchema):
    security_id: UUID
    model_key: str = Field(min_length=1, max_length=80)
    strategy_id: str = Field(min_length=1)
    web_research: StrictBool

    @field_validator("model_key", "strategy_id")
    @classmethod
    def identifier_is_explicit(cls, value: str) -> str:
        if not value.strip() or any(character.isspace() for character in value):
            raise ValueError("identifier must be non-empty and contain no whitespace")
        return value

    @field_validator("model_key")
    @classmethod
    def registered_model(cls, value: str) -> str:
        ModelRegistry().resolve(value)
        return value


class LedgerIdentityRead(StrictSchema):
    security_id: UUID
    symbol: str
    market: str
    instrument_type: InstrumentType
    snapshot_hash: str
    snapshot_as_of_timestamp: datetime
    analysis_mode: AnalysisMode
    request_schema_version: str
    output_schema_version: str
    runtime_config_version: str
    validator_version: str | None
    model_provider: str
    model_id: str
    strategy_id: str
    strategy_content_sha256: str
    strategy_artifact_id: UUID
    prompt_version: str
    prompt_content_sha256: str
    prompt_artifact_id: UUID
    created_at: datetime


class AnalysisRunRead(LedgerIdentityRead):
    analysis_run_id: UUID
    status: AnalysisStatus
    request_payload_json: str
    request_payload_sha256: str
    provider_response_id: str | None
    failure_kind: ReasoningFailureKind | None
    failure_reason: str | None
    validation_issues: tuple[ValidationIssue, ...]
    started_at: datetime
    completed_at: datetime


class DecisionSummaryRead(LedgerIdentityRead):
    decision_id: UUID
    analysis_run_id: UUID
    validator_version: str
    revision_no: int
    supersedes_decision_id: UUID | None
    one_line_thesis: str
    entry_advisory: EntryAdvisory
    holder_advisory_basis: HolderAdvisoryBasis
    holder_advisory: HolderAdvisory
    market_bias: MarketBias
    setup_family: SetupFamily
    setup_direction: SetupDirection
    setup_stage: SetupStage
    rr_status: RRStatus
    rr_t1: Decimal | None
    uncertainty_level: UncertaintyLevel

    @field_serializer("rr_t1")
    def serialize_rr(self, value: Decimal | None) -> str | None:
        return canonical_decimal_string(value) if value is not None else None


class DecisionRead(DecisionSummaryRead):
    result: PaqsEReasoningResultV1
    result_payload_sha256: str

    @field_serializer("result")
    def serialize_result(self, value: PaqsEReasoningResultV1) -> object:
        return json.loads(canonical_json(value))


class AnalyzeCreated(DecisionRead):
    status: Literal[AnalysisStatus.SUCCEEDED] = AnalysisStatus.SUCCEEDED


class DecisionHistoryRead(StrictSchema):
    items: list[DecisionSummaryRead]


class AnalysisFailureContext(StrictSchema):
    analysis_run_id: UUID
    status: AnalysisStatus
    failure_kind: ReasoningFailureKind | None
    validator_version: str | None
    validation_issues: tuple[ValidationIssue, ...]


class AnalysisProblem(Problem):
    analysis_run_id: UUID
    analysis_status: AnalysisStatus
    failure_kind: ReasoningFailureKind | None
    validator_version: str | None
    validation_issues: tuple[ValidationIssue, ...]
    analysis_run: AnalysisFailureContext


def analysis_run_read(run: AnalysisRun) -> AnalysisRunRead:
    values = {
        name: getattr(run, name)
        for name in AnalysisRunRead.model_fields
        if name != "analysis_run_id"
    }
    return AnalysisRunRead(analysis_run_id=run.id, **values)


def decision_read(decision: Decision) -> DecisionRead:
    values = {
        name: getattr(decision, name) for name in DecisionRead.model_fields if name != "decision_id"
    }
    return DecisionRead(decision_id=decision.id, **values)


def decision_summary_read(decision: Decision) -> DecisionSummaryRead:
    values = {
        name: getattr(decision, name)
        for name in DecisionSummaryRead.model_fields
        if name != "decision_id"
    }
    return DecisionSummaryRead(decision_id=decision.id, **values)


def analyze_created(persisted: PersistedAnalysis) -> AnalyzeCreated:
    if persisted.decision is None or persisted.run.status is not AnalysisStatus.SUCCEEDED:
        raise ValueError("successful analysis requires a persisted Decision")
    return AnalyzeCreated(**decision_read(persisted.decision).model_dump())
