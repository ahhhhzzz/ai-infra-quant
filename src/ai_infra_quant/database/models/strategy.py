from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from ai_infra_quant.database.base import Base
from ai_infra_quant.database.types import UTCDateTime


class StrategyDefinitionModel(Base):
    __tablename__ = "strategy_definitions"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_strategy_definitions_name_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    implementation_key: Mapped[str] = mapped_column(String(120), nullable=False)
    parameter_schema_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    default_parameters_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    definition_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    research_status: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class StrategyAssignmentModel(Base):
    __tablename__ = "strategy_assignments"
    __table_args__ = (
        Index(
            "uq_strategy_assignments_active_portfolio_security",
            "portfolio_id",
            "security_id",
            unique=True,
            sqlite_where=text("effective_to IS NULL AND portfolio_id IS NOT NULL"),
            postgresql_where=text("effective_to IS NULL AND portfolio_id IS NOT NULL"),
        ),
        Index(
            "uq_strategy_assignments_active_global_security",
            "security_id",
            unique=True,
            sqlite_where=text("effective_to IS NULL AND portfolio_id IS NULL"),
            postgresql_where=text("effective_to IS NULL AND portfolio_id IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    security_id: Mapped[str] = mapped_column(
        ForeignKey("securities.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    strategy_definition_id: Mapped[str] = mapped_column(
        ForeignKey("strategy_definitions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    portfolio_id: Mapped[str | None] = mapped_column(
        ForeignKey("portfolios.id", ondelete="RESTRICT"), index=True
    )
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    parameters_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
