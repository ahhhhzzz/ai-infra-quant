from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from ai_infra_quant.database.base import Base
from ai_infra_quant.database.types import UTCDateTime


class SettingModel(Base):
    __tablename__ = "settings"
    __table_args__ = (
        CheckConstraint("is_secret = false", name="never_secret"),
        Index(
            "uq_settings_system_scope_key",
            "scope_type",
            "key",
            unique=True,
            sqlite_where=text("scope_id IS NULL"),
            postgresql_where=text("scope_id IS NULL"),
        ),
        Index(
            "uq_settings_named_scope_key",
            "scope_type",
            "scope_id",
            "key",
            unique=True,
            sqlite_where=text("scope_id IS NOT NULL"),
            postgresql_where=text("scope_id IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_id: Mapped[str | None] = mapped_column(String(36))
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(32), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_secret: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
