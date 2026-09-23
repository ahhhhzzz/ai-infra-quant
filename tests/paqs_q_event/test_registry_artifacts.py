import ast
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from ai_infra_quant.application.paqs_q_artifacts import load_registry
from ai_infra_quant.application.paqs_q_event_artifacts import FILES, load_event_registry, verify
from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, canonical
from ai_infra_quant.core.domain.paqs_q.event_reference import ContextEvidence, EventEvidence
from ai_infra_quant.core.domain.paqs_q.results import make_result
from ai_infra_quant.core.strategy.paqs_q.event_context import (
    CONTEXT_ID,
    EVENT_ID,
    VERSION,
    context_config,
)
from ai_infra_quant.core.strategy.paqs_q.registry import SelectionError
from tools.research.event_engine.data import daily_input, demo_input

from .support import candle, prefix

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("timeframe", ["W1", "M30"])
def test_explicit_event_registry_accepts_calendar_qualified_timeframes(registry, timeframe):
    from .test_input_calendar import intraday, weekly

    data = weekly() if timeframe == "W1" else intraday()
    structure = registry.structure(data, CONTEXT_ID, VERSION)
    assert structure.status == "AVAILABLE"
    events = registry.event(data, structure, EVENT_ID, VERSION)
    assert events.status == "AVAILABLE"
    assert events.document()["evidence"]["readiness"]["atr"]
    assert events.document()["input_hash"] == data.input_hash
    if timeframe == "W1":
        assert data.bars[-1].end > data.as_of
        assert all(
            r["record"]["effective_at"] <= data.payload_as_of()
            for r in events.document()["records"]
        )


@pytest.mark.parametrize("timeframe", ["D1", "M30"])
def test_closed_calendar_fact_late_for_historical_prefix_blocks_registry(registry, timeframe):
    from .test_input_calendar import intraday

    data = demo_input() if timeframe == "D1" else intraday()
    closed = next(f for f in data.calendar if f.kind == "CLOSED" and f.day > data.calendar[0].day)
    changed = replace(
        data,
        calendar=tuple(
            replace(f, available_at=data.as_of, retrieved_at=data.as_of)
            if f.day == closed.day
            else f
            for f in data.calendar
        ),
    )
    source = registry.structure(changed, CONTEXT_ID, VERSION)
    assert source.status == "INSUFFICIENT"
    assert source.document()["reason_codes"] == ["HISTORICAL_CALENDAR_NOT_KNOWN_AT_COMPLETION"]
    result = registry.event(changed, source, EVENT_ID, VERSION)
    assert result.status == "UNAVAILABLE"
    assert result.document()["reason_codes"] == ["UPSTREAM_STRUCTURE_UNAVAILABLE"]


@pytest.fixture(scope="module")
def registry():
    return load_event_registry(ROOT, include_experimental=True)


def test_explicit_plugin_binding_defaults_and_f1_identity(registry):
    old = load_registry(ROOT, include_experimental=True)
    assert old.structures == registry.structures[: len(old.structures)]
    assert old.framework_code_hash == registry.framework_code_hash
    assert old.default_structure == registry.default_structure
    data = demo_input()
    assert registry.structure(data) == old.structure(data)
    source = registry.structure(data, CONTEXT_ID, VERSION)
    unconfigured = registry.event(data, source)
    assert unconfigured.status == "UNAVAILABLE"
    assert unconfigured.document()["reason_codes"] == ["EVENT_PLUGIN_NOT_CONFIGURED"]
    with pytest.raises(SelectionError, match="CAPABILITY_INCOMPATIBLE"):
        registry.event(data, registry.structure(data), EVENT_ID, VERSION)
    with pytest.raises(SelectionError):
        registry.structure(data, CONTEXT_ID, "9.0.0")
    with pytest.raises(SelectionError, match="UNKNOWN_PLUGIN_VERSION"):
        registry.structure(data, CONTEXT_ID, "1.0.0")
    with pytest.raises(SelectionError, match="UNKNOWN_PLUGIN_VERSION"):
        registry.event(data, source, EVENT_ID, "1.0.0")
    with pytest.raises(SelectionError):
        registry.structure(data, "paqs-q-a1", "1.0.0")
    result = registry.event(data, source, EVENT_ID, VERSION)
    doc = result.document()
    assert doc["upstream_structure_hash"] == source.canonical_result_hash
    assert doc["upstream_structure_binding"]["config_hash"] == context_config().config_hash
    for row in doc["records"]:
        assert row["record"]["upstream_structure_hash"] == source.canonical_result_hash
        assert EventEvidence.model_validate_json(canonical(row["record"]["evidence"]))


def test_f1_record_id_may_change_but_event_keys_and_past_facts_do_not(registry):
    full = demo_input()
    short = prefix(full, 90)
    records = []
    for data in (short, full):
        source = registry.structure(data, CONTEXT_ID, VERSION)
        result = registry.event(data, source, EVENT_ID, VERSION)
        records.append(
            {
                (r["record"]["evidence"]["event_key"], r["record"]["evidence"]["status"]): r
                for r in result.document()["records"]
                if r["record"]["evidence"]["bar_index"] < 90
            }
        )
    assert records[0].keys() == records[1].keys()
    for key, old in records[0].items():
        new = records[1][key]
        assert new["record"]["evidence"] == old["record"]["evidence"]
        assert new["record_id"] != old["record_id"]


@pytest.mark.parametrize(
    "mutation", ["extra", "missing", "decimal", "future_pivot", "atr", "prefix", "mode"]
)
def test_closed_context_schema_and_semantic_rejection(registry, mutation):
    data = demo_input()
    source = registry.structure(data, CONTEXT_ID, VERSION)
    evidence = source.document()["evidence"]
    if mutation == "extra":
        evidence["trading_ready"] = True
    elif mutation == "missing":
        evidence.pop("frames")
    elif mutation == "decimal":
        evidence["frames"][13]["atr"] = 1
    elif mutation == "future_pivot":
        evidence["frames"][0]["major"] = [evidence["pivots"][-1]["key"]]
    elif mutation == "atr":
        evidence["frames"][13]["atr"] = "999"
    elif mutation == "prefix":
        evidence["prefix_hashes"][20] = "f" * 64
    elif mutation == "mode":
        evidence["strict_confirmation"] = False
    plugin = next(p for p in registry.structures if p.descriptor.strategy_id == CONTEXT_ID)
    forged = make_result(
        data,
        plugin.descriptor,
        context_config(),
        "AVAILABLE",
        ("TEST_FORGED",),
        evidence=FrozenJSON.of(evidence),
    )
    assert registry.event(data, forged, EVENT_ID, VERSION).status == "INVALID"


def test_input_upstream_mismatch_and_empty_vs_warming_vs_unavailable(registry):
    data = demo_input()
    source = registry.structure(data, CONTEXT_ID, VERSION)
    with pytest.raises(SelectionError, match="UPSTREAM_STRUCTURE_MISMATCH"):
        registry.event(prefix(data, 80), source, EVENT_ID, VERSION)
    for count, expected in ((10, "COMPONENTS_WARMING"), (20, "NO_EVENTS")):
        data = daily_input([candle("100", h="101", low="99")] * count)
        source = registry.structure(data, CONTEXT_ID, VERSION)
        event = registry.event(data, source, EVENT_ID, VERSION)
        assert event.status == "AVAILABLE" and not event.document()["records"]
        assert event.document()["evidence"]["classification"] == expected
    data = replace(data, bars=())
    source = registry.structure(data, CONTEXT_ID, VERSION)
    assert source.status == "INSUFFICIENT"
    assert registry.event(data, source, EVENT_ID, VERSION).status == "UNAVAILABLE"


def test_event_schema_rejects_nonfinite_extra_unanchored_guard(registry):
    data = demo_input()
    source = registry.structure(data, CONTEXT_ID, VERSION)
    events = registry.event(data, source, EVENT_ID, VERSION).document()
    example = next(
        r["record"]["evidence"]
        for r in events["records"]
        if r["record"]["event_type"] == "PRICE_PATTERN"
    )
    for changes in (
        {"atr": "NaN"},
        {"atr": "not-a-number"},
        {"unknown": "field"},
        {"status": "HOLD"},
        {"anchor_key": "f" * 64},
        {"bar_index": True},
    ):
        with pytest.raises(ValueError):
            EventEvidence.model_validate_json(canonical({**example, **changes}))
    parsed = ContextEvidence.model_validate_json(canonical(source.document()["evidence"]))
    with pytest.raises(ValueError):
        parsed.pivots[0].price = "1"


def test_manifest_covers_recursive_project_imports_and_initializers():
    todo = ["ai_infra_quant.application.paqs_q_event_artifacts"]
    found = set()
    while todo:
        module = todo.pop()
        path = ROOT / "src" / Path(*module.split(".")).with_suffix(".py")
        if not path.is_file():
            path = ROOT / "src" / Path(*module.split(".")) / "__init__.py"
        if not path.is_file() or path in found:
            continue
        found.add(path)
        parts = module.split(".")
        todo.extend(".".join(parts[:i]) for i in range(1, len(parts)))
        package = parts if path.name == "__init__.py" else parts[:-1]
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                todo.extend(a.name for a in node.names if a.name.startswith("ai_infra_quant"))
            elif isinstance(node, ast.ImportFrom):
                base = package[: len(package) - node.level + 1] if node.level else []
                target = ".".join([*base, *((node.module or "").split("."))]).strip(".")
                assert not target.startswith("tools.research")
                if target.startswith("ai_infra_quant"):
                    todo.extend([target, *[target + "." + a.name for a in node.names]])
    assert {p.relative_to(ROOT).as_posix() for p in found} <= set(FILES)
    assert len(found) >= 40


def test_artifact_tamper_inventory_and_active_package_check(tmp_path):
    for name in (
        *FILES,
        f"src/ai_infra_quant/resources/paqs_q/event-context-{VERSION}.json",
        f"src/ai_infra_quant/resources/paqs_q/event-event-{VERSION}.json",
    ):
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dest)
    assert verify(tmp_path, "context") == verify(ROOT, "context")
    changed = tmp_path / "src/ai_infra_quant/core/strategy/paqs_q/event_rules.py"
    changed.write_bytes(changed.read_bytes() + b"\n# tampered\n")
    with pytest.raises(ValueError, match="CONTENT_OR_INVENTORY_MISMATCH"):
        verify(tmp_path, "context")
