"""Immutable, closed Setup/Risk evidence outside the F1 Structure/Event envelopes."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .canonical import FrozenJSON, digest, utc
from .event_reference import Hash, Price
from .inputs import QInput

VERSION = "1.0.0"
SETUP_ID = "paqs-q-setup-risk-reference"


@dataclass(frozen=True, slots=True)
class EntryReference:
    """Independent opening-price evidence; an M30 final OHLC is not this observation."""

    price: Decimal
    price_at: datetime
    available_at: datetime
    source: Literal["SYNTHETIC_OPEN", "PROVIDER_OPEN_EVENT"]
    source_ref: str
    adjustment: str
    security: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "price_at", utc(self.price_at))
        object.__setattr__(self, "available_at", utc(self.available_at))
        if not isinstance(self.price, Decimal) or not self.price.is_finite() or self.price <= 0:
            raise ValueError("ENTRY_REFERENCE_PRICE_INVALID")
        if (
            not self.source_ref.strip()
            or not self.adjustment.strip()
            or not self.security.strip()
            or self.available_at < self.price_at
            or self.source not in {"SYNTHETIC_OPEN", "PROVIDER_OPEN_EVENT"}
        ):
            raise ValueError("ENTRY_REFERENCE_PROVENANCE_INVALID")


@dataclass(frozen=True, slots=True)
class MultiInput:
    w1: QInput | None
    d1: QInput | None
    m30: QInput | None
    entry_references: tuple[EntryReference, ...] = ()

    def __post_init__(self) -> None:
        for name in ("w1", "d1", "m30"):
            item = getattr(self, name)
            if item is not None and (type(item) is not QInput or item.timeframe != name.upper()):
                raise ValueError("MULTIPERIOD_TIMEFRAME_INVALID")
        refs = tuple(self.entry_references)
        if any(type(ref) is not EntryReference for ref in refs):
            raise ValueError("ENTRY_REFERENCE_TYPE_INVALID")
        if len({ref.price_at for ref in refs}) != len(refs):
            raise ValueError("ENTRY_REFERENCE_DUPLICATE")
        object.__setattr__(self, "entry_references", tuple(sorted(refs, key=lambda r: r.price_at)))


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    def frozen(self) -> FrozenJSON:
        return FrozenJSON.of(self.model_dump())


class UpstreamBinding(Closed):
    timeframe: Literal["W1", "D1", "M30"]
    input_hash: Hash
    structure_result_hash: Hash
    event_result_hash: Hash
    structure_code_hash: Hash
    event_code_hash: Hash
    structure_config_hash: Hash
    event_config_hash: Hash
    structure_version: Literal["1.0.1"]
    event_version: Literal["1.0.1"]


class TargetEvidence(Closed):
    effective_price: Price
    lower: Price
    upper: Price
    sources: tuple[str, ...]
    source_keys: tuple[Hash, ...]
    known_at: datetime
    gap_original_lower: Price | None = None
    gap_original_upper: Price | None = None
    gap_status: Literal["OPEN", "PARTIALLY_FILLED"] | None = None

    @model_validator(mode="after")
    def geometry(self) -> "TargetEvidence":
        if not Decimal(self.lower) <= Decimal(self.effective_price) <= Decimal(self.upper):
            raise ValueError("TARGET_GEOMETRY_INVALID")
        if not self.sources or len(self.sources) != len(self.source_keys):
            raise ValueError("TARGET_PROVENANCE_REQUIRED")
        return self


FactStatus = Literal[
    "CREATED",
    "OBSERVED",
    "TRIGGER_PENDING",
    "FOLLOW_THROUGH_PENDING",
    "FOLLOW_THROUGH_CONFIRMED",
    "FOLLOW_THROUGH_NONE",
    "FOLLOW_THROUGH_FAILED",
    "ENTRY_PENDING_REVALIDATION",
    "LONG_READY",
    "OBSERVATIONAL_LONG_QUALIFIED",
    "VALID_SETUP_BUT_POOR_ENTRY",
    "NO_TRADE",
    "INVALIDATED",
    "EXPIRED",
]


class SetupFact(Closed):
    schema_version: Literal["paqs-q-setup-fact-v1"] = "paqs-q-setup-fact-v1"
    fact_key: Hash
    setup_key: Hash
    candidate_key: Hash | None
    family: Literal[
        "TREND_PULLBACK_LONG", "RANGE_FAILED_BREAKDOWN_LONG", "RIGHT_SIDE_BREAKOUT_LONG"
    ]
    variant: str
    status: FactStatus
    entry_advisory: Literal[
        "WATCH_LONG",
        "ENTRY_PENDING_REVALIDATION",
        "LONG_READY",
        "OBSERVATIONAL_LONG_QUALIFIED",
        "VALID_SETUP_BUT_POOR_ENTRY",
        "NO_TRADE",
    ]
    effective_at: datetime
    d1_index: int = Field(ge=0)
    m30_index: int | None = Field(default=None, ge=0)
    source_key: Hash
    origin_event_key: Hash | None
    anchor_price: Price
    invalidation_buffer_atr: Price
    atr: Price | None = None
    risk_reference_price: Price | None = None
    reference_price: Price | None = None
    target1: TargetEvidence | None = None
    target2: TargetEvidence | None = None
    rr_t1: Price | None = None
    rr_t2: Price | None = None
    entry_reference_source: str | None = None
    entry_reference_source_ref: str | None = None
    entry_reference_adjustment: str | None = None
    entry_reference_price_at: datetime | None = None
    entry_reference_available_at: datetime | None = None
    rejected_targets: tuple[str, ...] = ()
    reasons: tuple[str, ...]
    related_keys: tuple[Hash, ...] = ()

    @model_validator(mode="after")
    def evidence_required(self) -> "SetupFact":
        if not self.reasons or Decimal(self.anchor_price) <= 0:
            raise ValueError("SETUP_FACT_INVALID")
        if self.status in {"LONG_READY", "OBSERVATIONAL_LONG_QUALIFIED"} and (
            self.candidate_key is None
            or self.rr_t1 is None
            or self.entry_reference_source is None
            or self.entry_reference_source_ref is None
            or self.entry_reference_adjustment is None
            or self.entry_reference_price_at is None
            or self.entry_reference_available_at is None
            or self.entry_reference_available_at > self.entry_reference_price_at
        ):
            raise ValueError("ENTRY_QUALIFICATION_EVIDENCE_REQUIRED")
        return self


class SetupRun(Closed):
    schema_version: Literal["paqs-q-setup-run-v1"] = "paqs-q-setup-run-v1"
    strategy_id: Literal["paqs-q-setup-risk-reference"] = "paqs-q-setup-risk-reference"
    strategy_version: Literal["1.0.0"] = "1.0.0"
    code_hash: Hash
    config_hash: Hash
    entry_reference_hash: Hash
    mode: Literal["AS_OF", "OBSERVATIONAL"]
    security: str
    strict_confirmation: bool
    status: Literal["AVAILABLE", "INSUFFICIENT", "INVALID"]
    reasons: tuple[str, ...]
    bindings: tuple[UpstreamBinding, ...]
    facts: tuple[SetupFact, ...]

    @property
    def canonical_result_hash(self) -> str:
        return digest("paqs-q/setup-result/v1", self.model_dump())
