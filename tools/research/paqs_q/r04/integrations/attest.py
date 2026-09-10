"""Explicit read-only Capture reconstruction; no application startup or provider requests."""

import argparse
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...integrations.local_archive import load_capture, normalize_capture
from ...types import canonical, digest
from ..study import write_new
from .local import load


def attest(root: Path, database: Path, data_dir: Path, calendar: Path) -> dict[str, Any]:
    original, _, _ = load(root, data_dir, calendar)
    capture, batches = load_capture(database, "2babba19-e0ce-4bfa-aab9-93061a95818c")
    normalized = normalize_capture(capture, batches)
    records = {}
    for data in normalized:
        assert canonical(data) == canonical(original[data.timeframe]), data.timeframe
        records[data.timeframe] = {
            "canonical_dataset_equal": True,
            "bars": len(data.bars),
            "dataset_hash": digest("r04-normalized-dataset", data),
            "complete_derived_rows": sum(b.coverage == "COMPLETE" for b in data.bars),
            "provenance": dict(data.provenance),
        }
    return {
        "read_policy": "existing loader: SQLite mode=ro, query_only=ON, BEGIN snapshot",
        "database_path": str(database),
        "whole_database_hash_claim": None,
        "capture_id": capture["capture_id"],
        "datasets": records,
        "raw_memberships": {
            tf: {
                "count": len(rows),
                "ordered_version_hash": digest(
                    "r04-raw-membership", tuple(r["version_hash"] for r in rows)
                ),
            }
            for tf, rows in batches.items()
        },
        "accepted_helper_sha256": {
            str(p): sha256((root / p).read_bytes()).hexdigest()
            for p in (
                Path("tools/research/paqs_q/integrations/local_archive.py"),
                Path("src/ai_infra_quant/core/domain/paqs_input.py"),
            )
        },
        "boundary": (
            "Derived completeness is relative to captured schedule. "
            "R04 rejects unknown dates. No full archive or historical availability claim."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_new(args.output, attest(Path.cwd(), args.database, args.data_dir, args.calendar))
