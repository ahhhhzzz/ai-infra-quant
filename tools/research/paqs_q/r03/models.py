"""Two miniature proposed semantics: local certificates and recognition records."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, localcontext
from itertools import pairwise

from ..engine import prepare, validate_window
from ..temporal import availability_check
from ..types import CONTEXT, Bar, Dataset, digest, utc

LOCAL = "PROPOSED_SEMANTICS:R03-LOCAL-1"
RECORD = "PROPOSED_SEMANTICS:R03-RECORD-1"
N = 8


@dataclass(frozen=True)
class Event:
    kind: str
    price: Decimal
    extreme_ref: str
    confirmation_ref: str
    extreme_time: datetime
    reversal_time: datetime
    available_at: datetime
    support: tuple[str, ...]
    versions: tuple[str, ...]
    identity: str


@dataclass(frozen=True)
class Snapshot:
    rule: str
    cutoff: datetime
    warm: int
    status: str
    reason: str
    events: tuple[Event, ...]
    refs: tuple[str, ...]
    versions: tuple[str, ...]
    active_refs: tuple[str, ...]


def version(bar: Bar) -> str:
    # Source strings/retrieval time are transport provenance, not selected version identity.
    return digest("r03-version", (bar.ref, bar.available_at))


def raw(
    high: tuple[Decimal, ...], low: tuple[Decimal, ...], close: tuple[Decimal, ...], j: int
) -> tuple[bool, bool]:
    """Pure arithmetic kernel. Public callers validate shape/quality/time first."""
    scale = high[j - 1] - low[j - 1]
    down = scale > 0 and high[j] > max(high[j - 1], high[j + 1]) and high[j] - close[j + 1] >= scale
    up = scale > 0 and low[j] < min(low[j - 1], low[j + 1]) and close[j + 1] - low[j] >= scale
    return down, up


def kernel(
    high: tuple[Decimal, ...], low: tuple[Decimal, ...], close: tuple[Decimal, ...]
) -> tuple[tuple[int, str], ...]:
    if len(high) != len(low) or len(high) != len(close):
        raise ValueError("SHAPE")
    with localcontext(CONTEXT):
        found = []
        for j in range(2, len(high) - 1):
            down, up = raw(high, low, close, j)
            if down != up and not any(raw(high, low, close, j - 1)):
                found.append((j, "HIGH" if down else "LOW"))
        return tuple(found)


def evaluate(data: Dataset, cutoff: datetime, warm: int = 0) -> Snapshot:
    """Strict synthetic model wrapper; never upgrade incomplete market information."""
    utc(cutoff)
    if type(warm) is not int or warm not in (0, 2):
        raise ValueError("MODEL_WARM_DOMAIN")
    bars: tuple[Bar, ...] = ()
    status, reason = "INVALID", "INVALID_INPUT"
    events: tuple[Event, ...] = ()
    with localcontext(CONTEXT):
        try:
            bars = prepare(data, cutoff)[-N:]
            validate_window(bars, data)
            if availability_check(bars, data, cutoff)["violation_count"]:
                raise ValueError("TIME_BOUNDARY")
            if data.quality == "INVALID":
                raise ValueError("SOURCE_QUALITY_INVALID")
            if len(bars) != N:
                status, reason = "UNCERTAIN", "INSUFFICIENT_SUPPORT"
            elif data.quality != "COMPLETE" or data.mode != "AS_OF":
                status, reason = "UNCERTAIN", "STRICT_COMPLETE_AS_OF_REQUIRED"
            elif any(b.coverage != "COMPLETE" or b.available_at is None for b in bars):
                status, reason = "UNCERTAIN", "INCOMPLETE_EVIDENCE"
            elif any(
                a.end != b.start or a.end - a.start != b.end - b.start for a, b in pairwise(bars)
            ):
                status, reason = "UNCERTAIN", "GAP_OR_NONUNIFORM_INTERVAL"
            else:
                status, reason = "VALID", "LOCAL_CERTIFICATES_ONLY"
                events = build_events(bars, warm)
        except (ValueError, TypeError, ArithmeticError) as exc:
            status, reason = "INVALID", str(exc) if isinstance(exc, ValueError) else "NUMERIC"
            # A malformed selected record cannot be hashed into purported valid evidence.
            bars = ()
    return Snapshot(
        LOCAL,
        cutoff,
        warm,
        status,
        reason,
        events,
        tuple(b.ref for b in bars),
        tuple(version(b) for b in bars),
        tuple(b.ref for b in bars[warm:]),
    )


def build_events(bars: tuple[Bar, ...], warm: int) -> tuple[Event, ...]:
    result = []
    for j, kind in kernel(
        tuple(b.high for b in bars), tuple(b.low for b in bars), tuple(b.close for b in bars)
    ):
        if j < warm:
            continue
        support = bars[j - 2 : j + 2]
        refs = tuple(b.ref for b in support)
        versions = tuple(version(b) for b in support)
        price = bars[j].high if kind == "HIGH" else bars[j].low
        available = max(b.available_at for b in support if b.available_at is not None)
        identity = digest(LOCAL, (kind, price, refs, versions))
        result.append(
            Event(
                kind,
                price,
                bars[j].ref,
                bars[j + 1].ref,
                bars[j].end,
                bars[j + 1].completed_at,
                available,
                refs,
                versions,
                identity,
            )
        )
    return tuple(result)


@dataclass(frozen=True)
class Recognition:
    event: Event
    recognized_at: datetime
    lineage_before: str


@dataclass(frozen=True)
class History:
    """Explicit in-memory initial state and supplied schedule; no persisted ledger."""

    records: tuple[Recognition, ...] = ()
    cutoff: datetime | None = None
    lineage: str = digest(RECORD, "EMPTY")
    steps: int = 0


def advance(history: History, snapshot: Snapshot) -> History:
    if snapshot.rule != LOCAL or (history.cutoff is not None and snapshot.cutoff <= history.cutoff):
        raise ValueError("SCHEDULE_OR_MODEL")
    additions = []
    seen = {r.event.identity for r in history.records}
    if snapshot.status == "VALID":
        for event in snapshot.events:
            if event.available_at > snapshot.cutoff or event.reversal_time > snapshot.cutoff:
                raise ValueError("RECOGNITION_BEFORE_EVIDENCE")
            if event.identity not in seen:
                additions.append(Recognition(event, snapshot.cutoff, history.lineage))
                seen.add(event.identity)
    return History(
        history.records + tuple(additions),
        snapshot.cutoff,
        digest(RECORD, (history.lineage, snapshot)),
        history.steps + 1,
    )


def projection(history: History, snapshot: Snapshot) -> tuple[tuple[str, str], ...]:
    current = {e.identity for e in snapshot.events}
    active = set(snapshot.active_refs)
    return tuple(
        (
            r.event.identity,
            "CURRENT_SUPPORTED"
            if r.event.identity in current
            else "ENDPOINT_EXPIRED_OR_REVISED"
            if not {r.event.extreme_ref, r.event.confirmation_ref} <= active
            else "CURRENT_UNSUPPORTED",
        )
        for r in history.records
    )


def transition(old: Snapshot, new: Snapshot) -> dict[str, int]:
    """Keep endpoint metric; separately disclose stricter full-support opportunity loss."""

    def key(e: Event) -> str:
        return digest("r03-endpoint-metric", (e.kind, e.price, e.extreme_ref, e.confirmation_ref))

    a = {key(e): e for e in old.events}
    b = {key(e): e for e in new.events}
    common = set(old.active_refs) & set(new.active_refs)

    def eligible(e: Event) -> bool:
        return {e.extreme_ref, e.confirmation_ref} <= common

    opportunities = {k for k, e in a.items() if eligible(e)}
    full = {k for k in opportunities if set(a[k].versions) <= set(new.versions)}
    return {
        "endpoint_opportunities": len(opportunities),
        "lost": len(opportunities - b.keys()),
        "rediscovered": sum(
            k not in a and eligible(e) and e.reversal_time <= old.cutoff for k, e in b.items()
        ),
        "newly_confirmed": sum(e.reversal_time > old.cutoff for e in b.values()),
        "expired": sum(not eligible(e) for e in a.values()),
        "full_support_opportunities": len(full),
        "full_support_lost": len(full - b.keys()),
        "common_endpoint_witness_changed": sum(
            a[k].identity != b[k].identity for k in a.keys() & b.keys()
        ),
        "coverage_removed": len(opportunities - full),
    }
