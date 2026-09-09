"""Local UTF-8 fixture wire format; numeric price strings only."""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from .types import Bar, Dataset, canonical


def write_dataset(path: Path, data: Dataset) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        canonical({"schema": "qstr-observations-v1", "dataset": data}) + "\n", encoding="utf-8"
    )


def read_dataset(path: Path) -> Dataset:
    if path.stat().st_size > 100_000_000:
        raise ValueError("INPUT_FILE_BOUND")
    envelope = json.loads(path.read_text(encoding="utf-8"))
    if envelope["schema"] != "qstr-observations-v1":
        raise ValueError("INPUT_SCHEMA")
    data = dict(envelope["dataset"])
    parsed = []
    for raw in data.pop("bars"):
        bar: dict[str, Any] = dict(raw)
        for field in ("open", "high", "low", "close", "volume"):
            if not isinstance(bar[field], str) or len(bar[field]) > 64:
                raise ValueError("FINANCIAL_FIELD_REQUIRES_DECIMAL_TEXT")
            bar[field] = Decimal(bar[field])
        for field in ("start", "end", "completed_at", "available_at", "retrieved_at"):
            bar[field] = datetime.fromisoformat(bar[field]) if bar[field] is not None else None
        parsed.append(Bar(**bar))
    data["provenance"] = tuple(tuple(pair) for pair in data.get("provenance", ()))
    return Dataset(bars=tuple(parsed), **data)
