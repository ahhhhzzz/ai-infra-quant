"""Adverse public-boundary tests for F1 F01/F02/F03, using only synthetic inputs."""

from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

import pytest

from ai_infra_quant.application.paqs_q_artifacts import load_registry
from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, digest
from ai_infra_quant.core.domain.paqs_q.results import QResult, Record, make_record
from ai_infra_quant.core.strategy.paqs_q.registry import SelectionError
from tests.paqs_q.support import ROOT, synthetic
from tests.paqs_q.test_registry import fixtures


def seal(payload: dict[str, Any], *, records: bool = True) -> FrozenJSON:
    """A deliberately self-consistent hash is not proof of schema or upstream validity."""
    payload.pop("canonical_result_hash", None)
    binding = {
        k: payload[k]
        for k in (
            "strategy_id",
            "strategy_version",
            "config_hash",
            "code_hash",
            "capabilities",
            "plugin_status",
        )
    }
    if records:
        for record in payload["records"]:
            record["record_id"] = digest(
                "paqs-q/record/v1",
                {
                    "record_schema_version": record["record_schema_version"],
                    "binding_hash": digest("paqs-q/binding/v1", binding),
                    "input_hash": payload["input_hash"],
                    "as_of": payload["as_of"],
                    "record": record["record"],
                },
            )
    payload["canonical_result_hash"] = digest("paqs-q/result/v1", payload)
    return FrozenJSON.of(payload)


@pytest.fixture
def structure_case():
    data = synthetic()
    registry = load_registry(ROOT)
    return data, registry, registry.structure(data)


@pytest.mark.parametrize(
    "change",
    [
        "missing_price",
        "unknown_field",
        "object_price",
        "bool_price",
        "nonfinite_price",
        "noncanonical_price",
        "invalid_kind",
        "missing_support_field",
        "unknown_support_field",
        "support_hash",
        "calendar_field",
        "calendar_bool",
        "noncanonical_time",
    ],
)
def test_closed_record_schema_at_every_constructor(structure_case, change):
    data, registry, original = structure_case
    payload = original.document()
    row = payload["records"][0]
    identity = row["record"]
    if change == "missing_price":
        identity.pop("price")
    elif change == "unknown_field":
        identity["unexpected_field"] = True
    elif change == "object_price":
        identity["price"] = {"not": "a price"}
    elif change == "bool_price":
        identity["price"] = True
    elif change == "nonfinite_price":
        identity["price"] = "NaN"
    elif change == "noncanonical_price":
        identity["price"] = "1.00"
    elif change == "invalid_kind":
        identity["kind"] = "UNKNOWN"
    elif change == "missing_support_field":
        identity["price_support"][0].pop("completed")
    elif change == "unknown_support_field":
        identity["price_support"][0]["invented"] = True
    elif change == "support_hash":
        identity["price_support"][0]["version_ref"] = "0" * 64
    elif change == "calendar_field":
        identity["calendar_support"][0]["invented"] = True
    elif change == "calendar_bool":
        identity["calendar_support"][0]["complete"] = 1
    else:
        identity["confirmation_time"] = identity["confirmation_time"].replace("Z", "+00:00")
    with pytest.raises(ValueError):
        QResult(seal(payload))
    with pytest.raises(ValueError):
        Record(
            row["record_schema_version"],
            row["record_id"],
            FrozenJSON.of(identity),
            FrozenJSON.of({}),
        )
    # A factory accepts aware datetime domain values and canonicalizes them, so a UTC
    # spelling discrepancy applies only to decoded JSON, not the equivalent datetime.
    if change != "noncanonical_time":
        identity = dict(identity)
        for key in ("extreme_time", "confirmation_time"):
            identity[key] = datetime.fromisoformat(identity[key])
        plugin = registry.structures[0]
        with pytest.raises(ValueError):
            make_record(data, plugin.descriptor, plugin.resolve_config(None), identity)


@pytest.mark.parametrize("change", ["record_hash", "duplicate", "order", "stage", "upstream"])
def test_result_record_integrity(structure_case, change):
    _, _, original = structure_case
    payload = original.document()
    if change == "record_hash":
        payload["records"][0]["record_id"] = "0" * 64
    elif change == "duplicate":
        payload["records"].append(payload["records"][0])
    elif change == "order":
        data, _, _ = structure_case
        payload = (
            load_registry(ROOT, include_experimental=True)
            .structure(data, "paqs-q-structure-a1", "0.1.0", allow_experimental=True)
            .document()
        )
        assert len(payload["records"]) > 1
        payload["records"].reverse()
    elif change == "stage":
        payload["records"][0]["record"]["record_type"] = "EVENT"
    else:
        payload["upstream_structure_hash"] = "0" * 64
    with pytest.raises(ValueError):
        QResult(seal(payload, records=change != "record_hash"))


@pytest.mark.parametrize(
    "change",
    [
        "mode",
        "snapshot",
        "capabilities",
        "status",
        "lineage",
        "code",
        "version",
        "future",
        "future_record",
    ],
)
def test_upstream_rejected_before_event_or_structure_invocation(change, monkeypatch):
    base, events = fixtures()
    registry = replace(
        base,
        events=events,
        allowlist=(*base.allowlist, *(e.descriptor for e in events)),
        test_only=True,
    )
    data = synthetic()
    source = registry.structure(data).document()
    changes = {
        "mode": ("qualification_mode", "OBSERVATIONAL"),
        "snapshot": ("snapshot_identity", "1" * 64),
        "capabilities": ("capabilities", ["LOCAL_STRUCTURE_CERTIFICATE", "UNDECLARED"]),
        "status": ("plugin_status", "EXPERIMENTAL"),
        "lineage": ("lineage", {"invented": True}),
        "code": ("code_hash", "2" * 64),
        "version": ("strategy_version", "0.0.1"),
        "future": ("evidence", {"available_at": (data.as_of + timedelta(days=1)).isoformat()}),
    }
    if change == "future_record":
        source["records"][0]["record"]["extreme_time"] = (
            (data.as_of + timedelta(days=1))
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
    else:
        key, value = changes[change]
        source[key] = value
    altered = QResult(seal(source))

    def forbidden(*args, **kwargs):
        raise AssertionError("PLUGIN_INVOKED_BEFORE_UPSTREAM_VALIDATION")

    monkeypatch.setattr(type(events[0]), "evaluate", forbidden)
    monkeypatch.setattr(type(base.structures[0]), "evaluate", forbidden)
    with pytest.raises(SelectionError):
        registry.event(data, altered, "test-fixture-one", "1.0.0")


@pytest.mark.parametrize("field,value", [("security", "HK.00001"), ("timeframe", "D1")])
@pytest.mark.parametrize("mode", ["AS_OF", "OBSERVATIONAL"])
def test_foreign_old_bar_rejected_before_windowing(field, value, mode):
    data = replace(synthetic(), mode=mode)
    first = data.bars[0]
    old = replace(
        first,
        **{field: value},
        start=first.start - timedelta(days=1),
        end=first.end - timedelta(days=1),
        completed_at=first.completed_at - timedelta(days=1),
    )
    data = replace(data, bars=(old, *data.bars))
    registry = load_registry(ROOT, include_experimental=True)
    for arm, version in (("b0", "1.0.0"), ("a1", "0.1.0")):
        result = registry.structure(
            data, "paqs-q-structure-" + arm, version, allow_experimental=True
        ).document()
        assert result["status"] == "INVALID"
        assert result["reason_codes"] == ["BAR_IDENTITY_CONFLICT"]
        assert result["records"] == [] and result["evidence"] is None


def test_valid_roundtrip_and_event_swap(structure_case):
    data, _, structure = structure_case
    assert (
        QResult(FrozenJSON(structure.canonical_bytes)).canonical_bytes == structure.canonical_bytes
    )
    base, events = fixtures()
    registry = replace(
        base,
        events=events,
        allowlist=(*base.allowlist, *(e.descriptor for e in events)),
        test_only=True,
    )
    for event in events:
        result = registry.event(data, structure, event.descriptor.strategy_id, "1.0.0")
        assert QResult(FrozenJSON(result.canonical_bytes)).canonical_bytes == result.canonical_bytes
        assert result.document()["upstream_structure_hash"] == structure.canonical_result_hash


@pytest.mark.parametrize("change", ["missing", "unknown", "type", "upstream"])
def test_event_record_schema_and_upstream_integrity(change):
    data = synthetic()
    base, events = fixtures()
    event = events[0]
    result = event.evaluate(data, base.structure(data), event.resolve_config(None)).document()
    identity = result["records"][0]["record"]
    if change == "missing":
        identity.pop("event_type")
    elif change == "unknown":
        identity["unknown"] = 1
    elif change == "type":
        identity["event_type"] = True
    else:
        identity["upstream_structure_hash"] = "0" * 64
    with pytest.raises(ValueError):
        QResult(seal(result))
