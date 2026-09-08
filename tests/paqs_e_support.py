"""Synthetic credentials only. Never reads or mutates the user's OS credential set."""

from ai_infra_quant.core.ports.credentials import CredentialStoreUnavailable


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
