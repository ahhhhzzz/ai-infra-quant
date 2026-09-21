"""Explicit local artifact loading/verification OUTSIDE the pure evaluation core.

root is a source tree or unpacked wheel root, chosen explicitly by the caller.
No environment lookup, package discovery, network or mutable global registry.
"""

import hashlib
from pathlib import Path, PurePosixPath
from typing import Any

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, digest, hash_text
from ai_infra_quant.core.domain.paqs_q.results import STRUCTURE_SCHEMA, Descriptor
from ai_infra_quant.core.strategy.paqs_q.plugins import LocalStructurePlugin
from ai_infra_quant.core.strategy.paqs_q.registry import Registry

PACKAGE = "src/ai_infra_quant/"
# Explicit versioned closure, including import-executed package initializers.
FILES = tuple(
    sorted(
        PACKAGE + p
        for p in (
            "__init__.py",
            "application/__init__.py",
            "application/paqs_q_artifacts.py",
            "core/__init__.py",
            "core/domain/__init__.py",
            "core/domain/common.py",
            "core/domain/enums.py",
            "core/domain/execution.py",
            "core/domain/market_data.py",
            "core/domain/money.py",
            "core/domain/paqs_e_reasoning.py",
            "core/domain/paqs_input.py",
            "core/domain/paqs_market_snapshot.py",
            "core/domain/portfolio.py",
            "core/domain/providers.py",
            "core/domain/security.py",
            "core/ports/__init__.py",
            "core/ports/broker.py",
            "core/ports/event_data.py",
            "core/ports/fundamental_data.py",
            "core/ports/market_data.py",
            "core/ports/paqs_e_reasoning.py",
            "core/strategy/__init__.py",
            "core/domain/paqs_q/__init__.py",
            "core/domain/paqs_q/canonical.py",
            "core/domain/paqs_q/inputs.py",
            "core/domain/paqs_q/results.py",
            "core/ports/paqs_q.py",
            "core/strategy/paqs_q/__init__.py",
            "core/strategy/paqs_q/calendar.py",
            "core/strategy/paqs_q/qualification.py",
            "core/strategy/paqs_q/local.py",
            "core/strategy/paqs_q/plugins.py",
            "core/strategy/paqs_q/registry.py",
        )
    )
)


def content_hash(data: bytes, encoding: str) -> str:
    if encoding == "utf8-lf":
        if data.startswith(b"\xef\xbb\xbf"):
            raise ValueError("ARTIFACT_BOM_FORBIDDEN")
        data = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    elif encoding != "binary":
        raise ValueError("ARTIFACT_ENCODING_INVALID")
    return hashlib.sha256(data).hexdigest()


def artifact_path(root: Path, logical: str, *, wheel: bool = False) -> Path:
    path = PurePosixPath(logical)
    if (
        path.is_absolute()
        or "\\" in logical
        or ":" in logical
        or ".." in path.parts
        or str(path) != logical
        or not logical.startswith(PACKAGE)
    ):
        raise ValueError("ARTIFACT_PATH_INVALID")
    relative = logical.removeprefix("src/") if wheel else logical
    target = root / relative
    current = root
    if root.is_symlink():
        raise ValueError("ARTIFACT_SYMLINK_FORBIDDEN")
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("ARTIFACT_SYMLINK_FORBIDDEN")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("ARTIFACT_PATH_ESCAPE")
    return target


def build_manifest(root: Path, arm: str, *, wheel: bool = False) -> dict[str, Any]:
    if arm not in {"b0", "a1"}:
        raise ValueError("UNKNOWN_ARTIFACT")
    return {
        "artifact_schema_version": "paqs-q-implementation-v1",
        "entrypoint": "paqs-q-structure-" + arm,
        "files": [
            {
                "path": p,
                "encoding": "utf8-lf",
                "sha256": content_hash(artifact_path(root, p, wheel=wheel).read_bytes(), "utf8-lf"),
            }
            for p in FILES
        ],
    }


def verify_manifest(root: Path, manifest: dict[str, Any], arm: str, *, wheel: bool = False) -> str:
    if set(manifest) != {"artifact_schema_version", "entrypoint", "files"}:
        raise ValueError("ARTIFACT_SCHEMA_INVALID")
    if (
        manifest["artifact_schema_version"] != "paqs-q-implementation-v1"
        or manifest["entrypoint"] != "paqs-q-structure-" + arm
    ):
        raise ValueError("ARTIFACT_ENTRYPOINT_INVALID")
    rows = manifest["files"]
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise ValueError("ARTIFACT_FILES_INVALID")
    if any(set(r) != {"path", "encoding", "sha256"} for r in rows):
        raise ValueError("ARTIFACT_FILE_SCHEMA_INVALID")
    if tuple(r["path"] for r in rows) != FILES:
        raise ValueError("ARTIFACT_INVENTORY_MISMATCH")
    for row in rows:
        hash_text(row["sha256"])
        if row["encoding"] != "utf8-lf":
            raise ValueError("ARTIFACT_ENCODING_MISMATCH")
        actual = content_hash(
            artifact_path(root, row["path"], wheel=wheel).read_bytes(), row["encoding"]
        )
        if actual != row["sha256"]:
            raise ValueError("ARTIFACT_CONTENT_MISMATCH")
    return digest("paqs-q/implementation/v1", manifest)


def load_plugin(root: Path, arm: str, *, wheel: bool = False) -> LocalStructurePlugin:
    if arm not in {"b0", "a1"}:
        raise ValueError("UNKNOWN_ARTIFACT")
    path = PACKAGE + "resources/paqs_q/" + arm + ".json"
    encoded = artifact_path(root, path, wheel=wheel).read_bytes()
    # Duplicate keys, noncanonical values and schema drift are rejected before verification.
    frozen = FrozenJSON(encoded.replace(b"\r\n", b"\n").removesuffix(b"\n"))
    manifest = frozen.document()
    code = verify_manifest(root, manifest, arm, wheel=wheel)
    # A caller cannot bind the currently imported implementation to a different old tree.
    # Absolute paths are verification locations only, never identity/hash preimages.
    active_package = Path(__file__).resolve().parents[1]
    for row in manifest["files"]:
        active_file = active_package / row["path"].removeprefix(PACKAGE)
        if content_hash(active_file.read_bytes(), row["encoding"]) != row["sha256"]:
            raise ValueError("ACTIVE_IMPLEMENTATION_MISMATCH")
    b0 = arm == "b0"
    lineage = FrozenJSON.of(
        {
            "rule": "PROPOSED_SEMANTICS:R04-CALENDAR-LOCAL-1"
            if b0
            else "PROPOSED_SEMANTICS:R05-NO-PRIOR-RAW-VETO-4SUPPORT-1",
            "source_sha": "c4e21a0204cf6cdd7bb139584b02f01792a49f13"
            if b0
            else "b10e87cbb324442d1fc744d5fa94522802f870c1",
            "reviewed_r05": "7487cf57161a834d9100f983bab9d8534a1c0488",
            "golden_origin": "tests/paqs_q/golden/r05.json",
        }
    )
    d = Descriptor(
        "paqs-q-structure-" + arm,
        "1.0.0" if b0 else "0.1.0",
        code,
        ("LOCAL_STRUCTURE_CERTIFICATE",),
        "REFERENCE" if b0 else "EXPERIMENTAL",
        "STRUCTURE",
        STRUCTURE_SCHEMA,
        lineage,
    )
    return LocalStructurePlugin(d, b0)


def load_registry(
    root: Path, *, include_experimental: bool = False, wheel: bool = False
) -> Registry:
    if type(include_experimental) is not bool:
        raise ValueError("EXPERIMENTAL_INVENTORY_FLAG_INVALID")
    plugins: tuple[LocalStructurePlugin, ...] = (load_plugin(root, "b0", wheel=wheel),)
    if include_experimental:
        plugins += (load_plugin(root, "a1", wheel=wheel),)
    return Registry(
        plugins,
        (),
        tuple(p.descriptor for p in plugins),
        ("paqs-q-structure-b0", "1.0.0"),
        plugins[0].descriptor.code_hash,
    )
