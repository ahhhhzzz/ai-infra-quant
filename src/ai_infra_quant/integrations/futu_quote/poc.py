"""Local smoke runner for the approved quote-only Futu OpenD PoC."""

from __future__ import annotations

import json
import socket
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from ai_infra_quant.config import Settings
from ai_infra_quant.core.domain.market_data import ProviderResult
from ai_infra_quant.integrations.futu_quote.adapter import FutuQuoteAdapter
from ai_infra_quant.integrations.futu_quote.symbols import POC_SECURITIES


def opend_reachable(host: str, port: int, timeout_seconds: float = 1.0) -> tuple[bool, str | None]:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True, None
    except OSError as exc:
        return False, str(exc)


def run_live_poc(settings: Settings | None = None) -> dict[str, object]:
    settings = settings or Settings()
    reachable, reason = opend_reachable(settings.futu_opend_host, settings.futu_opend_port)
    if not reachable:
        return {
            "result": "LIVE_POC_BLOCKED",
            "provider": "futu_opend_quote",
            "endpoint": f"{settings.futu_opend_host}:{settings.futu_opend_port}",
            "reason": f"OpenD TCP endpoint is not reachable: {reason}",
            "securities": [security.display_symbol for security in POC_SECURITIES],
        }

    try:
        with FutuQuoteAdapter(settings.futu_opend_host, settings.futu_opend_port) as adapter:
            capability_status = adapter.provider_status()
            security_reports: dict[str, object] = {}
            statuses: list[str] = []
            for security in POC_SECURITIES:
                capabilities: dict[str, ProviderResult[Any]] = {
                    "latest": adapter.get_latest_quote(security),
                    "market_status": adapter.get_market_status(security),
                    "daily": adapter.get_daily_bars(security),
                    "1m": adapter.get_current_session_minute_bars(security),
                }
                statuses.extend(result.status.value for result in capabilities.values())
                security_reports[security.display_symbol] = capabilities
    except Exception as exc:
        return {
            "result": "LIVE_POC_BLOCKED",
            "provider": "futu_opend_quote",
            "endpoint": f"{settings.futu_opend_host}:{settings.futu_opend_port}",
            "reason": f"OpenD quote context could not be used: {str(exc)[:500]}",
            "securities": [security.display_symbol for security in POC_SECURITIES],
        }

    overall = (
        "LIVE_POC_AVAILABLE"
        if all(status == "AVAILABLE" for status in statuses)
        else "LIVE_POC_PARTIAL"
    )
    return {
        "result": overall,
        "provider": "futu_opend_quote",
        "endpoint": f"{settings.futu_opend_host}:{settings.futu_opend_port}",
        "provider_status": capability_status,
        "securities": security_reports,
    }


def _json_default(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"cannot serialize {type(value).__name__}")


def main() -> int:
    report = run_live_poc()
    print(json.dumps(report, default=_json_default, indent=2, sort_keys=True))
    return 2 if report["result"] == "LIVE_POC_BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
