"""Immutable descriptors, resolved config, evidence records and result envelopes."""

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from .canonical import FrozenJSON, canonical, decimal_text, digest, hash_text, primitive, utc
from .inputs import INPUT_SCHEMA, Bar, Fact, QInput

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
        if (
            type(self.strategy_id) is not str
            or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", self.strategy_id) is None
        ):
            raise ValueError("PLUGIN_ID_INVALID")
        if (
            type(self.strategy_version) is not str
            or re.fullmatch(
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
        return self.binding_for_hash(config.config_hash)

    def binding_for_hash(self, config_hash: str) -> dict[str, Any]:
        """Bind a retained resolved-config identity without guessing its original values."""
        hash_text(config_hash)
        return {
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "config_hash": config_hash,
            "code_hash": self.code_hash,
            "capabilities": self.capabilities,
            "plugin_status": self.plugin_status,
        }

    def binding_hash(self, config: Config) -> str:
        return digest("paqs-q/binding/v1", self.binding(config))


def _instant(value: Any) -> datetime:
    if type(value) is not str:
        raise ValueError("RECORD_TIME_INVALID")
    instant = utc(datetime.fromisoformat(value))
    if primitive(instant) != value:
        raise ValueError("RECORD_TIME_INVALID")
    return instant


def _decimal(value: Any) -> Decimal:
    if type(value) is not str:
        raise ValueError("RECORD_DECIMAL_INVALID")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("RECORD_DECIMAL_INVALID") from exc
    if not result.is_finite() or decimal_text(result) != value:
        raise ValueError("RECORD_DECIMAL_INVALID")
    return result


def _support(value: Any, *, calendar: bool) -> None:
    """Check the complete named fact schema, including its original version reference."""
    if not isinstance(value, list):
        raise ValueError("RECORD_SUPPORT_INVALID")
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("RECORD_SUPPORT_INVALID")
        fields = dict(item)
        try:
            hash_text(fields.pop("version_ref"))
            for name in ("retrieved_at", "available_at"):
                if fields[name] is not None or name == "retrieved_at":
                    fields[name] = _instant(fields[name])
            fact: Bar | Fact
            if calendar:
                fields["day"] = date.fromisoformat(fields.pop("date"))
                fields["segments"] = tuple(
                    (_instant(a), _instant(b)) for a, b in fields["segments"]
                )
                fact = Fact(**fields)
            else:
                fields["security"] = fields.pop("security_id")
                fields["start"] = fields.pop("start_utc")
                for name in ("start", "end", "completed_at"):
                    fields[name] = _instant(fields[name])
                for name in ("open", "high", "low", "close", "volume"):
                    fields[name] = _decimal(fields[name])
                fact = Bar(**fields)
            # This also rejects omitted fields with dataclass defaults and noncanonical dates.
            if primitive(fact.payload()) != item:
                raise ValueError("RECORD_SUPPORT_INVALID")
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("RECORD_SUPPORT_INVALID") from exc


def _record_identity(schema: str, identity: Any, display: Any) -> None:
    """Shared validation for direct records, factories and decoded result envelopes."""
    if schema not in {"paqs-q-structure-record-v1", "paqs-q-event-record-v1"}:
        raise ValueError("RESULT_RECORD_SCHEMA_INVALID")
    if not isinstance(identity, dict) or not isinstance(display, dict):
        raise ValueError("RECORD_FIELDS_INVALID")
    structure = schema == "paqs-q-structure-record-v1"
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
        if structure
        else {"record_type", "effective_at", "event_type", "evidence", "upstream_structure_hash"}
    )
    if set(identity) != required:
        raise ValueError("RECORD_FIELDS_INVALID")
    if identity["record_type"] != ("STRUCTURE" if structure else "EVENT"):
        raise ValueError("RECORD_TYPE_CONFLICT")
    if structure:
        _instant(identity["extreme_time"])
        _instant(identity["confirmation_time"])
        if type(identity["kind"]) is not str or identity["kind"] not in {"HIGH", "LOW"}:
            raise ValueError("RECORD_KIND_INVALID")
        for key in ("extreme_ref", "confirmation_ref"):
            hash_text(identity[key])
        if _decimal(identity["price"]) <= 0:
            raise ValueError("RECORD_PRICE_INVALID")
        _support(identity["price_support"], calendar=False)
        _support(identity["calendar_support"], calendar=True)
        if not isinstance(identity["legacy"], dict):
            raise ValueError("RECORD_LEGACY_INVALID")
    else:
        _instant(identity["effective_at"])
        if type(identity["event_type"]) is not str or not identity["event_type"]:
            raise ValueError("RECORD_EVENT_TYPE_INVALID")
        if not isinstance(identity["evidence"], dict):
            raise ValueError("RECORD_EVIDENCE_INVALID")
        hash_text(identity["upstream_structure_hash"])


def _record_order(record: dict[str, Any]) -> tuple[str, ...]:
    identity = record["record"]
    names = (
        ("extreme_time", "confirmation_time", "kind", "extreme_ref", "confirmation_ref")
        if identity["record_type"] == "STRUCTURE"
        else ("effective_at", "event_type")
    )
    return (*tuple(identity[key] for key in names), record["record_id"])


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
        _record_identity(
            self.record_schema_version, self.identity.document(), self.display.document()
        )

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
    _record_identity(schema, primitive(identity), primitive(display if display is not None else {}))
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
        if not isinstance(payload["lineage"], dict) or (
            payload["evidence"] is not None and not isinstance(payload["evidence"], dict)
        ):
            raise ValueError("RESULT_EVIDENCE_INVALID")
        stage = "STRUCTURE" if payload["schema_version"] == STRUCTURE_SCHEMA else "EVENT"
        descriptor = Descriptor(
            payload["strategy_id"],
            payload["strategy_version"],
            payload["code_hash"],
            tuple(payload["capabilities"]),
            payload["plugin_status"],
            stage,
            payload["schema_version"],
            FrozenJSON.of(payload["lineage"]),
        )
        binding = descriptor.binding_for_hash(payload["config_hash"])
        if stage == "STRUCTURE":
            if (
                payload["upstream_structure_hash"] is not None
                or payload["upstream_structure_binding"] is not None
            ):
                raise ValueError("UPSTREAM_STRUCTURE_MISMATCH")
        else:
            hash_text(payload["upstream_structure_hash"])
            upstream_binding = payload["upstream_structure_binding"]
            if not isinstance(upstream_binding, dict) or set(upstream_binding) != set(binding):
                raise ValueError("UPSTREAM_BINDING_MISMATCH")
            upstream_descriptor = Descriptor(
                upstream_binding["strategy_id"],
                upstream_binding["strategy_version"],
                upstream_binding["code_hash"],
                tuple(upstream_binding["capabilities"]),
                upstream_binding["plugin_status"],
                "STRUCTURE",
                STRUCTURE_SCHEMA,
                FrozenJSON.of({}),
            )
            if (
                primitive(upstream_descriptor.binding_for_hash(upstream_binding["config_hash"]))
                != upstream_binding
            ):
                raise ValueError("UPSTREAM_BINDING_MISMATCH")
        ids: set[str] = set()
        for record in payload["records"]:
            _record_identity(record_schema, record["record"], record["display"])
            expected_id = digest(
                "paqs-q/record/v1",
                {
                    "record_schema_version": record_schema,
                    "binding_hash": digest("paqs-q/binding/v1", binding),
                    "input_hash": payload["input_hash"],
                    "as_of": payload["as_of"],
                    "record": record["record"],
                },
            )
            if record["record_id"] != expected_id or expected_id in ids:
                raise ValueError("RECORD_ID_MISMATCH")
            ids.add(expected_id)
            if (
                stage == "EVENT"
                and record["record"]["upstream_structure_hash"]
                != payload["upstream_structure_hash"]
            ):
                raise ValueError("UPSTREAM_RECORD_MISMATCH")
        if payload["records"] != sorted(payload["records"], key=_record_order):
            raise ValueError("RESULT_RECORD_ORDER_INVALID")

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
