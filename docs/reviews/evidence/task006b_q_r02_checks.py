"""Read-only R02 review checks; market evidence reconciliation is not a raw-data rerun.

Run from the repository root with PYTHONPATH=src:. python <this file>.
No acquisition, database access, evidence writes, or product calls.
"""

import json
import subprocess
from collections import Counter
from datetime import datetime
from itertools import pairwise
from pathlib import Path

from tools.research.paqs_q.fixtures import synthetic
from tools.research.paqs_q.r02 import engine
from tools.research.paqs_q.r02.phase_a import case
from tools.research.paqs_q.types import canonical

BASE = "d50d73eea28005bc96e5ed0721b6a8e385ecedf5"
HEAD = "ddb61c15f1aea026b26c116f35fa1e2b0b0d055a"
CONTRACT = "47e7020609e5655927c6aac11a3b1f35b03c96aa"
FREEZE = "251f2a2ea9609ddd875c5aff03f5758c81914c84"
ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs/evidence/TASK_006B_Q"
R02 = EVIDENCE / "research-02"


def tree(revision: str) -> dict[str, str]:
    output = subprocess.check_output(["git", "ls-tree", "-r", revision], cwd=ROOT, text=True)
    return {path: meta for meta, path in (line.split("\t", 1) for line in output.splitlines())}


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run() -> None:
    base, head, start, frozen = map(tree, (BASE, HEAD, CONTRACT, FREEZE))
    assert len(base) == 429
    assert all(head.get(path) == meta for path, meta in base.items())
    contract_path = "prompts/tasks/TASK-006B-Q_R02_STRUCTURE_STABILITY_RESEARCH.md"
    assert head[contract_path] == start[contract_path]
    for path in set(head) - set(start):
        assert (
            path.startswith(
                (
                    "tools/research/paqs_q/r02/",
                    "tests/research/paqs_q/r02/",
                    "docs/evidence/TASK_006B_Q/research-02/",
                )
            )
            or path == "docs/research/PAQS_Q_STRUCTURE_R02_CANDIDATES.md"
        ), path
    for path in (
        "docs/research/PAQS_Q_STRUCTURE_R02_CANDIDATES.md",
        "docs/evidence/TASK_006B_Q/research-02/EXPERIMENT_PLAN.md",
        "docs/evidence/TASK_006B_Q/research-02/freeze.json",
        "docs/evidence/TASK_006B_Q/research-02/phase-a-cases.json",
        "docs/evidence/TASK_006B_Q/research-02/phase-a-d1-census.json",
        "docs/evidence/TASK_006B_Q/research-02/phase-a-separation.json",
    ):
        assert head[path] == frozen[path], path
    print("Protected: 429 base files, issued contract, and six frozen documents unchanged.")

    data = synthetic("M30", 201, "path_lock")
    actual = case(data, data.bars[-1].completed_at, candidate=True)
    saved = read(R02 / "refined-causes/h1-rejection-counterexample.json")
    saved.pop("label")
    assert json.loads(canonical(actual)) == saved
    old = engine.evaluate(data, data.bars[-2].completed_at).document()["decision"]
    new = engine.evaluate(data, data.bars[-1].completed_at).document()["decision"]
    assert old["active_pivots"] == []
    assert len(new["active_pivots"]) == 13
    assert all(40 <= p["extreme"] < p["confirmed"] < 199 for p in new["active_pivots"])
    assert actual["cause"] == "SEED_PATH"
    assert len(actual["rediscovered_still_eligible"]) == 13
    print("H1 synthetic rejection: exact saved diagnostic reproduced; 13 old pivots rediscovered.")

    frozen_cutoffs = read(R02 / "freeze.json")["cutoffs"]
    total = 0
    for tf in ("W1", "D1", "M30"):
        current = read(R02 / f"comparison/US.AVGO.{tf}.comparison.json")
        prior = read(EVIDENCE / f"remediation-01/corrected-study/US.AVGO.{tf}.diagnostics.json")
        assert [datetime.fromisoformat(r["cutoff"]) for r in current["rows"]] == [
            datetime.fromisoformat(c) for c in frozen_cutoffs[tf]
        ]
        before = {
            datetime.fromisoformat(r["cutoff"]): r
            for r in prior["rows"]
            if r["status"] == "VALID_OBSERVATION"
        }
        rows = [r for r in current["rows"] if r["status"] == "VALID"]
        assert {datetime.fromisoformat(r["cutoff"]) for r in rows} == set(before)
        assert all(
            r["BASELINE"]["hash"] == before[datetime.fromisoformat(r["cutoff"])]["hash"]
            for r in rows
        )
        total += len(rows)
        for algorithm in ("BASELINE", "H1"):
            observations = [r[algorithm] for r in rows]
            stats = current["summary"][algorithm]
            assert dict(Counter(r["regime"] for r in observations)) == stats["regimes"]
            transitions = [r for r in observations if "events" in r]
            assert len(transitions) == stats["adjacent_transitions"]
            for field, summary_field in (
                ("opportunities", "opportunities"),
                ("lost", "lost_events"),
                ("expired", "expired_events"),
                ("rediscovered", "rediscovered_events"),
                ("newly_confirmed", "new_confirmations"),
            ):
                values = [r["events"][field] for r in transitions]
                count = sum(v if field == "opportunities" else len(v) for v in values)
                assert count == stats[summary_field], (tf, algorithm, field)
            for previous, current_row in pairwise(observations):
                change = current_row["events"]
                old_events = set(map(tuple, previous["structure"]["pivots"]))
                new_events = set(map(tuple, current_row["structure"]["pivots"]))
                expired = set(map(tuple, change["expired"]))
                lost = set(map(tuple, change["lost"]))
                assert expired <= old_events
                assert len(old_events - expired) == change["opportunities"]
                assert old_events - expired - new_events == lost
                assert new_events - old_events == set(map(tuple, change["rediscovered"])) | set(
                    map(tuple, change["newly_confirmed"])
                )
            print(
                tf, algorithm, f"loss/opportunities={stats['lost_events']}/{stats['opportunities']}"
            )
    assert total == 274
    print("274 baseline hashes match prior evidence; all 300 scheduled endpoints retained.")
    for row in read(R02 / "refined-causes/h1-geometry-causes.json"):
        assert row["final_cause"] == "ATR_GEOMETRY_PROPAGATION"
        old = (row["OLD"]["zones"], row["OLD"]["range"])
        held = (row["LEFT_WITH_OLD_ATR"]["zones"], row["LEFT_WITH_OLD_ATR"]["range"])
        left = (row["LEFT"]["zones"], row["LEFT"]["range"])
        assert old == held and old != left
    print("Six submitted geometry controls reconcile. Raw AVGO/public-response bytes not rerun.")


if __name__ == "__main__":
    run()
