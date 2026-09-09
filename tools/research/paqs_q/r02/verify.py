"""Additive R02 scope verifier; every development-base entry is protected."""

import argparse
import re
from pathlib import Path
from typing import Any

from ..verify import git
from .phase_a import write_new

BASE = "d50d73eea28005bc96e5ed0721b6a8e385ecedf5"
START = "47e7020609e5655927c6aac11a3b1f35b03c96aa"
FREEZE = "251f2a2ea9609ddd875c5aff03f5758c81914c84"
CONTRACT = "prompts/tasks/TASK-006B-Q_R02_STRUCTURE_STABILITY_RESEARCH.md"
PREFIXES = (
    "tools/research/paqs_q/r02/",
    "tests/research/paqs_q/r02/",
    "docs/evidence/TASK_006B_Q/research-02/",
)
SPEC = "docs/research/PAQS_Q_STRUCTURE_R02_CANDIDATES.md"


def verify(root: Path) -> dict[str, Any]:
    root = root.resolve()
    protected = {
        line.split("\t")[1]: line.split("\t")[0]
        for line in git(root, "ls-tree", "-r", BASE).splitlines()
    }
    actual = {}
    for line in git(root, "ls-files", "--stage").splitlines():
        meta, path = line.split("\t")
        mode, blob, stage = meta.split()
        if stage != "0":
            raise ValueError("UNMERGED_INDEX")
        actual[path] = f"{mode} blob {blob}"
    bad = [p for p, v in protected.items() if actual.get(p) != v]
    unstaged = set(git(root, "diff", "--name-only").splitlines())
    bad.extend(p for p in unstaged if p in protected or p == CONTRACT)
    changed = set(git(root, "diff", START, "--name-only").splitlines())
    changed.update(git(root, "ls-files", "--others", "--exclude-standard").splitlines())
    bad.extend(p for p in changed if not (p.startswith(PREFIXES) or p == SPEC))
    assert git(root, "rev-parse", f"{START}:{CONTRACT}") == git(
        root, "hash-object", f"--path={CONTRACT}", CONTRACT
    )
    frozen = [
        SPEC,
        "docs/evidence/TASK_006B_Q/research-02/EXPERIMENT_PLAN.md",
        "docs/evidence/TASK_006B_Q/research-02/freeze.json",
        "docs/evidence/TASK_006B_Q/research-02/phase-a-cases.json",
        "docs/evidence/TASK_006B_Q/research-02/phase-a-d1-census.json",
        "docs/evidence/TASK_006B_Q/research-02/phase-a-separation.json",
    ]
    for path in frozen:
        if git(root, "rev-parse", f"{FREEZE}:{path}") != git(
            root, "hash-object", f"--path={path}", path
        ):
            bad.append("FREEZE_CHANGED:" + path)
    links = 0
    documents = [root / SPEC, *((root / "docs/evidence/TASK_006B_Q/research-02").rglob("*.md"))]
    for document in documents:
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "#")):
                continue
            links += 1
            if not (document.parent / target.split("#")[0]).resolve().exists():
                bad.append(target)
    git(root, "diff", START, "--check")
    if bad:
        raise ValueError(str(bad))
    return {
        "status": "PASS",
        "development_base": BASE,
        "contract_sha": START,
        "freeze_sha": FREEZE,
        "protected_mode_type_blob_count": len(protected),
        "frozen_documents": frozen,
        "local_links": links,
        "added_paths": sorted(changed),
        "failures": bad,
        "note": "Index identities plus working changes; no old allowlist exemption.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_new(args.output, verify(Path.cwd()))
