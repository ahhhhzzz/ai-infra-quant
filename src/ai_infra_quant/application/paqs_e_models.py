"""Repository-owned model catalog and model-centric credential access; no network."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib.resources import files
from urllib.parse import urlsplit

from ai_infra_quant.core.ports.credentials import CredentialStore, CredentialStoreUnavailable


@dataclass(frozen=True, slots=True)
class ModelDescriptor:
    model_key: str
    display_name: str
    provider_id: str
    model_id: str
    credential_slot: str
    credential_label: str
    research_endpoint: str | None
    endpoint: str
    api_surface: str
    structured_output_mode: str
    web_research_mode: str
    enabled: bool

    @property
    def web_research_supported(self) -> bool:
        return self.web_research_mode != "disabled"


class ModelRegistry:
    def __init__(self) -> None:
        try:
            self._load()
        except (OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError):
            raise ValueError("Model registry is unavailable or invalid") from None

    def _load(self) -> None:
        source = files("ai_infra_quant").joinpath("resources/paqs_e/model_registry.json")
        data = json.loads(source.read_text(encoding="utf-8"))
        if set(data) != {"default_model_key", "models"}:
            raise ValueError("Invalid model registry")
        self.models = tuple(ModelDescriptor(**row) for row in data["models"])
        self.default_model_key: str = data["default_model_key"]
        keys: set[str] = set()
        identities: set[tuple[str, str]] = set()
        for item in self.models:
            url = urlsplit(item.endpoint)
            research_url = urlsplit(item.research_endpoint) if item.research_endpoint else None
            if (
                item.model_key in keys
                or (item.provider_id, item.model_id) in identities
                or any(
                    not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,79}", value)
                    for value in (
                        item.model_key,
                        item.provider_id,
                        item.model_id,
                        item.credential_slot,
                    )
                )
                or not item.display_name.strip()
                or not item.credential_label.strip()
                or url.scheme != "https"
                or not url.hostname
                or url.username
                or url.password
                or url.query
                or url.fragment
                or item.api_surface not in {"responses", "chat"}
                or item.structured_output_mode not in {"json_schema", "json_object"}
                or item.web_research_mode not in {"responses_search", "disabled"}
                or type(item.enabled) is not bool
                or (item.web_research_supported != bool(item.research_endpoint))
                or (
                    research_url is not None
                    and (
                        research_url.scheme != "https"
                        or research_url.hostname != url.hostname
                        or research_url.username
                        or research_url.password
                        or research_url.query
                        or research_url.fragment
                    )
                )
            ):
                raise ValueError("Invalid model registry")
            keys.add(item.model_key)
            identities.add((item.provider_id, item.model_id))
        self.resolve(self.default_model_key)

    def resolve(self, model_key: str) -> ModelDescriptor:
        for item in self.models:
            if item.model_key == model_key and item.enabled:
                return item
        raise ValueError("Model is not registered or enabled")


@dataclass(frozen=True, slots=True)
class CredentialStatus:
    credential_configured: bool
    credential_source: str
    secure_storage_available: bool


class ModelCredentials:
    def __init__(
        self, registry: ModelRegistry, store: CredentialStore, *, openai_fallback: str | None = None
    ) -> None:
        self.registry = registry
        self._store = store
        self._openai_fallback = openai_fallback

    def secret(self, model_key: str) -> str | None:
        model = self.registry.resolve(model_key)
        try:
            stored = self._store.read(model.credential_slot)
        except CredentialStoreUnavailable:
            stored = None
        if stored:
            return stored
        return self._openai_fallback if model.credential_slot == "openai" else None

    def status(self, model_key: str) -> CredentialStatus:
        model = self.registry.resolve(model_key)
        available = True
        try:
            stored = self._store.read(model.credential_slot)
        except CredentialStoreUnavailable:
            stored, available = None, False
        if stored:
            return CredentialStatus(True, "secure_store", available)
        if model.credential_slot == "openai" and self._openai_fallback:
            return CredentialStatus(True, "server_environment_read_only", available)
        return CredentialStatus(False, "missing", available)

    def save(self, model_key: str, secret: str) -> CredentialStatus:
        model = self.registry.resolve(model_key)
        if not 1 <= len(secret) <= 1024 or any(
            ord(char) < 33 or ord(char) > 126 for char in secret
        ):
            raise ValueError("Credential must contain 1-1024 non-whitespace ASCII characters")
        self._store.save(model.credential_slot, secret)
        return self.status(model_key)

    def delete(self, model_key: str) -> CredentialStatus:
        model = self.registry.resolve(model_key)
        self._store.delete(model.credential_slot)
        return self.status(model_key)

    def projection(self) -> list[dict[str, object]]:
        return [
            {
                "model_key": item.model_key,
                "display_name": item.display_name,
                "credential_label": item.credential_label,
                "credential_configured": self.status(item.model_key).credential_configured,
                "web_research_supported": item.web_research_supported,
            }
            for item in self.registry.models
            if item.enabled
        ]
