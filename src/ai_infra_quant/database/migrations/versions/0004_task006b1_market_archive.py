"""0004: additive immutable local market archive. No changes to 0001/0002/0003."""

import sqlalchemy as sa
from alembic import op

from ai_infra_quant.database.types import ExactDecimal, UTCDateTime

revision = "0004_task006b1_market_archive"
down_revision = "0003_task007c1_narrative_ledger"
branch_labels = None
depends_on = None
metadata = sa.MetaData()
sa.Table("securities", metadata, sa.Column("id", sa.String(36), primary_key=True))

captures = sa.Table(
    "market_archive_captures",
    metadata,
    sa.Column("capture_id", sa.String(36), primary_key=True),
    sa.Column(
        "security_id",
        sa.String(36),
        sa.ForeignKey("securities.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("recorded_at", UTCDateTime(), nullable=False),
    sa.Column("payload_json", sa.Text(), nullable=False),
    sa.Column("payload_hash", sa.String(64), nullable=False),
    sa.UniqueConstraint("capture_id", "security_id", name="uq_archive_capture_security"),
)
sa.Index(
    "ix_archive_capture_security_order",
    captures.c.security_id,
    captures.c.recorded_at,
    captures.c.capture_id,
)

versions = sa.Table(
    "market_archive_bar_versions",
    metadata,
    sa.Column("version_hash", sa.String(64), primary_key=True),
    sa.Column("identity_hash", sa.String(64), nullable=False),
    sa.Column(
        "security_id",
        sa.String(36),
        sa.ForeignKey("securities.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("timeframe", sa.String(2), nullable=False),
    sa.Column("sort_key", sa.String(32), nullable=False),
    sa.Column("payload_json", sa.Text(), nullable=False),
    *(
        sa.Column(name, ExactDecimal(), nullable=False)
        for name in ("open", "high", "low", "close", "volume")
    ),
    sa.CheckConstraint("timeframe IN ('D1','M1')", name="archive_version_timeframe"),
    sa.UniqueConstraint(
        "version_hash", "security_id", "timeframe", name="uq_archive_version_owner"
    ),
)
sa.Index("ix_archive_version_identity", versions.c.identity_hash, versions.c.version_hash)

memberships = sa.Table(
    "market_archive_memberships",
    metadata,
    sa.Column("capture_id", sa.String(36), primary_key=True),
    sa.Column("timeframe", sa.String(2), primary_key=True),
    sa.Column("ordinal", sa.Integer(), primary_key=True),
    sa.Column("security_id", sa.String(36), nullable=False),
    sa.Column("version_hash", sa.String(64), nullable=False),
    sa.Column("retrieved_at", UTCDateTime(), nullable=False),
    sa.ForeignKeyConstraint(
        ["capture_id", "security_id"],
        ["market_archive_captures.capture_id", "market_archive_captures.security_id"],
        ondelete="RESTRICT",
    ),
    sa.ForeignKeyConstraint(
        ["version_hash", "security_id", "timeframe"],
        [
            "market_archive_bar_versions.version_hash",
            "market_archive_bar_versions.security_id",
            "market_archive_bar_versions.timeframe",
        ],
        ondelete="RESTRICT",
    ),
    sa.UniqueConstraint(
        "capture_id", "timeframe", "version_hash", name="uq_archive_member_version"
    ),
    sa.CheckConstraint("ordinal >= 0", name="archive_member_ordinal"),
)


def upgrade():
    for table in (captures, versions, memberships):
        table.create(op.get_bind())
    if op.get_context().dialect.name == "sqlite":
        op.execute(
            "CREATE TRIGGER market_archive_membership_bound BEFORE INSERT ON "
            "market_archive_memberships WHEN NEW.ordinal >= COALESCE((SELECT "
            "json_extract(payload_json, '$.batches.' || NEW.timeframe || '.count') "
            "FROM market_archive_captures WHERE capture_id=NEW.capture_id), 0) "
            "BEGIN SELECT RAISE(ABORT, 'capture membership is sealed'); END"
        )
        for table in (captures, versions, memberships):
            for operation in ("update", "delete"):
                op.execute(
                    f"CREATE TRIGGER {table.name}_immutable_{operation} "
                    f"BEFORE {operation.upper()} ON {table.name} "
                    "BEGIN SELECT RAISE(ABORT, 'immutable market archive'); END"
                )
    elif op.get_context().dialect.name == "postgresql":
        op.execute(
            "CREATE FUNCTION market_archive_membership_bound() RETURNS trigger "
            "LANGUAGE plpgsql AS $$ DECLARE expected integer; BEGIN "
            "SELECT (payload_json::jsonb->'batches'->NEW.timeframe->>'count')::integer "
            "INTO expected FROM market_archive_captures WHERE capture_id=NEW.capture_id; "
            "IF NEW.ordinal >= COALESCE(expected,0) THEN "
            "RAISE EXCEPTION 'capture membership is sealed'; END IF; RETURN NEW; END; $$"
        )
        op.execute(
            "CREATE TRIGGER market_archive_membership_bound BEFORE INSERT ON "
            "market_archive_memberships FOR EACH ROW "
            "EXECUTE FUNCTION market_archive_membership_bound()"
        )
        op.execute(
            "CREATE FUNCTION market_archive_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN RAISE EXCEPTION 'immutable market archive'; END; $$"
        )
        for table in (captures, versions, memberships):
            op.execute(
                f"CREATE TRIGGER {table.name}_immutable BEFORE UPDATE OR DELETE ON {table.name} "
                "FOR EACH ROW EXECUTE FUNCTION market_archive_immutable()"
            )


def downgrade():
    for table in (memberships, versions, captures):
        table.drop(op.get_bind())
    if op.get_context().dialect.name == "postgresql":
        op.execute("DROP FUNCTION market_archive_membership_bound()")
        op.execute("DROP FUNCTION market_archive_immutable()")
