"""One-time pre-port extraction; only pinned evidence supplies expected outputs.

Run with the repository root and the already frozen offline price-export directory.
This is not an evaluator and imports neither research nor production algorithms.
"""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

BASE = "857823a0dc39b4c10a1986c575bcbcd9dda11c85"
R05 = "7487cf57161a834d9100f983bab9d8534a1c0488"
FIELDS = (
    "security",
    "timeframe",
    "start",
    "end",
    "completed_at",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "completed",
    "coverage",
    "adjustment",
    "session",
)


def digest(tag: str, value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((tag + "\0" + encoded).encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--frozen-prices", type=Path, required=True)
    args = parser.parse_args()
    root: Path = args.root.resolve()
    sources: dict[str, str] = {}

    def read(path: str) -> Any:
        data = subprocess.check_output(
            ["git", "-c", f"safe.directory={root.as_posix()}", "show", R05 + ":" + path],
            cwd=root,
        )
        sources[path] = hashlib.sha256(data).hexdigest()
        return json.loads(data)

    prefix = "docs/evidence/TASK_006B_Q/research-05/"
    manifest = read(prefix + "baseline-study/source-calendar-manifest.json")
    vectors = []
    case_count = 0
    for tf in ("W1", "D1", "M30"):
        name = f"US.AVGO.{tf}.json"
        raw = (args.frozen_prices / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == manifest["sources"]["price_hashes"][name]
        data = json.loads(raw)["dataset"]
        bars = {digest("qstr-bar", [b[k] for k in FIELDS]): b for b in data["bars"]}
        cases = [
            read(p.relative_to(root).as_posix())
            for p in sorted((root / prefix / "cases").glob(tf + ".*.json"))
        ]
        case_count += len(cases)
        cutoffs = {c["cutoff"] for c in cases}
        obs = read(prefix + f"frames/{tf}.OBSERVATIONAL.json")
        insufficient = next((r["cutoff"] for r in obs["rows"] if r["status"] != "VALID"), None)
        if insufficient:
            cutoffs.add(insufficient)
        for mode in ("OBSERVATIONAL", "AS_OF"):
            frame = obs if mode == "OBSERVATIONAL" else read(prefix + f"frames/{tf}.{mode}.json")
            for row in frame["rows"]:
                if row["cutoff"] not in cutoffs:
                    continue
                observed = next(r for r in obs["rows"] if r["cutoff"] == row["cutoff"])["B0"]
                price_rows = [bars[ref] for ref in observed["price_refs"]]
                calendar = obs["calendar_catalog"][observed["calendar_view_id"]]
                facts = [manifest["calendar_catalog"][ref] for _, ref in sorted(calendar.items())]
                expected = {}
                for arm in ("B0", "A1"):
                    packed = row[arm]
                    census = [
                        dict(
                            frame["census_catalog"][key],
                            index=i,
                            active=i >= packed["active_start"],
                        )
                        for i, key in enumerate(packed["census_ids"])
                    ]
                    expected[arm] = {
                        k: packed[k]
                        for k in (
                            "rule",
                            "security",
                            "timeframe",
                            "cutoff",
                            "mode",
                            "quality",
                            "status",
                            "reason",
                            "strict_confirmation",
                            "window_hash",
                            "calendar_hash",
                        )
                    }
                    expected[arm].update(
                        events=packed["events"], census=census, costs=packed["metrics"]["costs"]
                    )
                    if mode == "OBSERVATIONAL":
                        for case in cases:
                            if case["cutoff"] == row["cutoff"]:
                                left = case["first_window_index"]
                                right = left + len(case["bars"])
                                assert price_rows[left:right] == case["bars"]
                                assert census[left:right] == case["census_" + arm]
                                assert [
                                    e for e in packed["events"] if left <= e["index"] < right
                                ] == case["events_" + arm]
                vectors.append(
                    {
                        "name": tf + "." + mode + "." + row["cutoff"],
                        "input": {
                            "security": data["security"],
                            "timeframe": tf,
                            "market_timezone": data["market_timezone"],
                            "quality": data["quality"],
                            "mode": mode,
                            "as_of": row["cutoff"],
                            "bars": price_rows,
                            "calendar": facts,
                        },
                        "expected": expected,
                    }
                )
    output = root / "tests/paqs_q/golden/r05.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "paqs-q-f1-golden-v1",
        "baseline": BASE,
        "research_head": R05,
        "source_sha256": sources,
        "frozen_price_sha256": manifest["sources"]["price_hashes"],
        "cases_verified": case_count,
        "vectors": vectors,
    }
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        stream.write("\n")
    print(
        f"Frozen {len(vectors)} vectors / {case_count} cases: "
        f"{hashlib.sha256(output.read_bytes()).hexdigest()}"
    )


if __name__ == "__main__":
    main()
