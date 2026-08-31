from __future__ import annotations

from dataclasses import dataclass

from ai_infra_quant.core.domain.enums import CapabilityStatus


@dataclass(frozen=True, slots=True)
class StrategyDescriptor:
    implementation_key: str
    name: str
    version: str
    implementation_status: CapabilityStatus


class StrategyRegistry:
    def __init__(self) -> None:
        self._descriptors: dict[str, StrategyDescriptor] = {}

    def register(self, key: str, descriptor: StrategyDescriptor) -> None:
        normalized = key.strip().lower()
        if normalized != descriptor.implementation_key.strip().lower():
            raise ValueError("strategy key must match descriptor implementation_key")
        if normalized in self._descriptors:
            raise ValueError(f"strategy descriptor already registered: {normalized}")
        self._descriptors[normalized] = descriptor

    def get(self, key: str) -> StrategyDescriptor | None:
        return self._descriptors.get(key.strip().lower())

    def list(self) -> tuple[StrategyDescriptor, ...]:
        return tuple(self._descriptors[key] for key in sorted(self._descriptors))
