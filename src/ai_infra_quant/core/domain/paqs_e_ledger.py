"""Immutable PAQS-E evidence records; no provider or persistence dependencies."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum, StrEnum
from types import UnionType
from typing import Any, cast, get_args, get_origin, get_type_hints
from uuid import UUID

from ai_infra_quant.core.domain.common import require_utc
from ai_infra_quant.core.domain.enums import InstrumentType
from ai_infra_quant.core.domain.money import parse_decimal
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


class LedgerIntegrityError(ValueError):
    """Stored or supplied evidence cannot be trusted."""


class LedgerPersistenceError(RuntimeError):
    """A ledger transaction could not be committed."""


class AnalysisStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    PROVIDER_FAILED = "PROVIDER_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"


def payload_sha256(payload_text: str) -> str:
    return hashlib.sha256(payload_text.encode("utf-8")).hexdigest()


def verified_json(payload_text: str, expected_hash: str) -> Any:
    if payload_sha256(payload_text) != expected_hash:
        raise LedgerIntegrityError("PAQS-E evidence SHA-256 mismatch")
    try:
        value = json.loads(payload_text)
        if canonical_json(value) != payload_text:
            raise ValueError("non-canonical payload")
    except (ValueError, TypeError) as exc:
        raise LedgerIntegrityError("PAQS-E evidence JSON is invalid") from exc
    return value


def _decode(value: Any, annotation: Any) -> Any:
    """Decode only the dataclass/enum/scalar vocabulary used by the result contract."""
    origin = get_origin(annotation)
    if origin is UnionType:
        for option in get_args(annotation):
            try:
                return _decode(value, option)
            except (ValueError, TypeError):
                continue
        raise ValueError("invalid union value")
    if annotation is type(None):
        if value is not None:
            raise ValueError("expected null")
        return None
    if origin is tuple:
        if not isinstance(value, list):
            raise ValueError("expected array")
        element_type, tail = get_args(annotation)
        if tail is not Ellipsis:
            raise ValueError("unsupported tuple contract")
        return tuple(_decode(item, element_type) for item in value)
    if isinstance(annotation, type) and is_dataclass(annotation):
        if not isinstance(value, dict) or set(value) != {f.name for f in fields(annotation)}:
            raise ValueError("invalid structured fields")
        hints = get_type_hints(annotation)
        return annotation(**{key: _decode(item, hints[key]) for key, item in value.items()})
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        if not isinstance(value, str):
            raise ValueError("expected enum string")
        return annotation(value)
    if annotation is Decimal:
        if not isinstance(value, str):
            raise ValueError("expected exact decimal text")
        return parse_decimal(value)
    if annotation is datetime:
        if not isinstance(value, str):
            raise ValueError("expected UTC timestamp")
        return require_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
    if annotation in (str, bool, int) and type(value) is annotation:
        return value
    raise ValueError("invalid result field type")


def parse_result(payload_text: str, expected_hash: str) -> PaqsEReasoningResultV1:
    value = verified_json(payload_text, expected_hash)
    try:
        result = cast(PaqsEReasoningResultV1, _decode(value, PaqsEReasoningResultV1))
        if canonical_json(result) != payload_text:
            raise ValueError("non-canonical structured result")
        return result
    except (ValueError, TypeError, KeyError) as exc:
        raise LedgerIntegrityError("PAQS-E structured result evidence is invalid") from exc


@dataclass(frozen=True, slots=True, kw_only=True)
class LedgerIdentity:
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

    def verify_identity(self, payload: dict[str, Any]) -> None:
        for field in fields(LedgerIdentity):
            if field.name in {
                "security_id",
                "validator_version",
                "strategy_artifact_id",
                "prompt_artifact_id",
            }:
                continue
            source_key = {
                "strategy_id": "primary_strategy_id",
                "strategy_content_sha256": "primary_strategy_content_sha256",
            }.get(field.name, field.name)
            if canonical_json(getattr(self, field.name)) != canonical_json(payload.get(source_key)):
                raise LedgerIntegrityError("PAQS-E identity columns disagree with evidence")


@dataclass(frozen=True, slots=True, kw_only=True)
class AnalysisRun(LedgerIdentity):
    id: UUID
    request_payload_json: str
    request_payload_sha256: str
    status: AnalysisStatus
    provider_response_id: str | None
    failure_kind: str | None
    failure_reason: str | None
    validation_issues: tuple[ValidationIssue, ...]
    started_at: datetime
    completed_at: datetime
    created_at: datetime

    def __post_init__(self) -> None:
        request = verified_json(self.request_payload_json, self.request_payload_sha256)
        if not isinstance(request, dict):
            raise LedgerIntegrityError("PAQS-E request evidence must be an object")
        self.verify_identity(request)
        try:
            security_id = UUID(request["market_snapshot"]["security"]["security_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LedgerIntegrityError("PAQS-E request security evidence is invalid") from exc
        if security_id != self.security_id:
            raise LedgerIntegrityError("PAQS-E request security identity mismatch")
        for timestamp in (self.started_at, self.completed_at, self.created_at):
            require_utc(timestamp)
        if self.completed_at < self.started_at:
            raise LedgerIntegrityError("PAQS-E run timestamps are inconsistent")
        if self.status is AnalysisStatus.PROVIDER_FAILED:
            if self.failure_kind not in {
                "CONFIGURATION_ERROR",
                "PROVIDER_UNAVAILABLE",
                "PROVIDER_REFUSAL",
                "INVALID_STRUCTURED_OUTPUT",
            }:
                raise LedgerIntegrityError("PAQS-E provider failure kind is invalid")
            if (
                not self.failure_reason
                or self.validation_issues
                or self.validator_version is not None
            ):
                raise LedgerIntegrityError("PAQS-E provider failure evidence is inconsistent")
        elif self.failure_kind is not None or self.failure_reason is not None:
            raise LedgerIntegrityError("PAQS-E failure fields disagree with status")
        elif not self.validator_version or (
            bool(self.validation_issues) != (self.status is AnalysisStatus.VALIDATION_FAILED)
        ):
            raise LedgerIntegrityError("PAQS-E validation evidence disagrees with status")


@dataclass(frozen=True, slots=True, kw_only=True)
class Decision(LedgerIdentity):
    id: UUID
    analysis_run_id: UUID
    revision_no: int
    supersedes_decision_id: UUID | None
    result_payload_json: str
    result_payload_sha256: str
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
    created_at: datetime

    @property
    def result(self) -> PaqsEReasoningResultV1:
        return parse_result(self.result_payload_json, self.result_payload_sha256)

    def __post_init__(self) -> None:
        result = self.result
        self.verify_identity(json.loads(canonical_json(result.identity)))
        if not self.validator_version or self.revision_no < 1:
            raise LedgerIntegrityError("PAQS-E Decision validator/revision is invalid")
        if (self.revision_no == 1) != (self.supersedes_decision_id is None):
            raise LedgerIntegrityError("PAQS-E Decision revision predecessor is invalid")
        if self.supersedes_decision_id == self.id:
            raise LedgerIntegrityError("PAQS-E Decision cannot supersede itself")
        require_utc(self.created_at)
        for key, expected in result_summary(result).items():
            if getattr(self, key) != expected:
                raise LedgerIntegrityError("PAQS-E Decision summary disagrees with result evidence")


def result_summary(result: PaqsEReasoningResultV1) -> dict[str, Any]:
    return {
        "one_line_thesis": result.one_line_thesis,
        "entry_advisory": result.entry.advisory,
        "holder_advisory_basis": result.holder.advisory_basis,
        "holder_advisory": result.holder.advisory,
        "market_bias": result.context.market_bias,
        "setup_family": result.setup.family,
        "setup_direction": result.setup.direction,
        "setup_stage": result.setup.stage,
        "rr_status": result.risk_reward.rr_status,
        "rr_t1": result.risk_reward.rr_t1,
        "uncertainty_level": result.uncertainty.level,
    }


@dataclass(frozen=True, slots=True)
class PersistedAnalysis:
    run: AnalysisRun
    decision: Decision | None

    def __post_init__(self) -> None:
        if (self.run.status is AnalysisStatus.SUCCEEDED) != (self.decision is not None):
            raise LedgerIntegrityError("PAQS-E terminal run/Decision pairing is invalid")
        if self.decision is not None and self.decision.analysis_run_id != self.run.id:
            raise LedgerIntegrityError("PAQS-E Decision references a different Analysis Run")
