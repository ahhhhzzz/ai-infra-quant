from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_infra_quant.core.domain.common import utc_now
from ai_infra_quant.core.domain.enums import (
    DataAvailabilityStatus,
    InstrumentType,
    RecordSource,
    TradabilityStatus,
    VerificationStatus,
)
from ai_infra_quant.core.domain.security import (
    Security,
    SecurityIdentityConflict,
    TradingRules,
    canonicalize_security_identity,
    normalize_currency,
)
from ai_infra_quant.database.models.security import SecurityModel


def security_from_model(row: SecurityModel) -> Security:
    return Security(
        id=row.id,
        market=row.market,
        symbol=row.symbol,
        exchange=row.exchange,
        currency=row.currency,
        display_name=row.display_name,
        instrument_type=InstrumentType(row.instrument_type),
        enabled=row.enabled,
        record_source=RecordSource(row.record_source),
        verification_status=VerificationStatus(row.verification_status),
        tradability_status=TradabilityStatus(row.tradability_status),
        metadata_status=DataAvailabilityStatus(row.metadata_status),
        market_timezone=row.market_timezone,
        trading_calendar=row.trading_calendar,
        trading_rules=TradingRules(
            lot_size=row.lot_size,
            min_order_quantity=row.min_order_quantity,
            quantity_step=row.quantity_step,
            tick_size=row.tick_size,
            min_notional=row.min_notional,
            fractional_supported=row.fractional_supported,
            status=(
                DataAvailabilityStatus.AVAILABLE
                if all(
                    value is not None for value in (row.lot_size, row.quantity_step, row.tick_size)
                )
                else DataAvailabilityStatus.UNAVAILABLE
            ),
        ),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemySecurityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, security_id: str) -> Security | None:
        row = self._session.get(SecurityModel, security_id)
        return None if row is None else security_from_model(row)

    def get_by_identity(self, market: str, symbol: str) -> Security | None:
        normalized_market, normalized_symbol = canonicalize_security_identity(market, symbol)
        row = self._session.scalar(
            select(SecurityModel).where(
                SecurityModel.market == normalized_market,
                SecurityModel.symbol == normalized_symbol,
            )
        )
        return None if row is None else security_from_model(row)

    def add_user_supplied(
        self,
        *,
        market: str,
        symbol: str,
        currency: str,
        instrument_type: str,
        display_name: str | None,
    ) -> Security:
        normalized_market, normalized_symbol = canonicalize_security_identity(market, symbol)
        normalized_currency = normalize_currency(currency)
        normalized_type = InstrumentType(instrument_type.strip().upper())
        normalized_name = (display_name or normalized_symbol).strip()
        if not normalized_name or len(normalized_name) > 120:
            raise ValueError("display_name must contain 1-120 characters")
        now = utc_now()
        row = SecurityModel(
            id=str(uuid4()),
            market=normalized_market,
            symbol=normalized_symbol,
            exchange=None,
            currency=normalized_currency,
            display_name=normalized_name,
            instrument_type=normalized_type.value,
            enabled=True,
            lot_size=None,
            min_order_quantity=None,
            quantity_step=None,
            fractional_quantity_step=None,
            tick_size=None,
            min_notional=None,
            fractional_supported=False,
            market_timezone=None,
            trading_calendar=None,
            metadata_status=DataAvailabilityStatus.UNAVAILABLE.value,
            record_source=RecordSource.USER_SUPPLIED.value,
            verification_status=VerificationStatus.USER_SUPPLIED_UNVERIFIED.value,
            tradability_status=TradabilityStatus.UNVERIFIED.value,
            created_at=now,
            updated_at=now,
            version=1,
        )
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            existing = self.get_by_identity(normalized_market, normalized_symbol)
            if existing is not None:
                raise SecurityIdentityConflict(existing.id) from exc
            raise
        return security_from_model(row)
