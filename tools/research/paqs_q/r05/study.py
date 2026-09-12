"""Exclusive, frozen, offline B0 reproduction followed by a single A1 study."""

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from decimal import localcontext
from hashlib import sha256
from pathlib import Path
from typing import Any

from ..r04 import study as r04
from ..r04.integrations.local import load, stamp
from ..r04.model import compare
from ..r04.model import evaluate as baseline
from ..r04.verify import git
from ..types import CONTEXT, Dataset, canonical, digest
from .cases import choose, finalize
from .enumeration import enumerate_domain
from .metrics import disposition, metrics, summarize
from .model import ablate, dependency_audit, verify_pair

EVIDENCE = Path("docs/evidence/TASK_006B_Q/research-05")
REFERENCE = Path("docs/evidence/TASK_006B_Q/research-04/study-03")


def read(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def reconcile_baseline(reference: Path, reproduced: Path) -> dict[str, Any]:
    paths = sorted(p.relative_to(reference).as_posix() for p in reference.rglob("*") if p.is_file())
    assert paths == sorted(
        p.relative_to(reproduced).as_posix() for p in reproduced.rglob("*") if p.is_file()
    )
    ignored = []
    for path in paths:
        old, new = read(reference / path), read(reproduced / path)
        if path.startswith("US.AVGO."):
            assert old["recognition_records"].keys() == new["recognition_records"].keys()
            for identity, record in new["recognition_records"].items():
                old["recognition_records"][identity]["recognized_at"] = record["recognized_at"]
                ignored.append(path + "/recognition_records/" + identity + "/recognized_at")
        if path == "summary.json":
            for k in (
                "started_at",
                "finished_at",
                "runtime_seconds",
                "output_bytes_before_summary_and_plots",
            ):
                old[k] = new[k]
                ignored.append(path + "/" + k)
        assert old == new, (path, "B0_REFERENCE_DRIFT")
    return {
        "status": "PASS",
        "compared_files": paths,
        "ignored_exact_run_metadata": sorted(ignored),
        "all_semantic_fields_equal": True,
        "R04_reference": REFERENCE.as_posix(),
    }


def check_snapshot(snapshot: dict[str, Any], doc: dict[str, Any], index: int) -> None:
    record = doc["rows"][index]
    for k, value in snapshot.items():
        if k not in {"bars", "calendar", "events", "census"}:
            assert json.loads(canonical(value)) == record[k], (index, k)
    census = [
        dict(doc["census_catalog"][key], index=i, active=i >= record["active_start"])
        for i, key in enumerate(record["census_ids"])
    ]
    events = [dict(doc["event_catalog"][e["identity"]], **e) for e in record["events"]]
    assert json.loads(canonical(snapshot["census"])) == census
    assert json.loads(canonical(snapshot["events"])) == events
    with localcontext(CONTEXT):
        assert json.loads(canonical(r04.costs(snapshot))) == record["costs"]


class Catalog:
    """Retain every center through catalog references; never aggregate away rows."""

    def __init__(self) -> None:
        self.rows: dict[str, Any] = {}
        self.calendars: dict[str, Any] = {}

    def pack(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        packed = {k: v for k, v in snapshot.items() if k not in {"bars", "census", "calendar"}}
        ids = []
        for row in snapshot["census"]:
            payload = {k: v for k, v in row.items() if k not in {"index", "active"}}
            key = digest("r05-census", payload)
            self.rows[key] = payload
            ids.append(key)
        packed["census_ids"] = ids
        packed["active_start"] = next((r["index"] for r in snapshot["census"] if r["active"]), None)
        cal_key = digest("r05-calendar-view", snapshot["calendar"])
        self.calendars[cal_key] = snapshot["calendar"]
        packed["calendar_view_id"] = cal_key
        packed["price_refs"] = [b.ref for b in snapshot["bars"]]
        packed["metrics"] = metrics(snapshot)
        return packed


def check_times(
    result: dict[str, Any], facts_by_ref: dict[str, Any], recognition: dict[str, Any]
) -> None:
    cutoff = result["cutoff"]
    assert all(
        b.completed
        and b.completed_at <= cutoff
        and (b.available_at is None or b.available_at <= cutoff)
        for b in result["bars"]
    )
    if "audit" in result:
        assert result["audit"]["violation_count"] == 0
    rows = {r["center"]: r for r in result["census"]}
    for event in result["events"]:
        row = rows[event["extreme_ref"]]
        assert len(row["price_support"]) == 4
        assert event["reversal_time"] <= cutoff
        assert event["available_at"] is None or event["available_at"] <= cutoff
        assert recognition[event["identity"]]["recognized_at"] >= cutoff
        for _, ref in row["calendar_support"]:
            f = facts_by_ref[ref]
            assert f.available_at is None or f.available_at <= cutoff


def frame(
    data: Dataset,
    facts: tuple[Any, ...],
    cutoffs: list[str],
    doc: dict[str, Any],
    output: Path,
    mode: str,
) -> dict[str, Any]:
    records = []
    catalog = Catalog()
    selected: dict[str, Any] = {}
    recognized: dict[str, dict[str, Any]] = {"B0": {}, "A1": {}}
    previous: dict[str, Any] = {}
    unique_added, restored = set(), set()
    prior_kinds: Counter[str] = Counter()
    dependency_counts: Counter[str] = Counter()
    fact_refs = {f.ref: f for f in facts}
    for i, text in enumerate(cutoffs):
        cutoff = stamp(text)
        b = baseline(data, facts, cutoff, mode)
        check_snapshot(b, doc, i)
        a = ablate(b, facts)
        delta = verify_pair(b, a)
        dependencies = dependency_audit(b)
        row = {
            "cutoff": cutoff,
            "status": b["status"],
            "reason": b["reason"],
            "delta": delta,
            "dependency_audit": dependencies,
        }
        for arm, result in (("B0", b), ("A1", a)):
            r04.recognize(result, recognized[arm], datetime.now(UTC))
            check_times(result, fact_refs, recognized[arm])
            row[arm] = catalog.pack(result)
            if arm in previous:
                trans = compare(previous[arm], result, data)
                row[arm]["transition"] = trans
                assert trans.get("full_support_lost", 0) == 0
                assert "UNEXPLAINED_SAME_SUPPORT" not in trans.get("loss_causes", {}).values()
            previous[arm] = result
        for entry in delta["added"]:
            unique_added.add(entry["endpoint"])
            if entry["restored_more_extreme"]:
                restored.add(entry["endpoint"])
            prior_kinds[entry["previous_raw_kind"]] += 1
        for entry in dependencies:
            dependency_counts["all_centers"] += 1
            dependency_counts["active_centers"] += entry["active"]
            dependency_counts["active_current_xor"] += entry["active"] and entry["current_xor"]
        choose(b, a, delta, row["B0"]["metrics"], row["A1"]["metrics"], dependencies, selected)
        records.append(row)
        if i % 20 == 0:
            print(data.timeframe, mode, i + 1, "/", len(cutoffs), flush=True)
    cases, categories = finalize(selected)
    for case in cases:
        r04.write_new(output / "cases" / (data.timeframe + "." + case["case_id"] + ".json"), case)
    summary = {
        "timeframe": data.timeframe,
        "mode": mode,
        "scheduled": len(cutoffs),
        "status": Counter(r["status"] for r in records),
        "valid": sum(r["status"] == "VALID" for r in records),
        "B0": summarize(records, "B0"),
        "A1": summarize(records, "A1"),
        "added_occurrences": sum(len(r["delta"]["added"]) for r in records),
        "deduplicated_added": len(unique_added),
        "deduplicated_added_endpoints": sorted(unique_added),
        "deduplicated_restored_more_extreme": len(restored),
        "deduplicated_restored_more_extreme_endpoints": sorted(restored),
        "previous_raw_kind_occurrences": prior_kinds,
        "dependency_counts": dependency_counts,
        "case_categories": categories,
    }
    r04.write_new(
        output / "frames" / f"{data.timeframe}.{mode}.json",
        {
            "summary": summary,
            "rows": records,
            "census_catalog": catalog.rows,
            "calendar_catalog": catalog.calendars,
            "decode": (
                "Census index is array position; active iff index >= active_start. "
                "Calendar view resolves through calendar_catalog."
            ),
            "recognition_records": recognized,
        },
    )
    return summary


def verify_freeze(root: Path, sha: str, receipt: Path) -> dict[str, Any]:
    freeze = read(root / EVIDENCE / "freeze.json")
    assert read(receipt)["github_freeze_sha"] == sha
    assert git(root, "rev-parse", sha + "^") == freeze["contract_sha"]
    git(root, "merge-base", "--is-ancestor", sha, "HEAD")
    for path, expected in freeze["implementation_text_sha256"].items():
        assert sha256((root / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == expected, (
            path
        )
    return freeze


def run(
    root: Path, data_dir: Path, calendar: Path, output: Path, freeze_sha: str, receipt: Path
) -> None:
    frozen = verify_freeze(root, freeze_sha, receipt)
    for p in (
        "baseline-study",
        "frames",
        "cases",
        "baseline-reproduction.json",
        "ablation-results.json",
        "endpoint-delta.json",
        "dependency-audit.json",
        "proof-and-enumeration.json",
        "failure.json",
    ):
        if (output / p).exists():
            raise FileExistsError("FRESH_EXCLUSIVE_OUTPUT_REQUIRED: " + p)
    try:
        r04.run(root, data_dir, calendar, output / "baseline-study")
        reconciliation = reconcile_baseline(root / REFERENCE, output / "baseline-study")
        r04.write_new(output / "baseline-reproduction.json", reconciliation)
        data, facts, sources = load(root, data_dir, calendar)
        expected = read(root / REFERENCE / "source-calendar-manifest.json")["sources"]
        assert sources == expected
        frames = []
        for tf in ("W1", "D1", "M30"):
            for mode in ("OBSERVATIONAL", "AS_OF"):
                doc = read(root / REFERENCE / f"US.AVGO.{tf}.{mode}.json")
                frames.append(frame(data[tf], facts, frozen["cutoffs"][tf], doc, output, mode))
        obs = [f for f in frames if f["mode"] == "OBSERVATIONAL"]
        assert [f["valid"] for f in obs] == [100, 100, 74]
        assert [f["B0"]["active_reasons"]["PRIOR_RAW_VETO"] for f in obs] == [172, 939, 108]
        w1 = obs[0]["B0"]
        assert w1["overlapping_cutoff_totals"]["active_centers"] == 10400
        assert w1["segments_occurrences"]["UNRESOLVED_SEGMENT"]["centers"] == 1921
        assert (
            sum(
                v["centers"]
                for k, v in w1["segments_occurrences"].items()
                if k != "UNRESOLVED_SEGMENT"
            )
            == 8479
        )
        r04.write_new(
            output / "ablation-results.json",
            {
                "integrity": "VALID",
                "quantitative_disposition": disposition(frames),
                "case_review_required": True,
                "freeze_sha": freeze_sha,
                "frames": frames,
                "market_gate": "INCOMPLETE",
                "external_requests": 0,
                "database_access": False,
                "sources": sources,
                "finished_at": datetime.now(UTC),
            },
        )
        r04.write_new(
            output / "endpoint-delta.json",
            {
                "frames": [
                    {
                        k: f[k]
                        for k in (
                            "timeframe",
                            "mode",
                            "added_occurrences",
                            "deduplicated_added",
                            "deduplicated_added_endpoints",
                            "deduplicated_restored_more_extreme",
                            "deduplicated_restored_more_extreme_endpoints",
                            "previous_raw_kind_occurrences",
                        )
                    }
                    for f in frames
                ],
                "removed_endpoints": [],
                "detail": (
                    "Every endpoint, baseline reason, support and omission reference "
                    "retained in frames/* rows.delta"
                ),
            },
        )
        r04.write_new(
            output / "dependency-audit.json",
            {
                "frames": [
                    {
                        "timeframe": f["timeframe"],
                        "mode": f["mode"],
                        "counts": f["dependency_counts"],
                    }
                    for f in frames
                ],
                "emits_events": False,
                "detail": (
                    "Every center/active/segment/reason/XOR retained "
                    "in frames/* rows.dependency_audit"
                ),
            },
        )
        r04.write_new(output / "proof-and-enumeration.json", enumerate_domain())
    except Exception as exc:
        r04.write_new(
            output / "failure.json",
            {
                "status": "INVALID",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "freeze_sha": freeze_sha,
                "stop_required": True,
            },
        )
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze-sha", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    run(Path.cwd(), args.data_dir, args.calendar, args.output, args.freeze_sha, args.receipt)
