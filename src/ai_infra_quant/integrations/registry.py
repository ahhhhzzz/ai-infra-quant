from __future__ import annotations

from ai_infra_quant.core.domain.providers import AdapterDescriptor


class DescriptorRegistry[DescriptorT: AdapterDescriptor]:
    """Stores inert metadata and never imports, constructs, or connects an adapter."""

    def __init__(self) -> None:
        self._descriptors: dict[str, DescriptorT] = {}

    def register(self, descriptor: DescriptorT) -> None:
        key = descriptor.name.strip().lower()
        if not key:
            raise ValueError("descriptor name cannot be empty")
        if key in self._descriptors:
            raise ValueError(f"descriptor already registered: {key}")
        self._descriptors[key] = descriptor

    def get(self, key: str) -> DescriptorT | None:
        return self._descriptors.get(key.strip().lower())

    def list(self) -> tuple[DescriptorT, ...]:
        return tuple(self._descriptors[key] for key in sorted(self._descriptors))


class BrokerRegistry(DescriptorRegistry[AdapterDescriptor]):
    pass


class MarketDataRegistry(DescriptorRegistry[AdapterDescriptor]):
    pass


class FundamentalDataRegistry(DescriptorRegistry[AdapterDescriptor]):
    pass


class EventDataRegistry(DescriptorRegistry[AdapterDescriptor]):
    pass


class Registries:
    def __init__(self) -> None:
        self.brokers = BrokerRegistry()
        self.market_data = MarketDataRegistry()
        self.fundamental_data = FundamentalDataRegistry()
        self.event_data = EventDataRegistry()
