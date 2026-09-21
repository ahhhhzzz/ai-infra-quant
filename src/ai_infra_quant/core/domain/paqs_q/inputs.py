"""Immutable selected canonical facts, separate from acquisition and live snapshots."""

import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Any

from .canonical import FrozenJSON, digest, hash_text, legacy_digest, primitive, utc

CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
WINDOWS = {"W1": (26, 104), "D1": (60, 252), "M30": (40, 160)}
INPUT_SCHEMA = "paqs-q-input-v1"


def q(value: Decimal) -> Decimal:
    with localcontext(CONTEXT):
        result = value.quantize(Decimal("1e-18"))
    return result.copy_abs() if result == 0 else result


@dataclass(frozen=True, slots=True)
class Bar:
    security: str
    timeframe: str
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

    def __post_init__(self) -> None:
        for name in ("start", "end", "completed_at", "retrieved_at"):
            object.__setattr__(self, name, utc(getattr(self, name)))
        if self.available_at is not None:
            object.__setattr__(self, "available_at", utc(self.available_at))
        for value in (self.open, self.high, self.low, self.close, self.volume):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError("FINITE_DECIMAL_REQUIRED")
        if type(self.completed) is not bool:
            raise ValueError("COMPLETION_FLAG_NOT_BOOLEAN")
        if any(
            type(v) is not str
            for v in (
                self.security,
                self.timeframe,
                self.coverage,
                self.adjustment,
                self.session,
                self.source_ref,
            )
        ):
            raise ValueError("BAR_STRING_REQUIRED")

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

    @property
    def ref(self) -> str:
        return legacy_digest("qstr-bar", self.observation())

    @property
    def version_ref(self) -> str:
        return legacy_digest("r03-version", (self.ref, self.available_at))

    def payload(self) -> dict[str, Any]:
        return {
            "security_id": self.security,
            "timeframe": self.timeframe,
            "start_utc": self.start,
            "end": self.end,
            "completed_at": self.completed_at,
            "available_at": self.available_at,
            "retrieved_at": self.retrieved_at,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "completed": self.completed,
            "coverage": self.coverage,
            "adjustment": self.adjustment,
            "session": self.session,
            "source_ref": self.source_ref,
            "version_ref": self.version_ref,
        }


@dataclass(frozen=True, slots=True)
class Fact:
    day: date
    market: str
    timezone: str
    kind: str
    segments: tuple[tuple[datetime, datetime], ...]
    source: str
    retrieved_at: datetime
    available_at: datetime | None
    complete: bool

    def __post_init__(self) -> None:
        if type(self.day) is not date or type(self.complete) is not bool:
            raise ValueError("CALENDAR_SHAPE")
        if any(type(v) is not str for v in (self.market, self.timezone, self.kind, self.source)):
            raise ValueError("CALENDAR_STRING_REQUIRED")
        object.__setattr__(self, "segments", tuple((utc(a), utc(b)) for a, b in self.segments))
        object.__setattr__(self, "retrieved_at", utc(self.retrieved_at))
        if self.available_at is not None:
            object.__setattr__(self, "available_at", utc(self.available_at))

    @property
    def ref(self) -> str:
        return legacy_digest(
            "r04-calendar",
            (
                self.day.isoformat(),
                self.market,
                self.timezone,
                self.kind,
                self.segments,
                self.source,
                self.retrieved_at,
                self.available_at,
                self.complete,
            ),
        )

    def payload(self) -> dict[str, Any]:
        return {
            "date": self.day,
            "market": self.market,
            "timezone": self.timezone,
            "kind": self.kind,
            "segments": self.segments,
            "source": self.source,
            "retrieved_at": self.retrieved_at,
            "available_at": self.available_at,
            "complete": self.complete,
            "version_ref": self.ref,
        }


@dataclass(frozen=True, slots=True)
class QInput:
    security: str
    market: str
    currency: str
    market_timezone: str
    timeframe: str
    as_of: datetime
    bars: tuple[Bar, ...]
    calendar: tuple[Fact, ...]
    quality: str = "COMPLETE"
    mode: str = "AS_OF"
    snapshot_identity: str | None = None
    provenance: FrozenJSON = field(default_factory=lambda: FrozenJSON(b"{}"))
    schema_version: str = INPUT_SCHEMA
    _hash: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of", utc(self.as_of))
        bars, calendar = tuple(self.bars), tuple(self.calendar)
        if any(type(b) is not Bar for b in bars) or any(type(f) is not Fact for f in calendar):
            raise ValueError("CANONICAL_FACT_TYPE_REQUIRED")
        object.__setattr__(
            self,
            "bars",
            tuple(
                sorted(
                    bars,
                    key=lambda b: (b.security, b.timeframe, b.start, b.completed_at, b.version_ref),
                )
            ),
        )
        object.__setattr__(
            self, "calendar", tuple(sorted(calendar, key=lambda f: (f.market, f.day, f.ref)))
        )
        if type(self.provenance) is not FrozenJSON:
            raise ValueError("FROZEN_PROVENANCE_REQUIRED")
        if self.snapshot_identity is not None:
            hash_text(self.snapshot_identity)
        if self.schema_version != INPUT_SCHEMA:
            raise ValueError("INPUT_SCHEMA_UNSUPPORTED")
        if self.mode not in {"AS_OF", "OBSERVATIONAL"}:
            raise ValueError("OBSERVATION_MODE_INVALID")
        if self.timeframe not in WINDOWS:
            raise ValueError("UNSUPPORTED_TIMEFRAME")
        if self.quality not in {"COMPLETE", "PARTIAL", "UNKNOWN", "INVALID"}:
            raise ValueError("QUALITY_INVALID")
        expected = {"US": ("USD", "America/New_York"), "HK": ("HKD", "Asia/Hong_Kong")}
        if expected.get(self.market) != (self.currency, self.market_timezone):
            raise ValueError("IDENTITY_TIMEZONE_CONFLICT")
        prefix, _, symbol = self.security.partition(".")
        pattern = r"[A-Z0-9]+(?:[.-][A-Z0-9]+)*" if self.market == "US" else r"[0-9]{5}"
        if prefix != self.market or len(symbol) > 32 or re.fullmatch(pattern, symbol) is None:
            raise ValueError("CANONICAL_IDENTITY_INVALID")
        if len(bars) > 100000 or len(calendar) > 10000:
            raise ValueError("INPUT_BOUND")
        object.__setattr__(self, "_hash", digest("paqs-q/input/v1", self.payload()))

    def problem(self) -> str | None:
        if len({(b.security, b.timeframe, b.start) for b in self.bars}) != len(self.bars):
            return "CONFLICTING_TIME_VERSION"
        if len({(f.market, f.day) for f in self.calendar}) != len(self.calendar):
            return "CALENDAR_CONFLICT"
        if any(not b.completed for b in self.bars):
            return "UNFINISHED_BAR"
        if any(
            b.completed_at > self.as_of
            or (b.available_at is not None and b.available_at > self.as_of)
            for b in self.bars
        ):
            return "FUTURE_PRICE_EVIDENCE"
        if any(f.available_at is not None and f.available_at > self.as_of for f in self.calendar):
            return "FUTURE_CALENDAR_EVIDENCE"
        if any(
            f.market != self.market or f.timezone != self.market_timezone for f in self.calendar
        ):
            return "CALENDAR_IDENTITY"
        return None

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "security_id": self.security,
            "market": self.market,
            "currency": self.currency,
            "timezone": self.market_timezone,
            "timeframe": self.timeframe,
            "as_of": self.as_of,
            "qualification_mode": self.mode,
            "quality": self.quality,
            "bars": [b.payload() for b in self.bars],
            "calendar": [f.payload() for f in self.calendar],
            "snapshot_identity": self.snapshot_identity,
            "provenance": self.provenance.document(),
        }

    @property
    def input_hash(self) -> str:
        return self._hash

    def payload_as_of(self) -> str:
        return str(primitive(self.as_of))


def bounded_prefix(source: QInput, cutoff: datetime) -> QInput:
    """Explicit pure preparation of a larger supplied stream, before plugin evaluation.

    Never acquires data. Known future values are excluded before version selection;
    unknown availability is retained only in explicit observational mode.
    """
    cutoff = utc(cutoff)
    groups: dict[datetime, list[Bar]] = {}
    for bar in source.bars:
        if (
            not bar.completed
            or bar.completed_at > cutoff
            or (bar.available_at is not None and bar.available_at > cutoff)
            or (bar.available_at is None and source.mode == "AS_OF")
        ):
            continue
        groups.setdefault(bar.start, []).append(bar)
    selected: list[Bar] = []
    for group in groups.values():
        if (
            any(b.available_at is None for b in group)
            and any(b.available_at is not None for b in group)
            and len({b.ref for b in group}) != 1
        ):
            raise ValueError("UNORDERABLE_UNKNOWN_VERSION")
        latest = max((b.available_at for b in group if b.available_at is not None), default=None)
        candidates = [b for b in group if b.available_at == latest]
        if len({FrozenJSON.of(b.payload()).data for b in candidates}) != 1:
            raise ValueError("CONFLICTING_TIME_VERSION")
        selected.append(candidates[0])
    fact_groups: dict[date, list[Fact]] = {}
    for fact in source.calendar:
        if (fact.available_at is not None and fact.available_at > cutoff) or (
            fact.available_at is None and source.mode == "AS_OF"
        ):
            continue
        fact_groups.setdefault(fact.day, []).append(fact)
    facts: list[Fact] = []
    for group_f in fact_groups.values():
        if (
            any(f.available_at is None for f in group_f)
            and any(f.available_at is not None for f in group_f)
            and len({(f.kind, f.segments, f.complete) for f in group_f}) != 1
        ):
            raise ValueError("CALENDAR_UNKNOWN_VERSION_ORDER")
        newest = max((f.available_at for f in group_f if f.available_at is not None), default=None)
        chosen = [f for f in group_f if f.available_at == newest]
        if len({f.ref for f in chosen}) != 1:
            raise ValueError("CALENDAR_CONFLICT")
        facts.append(chosen[0])
    return replace(source, as_of=cutoff, bars=tuple(selected), calendar=tuple(facts))
