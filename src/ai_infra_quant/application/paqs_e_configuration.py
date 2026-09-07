"""Startup-only, non-secret projection of the accepted strategy runtime registry."""

from __future__ import annotations

import json
from dataclasses import dataclass

from ai_infra_quant.application import paqs_e_runtime as runtime


@dataclass(frozen=True, slots=True)
class StrategyOption:
    strategy_id: str
    display_name: str
    content_sha256: str


@dataclass(frozen=True, slots=True)
class PaqsEConfiguration:
    api_key_configured: bool
    default_strategy_id: str
    strategies: tuple[StrategyOption, ...]


def read_configuration(*, api_key_configured: bool) -> PaqsEConfiguration:
    # Reuse the accepted loader for validation of the complete registry and every file.
    # Do not add a second registry, fallback entry, or a provider probe.
    try:
        default = runtime.load_strategy_package()
        registry = json.loads(
            (runtime._REPOSITORY_ROOT / runtime._STRATEGY_REGISTRY).read_text(encoding="utf-8")
        )
        packages = tuple(
            runtime.load_strategy_package(entry["strategy_id"]) for entry in registry["strategies"]
        )
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        raise runtime.RuntimePackageError("PAQS-E configuration is unavailable") from exc
    return PaqsEConfiguration(
        api_key_configured=api_key_configured,
        default_strategy_id=default.strategy_id,
        strategies=tuple(
            StrategyOption(item.strategy_id, item.display_name, item.content_sha256)
            for item in packages
        ),
    )
