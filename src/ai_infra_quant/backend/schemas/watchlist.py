from pydantic import UUID4

from ai_infra_quant.backend.schemas.common import StrictSchema
from ai_infra_quant.backend.schemas.security import SecuritySummaryRead


class WatchlistAddRequestV1(StrictSchema):
    security_id: UUID4


class WatchlistItemRead(StrictSchema):
    security: SecuritySummaryRead
    added_at: str
    display_order: int


class WatchlistRead(StrictSchema):
    id: str
    name: str
    portfolio_id: str
    is_default: bool
    items: list[WatchlistItemRead]


class WatchlistAddResponse(StrictSchema):
    created: bool
    item: WatchlistItemRead
