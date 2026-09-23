"""Additive explicit Event loader. Historical F1 manifests and defaults stay intact."""

from pathlib import Path
from typing import Any

from ai_infra_quant.application.paqs_q_artifacts import (
    FILES as F1_FILES,
)
from ai_infra_quant.application.paqs_q_artifacts import (
    PACKAGE,
    artifact_path,
    content_hash,
    load_registry,
)
from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, digest, hash_text
from ai_infra_quant.core.domain.paqs_q.results import EVENT_SCHEMA, STRUCTURE_SCHEMA, Descriptor
from ai_infra_quant.core.strategy.paqs_q.event_context import (
    CAPABILITY,
    CONTEXT_ID,
    EVENT_ID,
    VERSION,
)
from ai_infra_quant.core.strategy.paqs_q.event_plugins import ContextPlugin, ReferenceEventPlugin
from ai_infra_quant.core.strategy.paqs_q.registry import Registry

FILES = tuple(
    sorted(
        {
            *F1_FILES,
            *(
                PACKAGE + p
                for p in (
                    "core/strategy/paqs_structure.py",
                    "core/domain/paqs_q/event_reference.py",
                    "core/strategy/paqs_q/event_calendar.py",
                    "core/strategy/paqs_q/event_context.py",
                    "core/strategy/paqs_q/event_rules.py",
                    "core/strategy/paqs_q/event_plugins.py",
                    "application/paqs_q_event_artifacts.py",
                    "resources/paqs_q/b0.json",
                    "resources/paqs_q/a1.json",
                    "resources/paqs_q/event-context-1.0.0.json",
                    "resources/paqs_q/event-event-1.0.0.json",
                )
            ),
        }
    )
)
ARTIFACTS = {"context": CONTEXT_ID, "event": EVENT_ID}


def build_manifest(root: Path, name: str, *, wheel: bool = False) -> dict[str, Any]:
    if name not in ARTIFACTS:
        raise ValueError("EVENT_ARTIFACT_UNKNOWN")
    return {
        "artifact_schema_version": "paqs-q-implementation-v1",
        "entrypoint": ARTIFACTS[name],
        "files": [
            {
                "path": p,
                "encoding": "utf8-lf",
                "sha256": content_hash(artifact_path(root, p, wheel=wheel).read_bytes(), "utf8-lf"),
            }
            for p in FILES
        ],
    }


def verify(root: Path, name: str, *, wheel: bool = False) -> str:
    path = PACKAGE + f"resources/paqs_q/event-{name}-{VERSION}.json"
    encoded = (
        artifact_path(root, path, wheel=wheel)
        .read_bytes()
        .replace(b"\r\n", b"\n")
        .removesuffix(b"\n")
    )
    manifest = FrozenJSON(encoded).document()
    if not isinstance(manifest, dict) or set(manifest) != {
        "artifact_schema_version",
        "entrypoint",
        "files",
    }:
        raise ValueError("EVENT_ARTIFACT_SCHEMA_INVALID")
    expected = build_manifest(root, name, wheel=wheel)
    if manifest != expected:
        raise ValueError("EVENT_ARTIFACT_CONTENT_OR_INVENTORY_MISMATCH")
    active_package = Path(__file__).resolve().parents[1]
    for row in manifest["files"]:
        hash_text(row["sha256"])
        if (
            content_hash(
                (active_package / row["path"].removeprefix(PACKAGE)).read_bytes(), row["encoding"]
            )
            != row["sha256"]
        ):
            raise ValueError("ACTIVE_EVENT_IMPLEMENTATION_MISMATCH")
    return digest("paqs-q/implementation/v1", manifest)


def load_event_registry(
    root: Path, *, include_experimental: bool = False, wheel: bool = False
) -> Registry:
    base = load_registry(root, include_experimental=include_experimental, wheel=wheel)
    lineage = FrozenJSON.of(
        {
            "authority": "TASK-006C-Q-OWNER-ADOPTED-REFERENCE-V1",
            "base_sha": "5326ff6cfa3cae19ebb186643bc3a16bed88b518",
            "rules": "docs/PAQS_Q_EVENT_V1.md",
        }
    )
    context = ContextPlugin(
        Descriptor(
            CONTEXT_ID,
            VERSION,
            verify(root, "context", wheel=wheel),
            (CAPABILITY,),
            "REFERENCE",
            "STRUCTURE",
            STRUCTURE_SCHEMA,
            lineage,
        )
    )
    event = ReferenceEventPlugin(
        Descriptor(
            EVENT_ID,
            VERSION,
            verify(root, "event", wheel=wheel),
            ("PRICE_EVENTS_V1",),
            "REFERENCE",
            "EVENT",
            EVENT_SCHEMA,
            lineage,
            structure_schema=STRUCTURE_SCHEMA,
            required_capabilities=(CAPABILITY,),
        )
    )
    return Registry(
        (*base.structures, context),
        (event,),
        (*base.allowlist, context.descriptor, event.descriptor),
        base.default_structure,
        base.framework_code_hash,
    )
