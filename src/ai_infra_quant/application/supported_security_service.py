from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ai_infra_quant.application.market_data_queries import MarketDataProviderFactory
from ai_infra_quant.application.unit_of_work import UnitOfWorkFactory
from ai_infra_quant.application.watchlist_service import WatchlistItemView
from ai_infra_quant.core.domain.common import utc_now
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus, InstrumentType
from ai_infra_quant.core.domain.market_data import MarketDataSecurity, ProviderResult, QuoteSnapshot
from ai_infra_quant.core.domain.security import (
    Security,
    SecurityIdentityConflict,
    canonicalize_security_identity,
)


@dataclass(frozen=True, slots=True)
class ProviderValidation:
    status: DataAvailabilityStatus
    provider: str
    retrieved_at: datetime


@dataclass(frozen=True, slots=True)
class SupportedSecurityAddResult:
    created_security: bool
    created_watchlist_item: bool
    item: WatchlistItemView
    provider_validation: ProviderValidation


class SupportedSecurityAddError(RuntimeError):
    def __init__(
        self,
        *,
        code: str,
        detail: str,
        provider_status: DataAvailabilityStatus | None = None,
        provider: str | None = None,
        retrieved_at: datetime | None = None,
    ) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.provider_status = provider_status
        self.provider = provider
        self.retrieved_at = retrieved_at


class SupportedSecurityService:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        *,
        provider_name: str,
        provider_factory: MarketDataProviderFactory | None,
    ) -> None:
        self._uow_factory = uow_factory
        self._provider_name = provider_name
        self._provider_factory = provider_factory

    def add(self, *, market: str, symbol: str) -> SupportedSecurityAddResult:
        normalized_market, normalized_symbol = canonicalize_security_identity(market, symbol)
        currency, timezone = _market_contract(normalized_market)
        market_security = MarketDataSecurity(
            normalized_market,
            normalized_symbol,
            currency,
            timezone,
        )
        validation = self._validate(market_security)

        try:
            with self._uow_factory() as uow:
                security = uow.securities.get_by_identity(normalized_market, normalized_symbol)
                created_security = security is None
                if security is None:
                    try:
                        security = uow.securities.add_user_supplied(
                            market=normalized_market,
                            symbol=normalized_symbol,
                            currency=currency,
                            instrument_type=InstrumentType.EQUITY.value,
                            display_name=normalized_symbol,
                        )
                    except SecurityIdentityConflict as exc:
                        security = uow.securities.get(exc.security_id)
                        created_security = False
                        if security is None:
                            raise
                _require_compatible_security(security, currency)
                created_item, item_security, added_at, display_order = uow.watchlists.add(
                    security.id
                )
                uow.commit()
        except SupportedSecurityAddError:
            raise
        except Exception as exc:
            raise SupportedSecurityAddError(
                code="SUPPORTED_SECURITY_PERSISTENCE_ERROR",
                detail=_safe_reason(exc),
                provider_status=validation.status,
                provider=validation.provider,
                retrieved_at=validation.retrieved_at,
            ) from exc
        return SupportedSecurityAddResult(
            created_security=created_security,
            created_watchlist_item=created_item,
            item=WatchlistItemView(item_security, added_at, display_order),
            provider_validation=validation,
        )

    def _validate(self, security: MarketDataSecurity) -> ProviderValidation:
        if self._provider_factory is None:
            raise SupportedSecurityAddError(
                code="MARKET_DATA_PROVIDER_NOT_CONFIGURED",
                detail="Market data provider is not configured; no local state was changed.",
            )
        try:
            with self._provider_factory() as provider:
                result = provider.get_latest_quote(security)
        except Exception as exc:
            raise SupportedSecurityAddError(
                code="MARKET_DATA_PROVIDER_UNAVAILABLE",
                detail=f"Provider validation could not run: {_safe_reason(exc)}",
                provider_status=DataAvailabilityStatus.UNAVAILABLE,
                provider=self._provider_name,
                retrieved_at=utc_now(),
            ) from exc
        _require_valid_quote(result, security)
        return ProviderValidation(result.status, result.provider, result.retrieved_at)


def _market_contract(market: str) -> tuple[str, str]:
    try:
        return {
            "US": ("USD", "America/New_York"),
            "HK": ("HKD", "Asia/Hong_Kong"),
        }[market]
    except KeyError as exc:
        raise ValueError("supported equity market must be US or HK") from exc


def _require_valid_quote(
    result: ProviderResult[QuoteSnapshot], security: MarketDataSecurity
) -> None:
    if result.status is not DataAvailabilityStatus.AVAILABLE or result.data is None:
        status_to_code = {
            DataAvailabilityStatus.NOT_ENTITLED: "MARKET_DATA_NOT_ENTITLED",
            DataAvailabilityStatus.UNAVAILABLE: "MARKET_DATA_PROVIDER_UNAVAILABLE",
            DataAvailabilityStatus.PROVIDER_ERROR: "MARKET_DATA_PROVIDER_ERROR",
        }
        raise SupportedSecurityAddError(
            code=status_to_code.get(result.status, "SYMBOL_VALIDATION_FAILED"),
            detail=(result.reason or "Provider did not validate the requested canonical symbol."),
            provider_status=result.status,
            provider=result.provider,
            retrieved_at=result.retrieved_at,
        )
    if result.data.security != security.display_symbol or result.data.currency != security.currency:
        raise SupportedSecurityAddError(
            code="SYMBOL_VALIDATION_FAILED",
            detail="Provider quote did not match the requested canonical symbol and currency.",
            provider_status=DataAvailabilityStatus.INVALID,
            provider=result.provider,
            retrieved_at=result.retrieved_at,
        )
    if result.data.is_equity is not True:
        detail = (
            "Provider explicitly classified the requested security as non-equity."
            if result.data.is_equity is False
            else "Provider did not supply an explicit, valid equity classification."
        )
        raise SupportedSecurityAddError(
            code="SYMBOL_VALIDATION_FAILED",
            detail=detail,
            provider_status=DataAvailabilityStatus.INVALID,
            provider=result.provider,
            retrieved_at=result.retrieved_at,
        )


def _require_compatible_security(security: Security, expected_currency: str) -> None:
    if security.currency != expected_currency:
        raise SupportedSecurityAddError(
            code="SECURITY_METADATA_CONFLICT",
            detail=(
                f"Existing {security.display_symbol} currency {security.currency} conflicts with "
                f"the supported market contract {expected_currency}."
            ),
        )
    if security.instrument_type is not InstrumentType.EQUITY or not security.enabled:
        raise SupportedSecurityAddError(
            code="SECURITY_METADATA_CONFLICT",
            detail="Existing canonical Security is not an enabled equity.",
        )


def _safe_reason(error: object) -> str:
    text = str(error).strip()
    return text[:500] if text else type(error).__name__
