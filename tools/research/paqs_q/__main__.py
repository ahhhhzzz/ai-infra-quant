"""Explicit local CLI. No provider initialization or product write operations."""

import argparse
import json
import platform
import statistics
import time
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Any

from .diagnostics import audit
from .engine import evaluate
from .fixtures import synthetic
from .io import read_dataset, write_dataset
from .types import Parameters, canonical


def benchmark(repeats: int = 10) -> dict[str, Any]:
    if not 3 <= repeats <= 100:
        raise ValueError("BENCHMARK_REPEATS_BOUND")
    cases = []
    for tf in ("W1", "D1", "M30"):
        params = Parameters.default(tf)
        data = synthetic(tf, params.total)
        durations = []
        peaks = []
        result = evaluate(data, data.bars[-1].completed_at)
        for _ in range(repeats):
            tracemalloc.start()
            start = time.perf_counter_ns()
            result = evaluate(data, data.bars[-1].completed_at)
            durations.append((time.perf_counter_ns() - start) / 1_000_000)
            peaks.append(tracemalloc.get_traced_memory()[1])
            tracemalloc.stop()
        durations.sort()
        doc = result.document()
        cases.append(
            {
                "timeframe": tf,
                "bars": params.total,
                "repeats": repeats,
                "fixture": "SYNTHETIC triangular period 24, no return optimization",
                "p50_ms": str(statistics.median(durations)),
                "p95_ms_nearest_rank": str(durations[(95 * repeats + 99) // 100 - 1]),
                "tracemalloc_peak_bytes": max(peaks),
                "pivot_count": len(doc["diagnostics"]["all_pivots"]),
                "zone_candidates": len(doc["diagnostics"]["zones"]),
                "comparisons": doc["diagnostics"]["comparison_counts"],
            }
        )
    return {
        "hardware": platform.processor(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "timing_includes_tracemalloc": True,
        "scope": "full bounded evaluate including canonical serialization and hashing",
        "complexity": (
            "ATR/pivots O(N); complete-link O(P^2); repeated merge worst O(P^3); "
            "range O(Z^2*(L+P)); no unbounded calculation history"
        ),
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    example = sub.add_parser("example")
    example.add_argument("--timeframe", choices=("W1", "D1", "M30"), default="D1")
    example.add_argument("--pattern", default="oscillation")
    example.add_argument("--count", type=int, default=440)
    example.add_argument("--output", type=Path, required=True)
    for name in ("analyze", "audit"):
        command = sub.add_parser(name)
        command.add_argument("input", type=Path)
        command.add_argument("--cutoff", required=True)
        command.add_argument("--output", type=Path, required=True)
    archive = sub.add_parser("archive")
    archive.add_argument("--database", type=Path, required=True)
    archive.add_argument("--capture", required=True)
    archive.add_argument("--output-dir", type=Path, required=True)
    bench = sub.add_parser("benchmark")
    bench.add_argument("--repeats", type=int, default=10)
    bench.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "example":
            write_dataset(args.output, synthetic(args.timeframe, args.count, args.pattern))
            return
        if args.command == "archive":
            from .integrations.local_archive import read_archive

            for data in read_archive(args.database, args.capture):
                write_dataset(args.output_dir / f"{data.security}.{data.timeframe}.json", data)
            return
        if args.command == "benchmark":
            result = benchmark(args.repeats)
        else:
            data = read_dataset(args.input)
            cutoff = datetime.fromisoformat(args.cutoff)
            result = (
                evaluate(data, cutoff).document()
                if args.command == "analyze"
                else audit(data, ceiling=cutoff)
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(canonical(result) + "\n", encoding="utf-8")
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.exit(
            2, json.dumps({"status": "INVALID_INPUT", "error_type": type(exc).__name__}) + "\n"
        )


if __name__ == "__main__":
    main()
