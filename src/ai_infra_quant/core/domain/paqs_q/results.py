"""Immutable descriptors, resolved config, evidence records and result envelopes."""

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from .canonical import FrozenJSON, canonical, digest, hash_text, primitive, utc
from .inputs import INPUT_SCHEMA, QInput

STRUCTURE_SCHEMA = "paqs-q-structure-result-v1"
EVENT_SCHEMA = "paqs-q-event-result-v1"
Status = Literal["AVAILABLE", "INSUFFICIENT", "UNAVAILABLE", "INVALID"]


@dataclass(frozen=True, slots=True)
class Config:
    """Resolved schema-owned config; no silent unknown keys or mutable aliases."""

    schema_version: str
    values: FrozenJSON

    def __post_init__(self) -> None:
        if type(self.schema_version) is not str or not self.schema_version:
            raise ValueError("CONFIG_SCHEMA_REQUIRED")
        if type(self.values) is not FrozenJSON or not isinstance(self.values.document(), dict):
            raise ValueError("CONFIG_OBJECT_REQUIRED")

    @property
    def config_hash(self) -> str:
        return digest(
            "paqs-q/config/v1",
            {"config_schema_version": self.schema_version, "values": self.values.document()},
        )


def structure_config(**values: Any) -> Config:
    defaults = {
        "coefficient": Decimal("1"),
        "W1": (26, 104, 130),
        "D1": (60, 252, 312),
        "M30": (40, 160, 200),
    }
    if set(values) - set(defaults):
        raise ValueError("UNKNOWN_CONFIG_KEY")
    resolved = defaults | values
    if not isinstance(resolved["coefficient"], Decimal):
        raise ValueError("FINITE_DECIMAL_REQUIRED")
    if canonical(resolved) != canonical(defaults):
        raise ValueError("OUTSIDE_FROZEN_PROFILE")
    return Config("paqs-q-local-config-v1", FrozenJSON.of(resolved))


@dataclass(frozen=True, slots=True)
class Descriptor:
    strategy_id: str
    strategy_version: str
    code_hash: str
    capabilities: tuple[str, ...]
    plugin_status: str
    stage: str
    output_schema: str
    lineage: FrozenJSON
    input_schema: str = INPUT_SCHEMA
    structure_schema: str | None = None
    required_capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", self.strategy_id) is None:
            raise ValueError("PLUGIN_ID_INVALID")
        if (
            re.fullmatch(
                r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", self.strategy_version
            )
            is None
        ):
            raise ValueError("PLUGIN_VERSION_INVALID")
        hash_text(self.code_hash)
        if self.plugin_status not in {"REFERENCE", "EXPERIMENTAL", "DISABLED"}:
            raise ValueError("PLUGIN_STATUS_INVALID")
        if self.stage not in {"STRUCTURE", "EVENT"}:
            raise ValueError("PLUGIN_STAGE_INVALID")
        if type(self.lineage) is not FrozenJSON:
            raise ValueError("FROZEN_LINEAGE_REQUIRED")
        for field in ("capabilities", "required_capabilities"):
            values = tuple(getattr(self, field))
            if any(type(v) is not str or not v for v in values):
                raise ValueError("CAPABILITY_INVALID")
            object.__setattr__(self, field, tuple(sorted(set(values))))

    def binding(self, config: Config) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "config_hash": config.config_hash,
            "code_hash": self.code_hash,
            "capabilities": self.capabilities,
            "plugin_status": self.plugin_status,
        }

    def binding_hash(self, config: Config) -> str:
        return digest("paqs-q/binding/v1", self.binding(config))


@dataclass(frozen=True, slots=True)
class Record:
    record_schema_version: str
    record_id: str
    identity: FrozenJSON
    display: FrozenJSON

    def __post_init__(self) -> None:
        hash_text(self.record_id)
        if type(self.identity) is not FrozenJSON or type(self.display) is not FrozenJSON:
            raise ValueError("FROZEN_RECORD_REQUIRED")

    def payload(self) -> dict[str, Any]:
        return {
            "record_schema_version": self.record_schema_version,
            "record_id": self.record_id,
            "record": self.identity.document(),
            "display": self.display.document(),
        }


def make_record(
    data: QInput,
    descriptor: Descriptor,
    config: Config,
    identity: dict[str, Any],
    display: dict[str, Any] | None = None,
) -> Record:
    schema = "paqs-q-" + descriptor.stage.lower() + "-record-v1"
    required = (
        {
            "record_type",
            "extreme_time",
            "confirmation_time",
            "kind",
            "extreme_ref",
            "confirmation_ref",
            "price",
            "price_support",
            "calendar_support",
            "legacy",
        }
        if descriptor.stage == "STRUCTURE"
        else {"record_type", "effective_at", "event_type", "evidence", "upstream_structure_hash"}
    )
    if set(identity) != required:
        raise ValueError("RECORD_FIELDS_INVALID")
    times = (
        ("extreme_time", "confirmation_time")
        if descriptor.stage == "STRUCTURE"
        else ("effective_at",)
    )
    # W1 nominal extreme_time is geometry; confirmation_time is the factual cutoff gate.
    for field in times:
        value = identity[field]
        if not isinstance(value, datetime):
            raise ValueError("RECORD_TIME_REQUIRED")
        if (field != "extreme_time" or data.timeframe != "W1") and utc(value) > data.as_of:
            raise ValueError("FUTURE_RECORD_EVIDENCE")
    if identity["record_type"] != descriptor.stage:
        raise ValueError("RECORD_TYPE_CONFLICT")
    if descriptor.stage == "EVENT":
        hash_text(identity["upstream_structure_hash"])
    preimage = {
        "record_schema_version": schema,
        "binding_hash": descriptor.binding_hash(config),
        "input_hash": data.input_hash,
        "as_of": data.as_of,
        "record": identity,
    }
    return Record(
        schema,
        digest("paqs-q/record/v1", preimage),
        FrozenJSON.of(identity),
        FrozenJSON.of(display or {}),
    )


@dataclass(frozen=True, slots=True)
class QResult:
    """Structure/Event envelope; canonical bytes are the immutable authority."""

    envelope: FrozenJSON

    def __post_init__(self) -> None:
        if type(self.envelope) is not FrozenJSON:
            raise ValueError("FROZEN_RESULT_REQUIRED")
        payload = self.envelope.document()
        if not isinstance(payload, dict):
            raise ValueError("RESULT_OBJECT_REQUIRED")
        expected = {
            "schema_version",
            "strategy_id",
            "strategy_version",
            "config_hash",
            "code_hash",
            "capabilities",
            "plugin_status",
            "input_hash",
            "snapshot_identity",
            "as_of",
            "qualification_mode",
            "lineage",
            "status",
            "reason_codes",
            "records",
            "evidence",
            "upstream_structure_hash",
            "upstream_structure_binding",
            "canonical_result_hash",
        }
        if set(payload) != expected:
            raise ValueError("RESULT_FIELDS_INVALID")
        if payload["schema_version"] not in {STRUCTURE_SCHEMA, EVENT_SCHEMA}:
            raise ValueError("RESULT_SCHEMA_UNSUPPORTED")
        if payload["status"] not in {"AVAILABLE", "INSUFFICIENT", "UNAVAILABLE", "INVALID"}:
            raise ValueError("RESULT_STATUS_INVALID")
        for key in ("config_hash", "code_hash", "input_hash", "canonical_result_hash"):
            hash_text(payload[key])
        if payload["snapshot_identity"] is not None:
            hash_text(payload["snapshot_identity"])
        if payload["qualification_mode"] not in {"AS_OF", "OBSERVATIONAL"}:
            raise ValueError("RESULT_MODE_INVALID")
        if payload["plugin_status"] not in {"REFERENCE", "EXPERIMENTAL", "DISABLED"}:
            raise ValueError("RESULT_PLUGIN_STATUS_INVALID")
        if primitive(utc(datetime.fromisoformat(payload["as_of"]))) != payload["as_of"]:
            raise ValueError("RESULT_TIME_INVALID")
        for key in ("capabilities", "reason_codes"):
            values = payload[key]
            if (
                not isinstance(values, list)
                or any(type(v) is not str for v in values)
                or values != sorted(set(values))
            ):
                raise ValueError("RESULT_SET_ORDER_INVALID")
        if not isinstance(payload["records"], list):
            raise ValueError("RESULT_RECORDS_INVALID")
        record_schema = payload["schema_version"].replace("-result-", "-record-")
        for record in payload["records"]:
            if (
                not isinstance(record, dict)
                or set(record) != {"record_schema_version", "record_id", "record", "display"}
                or record["record_schema_version"] != record_schema
                or not isinstance(record["record"], dict)
                or not isinstance(record["display"], dict)
            ):
                raise ValueError("RESULT_RECORD_SCHEMA_INVALID")
            hash_text(record["record_id"])
        if payload["status"] != "AVAILABLE" and (
            payload["records"] or payload["evidence"] is not None
        ):
            raise ValueError("FAILURE_WITH_SUCCESS_PAYLOAD")
        value = payload.pop("canonical_result_hash")
        if value != digest("paqs-q/result/v1", payload):
            raise ValueError("RESULT_HASH_MISMATCH")

    @property
    def canonical_bytes(self) -> bytes:
        return self.envelope.data

    @property
    def canonical_result_hash(self) -> str:
        return str(self.envelope.document()["canonical_result_hash"])

    @property
    def status(self) -> str:
        return str(self.envelope.document()["status"])

    def document(self) -> dict[str, Any]:
        value: dict[str, Any] = self.envelope.document()
        return value


def make_result(
    data: QInput,
    descriptor: Descriptor,
    config: Config,
    status: Status,
    reasons: tuple[str, ...],
    records: tuple[Record, ...] = (),
    evidence: FrozenJSON | None = None,
    upstream: QResult | None = None,
) -> QResult:
    if descriptor.stage == "STRUCTURE":
        ordered = sorted(
            records,
            key=lambda r: (
                *tuple(
                    r.identity.document()[k]
                    for k in (
                        "extreme_time",
                        "confirmation_time",
                        "kind",
                        "extreme_ref",
                        "confirmation_ref",
                    )
                ),
                r.record_id,
            ),
        )
    else:
        ordered = sorted(
            records,
            key=lambda r: (
                r.identity.document()["effective_at"],
                r.identity.document()["event_type"],
                r.record_id,
            ),
        )
    upstream_doc = upstream.document() if upstream else None
    payload = {
        "schema_version": descriptor.output_schema,
        **descriptor.binding(config),
        "input_hash": data.input_hash,
        "snapshot_identity": data.snapshot_identity,
        "as_of": data.as_of,
        "qualification_mode": data.mode,
        "lineage": descriptor.lineage.document(),
        "status": status,
        "reason_codes": sorted(set(reasons)),
        "records": [r.payload() for r in ordered],
        "evidence": evidence.document() if evidence else None,
        "upstream_structure_hash": upstream.canonical_result_hash if upstream else None,
        "upstream_structure_binding": {k: upstream_doc[k] for k in descriptor.binding(config)}
        if upstream_doc
        else None,
    }
    payload["canonical_result_hash"] = digest("paqs-q/result/v1", payload)
    return QResult(FrozenJSON.of(primitive(payload)))
