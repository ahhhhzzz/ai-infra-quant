from fastapi import APIRouter

from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.portfolio import PortfolioRead
from ai_infra_quant.core.domain.money import decimal_string

router = APIRouter()


@router.get("/portfolio", response_model=PortfolioRead)
def get_portfolio(container: ContainerDep) -> PortfolioRead:
    view = container.portfolio_queries.portfolio()
    portfolio = view.portfolio
    snapshot = view.snapshot
    return PortfolioRead(
        id=portfolio.id,
        name=portfolio.name,
        base_currency=portfolio.base_currency,
        inception_date=portfolio.inception_date.isoformat(),
        valuation_timezone=portfolio.valuation_timezone,
        valuation_at=snapshot.valuation_at.isoformat().replace("+00:00", "Z"),
        total_equity=decimal_string(snapshot.total_equity),
        cash_value=decimal_string(snapshot.cash_value),
        market_value=decimal_string(snapshot.market_value),
        cost_basis=decimal_string(snapshot.cost_basis),
        realized_pnl=decimal_string(snapshot.realized_pnl),
        unrealized_pnl=decimal_string(snapshot.unrealized_pnl),
        fees=decimal_string(snapshot.fees),
        taxes=decimal_string(snapshot.taxes),
        equity_pnl=decimal_string(snapshot.equity_pnl),
        fx_pnl=decimal_string(snapshot.fx_pnl),
        units_outstanding=decimal_string(snapshot.units_outstanding),
        nav=decimal_string(snapshot.nav),
        cash_ratio=decimal_string(snapshot.cash_ratio),
        invested_ratio=decimal_string(snapshot.invested_ratio),
        quality_status=snapshot.quality_status,
        missing_data=[],
        capabilities={key: status.value for key, status in view.capabilities.items()},
    )
