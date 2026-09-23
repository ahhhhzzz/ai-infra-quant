"""Windows/local offline entry: python -m tools.research.setup_risk --demo all --output PATH."""

import argparse
import json
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

from ai_infra_quant.application.paqs_q_event_artifacts import load_event_registry
from ai_infra_quant.application.paqs_q_setup_artifacts import run as run_setup
from ai_infra_quant.core.domain.paqs_q.canonical import canonical
from ai_infra_quant.core.domain.paqs_q.inputs import QInput
from ai_infra_quant.core.domain.paqs_q.setup_reference import EntryReference, MultiInput
from ai_infra_quant.core.strategy.paqs_q.event_context import CONTEXT_ID, EVENT_ID
from tools.research.event_engine.data import read_input

from .demo import demo_bundle
from .report import write_report

ROOT = Path(__file__).resolve().parents[3]


def _period(registry: Any, data: QInput | None, source: Path | None) -> dict[str, Any]:
    if data is None:
        return {
            "context_status": "MISSING",
            "event_status": "MISSING",
            "reasons": ["INPUT_MISSING"],
        }
    structure = registry.structure(data, CONTEXT_ID, "1.0.1")
    event = registry.event(data, structure, EVENT_ID, "1.0.1")
    summary = event.document()["evidence"] if event.status == "AVAILABLE" else None
    return {
        "bars": len(data.bars),
        "quality": data.quality,
        "mode": data.mode,
        "adjustment": sorted({b.adjustment for b in data.bars}),
        "as_of": data.as_of,
        "first_completed_at": data.bars[0].completed_at if data.bars else None,
        "last_completed_at": data.bars[-1].completed_at if data.bars else None,
        "unknown_bar_availability": sum(b.available_at is None for b in data.bars),
        "unknown_calendar_availability": sum(f.available_at is None for f in data.calendar),
        "input_hash": data.input_hash,
        "source_sha256": sha256(source.read_bytes()).hexdigest() if source else None,
        "context_status": structure.status,
        "event_status": event.status,
        "context_hash": structure.canonical_result_hash,
        "event_hash": event.canonical_result_hash,
        "regime": summary["regime"] if summary else None,
        "readiness": summary["readiness"] if summary else None,
        "reasons": [*structure.document()["reason_codes"], *event.document()["reason_codes"]],
        "provenance": data.provenance.document(),
    }


def write_bundle(
    bundle: MultiInput,
    output: Path,
    *,
    sources: dict[str, Path] | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("OUTPUT_MUST_BE_NEW_DIRECTORY")
    result = run_setup(bundle, root)
    registry = load_event_registry(root)
    periods = {}
    bars = {}
    for name, data in (("W1", bundle.w1), ("D1", bundle.d1), ("M30", bundle.m30)):
        selected = data
        if name == "W1" and data is not None and data.bars and not data.bars[-1].completed:
            selected = replace(data, bars=data.bars[:-1])
        periods[name] = _period(registry, selected, (sources or {}).get(name))
        periods[name]["excluded_partial_tail"] = (
            len(data.bars) - len(selected.bars) if data is not None and selected is not None else 0
        )
        bars[name] = [b.payload() for b in selected.bars] if selected is not None else []
    payload = {
        "schema_version": "paqs-q-setup-offline-report-v1",
        "run": result.model_dump(),
        "result_hash": result.canonical_result_hash,
        "periods": periods,
        "bars": bars,
        "entry_reference_count": len(bundle.entry_references),
        "limitations": [
            "QUALIFICATION_ONLY_NO_ORDERS_FILLS_POSITIONS_OR_PNL",
            "STRUCTURAL_RR_NOT_GUARANTEED_REALIZED_LOSS",
            *(("EXPLORATORY_NOT_POINT_IN_TIME",) if result.mode == "OBSERVATIONAL" else ()),
        ],
    }
    output.mkdir(parents=True)
    (output / "result.json").write_bytes(canonical(payload) + b"\n")
    write_report(output / "report.html", payload)
    return {
        "status": result.status,
        "reasons": result.reasons,
        "result_hash": result.canonical_result_hash,
        "facts": len(result.facts),
        "long_ready": sum(f.status == "LONG_READY" for f in result.facts),
        "observational_qualified": sum(
            f.status == "OBSERVATIONAL_LONG_QUALIFIED" for f in result.facts
        ),
        "report": str((output / "report.html").resolve()),
    }


def _references(path: Path | None) -> tuple[EntryReference, ...]:
    if path is None:
        return ()
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, list):
        raise ValueError("ENTRY_REFERENCES_MUST_BE_ARRAY")
    return tuple(
        EntryReference(
            Decimal(row["price"]),
            datetime.fromisoformat(row["price_at"]),
            datetime.fromisoformat(row["available_at"]),
            row["source"],
            row["source_ref"],
            row["adjustment"],
            row["security"],
        )
        for row in raw
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", choices=("all", "right", "range", "trend"))
    parser.add_argument("--w1", type=Path)
    parser.add_argument("--d1", type=Path)
    parser.add_argument("--m30", type=Path)
    parser.add_argument("--calendar", type=Path)
    parser.add_argument("--entry-references", type=Path)
    parser.add_argument("--mode", choices=("AS_OF", "OBSERVATIONAL"), default="AS_OF")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.demo:
            if any((args.w1, args.d1, args.m30, args.calendar, args.entry_references)):
                raise ValueError("DEMO_AND_REAL_INPUTS_ARE_EXCLUSIVE")
            choices = ("right", "range", "trend") if args.demo == "all" else (args.demo,)
            if args.output.exists():
                raise ValueError("OUTPUT_MUST_BE_NEW_DIRECTORY")
            summaries = {}
            for name in choices:
                if name == "right":
                    bundle = demo_bundle()
                elif name == "range":
                    bundle = demo_bundle(
                        daily_count=81, weekly_history=80, offset=Decimal("0"), range_failure=True
                    )
                else:
                    bundle = demo_bundle(
                        daily_count=68,
                        weekly_history=101,
                        offset=Decimal("-5.5"),
                        trend_pullback=True,
                    )
                if args.mode == "OBSERVATIONAL":
                    assert bundle.w1 is not None and bundle.d1 is not None
                    assert bundle.m30 is not None
                    bundle = MultiInput(
                        replace(bundle.w1, mode="OBSERVATIONAL"),
                        replace(bundle.d1, mode="OBSERVATIONAL"),
                        replace(bundle.m30, mode="OBSERVATIONAL"),
                        bundle.entry_references,
                    )
                summaries[name] = write_bundle(bundle, args.output / name)
            links = "".join(
                f'<li><a href="{name}/report.html">{name}</a> — {value["status"]}, '
                f"{value['long_ready']} LONG_READY</li>"
                for name, value in summaries.items()
            )
            (args.output / "index.html").write_text(
                '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
                "<title>PAQS-Q Setup 合成演示</title>"
                "<body><h1>合成三周期 OHLC 演示 · 非市场结果</h1><ul>"
                + links
                + "</ul></body></html>",
                encoding="utf-8",
                newline="\n",
            )
            print(canonical(summaries).decode("utf-8"))
            print(f"Index: {(args.output / 'index.html').resolve()}")
            if any(value["status"] != "AVAILABLE" for value in summaries.values()):
                parser.exit(2, "One or more synthetic inputs did not qualify.\n")
        else:
            if not any((args.w1, args.d1, args.m30)):
                raise ValueError("AT_LEAST_ONE_PERIOD_INPUT_REQUIRED")
            sources = {k: p for k, p in (("W1", args.w1), ("D1", args.d1), ("M30", args.m30)) if p}
            values = {k: read_input(p, args.calendar, args.mode) for k, p in sources.items()}
            bundle = MultiInput(
                values.get("W1"),
                values.get("D1"),
                values.get("M30"),
                _references(args.entry_references),
            )
            summary = write_bundle(bundle, args.output, sources=sources)
            print(canonical(summary).decode("utf-8"))
            if summary["status"] != "AVAILABLE":
                parser.exit(2, "Setup evidence insufficient/invalid; see report.\n")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Setup input/execution rejected: {exc}\n")


if __name__ == "__main__":
    main()
