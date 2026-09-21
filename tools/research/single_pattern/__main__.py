"""Windows: python -m tools.research.single_pattern --demo --output data/demo."""

import argparse
import json
import sys
from dataclasses import fields
from pathlib import Path

# Resolve this checkout's source, not a different editable checkout of the product.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from .integrations.local import demo, load
from .model import Config
from .report import run, write_report


def main() -> None:
    parser = argparse.ArgumentParser(description="PAQS-Q D1 单形态探索性回放;无网络/账户/订单")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--input", type=Path)
    inputs.add_argument("--demo", action="store_true")
    parser.add_argument("--calendar", type=Path)
    parser.add_argument("--timezone", default="America/New_York")
    parser.add_argument("--currency", choices=("USD", "HKD"), default="USD")
    parser.add_argument("--output", type=Path, required=True)
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
        if args.demo:
            if args.calendar:
                raise ValueError("DEMO_HAS_ITS_OWN_CALENDAR")
            source, calendar = demo(args.output.with_name(args.output.name + "-input"))
        else:
            source, calendar = args.input, args.calendar
            if calendar is None:
                raise ValueError("EXPLICIT_CALENDAR_REQUIRED")
        data = load(source, calendar, args.timezone, args.currency)
        result = run(data, config)
        write_report(result, args.output)
        print(
            json.dumps(
                {
                    "data": result["metadata"]["data_kind"],
                    "summary": result["summary"],
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
