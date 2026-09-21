"""Explicit immutable allowlists and two-stage orchestration; no concrete strategy import."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, digest, utc
from ai_infra_quant.core.domain.paqs_q.inputs import INPUT_SCHEMA, QInput
from ai_infra_quant.core.domain.paqs_q.results import (
    EVENT_SCHEMA,
    STRUCTURE_SCHEMA,
    Config,
    Descriptor,
    QResult,
    make_result,
)
from ai_infra_quant.core.ports.paqs_q import EventPlugin, StructurePlugin


class SelectionError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Registry:
    structures: tuple[StructurePlugin, ...]
    events: tuple[EventPlugin, ...]
    allowlist: tuple[Descriptor, ...]
    default_structure: tuple[str, str]
    framework_code_hash: str
    test_only: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "structures", tuple(self.structures))
        object.__setattr__(self, "events", tuple(self.events))
        object.__setattr__(self, "allowlist", tuple(self.allowlist))
        object.__setattr__(self, "default_structure", tuple(self.default_structure))
        if type(self.test_only) is not bool:
            raise SelectionError("TEST_REGISTRY_FLAG_INVALID")
        seen: dict[tuple[str, str], Descriptor] = {}
        for d in self.allowlist:
            key = (d.strategy_id, d.strategy_version)
            if key in seen:
                raise SelectionError("DUPLICATE_ALLOWLIST_BINDING")
            seen[key] = d
        seen.clear()
        for stage, plugins in (("STRUCTURE", self.structures), ("EVENT", self.events)):
            for plugin in plugins:
                d = plugin.descriptor
                key = (d.strategy_id, d.strategy_version)
                if key in seen:
                    raise SelectionError(
                        "DUPLICATE_PLUGIN" if seen[key] == d else "VERSION_CONTENT_CONFLICT"
                    )
                seen[key] = d
                if d not in self.allowlist:
                    raise SelectionError("PLUGIN_NOT_ALLOWLISTED")
                if "TEST_ONLY" in d.capabilities and not self.test_only:
                    raise SelectionError("TEST_PLUGIN_FORBIDDEN")
                expected = STRUCTURE_SCHEMA if stage == "STRUCTURE" else EVENT_SCHEMA
                if (
                    d.stage != stage
                    or d.input_schema != INPUT_SCHEMA
                    or d.output_schema != expected
                ):
                    raise SelectionError("PLUGIN_SCHEMA_INCOMPATIBLE")
                if stage == "EVENT" and d.structure_schema != STRUCTURE_SCHEMA:
                    raise SelectionError("STRUCTURE_SCHEMA_INCOMPATIBLE")
        default = seen.get(self.default_structure)
        if default is None or default.stage != "STRUCTURE" or default.plugin_status != "REFERENCE":
            raise SelectionError("DEFAULT_REFERENCE_REQUIRED")

    def _select(
        self, stage: str, strategy_id: str | None, version: str | None, allow_experimental: bool
    ) -> Any:
        if type(allow_experimental) is not bool:
            raise SelectionError("EXPERIMENTAL_PERMISSION_INVALID")
        explicit = strategy_id is not None and version is not None
        if (strategy_id is None) != (version is None):
            raise SelectionError("EXPLICIT_ID_VERSION_REQUIRED")
        key = (strategy_id, version) if explicit else self.default_structure
        plugins = self.structures if stage == "STRUCTURE" else self.events
        for plugin in plugins:
            d = plugin.descriptor
            if key != (d.strategy_id, d.strategy_version):
                continue
            if d not in self.allowlist:
                raise SelectionError("PLUGIN_BINDING_CHANGED")
            if d.plugin_status == "DISABLED":
                raise SelectionError("PLUGIN_DISABLED")
            if d.plugin_status == "EXPERIMENTAL" and not (explicit and allow_experimental):
                raise SelectionError("EXPERIMENTAL_PERMISSION_REQUIRED")
            return plugin
        raise SelectionError("UNKNOWN_PLUGIN_VERSION")

    def structure(
        self,
        data: QInput,
        strategy_id: str | None = None,
        version: str | None = None,
        *,
        allow_experimental: bool = False,
        config: Config | None = None,
    ) -> QResult:
        plugin: StructurePlugin = self._select(
            "STRUCTURE", strategy_id, version, allow_experimental
        )
        resolved = plugin.resolve_config(config)
        if problem := data.problem():
            return make_result(data, plugin.descriptor, resolved, "INVALID", (problem,))
        result = plugin.evaluate(data, resolved)
        self._verify(data, plugin.descriptor, resolved, result, None)
        return result

    def event(
        self,
        data: QInput,
        structure: QResult,
        strategy_id: str | None = None,
        version: str | None = None,
        *,
        allow_experimental: bool = False,
        config: Config | None = None,
    ) -> QResult:
        source = structure.document()
        if (
            source["schema_version"] != STRUCTURE_SCHEMA
            or source["input_hash"] != data.input_hash
            or source["as_of"] != data.payload_as_of()
        ):
            raise SelectionError("UPSTREAM_STRUCTURE_MISMATCH")
        if strategy_id is None and version is None:
            descriptor = Descriptor(
                "paqs-q-event-unconfigured",
                "1.0.0",
                self.framework_code_hash,
                (),
                "DISABLED",
                "EVENT",
                EVENT_SCHEMA,
                FrozenJSON.of({}),
                structure_schema=STRUCTURE_SCHEMA,
            )
            return make_result(
                data,
                descriptor,
                Config("paqs-q-empty-v1", FrozenJSON.of({})),
                "UNAVAILABLE",
                ("EVENT_PLUGIN_NOT_CONFIGURED",),
                upstream=structure,
            )
        plugin: EventPlugin = self._select("EVENT", strategy_id, version, allow_experimental)
        d = plugin.descriptor
        if not set(d.required_capabilities) <= set(source["capabilities"]):
            raise SelectionError("CAPABILITY_INCOMPATIBLE")
        resolved = plugin.resolve_config(config)
        if problem := data.problem():
            return make_result(data, d, resolved, "INVALID", (problem,), upstream=structure)
        if structure.status != "AVAILABLE":
            return make_result(
                data,
                d,
                resolved,
                "UNAVAILABLE",
                ("UPSTREAM_STRUCTURE_UNAVAILABLE",),
                upstream=structure,
            )
        result = plugin.evaluate(data, structure, resolved)
        self._verify(data, d, resolved, result, structure)
        return result

    @staticmethod
    def _verify(
        data: QInput, d: Descriptor, config: Config, result: QResult, upstream: QResult | None
    ) -> None:
        payload = result.document()
        if (
            any(payload[k] != v for k, v in FrozenJSON.of(d.binding(config)).document().items())
            or payload["input_hash"] != data.input_hash
            or payload["as_of"] != data.payload_as_of()
            or payload["schema_version"] != d.output_schema
            or payload["qualification_mode"] != data.mode
            or payload["snapshot_identity"] != data.snapshot_identity
            or payload["lineage"] != d.lineage.document()
        ):
            raise SelectionError("RESULT_BINDING_MISMATCH")
        expected = upstream.canonical_result_hash if upstream else None
        if payload["upstream_structure_hash"] != expected:
            raise SelectionError("UPSTREAM_STRUCTURE_MISMATCH")
        upstream_binding = (
            {k: upstream.document()[k] for k in d.binding(config)} if upstream else None
        )
        if payload["upstream_structure_binding"] != upstream_binding:
            raise SelectionError("UPSTREAM_BINDING_MISMATCH")

        def times(value: Any) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    if (
                        key
                        in {
                            "effective_at",
                            "confirmation_time",
                            "reversal_time",
                            "completed_at",
                            "available_at",
                        }
                        and item is not None
                    ) and (
                        not isinstance(item, str) or utc(datetime.fromisoformat(item)) > data.as_of
                    ):
                        raise SelectionError("FUTURE_RESULT_EVIDENCE")
                    times(item)
            elif isinstance(value, list):
                for item in value:
                    times(item)

        times(payload["records"])
        times(payload["evidence"])
        ids = set()
        for record in payload["records"]:
            identity = record["record"]
            if upstream and identity["upstream_structure_hash"] != expected:
                raise SelectionError("UPSTREAM_RECORD_MISMATCH")
            preimage = {
                "record_schema_version": record["record_schema_version"],
                "binding_hash": d.binding_hash(config),
                "input_hash": data.input_hash,
                "as_of": data.as_of,
                "record": identity,
            }
            if (
                record["record_id"] != digest("paqs-q/record/v1", preimage)
                or record["record_id"] in ids
            ):
                raise SelectionError("RECORD_ID_MISMATCH")
            ids.add(record["record_id"])

    def historical_binding_status(self, result: QResult) -> str:
        """No latest fallback or rewriting when an old implementation is absent."""
        payload = result.document()
        descriptors = tuple(p.descriptor for p in self.structures) + tuple(
            p.descriptor for p in self.events
        )
        return (
            "AVAILABLE"
            if any(
                (d.strategy_id, d.strategy_version, d.code_hash)
                == (payload["strategy_id"], payload["strategy_version"], payload["code_hash"])
                for d in descriptors
                if d.plugin_status != "DISABLED"
            )
            else "UNAVAILABLE"
        )
