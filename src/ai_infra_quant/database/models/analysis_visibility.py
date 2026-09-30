"""Mutable visibility only; immutable Q/E evidence remains untouched."""

import sqlalchemy as sa

from ai_infra_quant.database.base import Base
from ai_infra_quant.database.types import UTCDateTime

visibility = sa.Table(
    "analysis_visibility",
    Base.metadata,
    sa.Column("record_type", sa.String(1), primary_key=True),
    sa.Column("record_id", sa.String(36), primary_key=True),
    sa.Column("deleted_at", UTCDateTime(), nullable=True),
    sa.CheckConstraint("record_type IN ('Q','E')", name="analysis_visibility_record_type"),
)
