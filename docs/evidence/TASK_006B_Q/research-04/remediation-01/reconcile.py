"""Independent census oracle and exhaustive R04-F01 evidence reconciliation.

Run from repository root. Never rewrites prior evidence or either study.
"""

import argparse
import copy
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any

from tools.research.paqs_q.r04.study import write_new

ROOT = Path("docs/evidence/TASK_006B_Q/research-04")


def read(path: Path) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return value


def reconcile() -> dict[str, Any]:
    old_dir, new_dir = ROOT / "study-02", ROOT / "study-03"
    old_paths = {p.relative_to(old_dir) for p in old_dir.rglob("*") if p.is_file()}
    new_paths = {p.relative_to(new_dir) for p in new_dir.rglob("*") if p.is_file()}
    assert old_paths == new_paths
    series: list[dict[str, Any]] = []
    totals: Counter[str] = Counter()
    case_hashes: dict[str, str] = {}
    byte_equal: list[str] = []
    compared: list[str] = []
    ignored: list[str] = []
    valid = invalid = 0
    for path in sorted(old_paths):
        old_bytes, new_bytes = (old_dir / path).read_bytes(), (new_dir / path).read_bytes()
        old, new = read(old_dir / path), read(new_dir / path)
        if path.parts[0] == "cases":
            assert old_bytes == new_bytes, path
            case_hashes[path.as_posix()] = sha256(new_bytes).hexdigest()
        if old_bytes == new_bytes:
            byte_equal.append(path.as_posix())
        expected = copy.deepcopy(old)
        if path.name.startswith("US.AVGO."):
            assert len(old["rows"]) == len(new["rows"]) == 100
            for index, (before, after) in enumerate(zip(old["rows"], new["rows"], strict=True)):
                centers: Counter[str] = Counter()
                support: Counter[str] = Counter()
                events: Counter[str] = Counter()
                for i, identity in enumerate(after["census_ids"]):
                    if i < after["active_start"]:
                        continue
                    row = new["census_catalog"][identity]
                    key = "UNRESOLVED_SEGMENT" if row["segment"] is None else row["segment"]
                    centers[key] += 1
                    support[key] += row["support_hash"] is not None
                for event in after["events"]:
                    raw = new["event_catalog"][event["identity"]]["segment"]
                    key = "UNRESOLVED_SEGMENT" if raw is None else raw
                    events[key] += 1
                oracle = {
                    k: {"centers": centers[k], "support": support[k], "events": events[k]}
                    for k in centers.keys() | events.keys()
                }
                stats = after["costs"]
                assert stats["segments"] == oracle, (path, index, "CENSUS_ORACLE")
                assert "None" not in oracle
                for counter, total in (
                    (centers, "active_centers"),
                    (support, "complete_support_active"),
                    (events, "events"),
                ):
                    assert sum(counter.values()) == stats[total], (path, index, total)
                if after["status"] == "VALID":
                    valid += 1
                else:
                    invalid += 1
                    assert oracle == {}
                if path.name == "US.AVGO.W1.OBSERVATIONAL.json":
                    assert after["status"] == "VALID"
                    assert before["costs"]["segments"]["None"] == {
                        "centers": 0,
                        "support": 0,
                        "events": 0,
                    }
                    unresolved = centers["UNRESOLVED_SEGMENT"]
                    assert unresolved > 0
                    assert support["UNRESOLVED_SEGMENT"] == events["UNRESOLVED_SEGMENT"] == 0
                    corrected = expected["rows"][index]["costs"]["segments"]
                    del corrected["None"]
                    corrected["UNRESOLVED_SEGMENT"] = {
                        "centers": unresolved,
                        "support": 0,
                        "events": 0,
                    }
                    assert corrected == oracle  # Every resolved segment is unchanged.
                    series.append(
                        {
                            "cutoff": after["cutoff"],
                            "old_invalid_unresolved_centers": 0,
                            "unresolved_centers": unresolved,
                            "resolved_centers": sum(centers.values()) - unresolved,
                            "active_centers": stats["active_centers"],
                        }
                    )
                    totals.update(
                        {
                            k: series[-1][k]
                            for k in ("unresolved_centers", "resolved_centers", "active_centers")
                        }
                    )
                else:
                    assert before["costs"]["segments"] == stats["segments"]
            assert old["recognition_records"].keys() == new["recognition_records"].keys()
            for identity, record in new["recognition_records"].items():
                expected["recognition_records"][identity]["recognized_at"] = record["recognized_at"]
                ignored.append(f"{path}/recognition_records/{identity}/recognized_at")
        elif path.name == "summary.json":
            for field in (
                "started_at",
                "finished_at",
                "runtime_seconds",
                "output_bytes_before_summary_and_plots",
            ):
                expected[field] = new[field]
                ignored.append(f"summary.json/{field}")
        # Compare every field after precisely the allowed substitutions, no broad exclusions.
        assert expected == new, (path, "UNAUTHORIZED_SEMANTIC_DELTA")
        compared.append(path.as_posix())
    old_audit = read(ROOT / "audit-02.json")
    new_audit = read(ROOT / "remediation-01/audit-03.json")
    old_audit["checked_at"] = new_audit["checked_at"]
    assert old_audit == new_audit, "AUDIT_SEMANTIC_DELTA"
    ignored.append("audit-03.json/checked_at (versus audit-02.json)")
    assert len(series) == 100 and len(case_hashes) == 12
    assert valid == 274 and invalid == 326
    assert totals == {"active_centers": 10400, "resolved_centers": 8479, "unresolved_centers": 1921}
    charts = {
        p.name: sha256(p.read_bytes()).hexdigest()
        for p in sorted((ROOT / "charts-02").glob("*.png"))
    }
    assert len(charts) == 12
    return {
        "status": "PASS",
        "scope": "F01 aggregation only; not market applicability PASS",
        "compared_files": compared,
        "byte_identical_files": byte_equal,
        "ignored_exact_volatile_fields": ignored,
        "allowed_semantic_change": (
            "100 W1 OBSERVATIONAL segment maps only; null key normalized and centers restored"
        ),
        "unauthorized_semantic_changes": [],
        "W1_cutoff_series": series,
        "W1_totals": totals,
        "valid_cutoffs_all_three_invariants": valid,
        "nonvalid_empty_segment_cutoffs": invalid,
        "D1_M30_segments_equal": True,
        "all_other_fields_equal": True,
        "case_byte_identical_sha256": case_hashes,
        "reused_charts_02_sha256": charts,
        "audit_equal_except_checked_at": True,
        "clock_policy": (
            "Only actual timestamps replaced in comparison; unchanged first_seen_scheduled_cutoff "
            "and all evidence clocks checked by audit-03"
        ),
        "strict_history_and_broad_market_gate": "INCOMPLETE",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_new(args.output, reconcile())
