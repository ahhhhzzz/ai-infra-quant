from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ai_infra_quant.application.unit_of_work import UnitOfWorkFactory
from ai_infra_quant.core.domain.enums import (
    CapabilityStatus,
    DataAvailabilityStatus,
    SnapshotQualityStatus,
)
from ai_infra_quant.core.domain.portfolio import Portfolio, PortfolioSnapshot
from ai_infra_quant.core.domain.strategy import StrategyDefinition
from ai_infra_quant.core.strategy.registry import StrategyRegistry


@dataclass(frozen=True, slots=True)
class PortfolioView:
    portfolio: Portfolio
    snapshot: PortfolioSnapshot
    capabilities: dict[str, CapabilityStatus]


@dataclass(frozen=True, slots=True)
class PerformanceView:
    portfolio_id: str
    range: str
    frequency: str
    valuation_at: datetime
    nav: Decimal
    twr: Decimal
    daily_status: DataAvailabilityStatus
    weekly_status: DataAvailabilityStatus
    monthly_status: DataAvailabilityStatus
    since_inception_return: Decimal
    maximum_drawdown: Decimal
    benchmark_status: DataAvailabilityStatus
    quality_status: SnapshotQualityStatus


@dataclass(frozen=True, slots=True)
class StrategyStatusView:
    id: str
    name: str
    version: str
    implementation_status: CapabilityStatus
    research_status: str
    enabled: bool
    required_data_status: DataAvailabilityStatus


class PortfolioQueries:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        strategy_registry: StrategyRegistry,
        required_data_status: Callable[[StrategyDefinition], DataAvailabilityStatus],
    ) -> None:
        self._uow_factory = uow_factory
        self._strategy_registry = strategy_registry
        self._required_data_status = required_data_status

    def portfolio(self) -> PortfolioView:
        with self._uow_factory() as uow:
            result = uow.portfolios.get_default()
        if result is None:
            raise LookupError("PORTFOLIO_NOT_FOUND")
        portfolio, snapshot = result
        return PortfolioView(
            portfolio=portfolio,
            snapshot=snapshot,
            capabilities={
                "market_data": CapabilityStatus.UNAVAILABLE,
                "fx_data": CapabilityStatus.UNAVAILABLE,
                "fundamental_data": CapabilityStatus.UNAVAILABLE,
                "event_data": CapabilityStatus.UNAVAILABLE,
            },
        )

    def positions(self) -> list[dict[str, str]]:
        return []

    def performance(self, range_: str, frequency: str) -> PerformanceView:
        view = self.portfolio()
        zero = Decimal("0.000000000000")
        return PerformanceView(
            portfolio_id=view.portfolio.id,
            range=range_,
            frequency=frequency,
            valuation_at=view.snapshot.valuation_at,
            nav=view.snapshot.nav,
            twr=zero,
            daily_status=DataAvailabilityStatus.UNAVAILABLE,
            weekly_status=DataAvailabilityStatus.UNAVAILABLE,
            monthly_status=DataAvailabilityStatus.UNAVAILABLE,
            since_inception_return=zero,
            maximum_drawdown=zero,
            benchmark_status=DataAvailabilityStatus.UNAVAILABLE,
            quality_status=view.snapshot.quality_status,
        )

    def strategies(self) -> list[StrategyStatusView]:
        with self._uow_factory() as uow:
            definitions = list(uow.portfolios.list_strategies())
        result: list[StrategyStatusView] = []
        for definition in definitions:
            descriptor = self._strategy_registry.get(definition.implementation_key)
            implementation_status = (
                CapabilityStatus.UNKNOWN if descriptor is None else descriptor.implementation_status
            )
            result.append(
                StrategyStatusView(
                    id=definition.id,
                    name=definition.name,
                    version=definition.version,
                    implementation_status=implementation_status,
                    research_status=definition.research_status,
                    enabled=definition.enabled,
                    required_data_status=self._required_data_status(definition),
                )
            )
        return result
