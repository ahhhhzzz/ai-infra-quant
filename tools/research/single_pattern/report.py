"""Self-contained offline HTML and exact Decimal text exports."""

import csv
import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from jinja2 import Environment, StrictUndefined

from tools.research.paqs_q.types import canonical, primitive

from .model import STRATEGY, Config, Input
from .simulation import simulate
from .strategy import signals

ROOT = Path(__file__).resolve().parents[3]


def code_identity() -> dict[str, Any]:
    files = [*Path(__file__).parent.rglob("*.py"), Path(__file__).with_name("report.html")]
    files += [
        ROOT / path
        for path in (
            "tools/research/paqs_q/types.py",
            "tools/research/paqs_q/io.py",
            "src/ai_infra_quant/core/strategy/paqs_structure.py",
            "src/ai_infra_quant/resources/paqs_q/b0.json",
        )
    ]
    manifest = json.loads((ROOT / "src/ai_infra_quant/resources/paqs_q/b0.json").read_text())
    files.extend(ROOT / item["path"] for item in manifest["files"])
    hashes = {
        path.relative_to(ROOT).as_posix(): sha256(
            path.read_text(encoding="utf-8").encode()
        ).hexdigest()
        for path in sorted(set(files))
    }
    return {"files": hashes, "sha256": sha256(canonical(hashes).encode()).hexdigest()}


def run(source: Input, config: Config) -> dict[str, Any]:
    strategy = signals(source.data, config)
    simulation = simulate(source.data, strategy["signals"], config)
    return cast(
        dict[str, Any],
        primitive(
            {
                "schema": "single-pattern-research-v1",
                "strategy_id": STRATEGY,
                "security": source.data.security,
                "currency": source.currency,
                "timezone": source.data.market_timezone,
                "metadata": source.metadata,
                "config": asdict(config),
                "code": code_identity(),
                "bars": source.data.bars,
                "strategy": strategy,
                **simulation,
            }
        ),
    )


def write_report(result: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for name, rows in (
        ("trades", result["trades"]),
        ("signals", result["strategy"]["signals"]),
        ("equity", result["equity"]),
    ):
        fields = list(rows[0]) if rows else ["status"]
        with (directory / f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        key: json.dumps(value, ensure_ascii=False)
                        if isinstance(value, list | dict)
                        else value
                        for key, value in row.items()
                    }
                )
    env = Environment(autoescape=True, undefined=StrictUndefined)
    template = env.from_string(Path(__file__).with_name("report.html").read_text(encoding="utf-8"))
    # Escape HTML delimiters even inside application/json; user-supplied text stays inert.
    payload = (
        json.dumps(result, ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    (directory / "report.html").write_text(
        template.render(result=result, payload=payload), encoding="utf-8"
    )
