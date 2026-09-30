"""Additive independent-search receipts; existing narrative rows are untouched."""

import sqlalchemy as sa
from alembic import op

from ai_infra_quant.database.types import UTCDateTime

revision = "0006_external_research"
down_revision = "0005_task006e_q_analysis"
branch_labels = None
depends_on = None
metadata = sa.MetaData()
sa.Table("securities", metadata, sa.Column("id", sa.String(36), primary_key=True))
searches = sa.Table(
    "paqs_e_external_research",
    metadata,
    sa.Column("research_id", sa.String(36), primary_key=True),
    sa.Column(
        "security_id",
        sa.String(36),
        sa.ForeignKey("securities.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("snapshot_hash", sa.String(64), nullable=False),
    sa.Column("snapshot_as_of", UTCDateTime(), nullable=False),
    sa.Column("status", sa.String(16), nullable=False),
    sa.Column("payload_json", sa.Text(), nullable=False),
    sa.Column("payload_sha256", sa.String(64), nullable=False),
    sa.Column("created_at", UTCDateTime(), nullable=False),
    sa.CheckConstraint("status IN ('SUCCEEDED','FAILED')", name="terminal_status"),
    sa.CheckConstraint("length(payload_sha256)=64", name="payload_hash_length"),
)


def upgrade() -> None:
    searches.create(op.get_bind())
    if op.get_context().dialect.name == "sqlite":
        for action in ("UPDATE", "DELETE"):
            op.execute(
                f"CREATE TRIGGER external_research_immutable_{action.lower()} "
                f"BEFORE {action} ON paqs_e_external_research "
                "BEGIN SELECT RAISE(ABORT, 'immutable search evidence'); END"
            )
    elif op.get_context().dialect.name == "postgresql":
        op.execute(
            "CREATE FUNCTION external_research_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN RAISE EXCEPTION 'immutable search evidence'; END; $$"
        )
        op.execute(
            "CREATE TRIGGER external_research_immutable BEFORE UPDATE OR DELETE "
            "ON paqs_e_external_research FOR EACH ROW "
            "EXECUTE FUNCTION external_research_immutable()"
        )


def downgrade() -> None:
    searches.drop(op.get_bind())
    if op.get_context().dialect.name == "postgresql":
        op.execute("DROP FUNCTION external_research_immutable()")
