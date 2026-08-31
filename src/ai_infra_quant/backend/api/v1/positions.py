from typing import Annotated

from fastapi import APIRouter, Query

from ai_infra_quant.backend.dependencies import ContainerDep
from ai_infra_quant.backend.schemas.common import Page

router = APIRouter()


@router.get("/positions", response_model=Page[dict[str, str]])
def get_positions(
    container: ContainerDep,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Page[dict[str, str]]:
    del cursor, limit
    return Page(items=container.portfolio_queries.positions())
