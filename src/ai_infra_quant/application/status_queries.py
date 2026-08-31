from __future__ import annotations

from typing import Protocol

from ai_infra_quant.core.domain.providers import AdapterDescriptor


class DescriptorLookup(Protocol):
    def get(self, key: str) -> AdapterDescriptor | None: ...

    def list(self) -> tuple[AdapterDescriptor, ...]: ...


class StatusQueries:
    def __init__(
        self,
        brokers: DescriptorLookup,
        market_data: DescriptorLookup,
        fundamental_data: DescriptorLookup,
        event_data: DescriptorLookup,
    ) -> None:
        self._brokers = brokers
        self._market_data = market_data
        self._fundamental_data = fundamental_data
        self._event_data = event_data

    def brokers(self) -> tuple[AdapterDescriptor, ...]:
        return self._brokers.list()

    def broker(self, name: str) -> AdapterDescriptor:
        descriptor = self._brokers.get(name)
        if descriptor is None:
            raise LookupError("BROKER_NOT_FOUND")
        return descriptor

    def market_data_providers(self) -> tuple[AdapterDescriptor, ...]:
        return self._market_data.list()

    def fundamental_data_providers(self) -> tuple[AdapterDescriptor, ...]:
        return self._fundamental_data.list()

    def event_data_providers(self) -> tuple[AdapterDescriptor, ...]:
        return self._event_data.list()
