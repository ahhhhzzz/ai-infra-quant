from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_infra_quant.core.domain.enums import SnapshotQualityStatus
from ai_infra_quant.core.domain.portfolio import Portfolio, PortfolioSnapshot
from ai_infra_quant.core.domain.strategy import StrategyDefinition
from ai_infra_quant.database.models.accounting import PortfolioSnapshotModel
from ai_infra_quant.database.models.portfolio import PortfolioModel
from ai_infra_quant.database.models.security import WatchlistModel
from ai_infra_quant.database.models.strategy import StrategyDefinitionModel


class SQLAlchemyPortfolioRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_default(self) -> tuple[Portfolio, PortfolioSnapshot] | None:
        portfolio_row = self._session.scalar(
            select(PortfolioModel)
            .join(WatchlistModel, WatchlistModel.portfolio_id == PortfolioModel.id)
            .where(PortfolioModel.status == "ACTIVE", WatchlistModel.is_default.is_(True))
        )
        if portfolio_row is None:
            return None
        snapshot_row = self._session.scalar(
            select(PortfolioSnapshotModel)
            .where(
                PortfolioSnapshotModel.portfolio_id == portfolio_row.id,
                PortfolioSnapshotModel.is_official.is_(True),
            )
            .order_by(PortfolioSnapshotModel.valuation_at.desc())
        )
        if snapshot_row is None:
            return None
        return (
            Portfolio(
                id=portfolio_row.id,
                name=portfolio_row.name,
                base_currency=portfolio_row.base_currency,
                inception_date=portfolio_row.inception_date,
                valuation_timezone=portfolio_row.valuation_timezone,
            ),
            PortfolioSnapshot(
                portfolio_id=portfolio_row.id,
                valuation_at=snapshot_row.valuation_at,
                total_equity=snapshot_row.total_equity,
                cash_value=snapshot_row.cash_value,
                market_value=snapshot_row.market_value,
                units_outstanding=snapshot_row.units_outstanding,
                nav=snapshot_row.nav_per_unit,
                cost_basis=snapshot_row.cost_basis,
                realized_pnl=snapshot_row.realized_pnl,
                unrealized_pnl=snapshot_row.unrealized_pnl,
                fees=snapshot_row.fees,
                taxes=snapshot_row.taxes,
                equity_pnl=snapshot_row.equity_pnl,
                fx_pnl=snapshot_row.fx_pnl,
                cash_ratio=snapshot_row.cash_ratio,
                invested_ratio=snapshot_row.invested_ratio,
                quality_status=SnapshotQualityStatus(snapshot_row.quality_status),
            ),
        )

    def list_strategies(self) -> list[StrategyDefinition]:
        rows = self._session.scalars(
            select(StrategyDefinitionModel).order_by(StrategyDefinitionModel.name)
        ).all()
        return [
            StrategyDefinition(
                id=row.id,
                name=row.name,
                version=row.version,
                implementation_key=row.implementation_key,
                research_status=row.research_status,
                enabled=row.enabled,
            )
            for row in rows
        ]
