"""Explicit provider-symbol mapping for the approved PoC securities."""

from ai_infra_quant.core.domain.market_data import MarketDataSecurity

POC_SECURITIES = (
    MarketDataSecurity("US", "AVGO", "USD", "America/New_York"),
    MarketDataSecurity("US", "VRT", "USD", "America/New_York"),
    MarketDataSecurity("HK", "09698", "HKD", "Asia/Hong_Kong"),
)

_FUTU_CODES = {security.display_symbol: security.display_symbol for security in POC_SECURITIES}


def futu_code_for(security: MarketDataSecurity) -> str:
    """Return the explicitly approved Futu code for a canonical security."""
    try:
        return _FUTU_CODES[security.display_symbol]
    except KeyError as exc:
        raise ValueError(f"unsupported Futu PoC security: {security.display_symbol}") from exc
