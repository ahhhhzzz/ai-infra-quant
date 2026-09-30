"""Visibility filters are separate from evidence verification and revision allocation."""

from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.core.domain.common import canonical_uuid
from ai_infra_quant.database.models.analysis_visibility import visibility
from ai_infra_quant.database.models.paqs_e_narrative import results
from ai_infra_quant.database.models.paqs_q_analysis import paqs_q_analysis_runs


class AnalysisDeletedError(RuntimeError):
    """The record still exists, but is not available in the ordinary workbench."""


def deleted_filter(kind: str, record_id: Any) -> Any:
    return sa.exists(
        sa.select(visibility.c.record_id).where(
            visibility.c.record_type == kind,
            visibility.c.record_id == record_id,
            visibility.c.deleted_at.is_not(None),
        )
    )


def require_visible(session: Session, kind: str, record_id: str) -> None:
    if session.scalar(sa.select(deleted_filter(kind, record_id))):
        raise AnalysisDeletedError("记录已删除; 可在已删除记录中恢复, 原始证据仍保留。")


def set_deleted(
    sessions: sessionmaker[Session], kind: str, record_id: str, security_id: str, deleted: bool
) -> dict[str, Any]:
    canonical_uuid(record_id)
    canonical_uuid(security_id)
    table = paqs_q_analysis_runs if kind == "Q" else results
    id_column = table.c.analysis_id if kind == "Q" else table.c.narrative_result_id
    with sessions.begin() as session:
        if session.get_bind().dialect.name == "sqlite":
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
        row = session.execute(
            sa.select(table.c.security_id).where(id_column == record_id).with_for_update()
        ).one_or_none()
        if row is None:
            raise LookupError("Analysis not found")
        if row.security_id != security_id:
            raise PermissionError("Analysis belongs to another security")
        predicate = sa.and_(visibility.c.record_type == kind, visibility.c.record_id == record_id)
        existing = session.execute(sa.select(visibility).where(predicate)).mappings().one_or_none()
        when = datetime.now(UTC) if deleted else None
        if existing is None:
            session.execute(
                sa.insert(visibility).values(record_type=kind, record_id=record_id, deleted_at=when)
            )
        elif (existing["deleted_at"] is not None) != deleted:
            session.execute(sa.update(visibility).where(predicate).values(deleted_at=when))
        else:
            when = existing["deleted_at"]
    return {
        "record_type": kind,
        "record_id": record_id,
        "security_id": security_id,
        "deleted": deleted,
        "deleted_at": when.isoformat() if when else None,
    }
