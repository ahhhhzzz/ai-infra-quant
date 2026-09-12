"""Explicit pre-result manifest creation; reads prior manifests, never evaluates market A1."""

from hashlib import sha256
from pathlib import Path
from typing import Any

from ..r04.study import write_new
from .enumeration import ALPHABET, STATES
from .model import RULE
from .protect import AUTHORITY, BASE, EVIDENCE, SPEC, START
from .study import read


def manifest(root: Path) -> dict[str, Any]:
    old = read(root / "docs/evidence/TASK_006B_Q/research-04/freeze.json")
    files = sorted(
        {
            p.relative_to(root).as_posix()
            for folder in ("tools/research/paqs_q/r05", "tests/research/paqs_q/r05")
            for p in (root / folder).rglob("*.py")
        }
        | {SPEC, EVIDENCE + "PLAN.md"}
    )
    schedules = [
        {"timeframe": tf, "mode": mode, "cutoff": cutoff}
        for tf in ("W1", "D1", "M30")
        for mode in ("OBSERVATIONAL", "AS_OF")
        for cutoff in old["cutoffs"][tf]
    ]
    assert len(schedules) == 600
    return {
        "contract_sha": START,
        "development_base": BASE,
        "authority": AUTHORITY,
        "review_substantive_pass": "2094118f270e209b5b037162813815886678fdbd",
        "B0": old["rule"],
        "A1": RULE,
        "only_intervention": "Remove prior-raw veto, retain entire four-observation eligibility",
        "implementation_text_sha256": {
            p: sha256((root / p).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for p in files
        },
        "hash_policy": "Canonical LF text; freeze Git commit additionally fixes mode/type/blob",
        "observation_hashes": old["observation_hashes"],
        "calendar_export_sha256": old["calendar_export_sha256"],
        "R04_freeze_sha256": sha256(
            (root / "docs/evidence/TASK_006B_Q/research-04/freeze.json")
            .read_bytes()
            .replace(b"\r\n", b"\n")
        ).hexdigest(),
        "cutoffs": old["cutoffs"],
        "scheduled_evaluations": schedules,
        "W_A_N": {"W1": [26, 104, 130], "D1": [60, 252, 312], "M30": [40, 160, 200]},
        "enumeration": {
            "alphabet_low_close_high_open_equals_close": ALPHABET,
            "calendar_states": STATES,
            "input_count": 40000,
        },
        "case_maximum": 15,
        "case_rubric": "PLAN.md deterministic first/extreme/chain/pair/dependency rubric",
        "metrics": "Exact formulas/endpoint identity in frozen specification; no outcome metric",
        "decision_table": ["RECOMMEND_CROSS_SAMPLE_ONLY", "REJECT_NO_VETO", "INCONCLUSIVE"],
        "hard_failure": "INVALID; preserve and stop",
        "external_research_requests": 0,
        "user_database_access": False,
        "pre_result_policy": "Push implementation freeze; read back GitHub SHA; then run A1 AVGO",
    }


if __name__ == "__main__":
    write_new(Path(EVIDENCE) / "freeze.json", manifest(Path.cwd()))
