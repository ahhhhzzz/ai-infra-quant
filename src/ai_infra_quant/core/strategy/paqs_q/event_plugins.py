"""F1 adapters for explicitly selected context and Event reference implementations."""

from dataclasses import dataclass
from typing import cast

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON
from ai_infra_quant.core.domain.paqs_q.event_reference import ContextEvidence, EventSummary
from ai_infra_quant.core.domain.paqs_q.inputs import QInput
from ai_infra_quant.core.domain.paqs_q.results import (
    Config,
    Descriptor,
    QResult,
    Status,
    make_record,
    make_result,
)

from .calendar import slot
from .event_calendar import Insufficient, qualify
from .event_context import (
    CAPABILITY,
    CONTEXT_ID,
    EVENT_ID,
    VERSION,
    compute_context,
    context_config,
    validate_context,
)
from .event_rules import Replay, event_config


@dataclass(frozen=True, slots=True)
class ContextPlugin:
    descriptor: Descriptor

    def __post_init__(self) -> None:
        if (self.descriptor.strategy_id, self.descriptor.strategy_version) != (CONTEXT_ID, VERSION):
            raise ValueError("CONTEXT_DESCRIPTOR_MISMATCH")

    def resolve_config(self, supplied: Config | None) -> Config:
        default = context_config()
        if supplied is not None and supplied != default:
            raise ValueError("OUTSIDE_EVENT_CONTEXT_V1_PROFILE")
        return default

    def evaluate(self, data: QInput, config: Config) -> QResult:
        config = self.resolve_config(config)
        try:
            context = compute_context(data)
        except (Insufficient, ValueError) as exc:
            status: Status = "INSUFFICIENT" if isinstance(exc, Insufficient) else "INVALID"
            return make_result(data, self.descriptor, config, status, (str(exc),))
        days = {f.day: f for f in data.calendar}
        records = []
        for p in context.pivots:
            e, c = data.bars[p.extreme_index], data.bars[p.confirmation_index]
            facts = {f.ref: f for b in (e, c) for f in slot(b, days, data.mode)[0]}
            records.append(
                make_record(
                    data,
                    self.descriptor,
                    config,
                    {
                        "record_type": "STRUCTURE",
                        "extreme_time": e.completed_at,
                        "confirmation_time": c.completed_at,
                        "kind": p.kind,
                        "price": getattr(e, "high" if p.kind == "HIGH" else "low"),
                        "extreme_ref": e.ref,
                        "confirmation_ref": c.ref,
                        "price_support": [e.payload(), c.payload()],
                        "calendar_support": [f.payload() for f in facts.values()],
                        "legacy": {
                            "schema_version": "paqs-q-reference-pivot-v1",
                            "pivot": p.model_dump(),
                        },
                    },
                )
            )
        return make_result(
            data,
            self.descriptor,
            config,
            "AVAILABLE",
            (
                "REFERENCE_CONTEXT_READY"
                if context.frames[-1].readiness.atr
                else "COMPONENTS_WARMING",
            ),
            tuple(records),
            context.frozen(),
        )


@dataclass(frozen=True, slots=True)
class ReferenceEventPlugin:
    descriptor: Descriptor

    def __post_init__(self) -> None:
        if (self.descriptor.strategy_id, self.descriptor.strategy_version) != (EVENT_ID, VERSION):
            raise ValueError("EVENT_DESCRIPTOR_MISMATCH")

    def resolve_config(self, supplied: Config | None) -> Config:
        default = event_config()
        if supplied is not None and supplied != default:
            raise ValueError("OUTSIDE_EVENT_V1_PROFILE")
        return default

    def evaluate(self, data: QInput, structure: QResult, config: Config) -> QResult:
        config = self.resolve_config(config)
        if CAPABILITY not in structure.document()["capabilities"]:
            raise ValueError("CAPABILITY_INCOMPATIBLE")
        try:
            qualify(data)
            context = ContextEvidence.model_validate_json(
                FrozenJSON.of(structure.document()["evidence"]).data
            )
            validate_context(context, data)
        except (Insufficient, ValueError) as exc:
            status: Status = "INSUFFICIENT" if isinstance(exc, Insufficient) else "INVALID"
            return make_result(
                data,
                self.descriptor,
                config,
                status,
                (
                    str(exc)
                    if isinstance(exc, Insufficient)
                    else "UPSTREAM_CONTEXT_EVIDENCE_INVALID",
                ),
                upstream=structure,
            )
        facts, regime = Replay(data, context).run()
        records = tuple(
            make_record(
                data,
                self.descriptor,
                config,
                {
                    "record_type": "EVENT",
                    "effective_at": data.bars[f.bar_index].completed_at,
                    "event_type": f.kind,
                    "evidence": f.model_dump(),
                    "upstream_structure_hash": structure.canonical_result_hash,
                },
            )
            for f in facts
        )
        readiness = context.frames[-1].readiness
        summary = EventSummary(
            schema_version="paqs-q-price-event-summary-v1",
            strict_confirmation=context.strict_confirmation,
            limitations=context.limitations,
            readiness=readiness,
            regime=regime,
            event_count=len(facts),
            classification="EVENTS_PRESENT"
            if facts
            else "NO_EVENTS"
            if readiness.atr
            else "COMPONENTS_WARMING",
        )
        return make_result(
            data,
            self.descriptor,
            config,
            "AVAILABLE",
            (cast(str, summary.classification),),
            records,
            summary.frozen(),
            structure,
        )
