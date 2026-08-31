from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from ai_infra_quant.core.domain.enums import (
    BrokerEnvironment,
    CapabilityStatus,
    DataAvailabilityStatus,
)


@dataclass(frozen=True, slots=True)
class CapabilityItem:
    name: str
    status: CapabilityStatus
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class CapabilitySet:
    items: tuple[CapabilityItem, ...] = ()


@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    name: str
    implementation_status: CapabilityStatus
    connection_status: CapabilityStatus
    environment: BrokerEnvironment | None
    message: str
    capabilities: tuple[CapabilityItem, ...] = ()


BrokerCapabilities = CapabilitySet
MarketDataCapabilities = CapabilitySet
FundamentalDataCapabilities = CapabilitySet
EventDataCapabilities = CapabilitySet


@dataclass(frozen=True, slots=True)
class ConnectionResult:
    status: CapabilityStatus
    message: str | None = None


@dataclass(frozen=True, slots=True)
class Quote:
    security_id: str
    price: Decimal | None
    status: DataAvailabilityStatus
    observed_at: datetime | None = None
    source: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderRecord:
    security_id: str
    available_at: datetime
    source: str
    source_record_id: str
    values: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BrokerAccount:
    id: str
    display_label: str


@dataclass(frozen=True, slots=True)
class CashBalance:
    currency: str
    settled_amount: Decimal


@dataclass(frozen=True, slots=True)
class BrokerPosition:
    security_id: str
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class MarketStatus:
    market: str
    status: CapabilityStatus
