"""Synthetic credentials only. Never reads or mutates the user's OS credential set."""

from dataclasses import replace

from ai_infra_quant.application.paqs_e_models import ModelRegistry
from ai_infra_quant.core.ports.credentials import CredentialStoreUnavailable


def historical_deepseek_registry() -> ModelRegistry:
    """Historical protocol fixtures only; not current provider capability.

    Keep testing frozen native-search evidence and its parser without exposing
    the retired route in the real product catalog or contacting any provider.
    """
    registry = ModelRegistry()
    registry.models = tuple(
        replace(
            item,
            enabled=True,
            web_research_mode="responses_search",
            research_endpoint="https://api.deepseek.com/responses",
        )
        if item.model_key == "deepseek-v4-flash"
        else item
        for item in registry.models
    )
    return registry


class MemoryCredentials:
    def __init__(self, slots: frozenset[str] = frozenset()) -> None:
        self.values: dict[str, str] = {}
        self.writes: list[str] = []
        self.available = True

    def read(self, slot: str) -> str | None:
        if not self.available:
            raise CredentialStoreUnavailable()
        return self.values.get(slot)

    def save(self, slot: str, secret: str) -> None:
        if not self.available:
            raise CredentialStoreUnavailable()
        self.values[slot] = secret
        self.writes.append(slot)

    def delete(self, slot: str) -> None:
        if not self.available:
            raise CredentialStoreUnavailable()
        self.values.pop(slot, None)
        self.writes.append(slot)
