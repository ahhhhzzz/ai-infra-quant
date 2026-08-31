from typing import Literal

from fastapi import APIRouter, Query

from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.common import DataValue
from ai_infra_quant.backend.schemas.portfolio import (
    PerformancePointRead,
    PerformanceRead,
    PerformanceSummaryRead,
)
from ai_infra_quant.core.domain.money import decimal_string

router = APIRouter()


@router.get("/performance", response_model=PerformanceRead)
def get_performance(
    container: ContainerDep,
    range_: Literal["1D", "1W", "1M", "3M", "YTD", "SINCE_INCEPTION"] = Query(
        default="SINCE_INCEPTION", alias="range"
    ),
    frequency: Literal["DAILY", "WEEKLY", "MONTHLY"] = "DAILY",
) -> PerformanceRead:
    view = container.portfolio_queries.performance(range_, frequency)
    at = view.valuation_at.isoformat().replace("+00:00", "Z")
    return PerformanceRead(
        portfolio_id=view.portfolio_id,
        range=view.range,
        frequency=view.frequency,
        summary=PerformanceSummaryRead(
            twr=decimal_string(view.twr),
            daily_return=DataValue(
                value=None,
                status=view.daily_status,
                reason="At least two valuation points are required",
            ),
            weekly_return=DataValue(
                value=None,
                status=view.weekly_status,
                reason="Insufficient valuation history",
            ),
            monthly_return=DataValue(
                value=None,
                status=view.monthly_status,
                reason="Insufficient valuation history",
            ),
            since_inception_return=decimal_string(view.since_inception_return),
            maximum_drawdown=decimal_string(view.maximum_drawdown),
            benchmark_return=DataValue(
                value=None,
                status=view.benchmark_status,
                reason="No benchmark data source is configured",
            ),
        ),
        points=[
            PerformancePointRead(
                at=at,
                nav=decimal_string(view.nav),
                twr_index="1.000000000000",
                quality_status=view.quality_status,
            )
        ],
    )
