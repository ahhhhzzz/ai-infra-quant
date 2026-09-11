"""Read-only, task-specific mode/type/blob, scope, lineage and link audit."""

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from tools.research.paqs_q.r04.study import write_new
from tools.research.paqs_q.r04.verify import git, tree

BASE = "30fa67bcf4521600030ce76bf953fdff87d2e668"
START = "0215d687b0ece28dee4b7854226b3e8916420518"
FREEZE = "ce53cc86f358590b1778ebd486f91efcb6adc62a"
AUTHORITY = "8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f"
REVIEW = "4906985744512092fc098340f43e8eec1f41c494"
BRANCH = "task/006b-q-r04-local-certificate-market-applicability"
MUTABLE = {"tools/research/paqs_q/r04/study.py", "tests/research/paqs_q/r04/test_study.py"}
PREFIX = "docs/evidence/TASK_006B_Q/research-04/"
NEW = (PREFIX + "study-03/", PREFIX + "remediation-01/")


def verify(root: Path) -> dict[str, Any]:
    base, start, current = tree(root, BASE), tree(root, START), tree(root, "HEAD")
    assert len(base) == 580 and len(start) == 581
    assert git(root, "rev-parse", START + "^") == BASE
    assert git(root, "branch", "--show-current") == BRANCH
    git(root, "merge-base", "--is-ancestor", START, "HEAD")
    assert not git(root, "rev-list", "--merges", START + "..HEAD")
    assert git(root, "merge-base", "HEAD", AUTHORITY) == AUTHORITY
    assert git(root, "rev-parse", "origin/roadmap/no-live-trading") == AUTHORITY
    assert git(root, "rev-parse", "origin/review/006b-q-r04-independent") == REVIEW
    protected = {p: identity for p, identity in start.items() if p not in MUTABLE}
    assert len(protected) == 579
    index = {
        line.split("\t", 1)[1]: line.split("\t", 1)[0].split()
        for line in git(root, "ls-files", "-s").splitlines()
    }
    for path, identity in protected.items():
        assert current[path] == identity, (path, "HEAD")
        mode, kind, blob = identity.split()
        assert kind == "blob" and mode in {"100644", "100755"}
        assert index[path] == [mode, blob, "0"], (path, "INDEX")
        assert not (root / path).is_symlink()
        assert git(root, "hash-object", f"--path={path}", path) == blob, (path, "WORKTREE")
    changes = git(root, "diff", "--name-status", START).splitlines()
    changed = {line.split("\t", 1)[1]: line.split("\t", 1)[0] for line in changes}
    assert {p for p in changed if p in start} == MUTABLE
    assert all(status == ("M" if p in MUTABLE else "A") for p, status in changed.items())
    untracked = set(git(root, "ls-files", "--others", "--exclude-standard").splitlines())
    added = (set(changed) - MUTABLE) | untracked
    assert all(p.startswith(NEW) for p in added)
    assert not git(root, "diff", "--summary", START) or all(
        line.lstrip().startswith("create mode 100644 ")
        for line in git(root, "diff", "--summary", START).splitlines()
    )
    for path in set(changed) | added:
        assert not (root / path).is_symlink()
        if path in index:
            assert index[path][0] == "100644"
    links: list[tuple[str, str]] = []
    for path in sorted(added):
        if not path.endswith(".md"):
            continue
        for target in re.findall(r"\]\(([^)]+)\)", (root / path).read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            file = unquote(target.split("#", 1)[0])
            assert (root / path).parent.joinpath(file).resolve().is_file(), (path, target)
            links.append((path, target))
    git(root, "diff", "--check", START)
    git(root, "diff", "--cached", "--check")
    frozen = tree(root, FREEZE)
    frozen_paths = (
        PREFIX + "PLAN.md",
        PREFIX + "freeze.json",
        "docs/research/PAQS_Q_LOCAL_CERTIFICATE_MARKET_APPLICABILITY_R04.md",
    )
    assert all(protected[p] == frozen[p] for p in frozen_paths)
    refs = json.loads((root / NEW[1] / "remote-heads-before.json").read_text(encoding="utf-8"))[
        "refs"
    ]
    return {
        "status": "PASS",
        "checked_head": git(root, "rev-parse", "HEAD"),
        "reviewed_R04": BASE,
        "contract": START,
        "protected_mode_type_blob_count": len(protected),
        "protected_identities": protected,
        "modified_existing_paths": sorted(MUTABLE),
        "added_paths": sorted(added),
        "relative_links_checked": links,
        "diff_check": "PASS",
        "no_deletion_rename_symlink_mode_change": True,
        "frozen_identities": {p: frozen[p] for p in frozen_paths},
        "authority": AUTHORITY,
        "review": REVIEW,
        "remote_refs_before_push": refs,
        "worktrees": git(root, "worktree", "list", "--porcelain"),
        "data_policy": (
            "No database access or writes in this remediation; frozen external inputs read only. "
            "No claim about concurrent external user database changes."
        ),
        "scope": "Only two approved existing files plus two approved new evidence directories",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(Path.cwd())
    if args.output:
        result["output_artifact"] = args.output.as_posix()
        result["added_paths"] = sorted(set(result["added_paths"]) | {args.output.as_posix()})
        write_new(args.output, result)
    print(
        json.dumps(
            {k: result[k] for k in ("status", "checked_head", "protected_mode_type_blob_count")}
        )
    )
