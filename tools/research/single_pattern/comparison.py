"""Two preselected sizing modes over identical inputs and v1 signal config."""

import csv
import json
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined

from tools.research.paqs_q.types import CONTEXT

from .model import Config, Input
from .report import run
from .sizing import SizingConfig

SIMULATION_KEYS = (
    "trades",
    "decisions",
    "equity",
    "open_position",
    "pending_signal",
    "summary",
    "sizing",
)
FILL_KEYS = (
    "signal_time",
    "signal_index",
    "entry_index",
    "entry_time",
    "entry_price",
    "stop",
    "target",
    "exit_index",
    "exit_time",
    "exit_bar_start",
    "exit_bar_end",
    "exit_phase",
    "exit_price",
    "exit_reason",
)


def positions(mode: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        *mode["trades"],
        *([mode["open_position"]] if mode["open_position"] is not None else []),
    ]


def compare(source: Input, config: Config, risk_fraction: Decimal) -> dict[str, Any]:
    # No setting is added to Config: its exact old preimage remains signal identity authority.
    cash = run(source, config, sizing=SizingConfig("cash", risk_fraction))
    risk = run(source, config, sizing=SizingConfig("fixed-risk", risk_fraction))
    if cash["strategy"] != risk["strategy"]:
        raise ValueError("COMPARISON_SIGNAL_MISMATCH")
    left = {p["signal_id"]: p for p in positions(cash)}
    right = {p["signal_id"]: p for p in positions(risk)}
    common = sorted(left.keys() & right.keys())
    for key in common:
        if any(left[key].get(field) != right[key].get(field) for field in FILL_KEYS):
            raise ValueError("COMPARISON_EXECUTION_MISMATCH")
    if any(
        a["buy_hold"] != b["buy_hold"] for a, b in zip(cash["equity"], risk["equity"], strict=True)
    ):
        raise ValueError("COMPARISON_BENCHMARK_MISMATCH")
    return {
        **{k: v for k, v in cash.items() if k not in SIMULATION_KEYS},
        "schema": "single-pattern-sizing-comparison-v1",
        "modes": {
            "cash": {k: cash[k] for k in SIMULATION_KEYS},
            "fixed-risk": {k: risk[k] for k in SIMULATION_KEYS},
        },
        "comparison": {
            "signals_equal": True,
            "common_fill_terms_equal": True,
            "common_entries": len(common),
            "cash_only": sorted(left.keys() - right.keys()),
            "fixed_risk_only": sorted(right.keys() - left.keys()),
            "benchmark_equal": True,
            "risk_fraction": str(risk_fraction),
        },
    }


def display(value: Any, percent: bool = False) -> str:
    if value is None:
        return "不适用"
    with localcontext(CONTEXT):
        number = Decimal(str(value)) * (100 if percent else 1)
        return format(number, ",.2f") + ("%" if percent else "")


def write_comparison(result: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    trade_rows: list[dict[str, Any]] = []
    equity_rows: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for name, mode in result["modes"].items():
        trade_rows.extend(
            {"mode": name, "status": "CLOSED" if "exit_index" in row else "OPEN", **row}
            for row in positions(mode)
        )
        equity_rows.extend({"mode": name, **row} for row in mode["equity"])
        decisions.extend({"mode": name, **row} for row in mode["decisions"])
        summaries.append({"mode": name, **mode["summary"]})
    for name, rows in (
        ("trades", trade_rows),
        ("equity", equity_rows),
        ("decisions", decisions),
        ("summary", summaries),
        ("signals", result["strategy"]["signals"]),
    ):
        fields = list(dict.fromkeys(key for row in rows for key in row)) or ["status"]
        with (directory / f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        k: json.dumps(v, ensure_ascii=False) if isinstance(v, list | dict) else v
                        for k, v in row.items()
                    }
                )
    env = Environment(autoescape=True, undefined=StrictUndefined)
    env.filters["amount"] = display
    env.filters["percent"] = lambda value: display(value, True)
    template = env.from_string(
        Path(__file__).with_name("comparison.html").read_text(encoding="utf-8")
    )
    payload = (
        json.dumps(result, ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    (directory / "report.html").write_text(
        template.render(result=result, payload=payload, positions=positions), encoding="utf-8"
    )
