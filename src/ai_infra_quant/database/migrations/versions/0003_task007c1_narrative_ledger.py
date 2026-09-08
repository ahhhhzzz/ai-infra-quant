"""Add immutable narrative ledger without changing legacy structured evidence."""

import sqlalchemy as sa
from alembic import op

revision = "0003_task007c1_narrative_ledger"
down_revision = "0002_task007b_paqs_e_ledger"
branch_labels = None
depends_on = None


def _timestamp():
    return sa.Text() if op.get_context().dialect.name == "sqlite" else sa.DateTime(timezone=True)


def upgrade():
    op.create_table(
        "paqs_e_narrative_runs",
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
        sa.Column("snapshot_as_of_timestamp", _timestamp(), nullable=False),
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
        sa.Column("started_at", _timestamp(), nullable=False),
        sa.Column("completed_at", _timestamp(), nullable=False),
        sa.Column("created_at", _timestamp(), nullable=False),
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
    op.create_index(
        "ix_narrative_runs_history",
        "paqs_e_narrative_runs",
        ["security_id", "strategy_id", "created_at"],
    )
    op.create_table(
        "paqs_e_narrative_results",
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
        sa.Column("snapshot_as_of_timestamp", _timestamp(), nullable=False),
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
        sa.Column("created_at", _timestamp(), nullable=False),
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
    op.create_index(
        "ix_narrative_results_history",
        "paqs_e_narrative_results",
        ["security_id", "strategy_id", "created_at"],
    )
    if op.get_context().dialect.name == "sqlite":
        for table in ("paqs_e_narrative_runs", "paqs_e_narrative_results"):
            for action in ("UPDATE", "DELETE"):
                op.execute(
                    f"CREATE TRIGGER {table}_{action.lower()} BEFORE {action} ON {table} "
                    "BEGIN SELECT RAISE(ABORT, 'narrative evidence is immutable'); END"
                )
        op.execute("""CREATE TRIGGER narrative_result_parent BEFORE INSERT ON
        paqs_e_narrative_results
        BEGIN SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM paqs_e_narrative_runs r WHERE
        r.narrative_run_id=NEW.narrative_run_id AND r.status='SUCCEEDED'
        AND r.security_id=NEW.security_id
        AND r.symbol=NEW.symbol
        AND r.market=NEW.market
        AND r.instrument_type=NEW.instrument_type
        AND r.snapshot_hash=NEW.snapshot_hash
        AND r.snapshot_as_of_timestamp=NEW.snapshot_as_of_timestamp
        AND r.analysis_mode=NEW.analysis_mode
        AND r.request_schema_version=NEW.request_schema_version
        AND r.output_format_version=NEW.output_format_version
        AND r.runtime_config_version=NEW.runtime_config_version
        AND r.model_provider=NEW.model_provider
        AND r.model_id=NEW.model_id
        AND r.strategy_id=NEW.strategy_id
        AND r.strategy_content_sha256=NEW.strategy_content_sha256
        AND r.strategy_artifact_id=NEW.strategy_artifact_id
        AND r.prompt_version=NEW.prompt_version
        AND r.prompt_content_sha256=NEW.prompt_content_sha256
        AND r.prompt_artifact_id=NEW.prompt_artifact_id
        AND r.web_research=NEW.web_research
        ) THEN RAISE(ABORT, 'narrative result requires matching successful run') END;
        SELECT CASE WHEN NEW.revision_no != COALESCE((SELECT MAX(revision_no)+1 FROM
        paqs_e_narrative_results WHERE security_id=NEW.security_id AND
        strategy_id=NEW.strategy_id),1)
        OR (NEW.revision_no > 1 AND NOT EXISTS (SELECT 1 FROM paqs_e_narrative_results p WHERE
        p.narrative_result_id=NEW.supersedes_narrative_result_id AND
        p.security_id=NEW.security_id AND p.strategy_id=NEW.strategy_id AND
        p.revision_no=NEW.revision_no-1))
        THEN RAISE(ABORT, 'invalid narrative lineage') END; END""")


def downgrade():
    if op.get_context().dialect.name == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS narrative_result_parent")
        for table in ("paqs_e_narrative_results", "paqs_e_narrative_runs"):
            for action in ("update", "delete"):
                op.execute(f"DROP TRIGGER IF EXISTS {table}_{action}")
    op.drop_table("paqs_e_narrative_results")
    op.drop_table("paqs_e_narrative_runs")
