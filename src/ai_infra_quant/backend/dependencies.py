from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.application.market_data_queries import (
    MarketDataProviderFactory,
    MarketDataQueries,
)
from ai_infra_quant.application.paqs_e_analysis import PaqsEAnalysisService
from ai_infra_quant.application.paqs_e_configuration import PaqsEConfiguration, read_configuration
from ai_infra_quant.application.paqs_e_runtime import PaqsEReasoningRuntime, RuntimePackageError
from ai_infra_quant.application.paqs_input_queries import PaqsInputQueries
from ai_infra_quant.application.paqs_market_snapshot_queries import PaqsMarketSnapshotQueries
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
from ai_infra_quant.core.ports.paqs_e_ledger import PaqsELedger
from ai_infra_quant.core.strategy.registry import StrategyRegistry
from ai_infra_quant.database.repositories.paqs_e_ledger import SQLAlchemyPaqsELedger
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork
from ai_infra_quant.integrations.futu_quote.adapter import FutuQuoteAdapter
from ai_infra_quant.integrations.openai_reasoning.adapter import OpenAIPaqsEReasoningAdapter
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
    paqs_market_snapshot_queries: PaqsMarketSnapshotQueries
    paqs_structure_queries: PaqsStructureQueries
    paqs_e_ledger: PaqsELedger
    paqs_e_analysis_service: PaqsEAnalysisService
    paqs_e_configuration: PaqsEConfiguration | None


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
    snapshot_queries = PaqsMarketSnapshotQueries(paqs_input_queries, market_data_queries)
    paqs_e_ledger = SQLAlchemyPaqsELedger(session_factory)
    # Match the adapter's effective credential source; only presence crosses this boundary.
    effective_key = (
        settings.openai_api_key.get_secret_value()
        if settings.openai_api_key is not None
        else os.environ.get("OPENAI_API_KEY", "")
    )
    try:
        configuration = read_configuration(api_key_configured=bool(effective_key.strip()))
    except RuntimePackageError:
        configuration = None
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
        paqs_market_snapshot_queries=snapshot_queries,
        paqs_structure_queries=PaqsStructureQueries(paqs_input_queries),
        paqs_e_ledger=paqs_e_ledger,
        paqs_e_configuration=configuration,
        paqs_e_analysis_service=PaqsEAnalysisService(
            snapshot_queries,
            PaqsEReasoningRuntime(OpenAIPaqsEReasoningAdapter(api_key=settings.openai_api_key)),
            paqs_e_ledger,
        ),
    )


def get_container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


ContainerDep = Annotated[AppContainer, Depends(get_container)]
