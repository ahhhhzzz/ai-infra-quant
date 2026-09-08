"""Additive narrative ledger SQL tables; legacy tables are unchanged."""

import sqlalchemy as sa

from ai_infra_quant.database.base import Base
from ai_infra_quant.database.types import UTCDateTime

runs = sa.Table(
    "paqs_e_narrative_runs",
    Base.metadata,
    sa.Column("narrative_run_id", sa.String(36), primary_key=True),
    sa.Column(
        "security_id",
        sa.String(36),
        sa.ForeignKey("securities.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("symbol", sa.String(32), nullable=False),
    sa.Column("market", sa.String(32), nullable=False),
    sa.Column("instrument_type", sa.String(16), nullable=False),
    sa.Column("snapshot_hash", sa.String(64), nullable=False),
    sa.Column("snapshot_as_of_timestamp", UTCDateTime(), nullable=False),
    sa.Column("analysis_mode", sa.String(32), nullable=False),
    sa.Column("request_schema_version", sa.String(80), nullable=False),
    sa.Column("output_format_version", sa.String(80), nullable=False),
    sa.Column("runtime_config_version", sa.String(80), nullable=False),
    sa.Column("model_provider", sa.String(80), nullable=False),
    sa.Column("model_id", sa.Text(), nullable=False),
    sa.Column("strategy_id", sa.String(120), nullable=False),
    sa.Column("strategy_content_sha256", sa.String(64), nullable=False),
    sa.Column(
        "strategy_artifact_id",
        sa.String(36),
        sa.ForeignKey("paqs_e_runtime_artifacts.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("prompt_version", sa.String(80), nullable=False),
    sa.Column("prompt_content_sha256", sa.String(64), nullable=False),
    sa.Column(
        "prompt_artifact_id",
        sa.String(36),
        sa.ForeignKey("paqs_e_runtime_artifacts.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("web_research", sa.Boolean(), nullable=False),
    sa.Column("request_payload_json", sa.Text(), nullable=False),
    sa.Column("request_payload_sha256", sa.String(64), nullable=False),
    sa.Column("status", sa.String(24), nullable=False),
    sa.Column("provider_response_id", sa.String(256), nullable=True),
    sa.Column("failure_kind", sa.String(32), nullable=True),
    sa.Column("failure_reason", sa.Text(), nullable=True),
    sa.Column("started_at", UTCDateTime(), nullable=False),
    sa.Column("completed_at", UTCDateTime(), nullable=False),
    sa.Column("created_at", UTCDateTime(), nullable=False),
    sa.CheckConstraint("status IN ('SUCCEEDED','PROVIDER_FAILED')", name="terminal_status"),
    sa.CheckConstraint(
        "(status='SUCCEEDED' AND failure_kind IS NULL AND failure_reason IS NULL) OR "
        "(status='PROVIDER_FAILED' AND failure_kind IN "
        "('CONFIGURATION_ERROR','PROVIDER_UNAVAILABLE','PROVIDER_REFUSAL','PROVIDER_INCOMPLETE','INVALID_FINAL_TEXT')"
        " AND failure_reason IS NOT NULL)",
        name="terminal_evidence",
    ),
    sa.CheckConstraint("completed_at >= started_at", name="time_order"),
)
results = sa.Table(
    "paqs_e_narrative_results",
    Base.metadata,
    sa.Column("narrative_result_id", sa.String(36), primary_key=True),
    sa.Column(
        "narrative_run_id",
        sa.String(36),
        sa.ForeignKey("paqs_e_narrative_runs.narrative_run_id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column(
        "security_id",
        sa.String(36),
        sa.ForeignKey("securities.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("symbol", sa.String(32), nullable=False),
    sa.Column("market", sa.String(32), nullable=False),
    sa.Column("instrument_type", sa.String(16), nullable=False),
    sa.Column("snapshot_hash", sa.String(64), nullable=False),
    sa.Column("snapshot_as_of_timestamp", UTCDateTime(), nullable=False),
    sa.Column("analysis_mode", sa.String(32), nullable=False),
    sa.Column("request_schema_version", sa.String(80), nullable=False),
    sa.Column("output_format_version", sa.String(80), nullable=False),
    sa.Column("runtime_config_version", sa.String(80), nullable=False),
    sa.Column("model_provider", sa.String(80), nullable=False),
    sa.Column("model_id", sa.Text(), nullable=False),
    sa.Column("strategy_id", sa.String(120), nullable=False),
    sa.Column("strategy_content_sha256", sa.String(64), nullable=False),
    sa.Column(
        "strategy_artifact_id",
        sa.String(36),
        sa.ForeignKey("paqs_e_runtime_artifacts.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("prompt_version", sa.String(80), nullable=False),
    sa.Column("prompt_content_sha256", sa.String(64), nullable=False),
    sa.Column(
        "prompt_artifact_id",
        sa.String(36),
        sa.ForeignKey("paqs_e_runtime_artifacts.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("web_research", sa.Boolean(), nullable=False),
    sa.Column("revision_no", sa.Integer(), nullable=False),
    sa.Column(
        "supersedes_narrative_result_id",
        sa.String(36),
        sa.ForeignKey("paqs_e_narrative_results.narrative_result_id", ondelete="RESTRICT"),
        nullable=True,
    ),
    sa.Column("response_text", sa.Text(), nullable=False),
    sa.Column("response_text_sha256", sa.String(64), nullable=False),
    sa.Column("created_at", UTCDateTime(), nullable=False),
    sa.CheckConstraint("revision_no > 0", name="positive_revision"),
    sa.CheckConstraint(
        "(revision_no=1 AND supersedes_narrative_result_id IS NULL) OR (revision_no>1"
        " AND supersedes_narrative_result_id IS NOT NULL AND "
        "supersedes_narrative_result_id != narrative_result_id)",
        name="predecessor",
    ),
    sa.CheckConstraint("length(response_text) BETWEEN 1 AND 100000", name="text_bound"),
    sa.CheckConstraint("length(response_text_sha256)=64", name="text_hash"),
    sa.UniqueConstraint("narrative_run_id", name="uq_narrative_result_run"),
    sa.UniqueConstraint(
        "security_id", "strategy_id", "revision_no", name="uq_narrative_result_revision"
    ),
)
