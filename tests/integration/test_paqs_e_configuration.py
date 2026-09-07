from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event

from ai_infra_quant.application import paqs_e_runtime as runtime
from ai_infra_quant.backend.main import create_app
from ai_infra_quant.config import Settings
from ai_infra_quant.integrations.futu_quote.adapter import FutuQuoteAdapter
from ai_infra_quant.integrations.openai_reasoning.adapter import OpenAIPaqsEReasoningAdapter

PATH = "/api/v1/paqs-e/configuration"


@pytest.mark.parametrize("credential", [None, "", " \t\n", "synthetic-presence-only-007c"])
def test_configuration_is_exact_read_only_and_secret_free(
    credential: str | None,
    monkeypatch: pytest.MonkeyPatch,
    migrated_engine: Engine,
    database_url: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    if credential is not None:
        monkeypatch.setenv("OPENAI_API_KEY", credential)

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("configuration must not call a provider")

    monkeypatch.setattr(OpenAIPaqsEReasoningAdapter, "reason", forbidden)
    monkeypatch.setattr(FutuQuoteAdapter, "__init__", forbidden)
    settings = Settings(database_url=database_url, market_data_provider="none")
    with TestClient(create_app(settings, migrated_engine)) as client:
        statements: list[str] = []

        def capture(*args: Any) -> None:
            statements.append(args[2])

        event.listen(migrated_engine, "before_cursor_execute", capture)
        try:
            response = client.get(PATH)
            assert client.get(PATH).json() == response.json()
        finally:
            event.remove(migrated_engine, "before_cursor_execute", capture)
        assert statements == []
        assert response.status_code == 200
        actual = runtime.load_strategy_package()
        assert response.json() == {
            "model_provider": "openai",
            "api_key_configured": bool(credential and credential.strip()),
            "default_strategy_id": actual.strategy_id,
            "strategies": [
                {
                    "strategy_id": actual.strategy_id,
                    "display_name": actual.display_name,
                    "content_sha256": actual.content_sha256,
                }
            ],
        }
        for secret in ("synthetic-presence", "only-007c", actual.content[:80], actual.source_path):
            assert secret not in response.text + caplog.text
        assert set(client.get("/openapi.json").json()["paths"][PATH]) == {"get"}


@pytest.mark.parametrize(
    "corruption",
    [
        "missing",
        "json",
        "shape",
        "default",
        "duplicate",
        "display",
        "file",
        "traversal",
        "utf8",
        "nullpath",
    ],
)
def test_bad_registry_or_package_is_safe_non_success(
    corruption: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    migrated_engine: Engine,
    database_url: str,
) -> None:
    registry = {
        "default_strategy_id": "paqs-e-master",
        "strategies": [
            {
                "strategy_id": "paqs-e-master",
                "display_name": "Synthetic registry",
                "source_path": "strategy.md",
            }
        ],
    }
    (tmp_path / "strategy.md").write_text("# synthetic strategy", encoding="utf-8")
    if corruption == "shape":
        registry["extra"] = "invalid"
    if corruption == "default":
        registry["default_strategy_id"] = "wrong"
    entries = registry["strategies"]
    assert isinstance(entries, list)
    if corruption == "duplicate":
        entries.append(entries[0])
    if corruption == "display":
        entries.append({"strategy_id": "second", "display_name": " ", "source_path": "strategy.md"})
    if corruption == "file":
        entries.append(
            {"strategy_id": "second", "display_name": "Second", "source_path": "absent.md"}
        )
    if corruption == "traversal":
        entries[0]["source_path"] = "../outside.md"
    if corruption == "nullpath":
        entries[0]["source_path"] = "invalid\x00.md"
    if corruption == "utf8":
        (tmp_path / "strategy.md").write_bytes(b"\xff")
    if corruption != "missing":
        (tmp_path / "registry.json").write_text(
            "{" if corruption == "json" else json.dumps(registry), encoding="utf-8"
        )
    monkeypatch.setattr(runtime, "_REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(runtime, "_STRATEGY_REGISTRY", Path("registry.json"))
    with TestClient(create_app(Settings(database_url=database_url), migrated_engine)) as client:
        response = client.get(PATH)
        assert response.status_code == 503
        assert response.json()["code"] == "PAQS_E_CONFIGURATION_UNAVAILABLE"
        for forbidden in (str(tmp_path), "outside.md", "Traceback", "synthetic strategy"):
            assert forbidden not in response.text


def test_configuration_enumerates_every_real_entry_and_is_restart_scoped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    migrated_engine: Engine,
    database_url: str,
) -> None:
    registry = {
        "default_strategy_id": "paqs-e-master",
        "strategies": [
            {"strategy_id": key, "display_name": key, "source_path": "strategy.md"}
            for key in ("paqs-e-master", "fixture-alternative")
        ],
    }
    (tmp_path / "strategy.md").write_text("# synthetic registry file", encoding="utf-8")
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(runtime, "_REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(runtime, "_STRATEGY_REGISTRY", Path("registry.json"))
    with TestClient(create_app(Settings(database_url=database_url), migrated_engine)) as client:
        before = client.get(PATH).json()
        assert [item["strategy_id"] for item in before["strategies"]] == [
            "paqs-e-master",
            "fixture-alternative",
        ]
        assert all(
            item["content_sha256"]
            == runtime.load_strategy_package(item["strategy_id"]).content_sha256
            for item in before["strategies"]
        )
        path.write_text("corrupt after startup", encoding="utf-8")
        assert client.get(PATH).json() == before
