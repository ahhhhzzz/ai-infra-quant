"""0005: append-only PAQS-Q product analysis evidence."""

import sqlalchemy as sa
from alembic import op

from ai_infra_quant.database.types import UTCDateTime

revision = "0005_task006e_q_analysis"
down_revision = "0004_task006b1_market_archive"
branch_labels = None
depends_on = None

metadata = sa.MetaData()
sa.Table("securities", metadata, sa.Column("id", sa.String(36), primary_key=True))
analyses = sa.Table(
    "paqs_q_analysis_runs",
    metadata,
    sa.Column("analysis_id", sa.String(36), primary_key=True),
    sa.Column(
        "security_id",
        sa.String(36),
        sa.ForeignKey("securities.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("snapshot_hash", sa.String(64), nullable=False),
    sa.Column("status", sa.String(40), nullable=False),
    sa.Column("created_at", UTCDateTime(), nullable=False),
    sa.Column("payload_json", sa.Text(), nullable=False),
    sa.Column("payload_sha256", sa.String(64), nullable=False),
    sa.CheckConstraint("length(snapshot_hash) = 64", name="snapshot_hash_length"),
    sa.CheckConstraint("length(payload_sha256) = 64", name="payload_hash_length"),
    sa.CheckConstraint("length(status) BETWEEN 1 AND 40", name="status_length"),
)
sa.Index(
    "ix_paqs_q_analysis_security_created",
    analyses.c.security_id,
    analyses.c.created_at,
    analyses.c.analysis_id,
)
sa.Index(
    "ix_paqs_q_analysis_snapshot",
    analyses.c.snapshot_hash,
    analyses.c.analysis_id,
)


def upgrade() -> None:
    analyses.create(op.get_bind())
    if op.get_context().dialect.name == "sqlite":
        for operation in ("update", "delete"):
            op.execute(
                f"CREATE TRIGGER paqs_q_analysis_runs_immutable_{operation} "
                f"BEFORE {operation.upper()} ON paqs_q_analysis_runs "
                "BEGIN SELECT RAISE(ABORT, 'immutable PAQS-Q analysis'); END"
            )
    elif op.get_context().dialect.name == "postgresql":
        op.execute(
            "CREATE FUNCTION paqs_q_analysis_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN RAISE EXCEPTION 'immutable PAQS-Q analysis'; END; $$"
        )
        op.execute(
            "CREATE TRIGGER paqs_q_analysis_runs_immutable BEFORE UPDATE OR DELETE "
            "ON paqs_q_analysis_runs FOR EACH ROW "
            "EXECUTE FUNCTION paqs_q_analysis_immutable()"
        )


def downgrade() -> None:
    analyses.drop(op.get_bind())
    if op.get_context().dialect.name == "postgresql":
        op.execute("DROP FUNCTION paqs_q_analysis_immutable()")
