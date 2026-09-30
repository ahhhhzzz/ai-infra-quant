"""Synthetic search credentials only; these tests never access the real OS store."""

from __future__ import annotations

import json

import pytest

from ai_infra_quant.application.search_credentials import SearchCredentials
from ai_infra_quant.core.ports.credentials import CredentialStoreUnavailable


class MemoryStore:
    def __init__(self) -> None:
        self.values: dict[str, str] = {"deepseek": "synthetic-model-key"}
        self.reads: list[str] = []
        self.writes: list[str] = []

    def read(self, slot: str) -> str | None:
        self.reads.append(slot)
        return self.values.get(slot)

    def save(self, slot: str, secret: str) -> None:
        self.writes.append(slot)
        self.values[slot] = secret

    def delete(self, slot: str) -> None:
        self.writes.append(slot)
        self.values.pop(slot, None)


class UnavailableStore:
    def read(self, slot: str) -> str | None:
        raise CredentialStoreUnavailable()

    def save(self, slot: str, secret: str) -> None:
        raise CredentialStoreUnavailable()

    def delete(self, slot: str) -> None:
        raise CredentialStoreUnavailable()


def test_independent_slot_safe_readback_and_read_only_environment_fallback() -> None:
    store = MemoryStore()
    credentials = SearchCredentials(store, fallback="synthetic-search-environment")
    assert credentials.secret() == "synthetic-search-environment"
    assert credentials.status() == {"credential_configured": True}
    assert store.writes == []
    saved = credentials.save("synthetic-search-stored")
    assert saved == {"credential_configured": True}
    assert credentials.secret() == "synthetic-search-stored"
    assert credentials.delete() == {"credential_configured": True}
    assert credentials.secret() == "synthetic-search-environment"
    assert set(store.reads) == {"tavily"}
    assert store.writes == ["tavily", "tavily"]
    assert store.values == {"deepseek": "synthetic-model-key"}
    assert "synthetic" not in json.dumps(saved) + repr(credentials)


def test_missing_credential_and_deletion_never_expose_storage_details() -> None:
    store = MemoryStore()
    credentials = SearchCredentials(store)
    assert credentials.secret() is None
    assert credentials.status() == {"credential_configured": False}
    credentials.save("synthetic-search-stored")
    assert credentials.delete() == {"credential_configured": False}
    assert credentials.secret() is None


@pytest.mark.parametrize("fallback", [None, "synthetic-search-environment"])
def test_unavailable_secure_store_has_no_writable_fallback(fallback: str | None) -> None:
    credentials = SearchCredentials(UnavailableStore(), fallback=fallback)
    assert credentials.secret() == fallback
    assert credentials.status() == {"credential_configured": fallback is not None}
    with pytest.raises(CredentialStoreUnavailable):
        credentials.save("synthetic-search-stored")
    with pytest.raises(CredentialStoreUnavailable):
        credentials.delete()
    assert credentials.secret() == fallback


@pytest.mark.parametrize("secret", ["", " ", "a b", "a\n", "a\t", "\x7f", "密钥", "x" * 1025])
def test_invalid_credentials_are_rejected_without_writes_or_secret_echo(secret: str) -> None:
    store = MemoryStore()
    credentials = SearchCredentials(store)
    with pytest.raises(ValueError) as error:
        credentials.save(secret)
    assert str(error.value) == "Credential must contain 1-1024 non-whitespace ASCII characters"
    assert store.writes == []
    assert credentials.status() == {"credential_configured": False}
    assert SearchCredentials(store, fallback=secret).status() == {"credential_configured": False}


@pytest.mark.parametrize("secret", ["!", "x" * 1024])
def test_ascii_credential_length_boundaries(secret: str) -> None:
    credentials = SearchCredentials(MemoryStore())
    assert credentials.save(secret) == {"credential_configured": True}
    assert credentials.secret() == secret
