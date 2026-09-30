"""Recoverable history visibility; no change to evidence or immutable triggers."""

import sqlalchemy as sa
from alembic import op

from ai_infra_quant.database.types import UTCDateTime

revision = "0007_analysis_visibility"
down_revision = "0006_external_research"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_visibility",
        sa.Column("record_type", sa.String(1), primary_key=True),
        sa.Column("record_id", sa.String(36), primary_key=True),
        sa.Column("deleted_at", UTCDateTime(), nullable=True),
        sa.CheckConstraint("record_type IN ('Q','E')", name="analysis_visibility_record_type"),
    )


def downgrade() -> None:
    op.drop_table("analysis_visibility")
