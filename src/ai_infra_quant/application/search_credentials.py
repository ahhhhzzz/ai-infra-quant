"""Independent search credential access; no network or plaintext persistence."""

from __future__ import annotations

from ai_infra_quant.core.ports.credentials import CredentialStore, CredentialStoreUnavailable


def _valid_secret(value: str | None) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 1024
        and all(33 <= ord(char) <= 126 for char in value)
    )


class SearchCredentials:
    """Use the isolated Tavily OS slot, then an optional read-only environment value."""

    def __init__(self, store: CredentialStore, *, fallback: str | None = None) -> None:
        self._store = store
        self._fallback = fallback if _valid_secret(fallback) else None

    def secret(self) -> str | None:
        try:
            stored = self._store.read("tavily")
        except CredentialStoreUnavailable:
            stored = None
        return stored if _valid_secret(stored) else self._fallback

    def status(self) -> dict[str, bool]:
        # Source, backend details and the secret itself never enter configuration readback.
        return {"credential_configured": self.secret() is not None}

    def save(self, secret: str) -> dict[str, bool]:
        if not _valid_secret(secret):
            raise ValueError("Credential must contain 1-1024 non-whitespace ASCII characters")
        self._store.save("tavily", secret)
        return self.status()

    def delete(self) -> dict[str, bool]:
        # Deletion only affects the secure slot; the caller-owned environment is read-only.
        self._store.delete("tavily")
        return self.status()
