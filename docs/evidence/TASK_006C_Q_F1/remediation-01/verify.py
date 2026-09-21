"""Read-only, exact-scope remediation protection and optional cross-OS receipt check."""

import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[4]
BASE = "d0e8dc22b38d85b0d1395cf76fc03f2de1e85122"
CONTRACT = "prompts/tasks/TASK-006C-Q-F1_VERSIONED_QUANT_EVENT_FRAMEWORK_FOUNDATION.md"
EDITED = {
    "src/ai_infra_quant/core/domain/paqs_q/inputs.py",
    "src/ai_infra_quant/core/domain/paqs_q/results.py",
    "src/ai_infra_quant/core/strategy/paqs_q/registry.py",
    "src/ai_infra_quant/resources/paqs_q/b0.json",
    "src/ai_infra_quant/resources/paqs_q/a1.json",
    "tests/architecture/test_task007b_boundaries.py",
    "tests/paqs_q/test_registry.py",
    "docs/engineering/PAQS_Q_FRAMEWORK.md",
    "docs/ROADMAP.md",
    "docs/MASTER_SPEC.md",
    "docs/ARCHITECTURE.md",
    "docs/STRATEGY_SPEC.md",
    "docs/REQUIREMENTS_MATRIX.md",
    "docs/engineering/PAQS_ENGINEERING_GUIDE.md",
}
NEW = {"tests/paqs_q/test_remediation_01.py", "prompts/tasks/TASK-006C-Q-F1_REMEDIATION_01.md"}
EVIDENCE = "docs/evidence/TASK_006C_Q_F1/remediation-01/"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=Path)
    args = parser.parse_args()
    git("merge-base", "--is-ancestor", BASE, "HEAD")
    baseline = {
        line.split("\t")[1]: line.split("\t")[0].split()
        for line in git("ls-tree", "-r", BASE).splitlines()
    }
    index = {
        line.split("\t")[1]: line.split("\t")[0].split()
        for line in git("ls-files", "-s").splitlines()
    }
    protected = 0
    for path, (mode, kind, blob) in baseline.items():
        if path in EDITED:
            continue
        target = ROOT / path
        assert kind == "blob" and index[path] == [mode, blob, "0"], path
        assert target.is_file() and not target.is_symlink(), path
        assert git("hash-object", "--path=" + path, path) == blob, path
        protected += 1
    assert (
        git("hash-object", "--path=" + CONTRACT, CONTRACT)
        == "c2c5448c1eb72fd0ece1572c31ba30246a761b51"
    )
    remediation_contract = "prompts/tasks/TASK-006C-Q-F1_REMEDIATION_01.md"
    assert (
        git("hash-object", "--path=" + remediation_contract, remediation_contract)
        == "612197e9763b7708c87b3af2272717c7edb3daad"
    )
    git("diff", "--check", BASE)
    changed = set(git("diff", "--name-only", BASE).splitlines())
    changed.update(git("ls-files", "--others", "--exclude-standard").splitlines())
    for path in changed:
        assert path in EDITED or path in NEW or path.startswith(EVIDENCE), path
        assert (ROOT / path).is_file() and not (ROOT / path).is_symlink(), path
    links = 0
    for path in sorted(changed):
        if not path.endswith(".md"):
            continue
        content = re.sub(
            r"^```.*?^```\s*$", "", (ROOT / path).read_text(encoding="utf-8"), flags=re.M | re.S
        )
        for target in re.findall(r"\]\(([^)]+)\)", content):
            if "://" in target:
                continue
            file, _, anchor = unquote(target).partition("#")
            dest = ((ROOT / path).parent / file).resolve() if file else ROOT / path
            assert dest.is_file(), (path, target)
            if anchor and dest.suffix == ".md":
                headings = re.findall(
                    r"^#{1,6}\s+(.+?)\s*#*$", dest.read_text(encoding="utf-8"), re.M
                )
                slugs = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
                assert anchor in slugs, (path, target)
            links += 1
    result = {
        "status": "PASS",
        "baseline": BASE,
        "baseline_objects": len(baseline),
        "protected_objects": protected,
        "changed_files": sorted(changed),
        "relative_links": links,
        "windows_comparison": "NOT_RUN",
    }
    if args.windows:
        windows = json.loads(args.windows.read_text(encoding="utf-8"))
        linux = json.loads((ROOT / EVIDENCE / "linux-vectors.json").read_text(encoding="utf-8"))
        assert windows["platform"] == "Windows" and linux["platform"] == "Linux"
        for key in ("vectors", "code_hashes", "vector_digest", "python", "tzdata"):
            assert windows[key] == linux[key], key
        result["windows_comparison"] = "PASS"
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
