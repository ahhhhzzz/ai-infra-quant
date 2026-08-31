from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ai_infra_quant.application.unit_of_work import UnitOfWorkFactory
from ai_infra_quant.core.domain.security import Security


@dataclass(frozen=True, slots=True)
class WatchlistItemView:
    security: Security
    added_at: datetime
    display_order: int


@dataclass(frozen=True, slots=True)
class WatchlistView:
    id: str
    name: str
    portfolio_id: str
    is_default: bool
    items: tuple[WatchlistItemView, ...]


@dataclass(frozen=True, slots=True)
class WatchlistAddResult:
    created: bool
    item: WatchlistItemView


class WatchlistService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def get(self) -> WatchlistView:
        with self._uow_factory() as uow:
            watchlist_id, name, portfolio_id, is_default = uow.watchlists.get_default()
            items = tuple(
                WatchlistItemView(security, added_at, display_order)
                for security, added_at, display_order in uow.watchlists.list_active()
            )
        return WatchlistView(watchlist_id, name, portfolio_id, is_default, items)

    def add(self, security_id: str) -> WatchlistAddResult:
        with self._uow_factory() as uow:
            created, security, added_at, display_order = uow.watchlists.add(security_id)
            uow.commit()
        return WatchlistAddResult(
            created=created,
            item=WatchlistItemView(security, added_at, display_order),
        )

    def remove(self, security_id: str) -> None:
        with self._uow_factory() as uow:
            uow.watchlists.remove(security_id)
            uow.commit()
