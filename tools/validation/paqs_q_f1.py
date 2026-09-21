"""Offline F1 artifact build, canonical vector receipt and baseline protection.

Run from the repository root with PYTHONPATH=src plus the repository root.
No database, provider or external environment provisioning.
"""

import argparse
import hashlib
import json
import platform
import re
import subprocess
from importlib.metadata import version
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from ai_infra_quant.application.paqs_q_artifacts import build_manifest, load_registry
from ai_infra_quant.core.domain.paqs_q.canonical import canonical, digest
from tests.paqs_q.support import decode, read_golden, synthetic

BASE = "857823a0dc39b4c10a1986c575bcbcd9dda11c85"
CONTRACT = "prompts/tasks/TASK-006C-Q-F1_VERSIONED_QUANT_EVENT_FRAMEWORK_FOUNDATION.md"
CONTRACT_BLOB = "c2c5448c1eb72fd0ece1572c31ba30246a761b51"
CURRENT_DOCS = {
    "docs/" + p
    for p in (
        "ROADMAP.md",
        "MASTER_SPEC.md",
        "ARCHITECTURE.md",
        "STRATEGY_SPEC.md",
        "REQUIREMENTS_MATRIX.md",
        "engineering/PAQS_ENGINEERING_GUIDE.md",
    )
}


def git(root: Path, *args: str) -> str:
    return (
        subprocess.check_output(["git", "-c", f"safe.directory={root.as_posix()}", *args], cwd=root)
        .decode("utf-8")
        .strip()
    )


def vectors(root: Path) -> dict[str, Any]:
    registry = load_registry(root, include_experimental=True)
    inputs = [(v["name"], decode(v["input"])) for v in read_golden()["vectors"]]
    inputs.extend(
        (name, synthetic(chain=chain))
        for name, chain in (("synthetic-flat", False), ("synthetic-chain", True))
    )
    rows = []
    for name, data in inputs:
        for arm, v in (("b0", "1.0.0"), ("a1", "0.1.0")):
            result = registry.structure(
                data, "paqs-q-structure-" + arm, v, allow_experimental=arm == "a1"
            )
            doc = result.document()
            rows.append(
                {
                    "name": name,
                    "arm": arm,
                    "input_hash": data.input_hash,
                    "result_hash": result.canonical_result_hash,
                    "bytes_sha256": hashlib.sha256(result.canonical_bytes).hexdigest(),
                    "record_ids": [r["record_id"] for r in doc["records"]],
                    "status": result.status,
                }
            )
    return {
        "schema": "paqs-q-f1-vector-receipt-v1",
        "platform": platform.system(),
        "python": platform.python_version(),
        "tzdata": version("tzdata"),
        "vector_digest": digest("paqs-q/validation-vectors/v1", rows),
        "vectors": rows,
        "code_hashes": {
            p.descriptor.strategy_id: p.descriptor.code_hash for p in registry.structures
        },
    }


def protection(root: Path) -> dict[str, Any]:
    baseline = {
        line.split("\t")[1]: line.split("\t")[0].split()
        for line in git(root, "ls-tree", "-r", BASE).splitlines()
    }
    index = {
        line.split("\t")[1]: line.split("\t")[0].split()
        for line in git(root, "ls-files", "-s").splitlines()
    }
    protected = 0
    for path, (mode, kind, blob) in baseline.items():
        if path in CURRENT_DOCS:
            continue
        if kind != "blob" or index[path] != [mode, blob, "0"]:
            raise ValueError("PROTECTED_INDEX_CHANGED:" + path)
        if (root / path).is_symlink() or git(root, "hash-object", "--path=" + path, path) != blob:
            raise ValueError("PROTECTED_CONTENT_CHANGED:" + path)
        protected += 1
    assert git(root, "rev-parse", BASE + ":" + CONTRACT) == CONTRACT_BLOB
    git(root, "diff", "--check", BASE)
    git(root, "diff", "--cached", "--check")
    changed = set(git(root, "diff", "--name-only", BASE).splitlines())
    changed.update(git(root, "ls-files", "--others", "--exclude-standard").splitlines())
    links = 0
    for path in sorted(changed):
        if not path.endswith(".md"):
            continue
        text = (root / path).read_text(encoding="utf-8")
        text = re.sub(r"^```.*?^```\s*$", "", text, flags=re.M | re.S)
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target:
                continue
            file, _, anchor = unquote(target).partition("#")
            dest = ((root / path).parent / file).resolve() if file else root / path
            if not dest.is_file():
                raise ValueError("BROKEN_LINK:" + path + ":" + target)
            if anchor and dest.suffix == ".md":
                headings = re.findall(
                    r"^#{1,6}\s+(.+?)\s*#*$", dest.read_text(encoding="utf-8"), re.M
                )
                slugs = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
                if anchor not in slugs:
                    raise ValueError("BROKEN_ANCHOR:" + path + ":" + target)
            links += 1
    return {
        "status": "PASS",
        "baseline": BASE,
        "protected_objects": protected,
        "baseline_objects": len(baseline),
        "contract_blob": CONTRACT_BLOB,
        "relative_links": links,
        "changed_files": sorted(changed),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--vectors", type=Path)
    parser.add_argument("--protect", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.write_artifacts:
        for arm in ("b0", "a1"):
            path = root / f"src/ai_infra_quant/resources/paqs_q/{arm}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(canonical(build_manifest(root, arm)) + b"\n")
        print("Built both explicit artifact manifests")
    for dest, value in (
        (args.vectors, vectors(root) if args.vectors else None),
        (args.protect, protection(root) if args.protect else None),
    ):
        if dest and value is not None:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            print(
                json.dumps(
                    {k: v for k, v in value.items() if k not in {"vectors", "changed_files"}}
                )
            )


if __name__ == "__main__":
    main()
