"""Additive archive tables; content versions and exact capture membership are distinct."""

import sqlalchemy as sa

from ai_infra_quant.database.base import Base
from ai_infra_quant.database.types import ExactDecimal, UTCDateTime

captures = sa.Table(
    "market_archive_captures",
    Base.metadata,
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
    Base.metadata,
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
    Base.metadata,
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
