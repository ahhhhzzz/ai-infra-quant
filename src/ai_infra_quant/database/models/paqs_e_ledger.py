from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ai_infra_quant.database.base import Base
from ai_infra_quant.database.types import ExactDecimal, UTCDateTime


class PaqsERuntimeArtifactModel(Base):
    __tablename__ = "paqs_e_runtime_artifacts"
    __table_args__ = (
        UniqueConstraint(
            "artifact_kind", "artifact_key", "content_sha256", name="uq_paqs_e_artifact_identity"
        ),
        CheckConstraint("artifact_kind IN ('STRATEGY','PROMPT')", name="artifact_kind"),
        CheckConstraint("length(content_sha256) = 64", name="content_hash_length"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    artifact_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    artifact_key: Mapped[str] = mapped_column(String(120), nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text(), nullable=True)
    source_path: Mapped[str] = mapped_column(Text(), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    content_text: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PaqsEAnalysisRunModel(Base):
    __tablename__ = "paqs_e_analysis_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('SUCCEEDED','PROVIDER_FAILED','VALIDATION_FAILED')", name="terminal_status"
        ),
        CheckConstraint(
            "(status = 'PROVIDER_FAILED' AND failure_kind IN "
            "('CONFIGURATION_ERROR','PROVIDER_UNAVAILABLE',"
            "'PROVIDER_REFUSAL','INVALID_STRUCTURED_OUTPUT') "
            "AND failure_reason IS NOT NULL AND validator_version IS NULL AND "
            "validation_issues_json = '[]') OR (status = 'SUCCEEDED' AND failure_kind "
            "IS NULL AND failure_reason IS NULL AND validator_version IS NOT NULL AND "
            "validation_issues_json = '[]') OR (status = 'VALIDATION_FAILED' AND "
            "failure_kind IS NULL AND failure_reason IS NULL AND validator_version IS "
            "NOT NULL AND validation_issues_json != '[]')",
            name="terminal_evidence",
        ),
        CheckConstraint("completed_at >= started_at", name="run_time_order"),
        Index("ix_paqs_e_runs_security_created", "security_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    security_id: Mapped[str] = mapped_column(
        ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(16), nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_as_of_timestamp: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    analysis_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    request_schema_version: Mapped[str] = mapped_column(String(80), nullable=False)
    output_schema_version: Mapped[str] = mapped_column(String(80), nullable=False)
    runtime_config_version: Mapped[str] = mapped_column(String(80), nullable=False)
    validator_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model_id: Mapped[str] = mapped_column(Text(), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(120), nullable=False)
    strategy_content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_artifact_id: Mapped[str] = mapped_column(
        ForeignKey("paqs_e_runtime_artifacts.id", ondelete="RESTRICT"), nullable=False
    )
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt_content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_artifact_id: Mapped[str] = mapped_column(
        ForeignKey("paqs_e_runtime_artifacts.id", ondelete="RESTRICT"), nullable=False
    )
    request_payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    request_payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    provider_response_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    failure_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    validation_issues_json: Mapped[str] = mapped_column(Text(), nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PaqsEDecisionModel(Base):
    __tablename__ = "paqs_e_decisions"
    __table_args__ = (
        UniqueConstraint("analysis_run_id", name="uq_paqs_e_decision_run"),
        UniqueConstraint(
            "security_id", "strategy_id", "revision_no", name="uq_paqs_e_decision_revision"
        ),
        CheckConstraint("revision_no > 0", name="positive_revision"),
        CheckConstraint(
            "supersedes_decision_id IS NULL OR supersedes_decision_id != id",
            name="no_self_supersedes",
        ),
        CheckConstraint(
            "(revision_no = 1 AND supersedes_decision_id IS NULL) OR (revision_no > 1 "
            "AND supersedes_decision_id IS NOT NULL)",
            name="revision_predecessor",
        ),
        Index("ix_paqs_e_decisions_security_created", "security_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    analysis_run_id: Mapped[str] = mapped_column(
        ForeignKey("paqs_e_analysis_runs.id", ondelete="RESTRICT"), nullable=False
    )
    security_id: Mapped[str] = mapped_column(
        ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(16), nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_as_of_timestamp: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    analysis_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    request_schema_version: Mapped[str] = mapped_column(String(80), nullable=False)
    output_schema_version: Mapped[str] = mapped_column(String(80), nullable=False)
    runtime_config_version: Mapped[str] = mapped_column(String(80), nullable=False)
    validator_version: Mapped[str] = mapped_column(String(80), nullable=False)
    model_provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model_id: Mapped[str] = mapped_column(Text(), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(120), nullable=False)
    strategy_content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_artifact_id: Mapped[str] = mapped_column(
        ForeignKey("paqs_e_runtime_artifacts.id", ondelete="RESTRICT"), nullable=False
    )
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt_content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_artifact_id: Mapped[str] = mapped_column(
        ForeignKey("paqs_e_runtime_artifacts.id", ondelete="RESTRICT"), nullable=False
    )
    revision_no: Mapped[int] = mapped_column(Integer(), nullable=False)
    supersedes_decision_id: Mapped[str | None] = mapped_column(
        ForeignKey("paqs_e_decisions.id", ondelete="RESTRICT"), nullable=True
    )
    result_payload_json: Mapped[str] = mapped_column(Text(), nullable=False)
    result_payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    one_line_thesis: Mapped[str] = mapped_column(Text(), nullable=False)
    entry_advisory: Mapped[str] = mapped_column(String(64), nullable=False)
    holder_advisory_basis: Mapped[str] = mapped_column(String(64), nullable=False)
    holder_advisory: Mapped[str] = mapped_column(String(64), nullable=False)
    market_bias: Mapped[str] = mapped_column(String(64), nullable=False)
    setup_family: Mapped[str] = mapped_column(String(64), nullable=False)
    setup_direction: Mapped[str] = mapped_column(String(64), nullable=False)
    setup_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    rr_status: Mapped[str] = mapped_column(String(64), nullable=False)
    rr_t1: Mapped[Decimal | None] = mapped_column(ExactDecimal(), nullable=True)
    uncertainty_level: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
