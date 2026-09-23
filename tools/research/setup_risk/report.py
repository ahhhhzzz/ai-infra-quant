"""One self-contained HTML report; exact decimals live in the adjacent JSON export."""

from pathlib import Path
from typing import Any

from ai_infra_quant.core.domain.paqs_q.canonical import canonical


def write_report(path: Path, payload: dict[str, Any]) -> None:
    encoded = canonical(payload).decode("utf-8").replace("<", "\\u003c").replace("&", "\\u0026")
    template = Path(__file__).with_name("report.html").read_text(encoding="utf-8")
    path.write_text(template.replace("__PAYLOAD__", encoded), encoding="utf-8", newline="\n")
