"""Test-only Event fixtures prove replacement without adding a production strategy."""

from dataclasses import dataclass, replace

import pytest

from ai_infra_quant.application.paqs_q_artifacts import load_registry
from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, digest
from ai_infra_quant.core.domain.paqs_q.inputs import QInput
from ai_infra_quant.core.domain.paqs_q.results import (
    EVENT_SCHEMA,
    STRUCTURE_SCHEMA,
    Config,
    Descriptor,
    QResult,
    make_record,
    make_result,
)
from ai_infra_quant.core.strategy.paqs_q.registry import Registry, SelectionError
from tests.paqs_q.support import ROOT, synthetic


@dataclass(frozen=True)
class FixtureEvent:
    descriptor: Descriptor

    def resolve_config(self, supplied: Config | None) -> Config:
        default = Config("test-fixture-config-v1", FrozenJSON.of({"label": "fixture"}))
        if supplied is not None and supplied != default:
            raise ValueError("UNKNOWN_FIXTURE_CONFIG")
        return default

    def evaluate(self, data: QInput, structure: QResult, config: Config) -> QResult:
        identity = {
            "record_type": "EVENT",
            "effective_at": data.as_of,
            "event_type": "FIXTURE_ONLY",
            "evidence": {"synthetic": True},
            "upstream_structure_hash": structure.canonical_result_hash,
        }
        record = make_record(data, self.descriptor, config, identity)
        return make_result(
            data,
            self.descriptor,
            config,
            "AVAILABLE",
            ("TEST_ONLY",),
            (record,),
            FrozenJSON.of({"synthetic": True}),
            structure,
        )


def fixtures() -> tuple[Registry, tuple[FixtureEvent, ...]]:
    base = load_registry(ROOT)
    events = tuple(
        FixtureEvent(
            Descriptor(
                "test-fixture-" + label,
                "1.0.0",
                digest("test-fixture", label),
                ("TEST_ONLY",),
                "REFERENCE",
                "EVENT",
                EVENT_SCHEMA,
                FrozenJSON.of({"synthetic": True}),
                structure_schema=STRUCTURE_SCHEMA,
                required_capabilities=("LOCAL_STRUCTURE_CERTIFICATE",),
            )
        )
        for label in ("one", "two")
    )
    return base, events


def test_default_and_two_explicit_experimental_gates():
    data = synthetic()
    default = load_registry(ROOT)
    assert len(default.structures) == 1 and default.events == ()
    assert default.structure(data).document()["strategy_id"] == "paqs-q-structure-b0"
    with pytest.raises(SelectionError, match="UNKNOWN_PLUGIN"):
        default.structure(data, "paqs-q-structure-a1", "0.1.0", allow_experimental=True)
    enabled = load_registry(ROOT, include_experimental=True)
    before = enabled.structure(data).canonical_bytes
    for kwargs in (
        {"strategy_id": "paqs-q-structure-a1"},
        {"version": "0.1.0"},
        {"strategy_id": "paqs-q-structure-a1", "version": "0.1.0"},
    ):
        with pytest.raises(SelectionError):
            enabled.structure(data, kwargs.get("strategy_id"), kwargs.get("version"))
    assert enabled.structure(data, allow_experimental=True).canonical_bytes == before
    a1 = enabled.structure(data, "paqs-q-structure-a1", "0.1.0", allow_experimental=True)
    assert a1.document()["plugin_status"] == "EXPERIMENTAL"
    assert a1.canonical_bytes != before
    assert enabled.structure(data).canonical_bytes == before
    unavailable = default.event(data, default.structure(data))
    assert unavailable.status == "UNAVAILABLE"
    assert unavailable.document()["reason_codes"] == ["EVENT_PLUGIN_NOT_CONFIGURED"]


def test_fixture_swap_upstream_binding_and_production_exclusion():
    data = synthetic()
    base, events = fixtures()
    allowed = (*base.allowlist, *(e.descriptor for e in events))
    with pytest.raises(SelectionError, match="TEST_PLUGIN_FORBIDDEN"):
        replace(base, events=events, allowlist=allowed)
    registry = replace(base, events=events, allowlist=allowed, test_only=True)
    structure = registry.structure(data)
    a, b = [registry.event(data, structure, p.descriptor.strategy_id, "1.0.0") for p in events]
    assert a.canonical_result_hash != b.canonical_result_hash
    assert a.document()["upstream_structure_hash"] == structure.canonical_result_hash
    assert (
        a.document()["records"][0]["record"]["upstream_structure_hash"]
        == structure.canonical_result_hash
    )
    with pytest.raises(SelectionError, match="UPSTREAM_STRUCTURE_MISMATCH"):
        registry.event(
            replace(data, snapshot_identity="1" * 64), structure, "test-fixture-one", "1.0.0"
        )
    insufficient = replace(data, bars=())
    result = registry.event(
        insufficient, registry.structure(insufficient), "test-fixture-one", "1.0.0"
    )
    assert result.status == "UNAVAILABLE"


@pytest.mark.parametrize(
    "case,code",
    [
        ("duplicate", "DUPLICATE_PLUGIN"),
        ("conflict", "VERSION_CONTENT_CONFLICT"),
        ("unknown", "PLUGIN_NOT_ALLOWLISTED"),
        ("schema", "PLUGIN_SCHEMA_INCOMPATIBLE"),
        ("structure_schema", "STRUCTURE_SCHEMA_INCOMPATIBLE"),
    ],
)
def test_registry_rejects_invalid_registrations(case, code):
    base, events = fixtures()
    first = events[0]
    second = first
    if case == "conflict":
        second = replace(first, descriptor=replace(first.descriptor, code_hash="2" * 64))
    elif case == "schema":
        first = replace(first, descriptor=replace(first.descriptor, input_schema="later"))
    elif case == "structure_schema":
        first = replace(first, descriptor=replace(first.descriptor, structure_schema="later"))
    selected = (first, second) if case in {"duplicate", "conflict"} else (first,)
    allowed = base.allowlist if case == "unknown" else (*base.allowlist, first.descriptor)
    with pytest.raises(SelectionError, match=code):
        replace(base, events=selected, allowlist=allowed, test_only=True)


def test_disabled_capability_and_absent_historical_binding():
    base, events = fixtures()
    data = synthetic()
    structure = base.structure(data)
    for status, caps, code in (
        ("DISABLED", (), "PLUGIN_DISABLED"),
        ("REFERENCE", ("NOT_PRESENT",), "CAPABILITY_INCOMPATIBLE"),
    ):
        event = replace(
            events[0],
            descriptor=replace(
                events[0].descriptor, plugin_status=status, required_capabilities=caps
            ),
        )
        registry = replace(
            base, events=(event,), allowlist=(*base.allowlist, event.descriptor), test_only=True
        )
        with pytest.raises(SelectionError, match=code):
            registry.event(data, structure, event.descriptor.strategy_id, "1.0.0")
    assert base.historical_binding_status(structure) == "AVAILABLE"
    payload = structure.document()
    payload.pop("canonical_result_hash")
    payload["strategy_version"] = "0.0.1"
    payload["canonical_result_hash"] = digest("paqs-q/result/v1", payload)
    old = QResult(FrozenJSON.of(payload))
    assert base.historical_binding_status(old) == "UNAVAILABLE"
    old_descriptor = replace(base.structures[0].descriptor, strategy_version="0.0.1")
    inventory_only = replace(base, allowlist=(*base.allowlist, old_descriptor))
    assert inventory_only.historical_binding_status(old) == "UNAVAILABLE"


def test_result_tamper_rejected():
    base = load_registry(ROOT)
    payload = base.structure(synthetic()).document()
    payload["strategy_version"] = "9.0.0"
    with pytest.raises(ValueError, match="RESULT_HASH"):
        QResult(FrozenJSON.of(payload))
    payload = base.structure(synthetic()).document()
    payload["records"][0]["record_schema_version"] = "unknown"
    with pytest.raises(ValueError, match="RESULT_RECORD_SCHEMA"):
        QResult(FrozenJSON.of(payload))


def test_experimental_rejected_before_plugin_invocation(monkeypatch):
    registry = load_registry(ROOT, include_experimental=True)
    data = synthetic()

    def forbidden(*args, **kwargs):
        raise AssertionError("PLUGIN_CALLED_WITHOUT_PERMISSION")

    monkeypatch.setattr(type(registry.structures[0]), "evaluate", forbidden)
    with pytest.raises(SelectionError, match="EXPERIMENTAL_PERMISSION_REQUIRED"):
        registry.structure(data, "paqs-q-structure-a1", "0.1.0")


def test_forged_event_upstream_and_future_evidence_are_rejected():
    from datetime import timedelta

    base, events = fixtures()
    data = synthetic()
    structure = base.structure(data)
    plugin = events[0]
    config = plugin.resolve_config(None)
    original = plugin.evaluate(data, structure, config)
    for change, code in (
        ("upstream", "UPSTREAM_STRUCTURE_MISMATCH"),
        ("future", "FUTURE_RESULT_EVIDENCE"),
    ):
        payload = original.document()
        payload.pop("canonical_result_hash")
        if change == "upstream":
            payload["upstream_structure_hash"] = "0" * 64
        else:
            payload["evidence"] = {"available_at": (data.as_of + timedelta(days=1)).isoformat()}
        payload["canonical_result_hash"] = digest("paqs-q/result/v1", payload)
        with pytest.raises(SelectionError, match=code):
            Registry._verify(
                data, plugin.descriptor, config, QResult(FrozenJSON.of(payload)), structure
            )
