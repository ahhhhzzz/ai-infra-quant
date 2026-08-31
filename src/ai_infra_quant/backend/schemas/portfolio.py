from ai_infra_quant.backend.schemas.common import DataValue, StrictSchema
from ai_infra_quant.core.domain.enums import SnapshotQualityStatus


class PortfolioRead(StrictSchema):
    id: str
    name: str
    base_currency: str
    inception_date: str
    valuation_timezone: str
    valuation_at: str
    total_equity: str
    cash_value: str
    market_value: str
    cost_basis: str
    realized_pnl: str
    unrealized_pnl: str
    fees: str
    taxes: str
    equity_pnl: str
    fx_pnl: str
    units_outstanding: str
    nav: str
    cash_ratio: str
    invested_ratio: str
    quality_status: SnapshotQualityStatus
    missing_data: list[str]
    capabilities: dict[str, str]


class PerformanceSummaryRead(StrictSchema):
    twr: str
    daily_return: DataValue
    weekly_return: DataValue
    monthly_return: DataValue
    since_inception_return: str
    maximum_drawdown: str
    benchmark_return: DataValue


class PerformancePointRead(StrictSchema):
    at: str
    nav: str
    twr_index: str
    quality_status: SnapshotQualityStatus


class PerformanceRead(StrictSchema):
    portfolio_id: str
    range: str
    frequency: str
    summary: PerformanceSummaryRead
    points: list[PerformancePointRead]
