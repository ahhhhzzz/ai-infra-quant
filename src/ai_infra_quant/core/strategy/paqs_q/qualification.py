"""Selected-window price qualification; acquisition/version preparation stays outside core."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from ai_infra_quant.core.domain.paqs_q.canonical import canonical, utc
from ai_infra_quant.core.domain.paqs_q.inputs import WINDOWS, Bar, QInput, q


@dataclass(frozen=True)
class Parameters:
    timeframe: str

    @classmethod
    def default(cls, timeframe: str) -> "Parameters":
        return cls(timeframe)

    @property
    def warm(self) -> int:
        return WINDOWS[self.timeframe][0]

    @property
    def total(self) -> int:
        return sum(WINDOWS[self.timeframe])


def quality_error(bar: Bar, data: QInput) -> str | None:
    """Aggregate quality may be more conservative, never more certain, than a used bar."""
    ranks = {"COMPLETE": 0, "PARTIAL": 1, "UNKNOWN": 2}
    if not isinstance(bar.coverage, str) or bar.coverage not in ranks:
        return "BAR_COVERAGE_INVALID"
    if data.quality in ranks and ranks[data.quality] < ranks[bar.coverage]:
        return "AGGREGATE_BAR_QUALITY_CONFLICT"
    return None


def prepare(data: QInput, cutoff: datetime) -> tuple[Bar, ...]:
    """Select versions before price validation, so unavailable future payloads cannot leak."""
    utc(cutoff)
    expected = {"US": "America/New_York", "HK": "Asia/Hong_Kong"}
    market, _, symbol = data.security.partition(".")
    if market not in expected or data.market_timezone != expected[market]:
        raise ValueError("IDENTITY_TIMEZONE_CONFLICT")
    pattern = r"[A-Z0-9]+(?:[.-][A-Z0-9]+)*" if market == "US" else r"[0-9]{5}"
    if len(symbol) > 32 or re.fullmatch(pattern, symbol) is None:
        raise ValueError("CANONICAL_IDENTITY_INVALID")
    if data.quality not in {"COMPLETE", "PARTIAL", "UNKNOWN", "INVALID"}:
        raise ValueError("QUALITY_INVALID")
    if data.mode not in {"AS_OF", "OBSERVATIONAL"}:
        raise ValueError("OBSERVATION_MODE_INVALID")
    if len(data.bars) > 100000:
        raise ValueError("INPUT_BOUND")
    versions: dict[datetime, list[Bar]] = {}
    for bar in data.bars:
        if utc(bar.completed_at) > cutoff or not bar.completed:
            continue
        if bar.available_at is not None and utc(bar.available_at) > cutoff:
            continue
        if bar.available_at is None and data.mode == "AS_OF":
            continue
        versions.setdefault(utc(bar.start), []).append(bar)
    selected: list[Bar] = []
    minimum = datetime.min.replace(tzinfo=UTC)
    for key in sorted(versions):
        group = versions[key]
        latest = max(utc(b.available_at) if b.available_at is not None else minimum for b in group)
        finalists = [
            b
            for b in group
            if (utc(b.available_at) if b.available_at is not None else minimum) == latest
        ]
        if len({canonical(b.observation()) for b in finalists}) != 1:
            raise ValueError("CONFLICTING_TIME_VERSION")
        if (
            any(b.available_at is None for b in group)
            and any(b.available_at is not None for b in group)
            and len({canonical(b.observation()) for b in group}) != 1
        ):
            raise ValueError("UNORDERABLE_UNKNOWN_VERSION")
        bar = finalists[0]
        # Exclude only legitimate partial derived bars, after selecting the current version.
        # Invalid or contradictory quality remains visible for bounded fail-closed validation.
        if (
            bar.timeframe in {"W1", "M30"}
            and bar.coverage != "COMPLETE"
            and not quality_error(bar, data)
        ):
            continue
        selected.append(bar)
    return tuple(selected)


def validate_window(bars: tuple[Bar, ...], data: QInput) -> None:
    previous: Bar | None = None
    for bar in bars:
        if error := quality_error(bar, data):
            raise ValueError(error)
        if type(bar.completed) is not bool:
            raise ValueError("COMPLETION_FLAG_NOT_BOOLEAN")
        if (bar.security, bar.timeframe) != (data.security, data.timeframe):
            raise ValueError("BAR_IDENTITY_CONFLICT")
        start, end, completed = utc(bar.start), utc(bar.end), utc(bar.completed_at)
        utc(bar.retrieved_at)
        if end <= start or completed < start:
            raise ValueError("BAR_TIME_INVALID")
        if bar.available_at is not None and utc(bar.available_at) < completed:
            raise ValueError("AVAILABLE_BEFORE_COMPLETION")
        if previous is not None and start < previous.end:
            raise ValueError("OVERLAPPING_INTERVALS")
        if bar.timeframe != "W1" and completed < end:
            raise ValueError("COMPLETION_BEFORE_END")
        if bar.timeframe == "M30" and (
            end - start != timedelta(minutes=30) or bar.session != "REGULAR"
        ):
            raise ValueError("M30_SESSION_INVALID")
        values = (bar.open, bar.high, bar.low, bar.close, bar.volume)
        for value in values:
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError("NONFINITE_OR_NONDECIMAL")
            if abs(value) >= Decimal("1e20") or q(value) != value:
                raise ValueError("DECIMAL_38_18_BOUND")
        if min(values[:4]) <= 0 or bar.volume < 0:
            raise ValueError("NONPOSITIVE_PRICE_OR_NEGATIVE_VOLUME")
        if bar.high < max(bar.open, bar.low, bar.close) or bar.low > min(
            bar.open, bar.high, bar.close
        ):
            raise ValueError("OHLC_INVALID")
        previous = bar
    if len({bar.adjustment for bar in bars}) > 1:
        raise ValueError("ADJUSTMENT_BASIS_MISMATCH")
