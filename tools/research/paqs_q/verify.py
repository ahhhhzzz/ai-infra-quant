"""Read-only Git allowlist, protected identities, evidence links and rule matrix checks."""

import argparse
import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import unquote

BASE = "8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f"
START = "3e547189fa446bb04913e5fecc73720e424cc240"
CONTRACT = "prompts/tasks/TASK-006B-Q_STRUCTURE_FORMALIZATION_AND_STABILITY.md"
PREFIXES = ("tools/research/paqs_q/", "tests/research/paqs_q/", "docs/evidence/TASK_006B_Q/")
DOCUMENTS = (
    "docs/research/PAQS_Q_STRUCTURE_MATH_CANDIDATE_V1.md",
    "docs/reports/TASK_006B_Q_IMPLEMENTATION_REPORT.md",
)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={root.as_posix()}", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).strip()


def allowed(path: str) -> bool:
    return path in DOCUMENTS or path.startswith(PREFIXES)


def verify(root: Path) -> dict[str, Any]:
    root = root.resolve()
    baseline = {}
    for line in git(root, "ls-tree", "-r", BASE).splitlines():
        metadata, path = line.split("\t", 1)
        baseline[path] = metadata
    current = {}
    for line in git(root, "ls-files", "--stage").splitlines():
        metadata, path = line.split("\t", 1)
        mode, blob, stage = metadata.split()
        if stage != "0":
            raise ValueError("UNMERGED_INDEX")
        current[path] = f"{mode} blob {blob}"
    failures = []
    protected = 0
    for path, metadata in baseline.items():
        if allowed(path):
            continue
        protected += 1
        if current.get(path) != metadata:
            failures.append("INDEX_IDENTITY:" + path)
    changed = git(root, "diff", BASE, "--name-only").splitlines()
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    failures.extend(
        "OUTSIDE_ALLOWLIST:" + p for p in changed + untracked if not allowed(p) and p != CONTRACT
    )
    expected_contract = git(root, "rev-parse", f"{START}:{CONTRACT}")
    actual_contract = git(root, "hash-object", f"--path={CONTRACT}", CONTRACT)
    if expected_contract != actual_contract:
        failures.append("ISSUED_CONTRACT_CHANGED")
    matrix_path = root / "docs/evidence/TASK_006B_Q/rule-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    if {r["id"] for r in matrix} != {f"QSTR-{i:03}" for i in range(1, 13)}:
        failures.append("RULE_MATRIX_INCOMPLETE")
    for row in matrix:
        for reference in row["functions"] + row["tests"]:
            path, name = reference.split("::")
            tree = ast.parse((root / path).read_text(encoding="utf-8"))
            if not any(isinstance(n, ast.FunctionDef) and n.name == name for n in ast.walk(tree)):
                failures.append("MATRIX_REFERENCE:" + reference)
    link_count = 0
    for filename in (*DOCUMENTS, "docs/evidence/TASK_006B_Q/README.md"):
        document_path = root / filename
        for target in re.findall(r"\]\(([^)]+)\)", document_path.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "#")):
                continue
            link_count += 1
            linked = (document_path.parent / unquote(target.split("#", 1)[0])).resolve()
            if not linked.is_file():
                failures.append("BROKEN_LOCAL_LINK:" + filename + ":" + target)
    git(root, "diff", "--check")
    if failures:
        raise ValueError(json.dumps(failures))
    return {
        "base": BASE,
        "start": START,
        "protected_mode_type_blob_count": protected,
        "issued_contract_blob": actual_contract,
        "matrix_rules": len(matrix),
        "local_document_links": link_count,
        "changed_paths": sorted(set(changed + untracked)),
        "status": "PASS",
        "note": "Git index mode/type/blob plus working-tree diff; no network or mutation",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.root)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
