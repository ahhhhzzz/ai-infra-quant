from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from ai_infra_quant.core.domain.enums import (
    DataAvailabilityStatus,
    InstrumentType,
    OrderSide,
    OrderType,
    RecordSource,
    TimeInForce,
    TradabilityStatus,
    VerificationStatus,
)
from ai_infra_quant.core.domain.execution import StandardOrder
from ai_infra_quant.core.domain.security import Security
from ai_infra_quant.core.domain.strategy import Strategy


def test_user_supplied_security_is_fail_closed() -> None:
    now = datetime.now(UTC)
    security = Security(
        id=str(uuid4()),
        market=" us ",
        symbol=" example ",
        currency="usd",
        display_name="Local label",
        instrument_type=InstrumentType.EQUITY,
        enabled=True,
        record_source=RecordSource.USER_SUPPLIED,
        verification_status=VerificationStatus.USER_SUPPLIED_UNVERIFIED,
        tradability_status=TradabilityStatus.UNVERIFIED,
        metadata_status=DataAvailabilityStatus.UNAVAILABLE,
        created_at=now,
        updated_at=now,
    )
    assert security.display_symbol == "US.EXAMPLE"
    assert security.strategy_and_orders_allowed is False


def test_user_supplied_security_cannot_claim_verification() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="remain unverified"):
        Security(
            id=str(uuid4()),
            market="US",
            symbol="EXAMPLE",
            currency="USD",
            display_name="Example",
            instrument_type=InstrumentType.EQUITY,
            enabled=True,
            record_source=RecordSource.USER_SUPPLIED,
            verification_status=VerificationStatus.VERIFIED,
            tradability_status=TradabilityStatus.UNVERIFIED,
            metadata_status=DataAvailabilityStatus.UNAVAILABLE,
            created_at=now,
            updated_at=now,
        )


def test_canonical_order_validates_limit_combination_without_executing() -> None:
    now = datetime.now(UTC)
    identifier = str(uuid4())
    with pytest.raises(ValueError, match="require a limit price"):
        StandardOrder(
            internal_order_id=identifier,
            client_order_id="client-1",
            idempotency_key="idempotency-1",
            portfolio_id=str(uuid4()),
            account_id=str(uuid4()),
            broker_profile_id=str(uuid4()),
            security_id=str(uuid4()),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1"),
            currency="USD",
            time_in_force=TimeInForce.DAY,
            created_at=now,
        )


def test_strategy_contract_is_abstract_and_has_no_phase_one_implementation() -> None:
    with pytest.raises(TypeError):
        Strategy()  # type: ignore[abstract]
