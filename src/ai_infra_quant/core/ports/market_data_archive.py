"""Local immutable archive persistence; reads never require a market provider."""

from typing import Any, Protocol

from ai_infra_quant.core.domain.market_data_archive import ArchivedBar


class ArchiveNotFound(LookupError):
    pass


class ArchivePersistenceError(RuntimeError):
    pass


class MarketDataArchive(Protocol):
    def record(self, capture: dict[str, Any], bars: tuple[ArchivedBar, ...]) -> None: ...

    def detail(self, capture_id: str) -> dict[str, Any]: ...

    def list_captures(self, security_id: str, limit: int, cursor: str | None) -> dict[str, Any]: ...

    def read_bars(
        self, capture_id: str, timeframe: str, limit: int, cursor: str | None
    ) -> dict[str, Any]: ...
