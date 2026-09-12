"""R05 additive scope, Git identity, freeze lineage and relative-link verification."""

import argparse
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from ..r04.study import write_new
from ..r04.verify import git, tree

BASE = "c4e21a0204cf6cdd7bb139584b02f01792a49f13"
START = "0d8ca48b046325c4d03a1716c806d42a333153ec"
AUTHORITY = "8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f"
REVIEW = "56020173b223dcf277ef8f125eeeaaa3fa135bcc"
SPEC = "docs/research/PAQS_Q_PRIOR_RAW_VETO_ABLATION_R05.md"
EVIDENCE = "docs/evidence/TASK_006B_Q/research-05/"
PREFIXES = ("tools/research/paqs_q/r05/", "tests/research/paqs_q/r05/", EVIDENCE)


def verify(root: Path, freeze_sha: str | None = None) -> dict[str, Any]:
    base, start, current = tree(root, BASE), tree(root, START), tree(root, "HEAD")
    assert len(base) == 611 and len(start) == 612
    assert git(root, "rev-parse", START + "^") == BASE
    assert git(root, "branch", "--show-current") == "task/006b-q-r05-prior-raw-veto-ablation"
    git(root, "merge-base", "--is-ancestor", START, "HEAD")
    assert not git(root, "rev-list", "--merges", START + "..HEAD")
    assert git(root, "merge-base", "HEAD", AUTHORITY) == AUTHORITY
    protected = dict(start)
    frozen = {}
    if freeze_sha:
        assert git(root, "rev-parse", freeze_sha + "^") == START
        git(root, "merge-base", "--is-ancestor", freeze_sha, "HEAD")
        frozen = {
            p: value
            for p, value in tree(root, freeze_sha).items()
            if p == SPEC
            or p.startswith(PREFIXES[:2])
            or p in {EVIDENCE + "PLAN.md", EVIDENCE + "freeze.json"}
        }
        assert frozen
        protected.update(frozen)
    index = {
        line.split("\t", 1)[1]: line.split("\t", 1)[0].split()
        for line in git(root, "ls-files", "-s").splitlines()
    }
    for p, identity in protected.items():
        mode, kind, blob = identity.split()
        assert current[p] == identity and kind == "blob" and mode in {"100644", "100755"}
        assert index[p] == [mode, blob, "0"]
        assert not (root / p).is_symlink()
        assert git(root, "hash-object", f"--path={p}", p) == blob, p
    diff = git(root, "diff", "--name-status", START).splitlines()
    assert all(line.startswith("A\t") for line in diff)
    paths = {line.split("\t", 1)[1] for line in diff}
    paths.update(git(root, "ls-files", "--others", "--exclude-standard").splitlines())
    assert all(p == SPEC or p.startswith(PREFIXES) for p in paths)
    assert all(
        line.lstrip().startswith("create mode 100644 ")
        for line in git(root, "diff", "--summary", START).splitlines()
    )
    for p in paths:
        assert not (root / p).is_symlink()
        if p in index:
            assert index[p][0] == "100644"
    links = []
    for p in sorted(paths):
        if not p.endswith(".md"):
            continue
        for target in re.findall(r"\]\(([^)]+)\)", (root / p).read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            file = unquote(target.split("#", 1)[0])
            assert (root / p).parent.joinpath(file).resolve().is_file(), (p, target)
            links.append((p, target))
    git(root, "diff", "--check", START)
    git(root, "diff", "--cached", "--check")
    for branch, expected in (
        ("roadmap/no-live-trading", AUTHORITY),
        ("review/006b-q-r04-independent", REVIEW),
        ("task/006b-q-r04-local-certificate-market-applicability", BASE),
    ):
        assert git(root, "rev-parse", "origin/" + branch) == expected
    return {
        "status": "PASS",
        "checked_head": git(root, "rev-parse", "HEAD"),
        "base_protected_objects": len(start),
        "frozen_objects": frozen,
        "protected_identities": protected,
        "added_paths": sorted(paths),
        "links": sorted(links),
        "freeze_sha": freeze_sha,
        "git_status_porcelain": git(root, "status", "--porcelain"),
        "mode_type_blob": "PASS",
        "diff": "PASS",
        "scope": "pure additions",
        "database": "R05 did not access user database",
        "remote_scope": "GitHub refs read back independently at freeze and final delivery",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-sha")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(Path.cwd(), args.freeze_sha)
    if args.output:
        result["added_paths"] = sorted(set(result["added_paths"]) | {args.output.as_posix()})
        write_new(args.output, result)
    print(
        {k: result[k] for k in ("status", "checked_head", "base_protected_objects", "freeze_sha")}
    )
