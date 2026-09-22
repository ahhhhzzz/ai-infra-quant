from dataclasses import replace
from decimal import Decimal

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, digest
from ai_infra_quant.core.domain.paqs_q.event_reference import ContextEvidence, Frame, Source
from ai_infra_quant.core.domain.paqs_q.inputs import QInput
from ai_infra_quant.core.strategy.paqs_q.event_context import compute_context, series_prefixes
from ai_infra_quant.core.strategy.paqs_q.event_rules import Replay
from tools.research.event_engine.data import daily_input

D = Decimal


def candle(c="100", *, o=None, h=None, low=None):
    opened, close = D(o or c), D(c)
    return (
        str(opened),
        str(D(h) if h is not None else max(opened, close) + D(".1")),
        str(D(low) if low is not None else min(opened, close) - D(".1")),
        str(close),
    )


def prefix(data: QInput, count: int) -> QInput:
    bars = data.bars[:count]
    calendar = tuple(f for f in data.calendar if f.day <= bars[-1].completed_at.date())
    return replace(data, bars=bars, calendar=calendar, as_of=bars[-1].completed_at)


def replay(data):
    context = compute_context(data)
    facts, regime = Replay(data, context).run()
    return context, facts, regime


def controlled(monkeypatch, rows, *, sign=1, first="99"):
    """Isolated equation tests use constant ATR=1. E2E tests separately use real context."""
    values = [candle(first), candle(first), *rows]
    if sign == -1:
        values = [
            (str(200 - D(o)), str(200 - D(low)), str(200 - D(h)), str(200 - D(c)))
            for o, h, low, c in values
        ]
    data = daily_input(values)
    series, prefixes = series_prefixes(data)
    frames = tuple(
        Frame.model_validate_json(
            FrozenJSON.of(
                {
                    "index": i,
                    "bar_ref": b.version_ref,
                    "atr": "1",
                    "micro": (),
                    "major": (),
                    "zones": (),
                    "ranges": (),
                    "active_range": None,
                    "base_regime": "UNCERTAIN",
                    "readiness": {
                        "atr": True,
                        "micro": False,
                        "major": False,
                        "zone": False,
                        "range": False,
                    },
                }
            ).data
        )
        for i, b in enumerate(data.bars)
    )
    context = ContextEvidence(
        schema_version="paqs-q-event-context-evidence-v1",
        series_key=series,
        prefix_hashes=prefixes,
        strict_confirmation=True,
        limitations=(),
        calendar_refs=tuple(f.ref for f in data.calendar),
        pivots=(),
        zones=(),
        ranges=(),
        frames=frames,
    )
    row = {
        "source_key": digest("unit-source", sign),
        "source_type": "MAJOR_SWING",
        "role": "RESISTANCE" if sign == 1 else "SUPPORT",
        "lower": "100",
        "upper": "100",
        "confirmation_index": 1,
        "support_refs": (data.bars[0].version_ref, data.bars[1].version_ref),
        "range_key": None,
        "range_version": None,
    }
    source = Source.model_validate_json(
        FrozenJSON.of({**row, "version_key": digest("unit-version", row)}).data
    )
    monkeypatch.setattr(
        "ai_infra_quant.core.strategy.paqs_q.event_rules.sources",
        lambda c, f: (source,) if f.index >= 1 else (),
    )
    engine = Replay(data, context)
    # These are isolated price/window equations; transitions use real context E2E below.
    monkeypatch.setattr(engine, "open_transition", lambda a, f: None)
    return data, context, engine, source


def select(facts, kind, status=None):
    return [e for e in facts if e.kind == kind and (status is None or e.status == status)]
