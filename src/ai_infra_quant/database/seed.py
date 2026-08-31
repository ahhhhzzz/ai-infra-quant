from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, time
from decimal import Decimal
from uuid import UUID, uuid5
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ai_infra_quant.config import Settings
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus, SnapshotQualityStatus
from ai_infra_quant.core.domain.money import canonical_decimal_string
from ai_infra_quant.core.domain.security import canonicalize_security_identity
from ai_infra_quant.database.models.accounting import (
    CashBalanceModel,
    CashFlowModel,
    LedgerAccountModel,
    LedgerEntryModel,
    LedgerTransactionModel,
    PortfolioSnapshotModel,
    UnitTransactionModel,
)
from ai_infra_quant.database.models.portfolio import (
    BrokerAccountModel,
    BrokerProfileModel,
    PortfolioAccountModel,
    PortfolioModel,
)
from ai_infra_quant.database.models.security import (
    SecurityModel,
    WatchlistItemModel,
    WatchlistModel,
)
from ai_infra_quant.database.models.settings import SettingModel
from ai_infra_quant.database.models.strategy import StrategyDefinitionModel
from ai_infra_quant.database.repositories.unit_of_work import SQLAlchemyUnitOfWork

_NAMESPACE = UUID("870405c9-cf22-4d8f-8806-94908f2e36a7")
_BOOTSTRAP_FINGERPRINT_KEY = "phase1_bootstrap_configuration_fingerprint"


class SeedConfigurationMismatch(RuntimeError):
    code = "SEED_CONFIGURATION_MISMATCH"


def opening_at(settings: Settings) -> datetime:
    local_midnight = datetime.combine(
        settings.inception_date,
        time.min,
        tzinfo=ZoneInfo(settings.valuation_timezone),
    )
    return local_midnight.astimezone(UTC)


def seed_configuration_fingerprint(settings: Settings) -> str:
    payload = {
        "base_currency": settings.initial_base_currency,
        "inception_date": settings.inception_date.isoformat(),
        "initial_capital": canonical_decimal_string(settings.initial_capital),
        "initial_nav": canonical_decimal_string(settings.initial_nav),
        "initial_units": canonical_decimal_string(settings.initial_units),
        "portfolio_name": settings.initial_portfolio_name,
        "valuation_timezone": settings.valuation_timezone,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def stable_id(key: str) -> str:
    return str(uuid5(_NAMESPACE, key))


@dataclass(frozen=True, slots=True)
class SeedResult:
    portfolio_id: str
    watchlist_id: str
    security_ids: tuple[str, ...]


_SECURITIES = (
    ("US", "AVGO", "USD", "America/New_York"),
    ("US", "VRT", "USD", "America/New_York"),
    ("HK", "09698", "HKD", "Asia/Hong_Kong"),
)


def _ensure_security(
    session: Session,
    market: str,
    symbol: str,
    currency: str,
    timezone: str,
    opening_instant: datetime,
) -> str:
    market, symbol = canonicalize_security_identity(market, symbol)
    security_id = stable_id(f"security:{market}:{symbol}")
    if session.get(SecurityModel, security_id) is None:
        session.add(
            SecurityModel(
                id=security_id,
                market=market,
                symbol=symbol,
                exchange=None,
                currency=currency,
                display_name=symbol,
                instrument_type="EQUITY",
                enabled=True,
                lot_size=None,
                min_order_quantity=None,
                quantity_step=None,
                fractional_quantity_step=None,
                tick_size=None,
                min_notional=None,
                fractional_supported=False,
                market_timezone=timezone,
                trading_calendar=None,
                metadata_status=DataAvailabilityStatus.UNAVAILABLE.value,
                record_source="SYSTEM_SEED",
                verification_status="SYSTEM_SEED_UNVERIFIED",
                tradability_status="UNVERIFIED",
                created_at=opening_instant,
                updated_at=opening_instant,
                version=1,
            )
        )
    return security_id


def _ensure_seed_configuration(
    session: Session, settings: Settings, opening_instant: datetime
) -> None:
    fingerprint = seed_configuration_fingerprint(settings)
    existing = session.scalar(
        select(SettingModel).where(
            SettingModel.scope_type == "SYSTEM",
            SettingModel.scope_id.is_(None),
            SettingModel.key == _BOOTSTRAP_FINGERPRINT_KEY,
        )
    )
    if existing is not None:
        if json.loads(existing.value_json) != fingerprint:
            raise SeedConfigurationMismatch(
                "SEED_CONFIGURATION_MISMATCH: bootstrap settings differ from the opening facts"
            )
        return
    if session.scalar(select(PortfolioModel.id).limit(1)) is not None:
        raise SeedConfigurationMismatch(
            "SEED_CONFIGURATION_MISMATCH: legacy Phase 1 draft database must be recreated"
        )
    session.add(
        SettingModel(
            id=stable_id("setting:system:phase1-bootstrap-configuration-fingerprint"),
            scope_type="SYSTEM",
            scope_id=None,
            key=_BOOTSTRAP_FINGERPRINT_KEY,
            value_json=json.dumps(fingerprint),
            value_type="SHA256",
            schema_version=1,
            is_secret=False,
            updated_at=opening_instant,
            version=1,
        )
    )


def bootstrap_phase_one(session_factory: sessionmaker[Session], settings: Settings) -> SeedResult:
    with SQLAlchemyUnitOfWork(session_factory) as uow:
        session = uow.session
        opening_instant = opening_at(settings)
        _ensure_seed_configuration(session, settings, opening_instant)
        security_ids = tuple(
            _ensure_security(session, market, symbol, currency, timezone, opening_instant)
            for market, symbol, currency, timezone in _SECURITIES
        )

        portfolio_id = stable_id("portfolio:phase1-opening-singleton")
        broker_profile_id = stable_id("broker-profile:paper")
        broker_account_id = stable_id("broker-account:paper-opening")
        portfolio_account_id = stable_id("portfolio-account:opening")
        watchlist_id = stable_id("watchlist:ai-infra-default")

        if session.get(BrokerProfileModel, broker_profile_id) is None:
            session.add(
                BrokerProfileModel(
                    id=broker_profile_id,
                    name="paper",
                    adapter_key="paper",
                    environment="PAPER",
                    implementation_status="NOT_IMPLEMENTED",
                    enabled=False,
                    configuration_json="{}",
                    created_at=opening_instant,
                    updated_at=opening_instant,
                    version=1,
                )
            )
        if session.get(BrokerAccountModel, broker_account_id) is None:
            session.add(
                BrokerAccountModel(
                    id=broker_account_id,
                    broker_profile_id=broker_profile_id,
                    external_account_id=None,
                    external_account_id_hash=None,
                    display_label="Phase 1 opening account",
                    account_type="CASH",
                    base_currency=settings.initial_base_currency,
                    status="NOT_IMPLEMENTED",
                    is_read_only=True,
                    last_reconciled_at=None,
                    created_at=opening_instant,
                    updated_at=opening_instant,
                    version=1,
                )
            )
        if session.get(PortfolioModel, portfolio_id) is None:
            session.add(
                PortfolioModel(
                    id=portfolio_id,
                    name=settings.initial_portfolio_name,
                    base_currency=settings.initial_base_currency,
                    inception_date=settings.inception_date,
                    valuation_timezone=settings.valuation_timezone,
                    daily_cutoff_policy=None,
                    initial_nav=settings.initial_nav,
                    status="ACTIVE",
                    created_at=opening_instant,
                    updated_at=opening_instant,
                    version=1,
                )
            )
        if session.get(PortfolioAccountModel, portfolio_account_id) is None:
            session.add(
                PortfolioAccountModel(
                    id=portfolio_account_id,
                    portfolio_id=portfolio_id,
                    broker_account_id=broker_account_id,
                    effective_from=opening_instant,
                    effective_to=None,
                    is_primary=True,
                )
            )
        if session.get(WatchlistModel, watchlist_id) is None:
            session.add(
                WatchlistModel(
                    id=watchlist_id,
                    portfolio_id=portfolio_id,
                    name=settings.initial_portfolio_name,
                    is_default=True,
                    created_at=opening_instant,
                    updated_at=opening_instant,
                )
            )
        session.flush()

        for display_order, security_id in enumerate(security_ids, start=1):
            prior = session.scalar(
                select(WatchlistItemModel.id).where(
                    WatchlistItemModel.watchlist_id == watchlist_id,
                    WatchlistItemModel.security_id == security_id,
                )
            )
            if prior is None:
                session.add(
                    WatchlistItemModel(
                        id=stable_id(f"watchlist-item:{security_id}"),
                        watchlist_id=watchlist_id,
                        security_id=security_id,
                        added_at=opening_instant,
                        removed_at=None,
                        display_order=display_order,
                        note=None,
                    )
                )

        strategy_id = stable_id("strategy:AIInfraStrategy:1.0.0")
        if session.get(StrategyDefinitionModel, strategy_id) is None:
            session.add(
                StrategyDefinitionModel(
                    id=strategy_id,
                    name="AIInfraStrategy",
                    version="1.0.0",
                    implementation_key="ai_infra",
                    parameter_schema_json="{}",
                    default_parameters_json="{}",
                    definition_hash="phase1-unapproved-not-implemented",
                    research_status="RESEARCH_UNVALIDATED",
                    enabled=False,
                    created_at=opening_instant,
                )
            )

        transaction_id = stable_id("ledger-transaction:initial-contribution")
        if session.get(LedgerTransactionModel, transaction_id) is None:
            cash_account_id = stable_id("ledger-account:cash-hkd")
            capital_account_id = stable_id("ledger-account:contributed-capital-hkd")
            session.add_all(
                [
                    LedgerAccountModel(
                        id=cash_account_id,
                        portfolio_id=portfolio_id,
                        broker_account_id=broker_account_id,
                        security_id=None,
                        account_code="CASH_HKD",
                        account_type="CASH_ASSET",
                        currency=settings.initial_base_currency,
                        normal_balance="DEBIT",
                        active=True,
                        created_at=opening_instant,
                        updated_at=opening_instant,
                    ),
                    LedgerAccountModel(
                        id=capital_account_id,
                        portfolio_id=portfolio_id,
                        broker_account_id=None,
                        security_id=None,
                        account_code="CONTRIBUTED_CAPITAL_HKD",
                        account_type="CONTRIBUTED_CAPITAL",
                        currency=settings.initial_base_currency,
                        normal_balance="CREDIT",
                        active=True,
                        created_at=opening_instant,
                        updated_at=opening_instant,
                    ),
                ]
            )
            session.flush()
            transaction = LedgerTransactionModel(
                id=transaction_id,
                sequence_no=1,
                portfolio_id=portfolio_id,
                transaction_type="INITIAL_CONTRIBUTION",
                effective_at=opening_instant,
                recorded_at=opening_instant,
                source_type="SYSTEM_BOOTSTRAP",
                source_id="phase1-opening",
                idempotency_key="phase1-opening-contribution",
                reverses_transaction_id=None,
                description="Phase 1 opening contribution",
                created_by="system-bootstrap",
            )
            entries = [
                LedgerEntryModel(
                    id=stable_id("ledger-entry:opening:debit"),
                    ledger_transaction_id=transaction_id,
                    ledger_account_id=cash_account_id,
                    entry_no=1,
                    direction="DEBIT",
                    amount=settings.initial_capital,
                    currency=settings.initial_base_currency,
                    base_currency=settings.initial_base_currency,
                    base_fx_rate=Decimal("1"),
                    base_amount=settings.initial_capital,
                    quantity=None,
                    unit_price=None,
                    security_id=None,
                    effective_at=opening_instant,
                    created_at=opening_instant,
                ),
                LedgerEntryModel(
                    id=stable_id("ledger-entry:opening:credit"),
                    ledger_transaction_id=transaction_id,
                    ledger_account_id=capital_account_id,
                    entry_no=2,
                    direction="CREDIT",
                    amount=settings.initial_capital,
                    currency=settings.initial_base_currency,
                    base_currency=settings.initial_base_currency,
                    base_fx_rate=Decimal("1"),
                    base_amount=settings.initial_capital,
                    quantity=None,
                    unit_price=None,
                    security_id=None,
                    effective_at=opening_instant,
                    created_at=opening_instant,
                ),
            ]
            uow.add_balanced_transaction(transaction, entries)

            cash_flow_id = stable_id("cash-flow:initial-contribution")
            session.add(
                CashFlowModel(
                    id=cash_flow_id,
                    portfolio_id=portfolio_id,
                    broker_account_id=broker_account_id,
                    currency=settings.initial_base_currency,
                    flow_type="INITIAL_CONTRIBUTION",
                    amount=settings.initial_capital,
                    effective_at=opening_instant,
                    requested_at=opening_instant,
                    posted_at=opening_instant,
                    idempotency_key="phase1-opening-contribution",
                    status="POSTED",
                    base_fx_rate=Decimal("1"),
                    base_amount=settings.initial_capital,
                    pre_flow_nav=settings.initial_nav,
                    units_issued=settings.initial_units,
                    units_redeemed=Decimal("0"),
                    pre_flow_snapshot_id=None,
                    ledger_transaction_id=transaction_id,
                    reverses_cash_flow_id=None,
                )
            )
            session.flush()
            session.add(
                UnitTransactionModel(
                    id=stable_id("unit-transaction:initial-issue"),
                    portfolio_id=portfolio_id,
                    cash_flow_id=cash_flow_id,
                    unit_event_type="INITIAL_ISSUE",
                    effective_at=opening_instant,
                    nav_per_unit=settings.initial_nav,
                    unit_quantity=settings.initial_units,
                    base_amount=settings.initial_capital,
                    reverses_unit_transaction_id=None,
                )
            )
            session.add(
                CashBalanceModel(
                    id=stable_id("cash-balance:paper:HKD"),
                    broker_account_id=broker_account_id,
                    currency=settings.initial_base_currency,
                    settled_amount=settings.initial_capital,
                    unsettled_receivable=Decimal("0"),
                    unsettled_payable=Decimal("0"),
                    reserved_amount=Decimal("0"),
                    reported_buying_power=None,
                    reported_at=None,
                    as_of_ledger_sequence=1,
                    updated_at=opening_instant,
                    version=1,
                )
            )
            session.add(
                PortfolioSnapshotModel(
                    id=stable_id("portfolio-snapshot:inception"),
                    portfolio_id=portfolio_id,
                    valuation_at=opening_instant,
                    valuation_kind="INCEPTION",
                    base_currency=settings.initial_base_currency,
                    cash_value=settings.initial_capital,
                    market_value=Decimal("0"),
                    receivables=Decimal("0"),
                    payables=Decimal("0"),
                    total_equity=settings.initial_capital,
                    units_outstanding=settings.initial_units,
                    nav_per_unit=settings.initial_nav,
                    cost_basis=Decimal("0"),
                    realized_pnl=Decimal("0"),
                    unrealized_pnl=Decimal("0"),
                    fees=Decimal("0"),
                    taxes=Decimal("0"),
                    equity_pnl=Decimal("0"),
                    fx_pnl=Decimal("0"),
                    cash_ratio=Decimal("1"),
                    invested_ratio=Decimal("0"),
                    price_manifest_hash=None,
                    fx_manifest_hash=None,
                    ledger_sequence=1,
                    is_official=True,
                    quality_status=SnapshotQualityStatus.COMPLETE.value,
                    missing_data_json="[]",
                )
            )

        phase_setting_id = stable_id("setting:system:phase")
        if session.get(SettingModel, phase_setting_id) is None:
            session.add(
                SettingModel(
                    id=phase_setting_id,
                    scope_type="SYSTEM",
                    scope_id=None,
                    key="phase",
                    value_json='"1"',
                    value_type="STRING",
                    schema_version=1,
                    is_secret=False,
                    updated_at=opening_instant,
                    version=1,
                )
            )

        uow.commit()
        return SeedResult(
            portfolio_id=portfolio_id,
            watchlist_id=watchlist_id,
            security_ids=security_ids,
        )
