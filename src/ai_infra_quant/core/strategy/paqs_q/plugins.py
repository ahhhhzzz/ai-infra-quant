"""B0/A1 semantic adapter; the sole difference is the prior-raw veto."""

from dataclasses import dataclass
from decimal import localcontext
from typing import Any

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON
from ai_infra_quant.core.domain.paqs_q.inputs import CONTEXT, QInput
from ai_infra_quant.core.domain.paqs_q.results import (
    Config,
    Descriptor,
    QResult,
    Record,
    Status,
    make_record,
    make_result,
    structure_config,
)

from .local import costs, evaluate


@dataclass(frozen=True, slots=True)
class LocalStructurePlugin:
    descriptor: Descriptor
    prior_raw_veto: bool

    def __post_init__(self) -> None:
        expected = (
            ("paqs-q-structure-b0", "1.0.0", "REFERENCE")
            if self.prior_raw_veto
            else ("paqs-q-structure-a1", "0.1.0", "EXPERIMENTAL")
        )
        d = self.descriptor
        if (d.strategy_id, d.strategy_version, d.plugin_status) != expected:
            raise ValueError("LOCAL_PLUGIN_BINDING_CONFLICT")

    def resolve_config(self, supplied: Config | None) -> Config:
        default = structure_config()
        if supplied is not None and supplied != default:
            raise ValueError("OUTSIDE_FROZEN_PROFILE")
        return default

    def evaluate(self, data: QInput, config: Config) -> QResult:
        config = self.resolve_config(config)
        if problem := data.problem():
            return make_result(data, self.descriptor, config, "INVALID", (problem,))
        with localcontext(CONTEXT):
            legacy = evaluate(
                data, data.calendar, data.as_of, data.mode, prior_raw_veto=self.prior_raw_veto
            )
            legacy["costs"] = costs(legacy)
        if legacy["status"] != "VALID":
            status: Status = "INVALID" if legacy["status"] == "INVALID" else "INSUFFICIENT"
            return make_result(data, self.descriptor, config, status, (legacy["reason"],))
        if legacy["costs"]["complete_support_active"] == 0:
            return make_result(
                data, self.descriptor, config, "INSUFFICIENT", ("CALENDAR_SUPPORT_UNAVAILABLE",)
            )
        records: list[Record] = []
        bars = {b.ref: b for b in data.bars}
        facts = {f.ref: f for f in data.calendar}
        for event in legacy["events"]:
            row = legacy["census"][event["index"]]
            identity: dict[str, Any] = {
                "record_type": "STRUCTURE",
                "extreme_time": event["extreme_time"],
                "confirmation_time": event["reversal_time"],
                "kind": event["kind"],
                "extreme_ref": event["extreme_ref"],
                "confirmation_ref": event["confirmation_ref"],
                "price": event["price"],
                "price_support": [bars[r].payload() for r in row["price_support"]],
                "calendar_support": [facts[r].payload() for _, r in row["calendar_support"]],
                "legacy": {
                    k: event[k]
                    for k in (
                        "key",
                        "identity",
                        "support_hash",
                        "available_at",
                        "mode",
                        "scale",
                        "segment",
                    )
                },
            }
            records.append(
                make_record(
                    data,
                    self.descriptor,
                    config,
                    identity,
                    {k: event[k] for k in ("index", "age_bars")},
                )
            )
        projection = {
            k: legacy[k]
            for k in (
                "rule",
                "security",
                "timeframe",
                "cutoff",
                "mode",
                "quality",
                "status",
                "reason",
                "strict_confirmation",
                "window_hash",
                "calendar_hash",
                "events",
                "census",
                "costs",
            )
        }
        # Complete selected input remains hash-bound; result evidence contains the qualified window.
        return make_result(
            data,
            self.descriptor,
            config,
            "AVAILABLE",
            (legacy["reason"],),
            tuple(records),
            FrozenJSON.of(projection),
        )
