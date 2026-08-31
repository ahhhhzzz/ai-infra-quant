from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_infra_quant.core.domain.common import utc_now
from ai_infra_quant.core.domain.security import Security
from ai_infra_quant.database.models.security import (
    SecurityModel,
    WatchlistItemModel,
    WatchlistModel,
)
from ai_infra_quant.database.repositories.security import security_from_model


class SQLAlchemyWatchlistRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _default_row(self) -> WatchlistModel:
        row = self._session.scalar(
            select(WatchlistModel).where(WatchlistModel.is_default.is_(True))
        )
        if row is None:
            raise RuntimeError("default watchlist is not initialized")
        return row

    def get_default(self) -> tuple[str, str, str, bool]:
        row = self._default_row()
        if row.portfolio_id is None:
            raise RuntimeError("default watchlist has no portfolio")
        return row.id, row.name, row.portfolio_id, row.is_default

    def list_active(self) -> list[tuple[Security, datetime, int]]:
        watchlist = self._default_row()
        rows = self._session.execute(
            select(SecurityModel, WatchlistItemModel.added_at, WatchlistItemModel.display_order)
            .join(WatchlistItemModel, WatchlistItemModel.security_id == SecurityModel.id)
            .where(
                WatchlistItemModel.watchlist_id == watchlist.id,
                WatchlistItemModel.removed_at.is_(None),
            )
            .order_by(WatchlistItemModel.display_order, SecurityModel.market, SecurityModel.symbol)
        ).all()
        return [
            (security_from_model(security_row), added_at, display_order)
            for security_row, added_at, display_order in rows
        ]

    def _active_item(self, watchlist_id: str, security_id: str) -> WatchlistItemModel | None:
        return self._session.scalar(
            select(WatchlistItemModel).where(
                WatchlistItemModel.watchlist_id == watchlist_id,
                WatchlistItemModel.security_id == security_id,
                WatchlistItemModel.removed_at.is_(None),
            )
        )

    def add(self, security_id: str) -> tuple[bool, Security, datetime, int]:
        security_row = self._session.get(SecurityModel, security_id)
        if security_row is None:
            raise LookupError("SECURITY_NOT_FOUND")
        if not security_row.enabled:
            raise PermissionError("SECURITY_DISABLED")
        watchlist = self._default_row()
        active = self._active_item(watchlist.id, security_id)
        if active is not None:
            return False, security_from_model(security_row), active.added_at, active.display_order
        maximum = self._session.scalar(
            select(func.max(WatchlistItemModel.display_order)).where(
                WatchlistItemModel.watchlist_id == watchlist.id,
                WatchlistItemModel.removed_at.is_(None),
            )
        )
        added_at = utc_now()
        item = WatchlistItemModel(
            id=str(uuid4()),
            watchlist_id=watchlist.id,
            security_id=security_id,
            added_at=added_at,
            removed_at=None,
            display_order=(maximum or 0) + 1,
            note=None,
        )
        self._session.add(item)
        try:
            self._session.flush()
        except IntegrityError:
            self._session.rollback()
            security_row = self._session.get(SecurityModel, security_id)
            watchlist = self._default_row()
            active = self._active_item(watchlist.id, security_id)
            if security_row is None or active is None:
                raise
            return False, security_from_model(security_row), active.added_at, active.display_order
        return True, security_from_model(security_row), added_at, item.display_order

    def remove(self, security_id: str) -> None:
        watchlist = self._default_row()
        active = self._session.scalar(
            select(WatchlistItemModel).where(
                WatchlistItemModel.watchlist_id == watchlist.id,
                WatchlistItemModel.security_id == security_id,
                WatchlistItemModel.removed_at.is_(None),
            )
        )
        if active is not None:
            active.removed_at = utc_now()
            self._session.flush()
