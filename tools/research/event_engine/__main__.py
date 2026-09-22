"""Windows/local offline entry point: python -m tools.research.event_engine."""

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from ai_infra_quant.application.paqs_q_event_artifacts import load_event_registry
from ai_infra_quant.core.domain.paqs_q.canonical import canonical
from ai_infra_quant.core.domain.paqs_q.inputs import QInput
from ai_infra_quant.core.strategy.paqs_q.event_context import (
    CONTEXT_ID,
    EVENT_ID,
    VERSION,
    context_config,
)
from ai_infra_quant.core.strategy.paqs_q.event_rules import event_config

from .data import demo_input, read_input
from .report import write_report

ROOT = Path(__file__).resolve().parents[3]


def run(data: QInput, output: Path, *, root: Path = ROOT) -> dict[str, Any]:
    if output.exists():
        raise ValueError("OUTPUT_MUST_BE_NEW_DIRECTORY")
    registry = load_event_registry(root)
    structure = registry.structure(data, CONTEXT_ID, VERSION)
    events = registry.event(data, structure, EVENT_ID, VERSION)
    context_doc, event_doc = structure.document(), events.document()
    counts = Counter(
        r["record"]["event_type"] + "/" + r["record"]["evidence"]["status"]
        for r in event_doc["records"]
    )
    summary = {
        "schema_version": "paqs-q-event-run-v1",
        "security": data.security,
        "timeframe": data.timeframe,
        "mode": data.mode,
        "bars": len(data.bars),
        "strict_confirmation": data.mode == "AS_OF" and structure.status == "AVAILABLE",
        "input_hash": data.input_hash,
        "provenance": data.provenance.document(),
        "first_completed_at": data.bars[0].completed_at if data.bars else None,
        "last_completed_at": data.bars[-1].completed_at if data.bars else None,
        "context_status": structure.status,
        "event_status": events.status,
        "context_reasons": context_doc["reason_codes"],
        "event_reasons": event_doc["reason_codes"],
        "context_hash": structure.canonical_result_hash,
        "event_hash": events.canonical_result_hash,
        "context_code_hash": context_doc["code_hash"],
        "event_code_hash": event_doc["code_hash"],
        "context_config_hash": context_doc["config_hash"],
        "event_config_hash": event_doc["config_hash"],
        "context_parameters": context_config().values.document(),
        "event_parameters": event_config().values.document(),
        "counts": dict(sorted(counts.items())),
        "event_summary": event_doc["evidence"],
        "data_limitations": {
            "quality": data.quality,
            "adjustments": sorted({b.adjustment for b in data.bars}),
            "unknown_bar_availability": sum(b.available_at is None for b in data.bars),
            "unknown_calendar_availability": sum(f.available_at is None for f in data.calendar),
            "history": "FIXED_START",
            "trading_qualification": "NOT_IMPLEMENTED",
        },
    }
    output.mkdir(parents=True)
    for name, payload in (
        ("input.json", canonical(data.payload())),
        ("structure.json", structure.canonical_bytes),
        ("events.json", events.canonical_bytes),
        ("summary.json", canonical(summary)),
    ):
        (output / name).write_bytes(payload + b"\n")
    write_report(output / "report.html", data, summary, context_doc, event_doc)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--input", type=Path)
    inputs.add_argument(
        "--demo", action="store_true", help="labelled synthetic D1, not market data"
    )
    parser.add_argument("--calendar", type=Path)
    parser.add_argument("--mode", choices=("AS_OF", "OBSERVATIONAL"), default="AS_OF")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = (
            demo_input(mode=args.mode)
            if args.demo
            else read_input(args.input, args.calendar, args.mode)
        )
        summary = run(data, args.output)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Event input/execution rejected: {exc}\n")
    print(canonical(summary).decode("utf-8"))
    print(f"Report: {(args.output / 'report.html').resolve()}")
    if summary["context_status"] != "AVAILABLE" or summary["event_status"] != "AVAILABLE":
        parser.exit(
            2, "Evidence insufficient/invalid; inspect summary and report (no downgrade).\n"
        )


if __name__ == "__main__":
    main()
