"""Post-run denominators, input-time exclusions and evidence cross-checks; no reevaluation."""

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..types import canonical
from .integrations.local import load, stamp
from .study import write_new


def audit(root: Path, data_dir: Path, calendar: Path, study: Path) -> dict[str, Any]:
    datasets, facts, _ = load(root, data_dir, calendar)
    fact_by_ref = {f.ref: f for f in facts}
    all_rows = []
    frame_summaries = []
    for path in sorted(study.glob("US.AVGO.*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        data = datasets[doc["summary"]["timeframe"]]
        catalog = doc["census_catalog"]
        distribution: dict[str, list[Decimal]] = {"ages": [], "separations": [], "amplitudes": []}
        by_segment: dict[str, Counter[str]] = {}
        violations = 0
        for row in doc["rows"]:
            cutoff = stamp(row["cutoff"])
            completed = [b for b in data.bars if b.completed and b.completed_at <= cutoff]
            eligible = [
                b
                for b in completed
                if (b.available_at is None and row["mode"] == "OBSERVATIONAL")
                or (b.available_at is not None and b.available_at <= cutoff)
            ]
            rejected_derived = [
                b for b in eligible if b.timeframe != "D1" and b.coverage in {"PARTIAL", "UNKNOWN"}
            ]
            all_rows.append(
                {
                    "timeframe": data.timeframe,
                    "mode": row["mode"],
                    "cutoff": row["cutoff"],
                    "raw_records": len(data.bars),
                    "unfinished": sum(not b.completed for b in data.bars),
                    "completed_after_cutoff": sum(
                        b.completed and b.completed_at > cutoff for b in data.bars
                    ),
                    "completed_by_cutoff": len(completed),
                    "known_available_later": sum(
                        b.available_at is not None and b.available_at > cutoff for b in completed
                    ),
                    "unknown_price_availability": sum(b.available_at is None for b in completed),
                    "derived_incomplete_filtered": len(rejected_derived),
                    "raw_version_extra_records": len(data.bars) - len({b.start for b in data.bars}),
                    "unknown_calendar_availability": sum(f.available_at is None for f in facts),
                    "known_calendar_available_later": sum(
                        f.available_at is not None and f.available_at > cutoff for f in facts
                    ),
                    "status": row["status"],
                    "reason": row["reason"],
                }
            )
            if row["status"] != "VALID":
                assert not row["census_ids"] and not row["events"]
                continue
            reasons: Counter[str] = Counter()
            for i, key in enumerate(row["census_ids"]):
                center = catalog[key]
                if i < row["active_start"]:
                    continue
                reasons[center["reason"]] += 1
                segment = center["segment"] or "UNRESOLVED_SEGMENT"
                counts = by_segment.setdefault(segment, Counter())
                counts["center_uses"] += 1
                counts["full_support_uses"] += center["support_hash"] is not None
                counts["event_uses"] += center["reason"] == "ACCEPTED_ACTIVE"
            assert reasons == row["costs"]["reasons_active"]
            assert len(row["events"]) == row["costs"]["events"]
            distribution["ages"].extend(Decimal(a) for a in row["costs"]["ages"])
            distribution["separations"].extend(Decimal(a) for a in row["costs"]["separations"])
            distribution["amplitudes"].extend(
                Decimal(a) for a in row["costs"]["amplitudes_current_prior_range"]
            )
            violations += row["audit"]["violation_count"]
            for reference in row["events"]:
                event = doc["event_catalog"][reference["identity"]]
                assert stamp(event["reversal_time"]) <= cutoff
                assert event["available_at"] is None or stamp(event["available_at"]) <= cutoff
                witness = catalog[row["census_ids"][reference["index"]]]
                assert witness["support_hash"] == event["support_hash"]
                assert len(witness["price_support"]) == 4
                for _, calendar_ref in witness["calendar_support"]:
                    f = fact_by_ref[calendar_ref]
                    assert f.available_at is None or f.available_at <= cutoff
                record = doc["recognition_records"][reference["identity"]]
                assert stamp(record["recognized_at"]) >= stamp(
                    record["first_seen_scheduled_cutoff"]
                )
                assert stamp(record["recognized_at"]) >= stamp(record["reversal_time"])
        frame_summaries.append(
            {
                "timeframe": data.timeframe,
                "mode": doc["summary"]["mode"],
                "time_violations": violations,
                "segments": by_segment,
                "distributions": {
                    k: {
                        "count": len(v),
                        "min": min(v) if v else None,
                        "max": max(v) if v else None,
                        "lower_median": sorted(v)[(len(v) - 1) // 2] if v else None,
                    }
                    for k, v in distribution.items()
                },
            }
        )
    case_paths = sorted((study / "cases").glob("*.json"))
    assert len(case_paths) <= 20
    for path in case_paths:
        case = json.loads(path.read_text(encoding="utf-8"))
        assert len(case["bars"]) <= 40
        assert all(stamp(b["completed_at"]) <= stamp(case["cutoff"]) for b in case["bars"])
    return {
        "status": "PASS",
        "checked_at": datetime.now(UTC),
        "cutoff_rows": len(all_rows),
        "case_count": len(case_paths),
        "input_time_census": all_rows,
        "structural_distributions": frame_summaries,
        "qualification": (
            "Unknown historical evidence retained; OBSERVATIONAL only; no synthesized prices"
        ),
        "data_identity": canonical({tf: len(d.bars) for tf, d in datasets.items()}),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_new(args.output, audit(Path.cwd(), args.data_dir, args.calendar, args.study))
