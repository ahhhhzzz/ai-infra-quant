"""Closed, immutable plugin-owned schemas; the F1 envelope/record schema is unchanged."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from .canonical import FrozenJSON, decimal_text, primitive, utc


def decimal_string(value: str) -> str:
    try:
        normalized = decimal_text(Decimal(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("EVENT_INVALID_DECIMAL") from exc
    if normalized != value:
        raise ValueError("EVENT_NONCANONICAL_DECIMAL")
    return value


def instant_string(value: str) -> str:
    if primitive(utc(datetime.fromisoformat(value))) != value:
        raise ValueError("EVENT_NONCANONICAL_INSTANT")
    return value


Price = Annotated[str, AfterValidator(decimal_string)]
Instant = Annotated[str, AfterValidator(instant_string)]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Index = Annotated[int, Field(ge=0)]
Direction = Literal["UP", "DOWN"]
Regime = Literal[
    "UNCERTAIN", "RANGE", "BULL_TREND", "BEAR_TREND", "BULL_TRANSITION", "BEAR_TRANSITION"
]


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    def frozen(self) -> FrozenJSON:
        return FrozenJSON.of(self.model_dump())


class PivotEvidence(Closed):
    key: Hash
    hierarchy: Literal["MICRO", "MAJOR"]
    kind: Literal["HIGH", "LOW"]
    price: Price
    extreme_index: Index
    confirmation_index: Index
    extreme_time: Instant
    confirmation_time: Instant
    support_refs: tuple[Hash, ...]
    label: Literal["HH", "LH", "EH", "HL", "LL", "EL"] | None
    previous_key: Hash | None
    tolerance: Price | None

    @model_validator(mode="after")
    def temporal_order(self) -> "PivotEvidence":
        if self.extreme_index >= self.confirmation_index or Decimal(self.price) <= 0:
            raise ValueError("EVENT_PIVOT_ORDER")
        if len(self.support_refs) != 2:
            raise ValueError("EVENT_PIVOT_SUPPORT")
        return self


class ZoneEvidence(Closed):
    key: Hash
    role: Literal["SUPPORT", "RESISTANCE"]
    status: Literal["CANDIDATE", "CONFIRMED"]
    lower: Price
    upper: Price
    center: Price
    reference_atr: Price
    mad: Price
    half_width: Price
    touches: tuple[Hash, ...]
    confirmation_index: Index
    last_touch_index: Index

    @model_validator(mode="after")
    def geometry(self) -> "ZoneEvidence":
        if not (Decimal(self.lower) <= Decimal(self.center) <= Decimal(self.upper)):
            raise ValueError("EVENT_ZONE_GEOMETRY")
        if (
            Decimal(self.reference_atr) <= 0
            or Decimal(self.mad) < 0
            or Decimal(self.half_width) <= 0
        ):
            raise ValueError("EVENT_ZONE_SCALE")
        if len(set(self.touches)) != len(self.touches):
            raise ValueError("EVENT_ZONE_DUPLICATE_TOUCH")
        return self


class RangeEvidence(Closed):
    key: Hash
    version_key: Hash
    support_key: Hash
    resistance_key: Hash
    lower: Price
    upper: Price
    inside_ratio: Price
    width_atr: Price
    touches: Index
    reactions: tuple[Literal["H", "L"], ...]
    active: bool
    calculation_index: Index

    @model_validator(mode="after")
    def geometry(self) -> "RangeEvidence":
        if (
            not Decimal(self.lower) < Decimal(self.upper)
            or not Decimal(".70") <= Decimal(self.inside_ratio) <= 1
        ):
            raise ValueError("EVENT_RANGE_GEOMETRY")
        if not 2 <= Decimal(self.width_atr) <= 12 or self.touches < 4 or len(self.reactions) < 4:
            raise ValueError("EVENT_RANGE_SUPPORT")
        if any(a == b for a, b in zip(self.reactions, self.reactions[1:], strict=False)):
            raise ValueError("EVENT_RANGE_REACTION_ORDER")
        return self


class Readiness(Closed):
    atr: bool
    micro: bool
    major: bool
    zone: bool
    range: bool


class Frame(Closed):
    index: Index
    bar_ref: Hash
    atr: Price | None
    micro: tuple[Hash, ...]
    major: tuple[Hash, ...]
    zones: tuple[Hash, ...]
    ranges: tuple[Hash, ...]
    active_range: Hash | None
    readiness: Readiness
    base_regime: Regime


class ContextEvidence(Closed):
    schema_version: Literal["paqs-q-event-context-evidence-v1"]
    series_key: Hash
    prefix_hashes: tuple[Hash, ...]
    strict_confirmation: bool
    limitations: tuple[str, ...]
    calendar_refs: tuple[Hash, ...]
    pivots: tuple[PivotEvidence, ...]
    zones: tuple[ZoneEvidence, ...]
    ranges: tuple[RangeEvidence, ...]
    frames: tuple[Frame, ...]


class Source(Closed):
    source_key: Hash
    version_key: Hash
    source_type: Literal["MAJOR_SWING", "ZONE", "RANGE_BOUNDARY"]
    role: Literal["SUPPORT", "RESISTANCE"]
    lower: Price
    upper: Price
    confirmation_index: Index
    support_refs: tuple[Hash, ...]
    range_key: Hash | None
    range_version: Hash | None

    @model_validator(mode="after")
    def geometry(self) -> "Source":
        if Decimal(self.lower) > Decimal(self.upper) or not self.support_refs:
            raise ValueError("EVENT_SOURCE_GEOMETRY")
        if self.source_type == "RANGE_BOUNDARY":
            if self.range_key is None or self.range_version is None:
                raise ValueError("EVENT_RANGE_SOURCE_BINDING")
        elif self.range_key is not None or self.range_version is not None:
            raise ValueError("EVENT_UNEXPECTED_RANGE_BINDING")
        if self.source_type == "MAJOR_SWING" and self.lower != self.upper:
            raise ValueError("EVENT_SWING_MUST_BE_POINT")
        return self


class Guard(Closed):
    kind: Literal["BREAKOUT", "RECLAIM"]
    direction: Direction
    boundary: Price
    atr_buffer: Price

    @model_validator(mode="after")
    def scale(self) -> "Guard":
        if self.atr_buffer != ("0.15" if self.kind == "BREAKOUT" else "0.1"):
            raise ValueError("EVENT_GUARD_PROFILE")
        return self


class EventEvidence(Closed):
    schema_version: Literal["paqs-q-price-event-evidence-v1"]
    event_key: Hash
    kind: Literal[
        "ATTEMPT",
        "BREAKOUT",
        "BREAKDOWN",
        "EXCURSION",
        "FAILED_BREAK",
        "BREAKOUT_FAILURE",
        "RETEST",
        "TRANSITION",
        "PRICE_PATTERN",
        "PRICE_TRIGGER_CANDIDATE",
        "FOLLOW_THROUGH",
        "EVENT_INVALIDATED",
    ]
    bar_index: Index
    direction: Direction
    status: Literal[
        "OBSERVED",
        "PENDING",
        "CONFIRMED",
        "START",
        "HOLD",
        "FAILURE",
        "EXPIRED",
        "FAILED",
        "NONE",
        "CANCELLED",
    ]
    source: Source | None
    anchor_key: Hash | None
    related_keys: tuple[Hash, ...]
    reasons: tuple[str, ...]
    event_guard: Guard | None
    atr: Price
    trigger_reasons: tuple[Literal["MICRO", "STRONG", "EVENT_CONFIRMATION"], ...]
    retest_number: Index | None
    regime: Regime | None
    excursion_extreme: Price | None

    @model_validator(mode="after")
    def consistency(self) -> "EventEvidence":
        states = {
            "ATTEMPT": {"OBSERVED"},
            "BREAKOUT": {"CONFIRMED"},
            "BREAKDOWN": {"CONFIRMED"},
            "EXCURSION": {"PENDING", "EXPIRED", "CANCELLED"},
            "FAILED_BREAK": {"CONFIRMED"},
            "BREAKOUT_FAILURE": {"CONFIRMED"},
            "RETEST": {"START", "HOLD", "FAILURE", "EXPIRED"},
            "TRANSITION": {"PENDING", "CONFIRMED", "CANCELLED"},
            "PRICE_PATTERN": {"OBSERVED"},
            "PRICE_TRIGGER_CANDIDATE": {"CONFIRMED"},
            "FOLLOW_THROUGH": {"PENDING", "CONFIRMED", "NONE", "FAILED"},
            "EVENT_INVALIDATED": {"FAILED"},
        }
        if self.status not in states[self.kind] or Decimal(self.atr) < 0 or not self.reasons:
            raise ValueError("EVENT_STATE_INVALID")
        if self.source is not None and self.source.confirmation_index >= self.bar_index:
            raise ValueError("EVENT_SOURCE_NOT_KNOWN_BEFORE_BAR")
        if (self.anchor_key is None) != (self.event_guard is None):
            raise ValueError("EVENT_ANCHOR_GUARD_BINDING")
        if self.event_guard is not None and self.event_guard.direction != self.direction:
            raise ValueError("EVENT_GUARD_DIRECTION")
        if self.kind == "PRICE_PATTERN" and (
            self.source is not None or self.anchor_key is not None
        ):
            raise ValueError("UNANCHORED_PATTERN_HAS_CONTEXT")
        if self.kind not in {"ATTEMPT", "EXCURSION", "PRICE_PATTERN"} and self.anchor_key is None:
            raise ValueError("EVENT_ANCHOR_REQUIRED")
        if (self.kind == "RETEST") != (self.retest_number is not None):
            raise ValueError("EVENT_RETEST_ORDINAL")
        if self.kind == "RETEST" and self.status in {"START", "HOLD"} and self.retest_number == 0:
            raise ValueError("EVENT_RETEST_NOT_STARTED")
        if (self.kind == "TRANSITION") != (self.regime is not None):
            raise ValueError("EVENT_TRANSITION_REGIME")
        return self


class EventSummary(Closed):
    schema_version: Literal["paqs-q-price-event-summary-v1"]
    strict_confirmation: bool
    limitations: tuple[str, ...]
    readiness: Readiness
    regime: Regime
    event_count: Index
    classification: Literal["NO_EVENTS", "EVENTS_PRESENT", "COMPONENTS_WARMING"]
