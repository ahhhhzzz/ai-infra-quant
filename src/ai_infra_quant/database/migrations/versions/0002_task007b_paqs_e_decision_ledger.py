"""TASK-007B immutable analysis evidence and Decision revisions.

Schema declarations are frozen here and deliberately independent of current ORM metadata.
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_task007b_paqs_e_ledger"
down_revision = "0001_phase1_foundation"
branch_labels = None
depends_on = None

TABLES = ("paqs_e_runtime_artifacts", "paqs_e_analysis_runs", "paqs_e_decisions")


def _timestamp():
    return sa.Text() if op.get_context().dialect.name == "sqlite" else sa.DateTime(timezone=True)


def _decimal():
    return sa.Text() if op.get_context().dialect.name == "sqlite" else sa.Numeric(38, 18)


def upgrade():
    op.create_table(
        "paqs_e_runtime_artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("artifact_kind", sa.String(16), nullable=False),
        sa.Column("artifact_key", sa.String(120), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("created_at", _timestamp(), nullable=False),
        sa.UniqueConstraint(
            "artifact_kind", "artifact_key", "content_sha256", name="uq_paqs_e_artifact_identity"
        ),
        sa.CheckConstraint("artifact_kind IN ('STRATEGY','PROMPT')", name="artifact_kind"),
        sa.CheckConstraint("length(content_sha256) = 64", name="content_hash_length"),
    )
    op.create_table(
        "paqs_e_analysis_runs",
        sa.Column("id", sa.String(36), primary_key=True),
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
        sa.Column("snapshot_as_of_timestamp", _timestamp(), nullable=False),
        sa.Column("analysis_mode", sa.String(32), nullable=False),
        sa.Column("request_schema_version", sa.String(80), nullable=False),
        sa.Column("output_schema_version", sa.String(80), nullable=False),
        sa.Column("runtime_config_version", sa.String(80), nullable=False),
        sa.Column("validator_version", sa.String(80), nullable=True),
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
        sa.Column("request_payload_json", sa.Text(), nullable=False),
        sa.Column("request_payload_sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("provider_response_id", sa.Text(), nullable=True),
        sa.Column("failure_kind", sa.String(32), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("validation_issues_json", sa.Text(), nullable=False),
        sa.Column("started_at", _timestamp(), nullable=False),
        sa.Column("completed_at", _timestamp(), nullable=False),
        sa.Column("created_at", _timestamp(), nullable=False),
        sa.CheckConstraint(
            "status IN ('SUCCEEDED','PROVIDER_FAILED','VALIDATION_FAILED')", name="terminal_status"
        ),
        sa.CheckConstraint(
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
        sa.CheckConstraint("completed_at >= started_at", name="run_time_order"),
    )
    op.create_index(
        "ix_paqs_e_runs_security_created", "paqs_e_analysis_runs", ["security_id", "created_at"]
    )
    op.create_table(
        "paqs_e_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "analysis_run_id",
            sa.String(36),
            sa.ForeignKey("paqs_e_analysis_runs.id", ondelete="RESTRICT"),
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
        sa.Column("snapshot_as_of_timestamp", _timestamp(), nullable=False),
        sa.Column("analysis_mode", sa.String(32), nullable=False),
        sa.Column("request_schema_version", sa.String(80), nullable=False),
        sa.Column("output_schema_version", sa.String(80), nullable=False),
        sa.Column("runtime_config_version", sa.String(80), nullable=False),
        sa.Column("validator_version", sa.String(80), nullable=False),
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
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column(
            "supersedes_decision_id",
            sa.String(36),
            sa.ForeignKey("paqs_e_decisions.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("result_payload_json", sa.Text(), nullable=False),
        sa.Column("result_payload_sha256", sa.String(64), nullable=False),
        sa.Column("one_line_thesis", sa.Text(), nullable=False),
        sa.Column("entry_advisory", sa.String(64), nullable=False),
        sa.Column("holder_advisory_basis", sa.String(64), nullable=False),
        sa.Column("holder_advisory", sa.String(64), nullable=False),
        sa.Column("market_bias", sa.String(64), nullable=False),
        sa.Column("setup_family", sa.String(64), nullable=False),
        sa.Column("setup_direction", sa.String(64), nullable=False),
        sa.Column("setup_stage", sa.String(64), nullable=False),
        sa.Column("rr_status", sa.String(64), nullable=False),
        sa.Column("rr_t1", _decimal(), nullable=True),
        sa.Column("uncertainty_level", sa.String(16), nullable=False),
        sa.Column("created_at", _timestamp(), nullable=False),
        sa.UniqueConstraint("analysis_run_id", name="uq_paqs_e_decision_run"),
        sa.UniqueConstraint(
            "security_id", "strategy_id", "revision_no", name="uq_paqs_e_decision_revision"
        ),
        sa.CheckConstraint("revision_no > 0", name="positive_revision"),
        sa.CheckConstraint(
            "supersedes_decision_id IS NULL OR supersedes_decision_id != id",
            name="no_self_supersedes",
        ),
        sa.CheckConstraint(
            "(revision_no = 1 AND supersedes_decision_id IS NULL) OR (revision_no > 1 "
            "AND supersedes_decision_id IS NOT NULL)",
            name="revision_predecessor",
        ),
    )
    op.create_index(
        "ix_paqs_e_decisions_security_created", "paqs_e_decisions", ["security_id", "created_at"]
    )
    if op.get_context().dialect.name == "sqlite":
        for table in TABLES:
            for action in ("UPDATE", "DELETE"):
                op.execute(
                    sa.text(
                        f"CREATE TRIGGER {table}_immutable_{action.lower()} "
                        f"BEFORE {action} ON {table} "
                        f"BEGIN SELECT RAISE(ABORT, '{table} is immutable'); END"
                    )
                )
        op.execute(
            sa.text(
                "CREATE TRIGGER paqs_e_decisions_series_insert BEFORE INSERT ON paqs_e_decisions "
                "WHEN NOT EXISTS (SELECT 1 FROM paqs_e_analysis_runs r "
                "WHERE r.id = NEW.analysis_run_id "
                "AND r.status = 'SUCCEEDED' AND r.security_id = NEW.security_id "
                "AND r.strategy_id = NEW.strategy_id) "
                "OR (NEW.revision_no > 1 AND NOT EXISTS (SELECT 1 FROM paqs_e_decisions p "
                "WHERE p.id = NEW.supersedes_decision_id AND p.security_id = NEW.security_id "
                "AND p.strategy_id = NEW.strategy_id AND p.revision_no = NEW.revision_no - 1)) "
                "BEGIN SELECT RAISE(ABORT, 'invalid PAQS-E Decision lineage'); END"
            )
        )


def downgrade():
    if op.get_context().dialect.name == "sqlite":
        op.execute(sa.text("DROP TRIGGER IF EXISTS paqs_e_decisions_series_insert"))
        for table in reversed(TABLES):
            for action in ("update", "delete"):
                op.execute(sa.text(f"DROP TRIGGER IF EXISTS {table}_immutable_{action}"))
    op.drop_index("ix_paqs_e_decisions_security_created", table_name="paqs_e_decisions")
    op.drop_index("ix_paqs_e_runs_security_created", table_name="paqs_e_analysis_runs")
    for table in reversed(TABLES):
        op.drop_table(table)
