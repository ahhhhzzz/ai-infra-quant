"""R04-only additive scope and full protected Git mode/type/blob verification."""

import argparse
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from .study import write_new

BASE = "cc909077a470f7a6e717787307e8a4a8062ff792"
CONTRACT = "9a9113fb9a0ced3f7a481d833be4033d29016fea"
FREEZE = "ce53cc86f358590b1778ebd486f91efcb6adc62a"
ISSUED = "prompts/tasks/TASK-006B-Q_R04_LOCAL_CERTIFICATE_MARKET_APPLICABILITY.md"
SPEC = "docs/research/PAQS_Q_LOCAL_CERTIFICATE_MARKET_APPLICABILITY_R04.md"
PREFIXES = (
    "tools/research/paqs_q/r04/",
    "tests/research/paqs_q/r04/",
    "docs/evidence/TASK_006B_Q/research-04/",
)
FROZEN = (SPEC, PREFIXES[2] + "PLAN.md", PREFIXES[2] + "freeze.json")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={root.as_posix()}", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).strip()


def tree(root: Path, rev: str) -> dict[str, str]:
    return {
        line.split("\t", 1)[1]: line.split("\t", 1)[0]
        for line in git(root, "ls-tree", "-r", rev).splitlines()
    }


def verify(root: Path) -> dict[str, Any]:
    base, current, frozen = tree(root, BASE), tree(root, "HEAD"), tree(root, FREEZE)
    assert len(base) == 482
    protected = {**base, ISSUED: tree(root, CONTRACT)[ISSUED], **{p: frozen[p] for p in FROZEN}}
    assert git(root, "rev-parse", FREEZE + "^") == CONTRACT
    assert git(root, "rev-parse", CONTRACT + "^") == BASE
    for path, identity in protected.items():
        assert current[path] == identity, ("COMMITTED_PROTECTED_CHANGE", path)
        assert git(root, "hash-object", f"--path={path}", path) == identity.split()[2], path
        assert git(root, "ls-files", "-s", "--", path).split()[:2] == [
            identity.split()[0],
            identity.split()[2],
        ], path
    differences = git(root, "diff", "--name-status", BASE).splitlines()
    assert all(line.startswith("A\t") for line in differences), differences
    paths = {line.split("\t", 1)[1] for line in differences}
    paths.update(git(root, "ls-files", "--others", "--exclude-standard").splitlines())
    paths.discard(ISSUED)
    assert all(p == SPEC or p.startswith(PREFIXES) for p in paths), paths
    links = []
    for path in sorted(paths):
        if not path.endswith(".md"):
            continue
        for target in re.findall(r"\]\(([^)]+)\)", (root / path).read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            file = unquote(target.split("#", 1)[0])
            assert (root / path).parent.joinpath(file).resolve().is_file(), (path, target)
            links.append((path, target))
    git(root, "diff", "--check", BASE)
    git(root, "diff", "--cached", "--check")
    return {
        "status": "PASS",
        "development_base": BASE,
        "contract": CONTRACT,
        "freeze": FREEZE,
        "checked_head": git(root, "rev-parse", "HEAD"),
        "protected_mode_type_blob_count": len(protected),
        "base_files": len(base),
        "frozen_identities": {p: frozen[p] for p in FROZEN},
        "added_paths": sorted(paths),
        "local_links": links,
        "diff_check": "PASS",
        "scope": "R04 additions only",
        "database": "No write access; no claim about externally changing whole-database bytes",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_new(args.output, verify(Path.cwd()))
