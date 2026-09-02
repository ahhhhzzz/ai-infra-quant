"""Canonical Futu symbols for the supported US/HK equity market-data scope."""

from ai_infra_quant.core.domain.market_data import MarketDataSecurity

POC_SECURITIES = (
    MarketDataSecurity("US", "AVGO", "USD", "America/New_York"),
    MarketDataSecurity("US", "VRT", "USD", "America/New_York"),
    MarketDataSecurity("HK", "09698", "HKD", "Asia/Hong_Kong"),
)


def futu_code_for(security: MarketDataSecurity) -> str:
    """Return the provider code without assuming that a quote is available."""
    expected = {
        "US": ("USD", "America/New_York"),
        "HK": ("HKD", "Asia/Hong_Kong"),
    }.get(security.market)
    if expected is None:
        raise ValueError(f"unsupported Futu equity market: {security.market}")
    if (security.currency, security.market_timezone) != expected:
        raise ValueError(f"incompatible Futu security metadata: {security.display_symbol}")
    return security.display_symbol
