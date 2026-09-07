"""Secrets cross this port only between local storage and the selected transport."""

from typing import Protocol


class CredentialStoreUnavailable(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Operating-system credential storage is unavailable")


class CredentialStore(Protocol):
    def read(self, slot: str) -> str | None: ...

    def save(self, slot: str, secret: str) -> None: ...

    def delete(self, slot: str) -> None: ...
