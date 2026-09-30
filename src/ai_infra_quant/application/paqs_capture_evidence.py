"""Retain the canonical acquisition, without claiming historical availability."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from ai_infra_quant.core.domain.market_data import MinuteBar
from ai_infra_quant.core.domain.paqs_input import PaqsInputBundle


@dataclass(frozen=True, slots=True)
class CapturedPaqsInputBundle(PaqsInputBundle):
    source_minute_bars: tuple[MinuteBar, ...]
    daily_retrieved_at: datetime
    minute_retrieved_at: datetime
    minute_window_start: datetime


def capture_payload(source: PaqsInputBundle) -> dict[str, Any]:
    payload = asdict(source)
    for day in payload["calendar"]["trading_days"]:
        for segment in day["session_segments"]:
            segment["start"] = segment["start"].isoformat()
            segment["end"] = segment["end"].isoformat()
    return payload
