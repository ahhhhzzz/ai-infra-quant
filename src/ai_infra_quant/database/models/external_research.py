"""Additive independent-search receipts; existing narrative rows are untouched."""

import sqlalchemy as sa

from ai_infra_quant.database.base import Base
from ai_infra_quant.database.types import UTCDateTime

searches = sa.Table(
    "paqs_e_external_research",
    Base.metadata,
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
