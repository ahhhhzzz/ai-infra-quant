"""Windows: python -m tools.research.single_pattern --demo --output data/demo."""

import argparse
import json
import sys
from dataclasses import fields
from decimal import Decimal
from pathlib import Path

# Resolve this checkout's source, not a different editable checkout of the product.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from .comparison import compare, write_comparison
from .integrations.local import demo, load
from .model import Config
from .report import run, write_report
from .sizing import SizingConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="PAQS-Q D1 单形态探索性回放;无网络/账户/订单")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--input", type=Path)
    inputs.add_argument("--demo", action="store_true")
    parser.add_argument("--calendar", type=Path)
    parser.add_argument("--timezone", default="America/New_York")
    parser.add_argument("--currency", choices=("USD", "HKD"), default="USD")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sizing-mode", choices=("cash", "fixed-risk", "compare"), default="cash")
    parser.add_argument("--risk-fraction", type=Decimal, default=None)
    defaults = Config()
    for field in fields(defaults):
        value = getattr(defaults, field.name)
        parser.add_argument(
            "--" + field.name.replace("_", "-"),
            type=type(value),
            default=value,
            help=f"default: {value}; see docs/PAQS_Q_SINGLE_PATTERN.md",
        )
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("OUTPUT_ALREADY_EXISTS:choose a new directory")
        config = Config(**{field.name: getattr(args, field.name) for field in fields(defaults)})
        if args.sizing_mode == "cash" and args.risk_fraction is not None:
            raise ValueError("RISK_FRACTION_REQUIRES_FIXED_RISK_OR_COMPARE")
        risk_fraction = args.risk_fraction if args.risk_fraction is not None else Decimal("0.01")
        sizing = SizingConfig("fixed-risk", risk_fraction)
        if args.demo:
            if args.calendar:
                raise ValueError("DEMO_HAS_ITS_OWN_CALENDAR")
            source, calendar = demo(args.output.with_name(args.output.name + "-input"))
        else:
            source, calendar = args.input, args.calendar
            if calendar is None:
                raise ValueError("EXPLICIT_CALENDAR_REQUIRED")
        data = load(source, calendar, args.timezone, args.currency)
        if args.sizing_mode == "compare":
            result = compare(data, config, risk_fraction)
            write_comparison(result, args.output)
            summary = {name: value["summary"] for name, value in result["modes"].items()}
        else:
            result = run(data, config, sizing=sizing if args.sizing_mode == "fixed-risk" else None)
            write_report(result, args.output)
            summary = result["summary"]
        print(
            json.dumps(
                {
                    "data": result["metadata"]["data_kind"],
                    "summary": summary,
                    "signals": len(result["strategy"]["signals"]),
                    "report": str((args.output / "report.html").resolve()),
                },
                ensure_ascii=True,
            )
        )
    except (ValueError, KeyError, TypeError, OSError, ArithmeticError) as exc:
        parser.exit(2, f"Research input/run rejected: {exc}\n")


if __name__ == "__main__":
    main()
