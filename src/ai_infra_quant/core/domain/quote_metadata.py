"""Optional display metadata; the frozen strategy quote contract stays unchanged."""

from dataclasses import dataclass

from ai_infra_quant.core.domain.market_data import QuoteSnapshot


@dataclass(frozen=True, slots=True)
class NamedQuoteSnapshot(QuoteSnapshot):
    display_name: str | None = None
