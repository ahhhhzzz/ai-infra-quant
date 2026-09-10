"""R03-only additive scope, protected Git identities and local documentation links."""

import argparse
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from .witnesses import write_new

BASE = "ddb61c15f1aea026b26c116f35fa1e2b0b0d055a"
CONTRACT = "8338144f0185f1b5b416daf08d5bcbff074bb345"
FREEZE = "2e048607414021e12984871db3a888cba7f20557"
ISSUED = "prompts/tasks/TASK-006B-Q_R03_CONFIRMATION_AND_ROLLING_STABILITY_CONTRACT.md"
PLAN = "docs/evidence/TASK_006B_Q/research-03/PLAN.md"
SPEC = "docs/research/PAQS_Q_CONFIRMATION_AND_ROLLING_STABILITY_R03.md"
PREFIXES = (
    "tools/research/paqs_q/r03/",
    "tests/research/paqs_q/r03/",
    "docs/evidence/TASK_006B_Q/research-03/",
)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={root.as_posix()}", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).strip()


def tree(root: Path, revision: str) -> dict[str, str]:
    return {
        line.split("\t", 1)[1]: line.split("\t", 1)[0]
        for line in git(root, "ls-tree", "-r", revision).splitlines()
    }


def verify(root: Path) -> dict[str, Any]:
    base, current = tree(root, BASE), tree(root, "HEAD")
    assert len(base) == 465
    protected = {**base, ISSUED: tree(root, CONTRACT)[ISSUED], PLAN: tree(root, FREEZE)[PLAN]}
    for path, identity in protected.items():
        assert current[path] == identity, ("COMMITTED_PROTECTED_CHANGE", path)
        blob = git(root, "hash-object", f"--path={path}", path)
        assert blob == identity.split()[2], ("WORKTREE_PROTECTED_CHANGE", path)
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
        "base_files": len(base),
        "protected_mode_type_blob_count": len(protected),
        "contract": CONTRACT,
        "freeze_commit": git(root, "rev-parse", FREEZE),
        "checked_head": git(root, "rev-parse", "HEAD"),
        "added_paths": sorted(paths),
        "local_links": links,
        "diff_check": "PASS",
        "user_database_access": "NONE; no filesystem/hash certification claimed",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_new(args.output, verify(Path.cwd()))
