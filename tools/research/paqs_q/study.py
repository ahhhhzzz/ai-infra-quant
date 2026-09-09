"""Reproduce the frozen local experiment; missing files remain missing universe members."""

import argparse
import json
from collections import Counter
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

from .__main__ import benchmark
from .diagnostics import audit, old_engine, structural
from .engine import evaluate
from .fixtures import synthetic
from .io import read_dataset
from .types import primitive


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(primitive(value), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def coverage(members: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for tf in ("W1", "D1", "M30"):
        for market in ("ALL", "US", "HK"):
            cohort = [m for m in members if market == "ALL" or m["market"] == market]
            found = [
                r
                for r in results
                if r["timeframe"] == tf and r["security"] in {m["security"] for m in cohort}
            ]
            rows.append(
                {
                    "timeframe": tf,
                    "market": market,
                    "denominator": len(cohort),
                    "valid_100": sum(r["cutoffs"] >= 100 for r in found),
                    "insufficient": sum(r["cutoffs"] < 100 for r in found),
                    "unavailable": len(cohort) - len(found),
                    "valid_cutoffs": sum(r["cutoffs"] for r in found),
                    "target_cutoffs": 100 * len(cohort),
                }
            )
    return {
        "real_market_gate": "INCOMPLETE"
        if any(r["valid_100"] < r["denominator"] for r in rows)
        else "REQUIRES_SEMANTIC_REVIEW",
        "denominators": rows,
    }


def boundary_case_lists(outliers: list[dict[str, Any]]) -> dict[str, list[str]]:
    """A review flag is not evidence that a case was caused only by the left boundary."""
    return {
        "material_left_only": [
            r["cutoff"]
            for r in outliers
            if r.get("classification") == "LEFT_ONLY" and r.get("material")
        ],
        "revision_confounded_cutoffs": [
            r["cutoff"] for r in outliers if r.get("classification") == "REVISION_CONFOUNDED"
        ],
    }


def run(data_dir: Path, output_dir: Path, manifest: Path) -> None:
    universe = json.loads(manifest.read_text(encoding="utf-8"))
    ceiling = datetime.fromisoformat(universe["cutoffs"]["not_after"])
    summaries = []
    file_hashes = {}
    unavailable = []
    for member in universe["members"]:
        for tf in ("W1", "D1", "M30"):
            filename = f"{member['security']}.{tf}.json"
            path = data_dir / filename
            if not path.is_file():
                unavailable.append(
                    {
                        "security": member["security"],
                        "timeframe": tf,
                        "reason": "NO_SUPPLIED_LOCAL_OBSERVATIONS",
                    }
                )
                continue
            data = read_dataset(path)
            if (data.security, data.timeframe) != (member["security"], tf):
                raise ValueError("MANIFEST_INPUT_IDENTITY_CONFLICT")
            result = audit(data, ceiling=ceiling)
            write(output_dir / f"{member['security']}.{tf}.diagnostics.json", result)
            file_hashes[filename] = sha256(path.read_bytes()).hexdigest()
            summary = {
                k: v for k, v in result.items() if k not in ("rows", "outliers", "provenance")
            }
            summary["boundary_classes"] = dict(
                Counter(r.get("boundary_class", "NO_ARM") for r in result["rows"])
            )
            summary["outlier_counts"] = dict(Counter(r["kind"] for r in result["outliers"]))
            summary.update(boundary_case_lists(result["outliers"]))
            summary["direct_directional_flips"] = [
                r["cutoff"] for r in result["outliers"] if r.get("direct_directional_flip")
            ]
            summary["old_new_regime_disagreements"] = sum(
                r.get("old_bounded_regime") != r["regime"] for r in result["rows"] if "regime" in r
            )
            summaries.append(summary)
            print(f"{data.security} {tf}: {result['cutoffs']}/100 eligible cutoffs", flush=True)
    write(
        output_dir / "coverage.json",
        {
            **coverage(universe["members"], summaries),
            "universe_sha256": sha256(manifest.read_bytes()).hexdigest(),
            "observation_file_hashes": file_hashes,
            "unavailable": unavailable,
            "available": summaries,
        },
    )
    cases = []
    for pattern in ("oscillation", "bull", "bear", "flat", "path_lock"):
        data = synthetic(pattern=pattern)
        current = evaluate(data, data.bars[-1].completed_at)
        cases.append(
            {
                "label": "SYNTHETIC",
                "pattern": pattern,
                "count": 440,
                "old_full": old_engine(data, data.bars),
                "old_bounded": old_engine(data, data.bars[-312:]),
                "new": structural(current),
                "new_hash": current.semantic_hash,
                "diagnostics": current.document()["diagnostics"],
            }
        )
    # Price relocation leaves historical confirmed levels; no new touch can renew them.
    data = synthetic(count=440)
    data = replace(
        data,
        bars=tuple(
            replace(
                b,
                open=b.open + Decimal(100),
                high=b.high + Decimal(100),
                low=b.low + Decimal(100),
                close=b.close + Decimal(100),
            )
            if i >= 250
            else b
            for i, b in enumerate(data.bars)
        ),
    )
    current = evaluate(data, data.bars[-1].completed_at)
    cases.append(
        {
            "label": "SYNTHETIC",
            "pattern": "relocation_plus_100_from_index_250",
            "old_full": old_engine(data, data.bars),
            "new": structural(current),
            "expired_new_candidates": current.document()["diagnostics"]["expired_zone_count"],
        }
    )
    write(output_dir / "synthetic-cases.json", cases)
    write(output_dir / "performance.json", benchmark())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--manifest", type=Path, default=Path("docs/evidence/TASK_006B_Q/universe.json")
    )
    args = parser.parse_args()
    run(args.data_dir, args.output_dir, args.manifest)


if __name__ == "__main__":
    main()
