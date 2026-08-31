from __future__ import annotations

from dataclasses import dataclass

from ai_infra_quant.application.unit_of_work import UnitOfWorkFactory
from ai_infra_quant.core.domain.security import (
    Security,
    SecurityIdentityConflict,
    canonicalize_security_identity,
)


@dataclass(frozen=True, slots=True)
class SecurityAlreadyExists(Exception):
    security_id: str


class SecurityService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def get(self, security_id: str) -> Security:
        with self._uow_factory() as uow:
            security = uow.securities.get(security_id)
        if security is None:
            raise LookupError("SECURITY_NOT_FOUND")
        return security

    def create(
        self,
        *,
        market: str,
        symbol: str,
        currency: str,
        instrument_type: str,
        display_name: str | None,
    ) -> Security:
        normalized_market, normalized_symbol = canonicalize_security_identity(market, symbol)
        with self._uow_factory() as uow:
            existing = uow.securities.get_by_identity(normalized_market, normalized_symbol)
            if existing is not None:
                raise SecurityAlreadyExists(existing.id)
            try:
                security = uow.securities.add_user_supplied(
                    market=normalized_market,
                    symbol=normalized_symbol,
                    currency=currency,
                    instrument_type=instrument_type,
                    display_name=display_name,
                )
            except SecurityIdentityConflict as exc:
                raise SecurityAlreadyExists(exc.security_id) from exc
            uow.commit()
            return security
