from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.application.market_data_queries import (
    MarketDataProviderFactory,
    MarketDataQueries,
)
from ai_infra_quant.application.paqs_input_queries import PaqsInputQueries
from ai_infra_quant.application.paqs_structure_queries import PaqsStructureQueries
from ai_infra_quant.application.portfolio_queries import PortfolioQueries
from ai_infra_quant.application.security_service import SecurityService
from ai_infra_quant.application.status_queries import StatusQueries
from ai_infra_quant.application.supported_security_service import SupportedSecurityService
from ai_infra_quant.application.watchlist_service import WatchlistService
from ai_infra_quant.config import Settings
from ai_infra_quant.core.domain.enums import CapabilityStatus, DataAvailabilityStatus
from ai_infra_quant.core.domain.market_data import PROVIDER_FUTU_QUOTE
from ai_infra_quant.core.domain.strategy import StrategyDefinition
from ai_infra_quant.core.strategy.registry import StrategyRegistry
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork
from ai_infra_quant.integrations.futu_quote.adapter import FutuQuoteAdapter
from ai_infra_quant.integrations.registry import Registries


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    registries: Registries
    strategy_registry: StrategyRegistry
    portfolio_queries: PortfolioQueries
    security_service: SecurityService
    watchlist_service: WatchlistService
    status_queries: StatusQueries
    market_data_queries: MarketDataQueries
    supported_security_service: SupportedSecurityService
    paqs_input_queries: PaqsInputQueries
    paqs_structure_queries: PaqsStructureQueries


def build_container(
    settings: Settings,
    engine: Engine,
    session_factory: sessionmaker[Session],
    registries: Registries,
    strategy_registry: StrategyRegistry,
) -> AppContainer:
    def uow_factory() -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory)

    def required_data_status(definition: StrategyDefinition) -> DataAvailabilityStatus:
        del definition
        descriptors = (
            registries.market_data.get(settings.market_data_provider),
            registries.fundamental_data.get(settings.fundamental_data_provider),
            registries.event_data.get(settings.event_data_provider),
        )
        if any(descriptor is None for descriptor in descriptors):
            return DataAvailabilityStatus.INVALID
        statuses = {
            status
            for descriptor in descriptors
            if descriptor is not None
            for status in (descriptor.implementation_status, descriptor.connection_status)
        }
        if statuses == {CapabilityStatus.SUPPORTED}:
            return DataAvailabilityStatus.AVAILABLE
        if CapabilityStatus.NOT_SUPPORTED in statuses:
            return DataAvailabilityStatus.NOT_SUPPORTED
        return DataAvailabilityStatus.UNAVAILABLE

    provider_name = "none"
    provider_factory: MarketDataProviderFactory | None = None
    if settings.market_data_provider == "futu":
        provider_name = PROVIDER_FUTU_QUOTE

        def create_futu_provider() -> FutuQuoteAdapter:
            return FutuQuoteAdapter(
                settings.futu_opend_host,
                settings.futu_opend_port,
            )

        provider_factory = create_futu_provider

    market_data_queries = MarketDataQueries(
        uow_factory,
        provider_name=provider_name,
        provider_factory=provider_factory,
    )
    paqs_input_queries = PaqsInputQueries(
        market_data_queries,
        provider_name=provider_name,
    )
    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        registries=registries,
        strategy_registry=strategy_registry,
        portfolio_queries=PortfolioQueries(uow_factory, strategy_registry, required_data_status),
        security_service=SecurityService(uow_factory),
        watchlist_service=WatchlistService(uow_factory),
        status_queries=StatusQueries(
            registries.brokers,
            registries.market_data,
            registries.fundamental_data,
            registries.event_data,
        ),
        market_data_queries=market_data_queries,
        supported_security_service=SupportedSecurityService(
            uow_factory,
            provider_name=provider_name,
            provider_factory=provider_factory,
        ),
        paqs_input_queries=paqs_input_queries,
        paqs_structure_queries=PaqsStructureQueries(paqs_input_queries),
    )


def get_container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


ContainerDep = Annotated[AppContainer, Depends(get_container)]
