"""Immutable research schemas and context-independent canonical identity."""

import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from hashlib import sha256
from typing import Any, Literal

Timeframe = Literal["W1", "D1", "M30"]
RULE = "QSTR-CANDIDATE-1.1"
CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("1e-18")
WINDOWS = {"W1": (26, 104, "1.8"), "D1": (60, 252, "1.8"), "M30": (40, 160, "1")}


def q(value: Decimal) -> Decimal:
    with localcontext(CONTEXT):
        result = value.quantize(QUANTUM)
    return result.copy_abs() if result == 0 else result


def decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("NONFINITE_NUMBER")
    if value == 0:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("NAIVE_TIME")
    return value.astimezone(UTC)


def primitive(value: Any) -> Any:
    if isinstance(value, Decimal):
        return decimal_text(value)
    if isinstance(value, datetime):
        return utc(value).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: primitive(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): primitive(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [primitive(item) for item in value]
    if value is None or isinstance(value, str | bool | int):
        return value
    raise TypeError(f"NONCANONICAL_TYPE:{type(value).__name__}")


def canonical(value: Any) -> str:
    return json.dumps(
        primitive(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


def digest(domain: str, value: Any) -> str:
    return sha256((domain + "\0" + canonical(value)).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class Parameters:
    timeframe: Timeframe
    pivot_lambda: Decimal
    zone_epsilon: Decimal = Decimal("0.5")
    zone_age: int = 126
    range_length: int = 40

    def __post_init__(self) -> None:
        if self.timeframe not in WINDOWS:
            raise ValueError("UNSUPPORTED_TIMEFRAME")
        choices = ("0.9", "1", "1.1") if self.timeframe == "M30" else ("1.7", "1.8", "1.9")
        if not isinstance(self.pivot_lambda, Decimal) or self.pivot_lambda not in map(
            Decimal, choices
        ):
            raise ValueError("LAMBDA_OUTSIDE_FROZEN_PROFILE")
        if not isinstance(self.zone_epsilon, Decimal) or self.zone_epsilon not in map(
            Decimal, ("0.45", "0.5", "0.55")
        ):
            raise ValueError("EPSILON_OUTSIDE_FROZEN_PROFILE")
        if type(self.zone_age) is not int or self.zone_age not in (100, 126, 160):
            raise ValueError("AGE_OUTSIDE_FROZEN_PROFILE")
        if type(self.range_length) is not int or self.range_length not in (30, 40, 60):
            raise ValueError("RANGE_OUTSIDE_FROZEN_PROFILE")

    @classmethod
    def default(cls, timeframe: Timeframe) -> "Parameters":
        return cls(timeframe, Decimal(WINDOWS[timeframe][2]))

    @property
    def warm(self) -> int:
        return WINDOWS[self.timeframe][0]

    @property
    def active(self) -> int:
        return WINDOWS[self.timeframe][1]

    @property
    def total(self) -> int:
        return self.warm + self.active

    @property
    def config_hash(self) -> str:
        return digest("qstr-config", (RULE, self, self.warm, self.active))


@dataclass(frozen=True, slots=True)
class Bar:
    security: str
    timeframe: Timeframe
    start: datetime
    end: datetime
    completed_at: datetime
    available_at: datetime | None
    retrieved_at: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    completed: bool = True
    coverage: str = "COMPLETE"
    adjustment: str = "SYNTHETIC"
    session: str = "REGULAR"
    source_ref: str = "SYNTHETIC"

    @property
    def ref(self) -> str:
        return digest("qstr-bar", self.observation())

    def observation(self) -> tuple[Any, ...]:
        return (
            self.security,
            self.timeframe,
            self.start,
            self.end,
            self.completed_at,
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
            self.completed,
            self.coverage,
            self.adjustment,
            self.session,
        )


@dataclass(frozen=True, slots=True)
class Dataset:
    security: str
    timeframe: Timeframe
    market_timezone: str
    bars: tuple[Bar, ...]
    quality: str = "COMPLETE"
    mode: str = "AS_OF"
    provenance: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class Evidence:
    rule: str
    operands: tuple[tuple[str, Any], ...]
    comparator: str
    threshold: Any
    refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Pivot:
    kind: str
    price: Decimal
    extreme: int
    confirmed: int
    extreme_ref: str
    confirmed_ref: str
    atr: Decimal
    evidence: Evidence
    identity: str


@dataclass(frozen=True, slots=True)
class Label:
    pivot: str
    previous: str
    value: str
    directional_eligible: bool
    evidence: Evidence


@dataclass(frozen=True, slots=True)
class Zone:
    role: str
    center: Decimal
    atr: Decimal
    mad: Decimal
    half_width: Decimal
    lower: Decimal
    upper: Decimal
    touches: tuple[Pivot, ...]
    identity: str
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True, slots=True)
class Box:
    lower: Decimal
    upper: Decimal
    inside_ratio: Decimal
    width_atr: Decimal
    recent_touches: int
    identity: str
    support: str
    resistance: str
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True, slots=True)
class Result:
    """JSON strings are immutable; parsing them cannot mutate the result."""

    decision_json: str
    diagnostics_json: str
    source_hash: str
    provenance: tuple[tuple[str, str], ...]

    @property
    def semantic_hash(self) -> str:
        return digest("qstr-decision", json.loads(self.decision_json))

    def document(self) -> dict[str, Any]:
        return {
            "semantic_hash": self.semantic_hash,
            "decision": json.loads(self.decision_json),
            "diagnostics": json.loads(self.diagnostics_json),
            "source_hash": self.source_hash,
            "provenance": dict(self.provenance),
        }
