"""Bounded, current schedule evidence; never a historical calendar certification.

Separate extensions preserve the accepted core domain/artifact identities. Only a
provider that guarantees an exhaustive schedule for the requested range may
return ScheduledTradingDays. Missing OHLC rows are not calendar evidence.
"""

from dataclasses import dataclass
from datetime import date

from ai_infra_quant.core.domain.market_data import ProviderResult, TradingDay
from ai_infra_quant.core.domain.paqs_input import CalendarMetadata


@dataclass(frozen=True, slots=True, kw_only=True)
class ScheduledTradingDays(ProviderResult[tuple[TradingDay, ...]]):
    coverage_start: date
    coverage_end: date
    schedule_basis: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ScheduledCalendarMetadata(CalendarMetadata):
    coverage_start: date
    coverage_end: date
    schedule_basis: str
