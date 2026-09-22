"""Self-contained offline HTML; decimal strings remain exact in the embedded/exported JSON."""

from html import escape
from pathlib import Path
from typing import Any

from ai_infra_quant.core.domain.paqs_q.canonical import canonical
from ai_infra_quant.core.domain.paqs_q.inputs import QInput


def write_report(
    path: Path,
    data: QInput,
    summary: dict[str, Any],
    context: dict[str, Any],
    events: dict[str, Any],
) -> None:
    payload = {
        "summary": summary,
        "bars": [b.payload() for b in data.bars],
        "context": context,
        "events": events,
    }
    # Escape script delimiters, including input-controlled metadata. No external requests.
    encoded = canonical(payload).decode("utf-8").replace("<", "\\u003c").replace("&", "\\u0026")
    html = TEMPLATE.replace("__TITLE__", escape(f"{data.security} · {data.timeframe} · Event v1"))
    path.write_text(html.replace("__PAYLOAD__", encoded), encoding="utf-8", newline="\n")


TEMPLATE = Path(__file__).with_name("report.html").read_text(encoding="utf-8")
