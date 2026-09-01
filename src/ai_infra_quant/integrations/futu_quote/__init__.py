"""Futu OpenD quote-only market-data proof of concept."""

from ai_infra_quant.integrations.futu_quote.adapter import FutuQuoteAdapter
from ai_infra_quant.integrations.futu_quote.symbols import POC_SECURITIES, futu_code_for

__all__ = ["POC_SECURITIES", "FutuQuoteAdapter", "futu_code_for"]
