"""Append-only PAQS-Q product analysis evidence."""

import sqlalchemy as sa

from ai_infra_quant.database.base import Base
from ai_infra_quant.database.types import UTCDateTime

paqs_q_analysis_runs = sa.Table(
    "paqs_q_analysis_runs",
    Base.metadata,
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
    paqs_q_analysis_runs.c.security_id,
    paqs_q_analysis_runs.c.created_at,
    paqs_q_analysis_runs.c.analysis_id,
)
sa.Index(
    "ix_paqs_q_analysis_snapshot",
    paqs_q_analysis_runs.c.snapshot_hash,
    paqs_q_analysis_runs.c.analysis_id,
)
