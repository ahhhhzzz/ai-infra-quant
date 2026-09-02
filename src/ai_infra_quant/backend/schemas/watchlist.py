from __future__ import annotations

from pydantic import UUID4, model_validator
from pydantic_core import PydanticCustomError

from ai_infra_quant.backend.schemas.common import StrictSchema
from ai_infra_quant.backend.schemas.security import SecuritySummaryRead
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus
from ai_infra_quant.core.domain.security import (
    SecurityIdentityError,
    canonicalize_security_identity,
)


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


class SupportedSecurityAddRequest(StrictSchema):
    market: str
    symbol: str

    @model_validator(mode="after")
    def canonicalize_identity(self) -> SupportedSecurityAddRequest:
        try:
            market, symbol = canonicalize_security_identity(self.market, self.symbol)
        except SecurityIdentityError as exc:
            raise PydanticCustomError(exc.code, str(exc)) from exc
        self.market = market
        self.symbol = symbol
        return self


class ProviderValidationRead(StrictSchema):
    status: DataAvailabilityStatus
    provider: str
    retrieved_at: str


class SupportedSecurityAddResponse(StrictSchema):
    created_security: bool
    created_watchlist_item: bool
    item: WatchlistItemRead
    provider_validation: ProviderValidationRead
