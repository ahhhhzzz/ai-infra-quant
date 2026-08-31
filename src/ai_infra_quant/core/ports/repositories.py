from __future__ import annotations

from datetime import datetime
from types import TracebackType
from typing import Protocol, Self

from ai_infra_quant.core.domain.portfolio import Portfolio, PortfolioSnapshot
from ai_infra_quant.core.domain.security import Security
from ai_infra_quant.core.domain.strategy import StrategyDefinition


class SecurityRepository(Protocol):
    def get(self, security_id: str) -> Security | None: ...

    def get_by_identity(self, market: str, symbol: str) -> Security | None: ...

    def add_user_supplied(
        self,
        *,
        market: str,
        symbol: str,
        currency: str,
        instrument_type: str,
        display_name: str | None,
    ) -> Security: ...


class PortfolioRepository(Protocol):
    def get_default(self) -> tuple[Portfolio, PortfolioSnapshot] | None: ...

    def list_strategies(self) -> list[StrategyDefinition]: ...


class WatchlistRepository(Protocol):
    def get_default(self) -> tuple[str, str, str, bool]: ...

    def list_active(self) -> list[tuple[Security, datetime, int]]: ...

    def add(self, security_id: str) -> tuple[bool, Security, datetime, int]: ...

    def remove(self, security_id: str) -> None: ...


class UnitOfWork(Protocol):
    @property
    def securities(self) -> SecurityRepository: ...

    @property
    def portfolios(self) -> PortfolioRepository: ...

    @property
    def watchlists(self) -> WatchlistRepository: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
