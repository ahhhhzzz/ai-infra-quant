from __future__ import annotations

from typing import TYPE_CHECKING

from ai_infra_quant.core.domain.enums import BrokerEnvironment, CapabilityStatus
from ai_infra_quant.core.domain.providers import AdapterDescriptor
from ai_infra_quant.core.strategy.registry import StrategyDescriptor, StrategyRegistry

if TYPE_CHECKING:
    from ai_infra_quant.integrations.registry import Registries


def build_phase_one_registries() -> Registries:
    from ai_infra_quant.integrations.registry import Registries

    registries = Registries()
    registries.brokers.register(
        AdapterDescriptor(
            name="paper",
            implementation_status=CapabilityStatus.NOT_IMPLEMENTED,
            connection_status=CapabilityStatus.UNAVAILABLE,
            environment=BrokerEnvironment.PAPER,
            message="PaperBroker begins in Phase 2",
        )
    )
    registries.brokers.register(
        AdapterDescriptor(
            name="futu",
            implementation_status=CapabilityStatus.NOT_IMPLEMENTED,
            connection_status=CapabilityStatus.UNAVAILABLE,
            environment=BrokerEnvironment.READ_ONLY,
            message="Futu integration begins in Phase 5",
        )
    )
    registries.brokers.register(
        AdapterDescriptor(
            name="eastmoney",
            implementation_status=CapabilityStatus.NOT_IMPLEMENTED,
            connection_status=CapabilityStatus.UNAVAILABLE,
            environment=BrokerEnvironment.READ_ONLY,
            message="No approved legitimate interface; Phase 8 decision required",
        )
    )
    registries.market_data.register(
        AdapterDescriptor(
            name="futu",
            implementation_status=CapabilityStatus.SUPPORTED,
            connection_status=CapabilityStatus.UNKNOWN,
            environment=BrokerEnvironment.READ_ONLY,
            message="Request-scoped Futu OpenD quote-only market data",
        )
    )
    for registry in (registries.market_data, registries.fundamental_data, registries.event_data):
        registry.register(
            AdapterDescriptor(
                name="none",
                implementation_status=CapabilityStatus.UNAVAILABLE,
                connection_status=CapabilityStatus.UNAVAILABLE,
                environment=None,
                message="No provider is configured",
            )
        )
    return registries


def build_phase_one_strategy_registry() -> StrategyRegistry:
    registry = StrategyRegistry()
    registry.register(
        "ai_infra",
        StrategyDescriptor(
            implementation_key="ai_infra",
            name="AIInfraStrategy",
            version="1.0.0",
            implementation_status=CapabilityStatus.NOT_IMPLEMENTED,
        ),
    )
    return registry
