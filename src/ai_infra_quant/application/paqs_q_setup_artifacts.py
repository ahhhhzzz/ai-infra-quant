"""Explicit Setup/Risk 1.0.1 loader over immutable Event 1.0.1 results."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, cast

from ai_infra_quant.application.paqs_q_artifacts import PACKAGE, artifact_path, content_hash
from ai_infra_quant.application.paqs_q_event_artifacts import FILES as EVENT_FILES
from ai_infra_quant.application.paqs_q_event_artifacts import load_event_registry
from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, digest, hash_text
from ai_infra_quant.core.domain.paqs_q.event_reference import ContextEvidence, EventEvidence
from ai_infra_quant.core.domain.paqs_q.inputs import QInput
from ai_infra_quant.core.domain.paqs_q.setup_reference import (
    SETUP_ID,
    MultiInput,
    SetupFact,
    SetupRun,
    UpstreamBinding,
)
from ai_infra_quant.core.strategy.paqs_q.event_context import CONTEXT_ID, EVENT_ID
from ai_infra_quant.core.strategy.paqs_q.setup_rules import Period, Replay, setup_config
from ai_infra_quant.core.strategy.paqs_q.setup_targets import next_regular_open

VERSION = "1.0.1"
FILES = tuple(
    sorted(
        {
            *EVENT_FILES,
            *(
                PACKAGE + name
                for name in (
                    "resources/paqs_q/event-context-1.0.1.json",
                    "resources/paqs_q/event-event-1.0.1.json",
                    "core/domain/paqs_q/setup_reference.py",
                    "core/strategy/paqs_q/setup_targets.py",
                    "core/strategy/paqs_q/setup_rules.py",
                    "application/paqs_q_setup_artifacts.py",
                )
            ),
        }
    )
)


def build_manifest(root: Path, *, wheel: bool = False) -> dict[str, Any]:
    return {
        "artifact_schema_version": "paqs-q-implementation-v1",
        "entrypoint": SETUP_ID,
        "files": [
            {
                "path": path,
                "encoding": "utf8-lf",
                "sha256": content_hash(
                    artifact_path(root, path, wheel=wheel).read_bytes(), "utf8-lf"
                ),
            }
            for path in FILES
        ],
    }


def verify(root: Path, *, wheel: bool = False) -> str:
    path = PACKAGE + "resources/paqs_q/setup-risk-1.0.1.json"
    encoded = artifact_path(root, path, wheel=wheel).read_bytes().replace(b"\r\n", b"\n")
    manifest = FrozenJSON(encoded.removesuffix(b"\n")).document()
    if manifest != build_manifest(root, wheel=wheel):
        raise ValueError("SETUP_ARTIFACT_CONTENT_OR_INVENTORY_MISMATCH")
    active_package = Path(__file__).resolve().parents[1]
    for row in manifest["files"]:
        hash_text(row["sha256"])
        if (
            content_hash(
                (active_package / row["path"].removeprefix(PACKAGE)).read_bytes(),
                row["encoding"],
            )
            != row["sha256"]
        ):
            raise ValueError("ACTIVE_SETUP_IMPLEMENTATION_MISMATCH")
    return digest("paqs-q/implementation/v1", manifest)


def _basis(data: QInput) -> tuple[str, str, str | None]:
    adjustments = {bar.adjustment for bar in data.bars}
    if len(adjustments) != 1:
        raise ValueError("MIXED_ADJUSTMENT_BASIS")
    adjustment = next(iter(adjustments))
    provenance = data.provenance.document()
    capture: str | None = None
    if isinstance(provenance, dict):
        original = provenance.get("original_provenance")
        if isinstance(original, list):
            original_map = dict(original)
            capture = original_map.get("capture_hash")
            if original_map.get("adjustment") != adjustment:
                raise ValueError("ADJUSTMENT_PROVENANCE_CONFLICT")
        historical = provenance.get("historical_evidence")
        if isinstance(historical, dict):
            capture = historical.get("adjustment_as_of")
    source = provenance.get("source", "") if isinstance(provenance, dict) else ""
    return adjustment, str(source), capture


def _compatible(bundle: MultiInput) -> tuple[str, ...]:
    periods = [item for item in (bundle.w1, bundle.d1, bundle.m30) if item is not None]
    missing = tuple(
        f"{name}_INPUT_MISSING"
        for name, item in (("W1", bundle.w1), ("D1", bundle.d1), ("M30", bundle.m30))
        if item is None
    )
    if missing:
        return missing
    if len({(p.security, p.market, p.currency, p.market_timezone, p.mode) for p in periods}) != 1:
        return ("MULTIPERIOD_IDENTITY_OR_MODE_MISMATCH",)
    bases = {_basis(p) for p in periods}
    if len(bases) != 1:
        return ("MULTIPERIOD_ADJUSTMENT_OR_PROVENANCE_MISMATCH",)
    if not next(iter(bases))[1] and not next(iter(bases))[2]:
        return ("MULTIPERIOD_ADJUSTMENT_PROVENANCE_UNKNOWN",)
    if periods[0].mode == "AS_OF" and any(p.quality != "COMPLETE" for p in periods):
        return ("STRICT_MULTIPERIOD_QUALITY_REQUIRED",)
    calendars: dict[Any, str] = {}
    for period in periods:
        for fact in period.calendar:
            prior = calendars.get(fact.day)
            if prior is not None and prior != fact.ref:
                return ("MULTIPERIOD_CALENDAR_VERSION_CONFLICT",)
            calendars[fact.day] = fact.ref
    assert bundle.w1 is not None and bundle.d1 is not None and bundle.m30 is not None
    for higher, lower in ((bundle.w1, bundle.d1), (bundle.d1, bundle.m30)):
        if not {b.completed_at for b in higher.bars} & {b.completed_at for b in lower.bars}:
            return ("MULTIPERIOD_PRICE_SCALE_UNPROVEN",)
    # Provider D1 and M30 closes can differ at one timestamp; a 2% consistency
    # tolerance detects a split-scale mismatch without asserting tick equality.
    observations: dict[Any, Decimal] = {}
    for period in periods:
        for bar in period.bars:
            other = observations.get(bar.completed_at)
            if other is not None and abs(other - bar.close) > min(other, bar.close) * Decimal(
                "0.02"
            ):
                return ("MULTIPERIOD_PRICE_SCALE_CONFLICT",)
            observations[bar.completed_at] = bar.close
    starts = {bar.start for bar in bundle.m30.bars if bar.session == "REGULAR"}
    if bundle.m30.bars:
        next_open = next_regular_open(bundle.m30, bundle.m30.bars[-1].completed_at)
        if next_open is not None and next_open <= bundle.m30.as_of:
            starts.add(next_open)
    if any(ref.price_at not in starts for ref in bundle.entry_references):
        return ("ENTRY_REFERENCE_NOT_REGULAR_M30_OPEN",)
    if any(ref.available_at > bundle.m30.as_of for ref in bundle.entry_references):
        return ("ENTRY_REFERENCE_FUTURE_AVAILABILITY",)
    return ()


def run(bundle: MultiInput, root: Path, *, wheel: bool = False) -> SetupRun:
    notes: tuple[str, ...] = ()
    if bundle.w1 is not None and any(not bar.completed for bar in bundle.w1.bars):
        prefix = tuple(bar for bar in bundle.w1.bars if bar.completed)
        if len(prefix) != len(bundle.w1.bars) - 1 or not prefix:
            raise ValueError("W1_PARTIAL_BAR_NOT_SINGLE_TAIL")
        bundle = MultiInput(
            replace(bundle.w1, bars=prefix), bundle.d1, bundle.m30, bundle.entry_references
        )
        notes = ("W1_PARTIAL_TAIL_EXCLUDED",)
    code_hash = verify(root, wheel=wheel)
    config_hash = setup_config().config_hash
    entry_reference_hash = digest(
        "paqs-q/entry-references/v1",
        [
            {
                "price": ref.price,
                "price_at": ref.price_at,
                "available_at": ref.available_at,
                "source": ref.source,
                "source_ref": ref.source_ref,
                "adjustment": ref.adjustment,
                "security": ref.security,
            }
            for ref in bundle.entry_references
        ],
    )
    first = next((p for p in (bundle.w1, bundle.d1, bundle.m30) if p is not None), None)
    mode = first.mode if first is not None else "AS_OF"
    security = first.security if first is not None else "UNKNOWN"

    def result(
        status: Literal["AVAILABLE", "INSUFFICIENT", "INVALID"],
        reasons: tuple[str, ...],
        bindings: tuple[UpstreamBinding, ...] = (),
        facts: tuple[SetupFact, ...] = (),
    ) -> SetupRun:
        return SetupRun(
            code_hash=code_hash,
            config_hash=config_hash,
            entry_reference_hash=entry_reference_hash,
            mode=cast(Literal["AS_OF", "OBSERVATIONAL"], mode),
            security=security,
            strict_confirmation=mode == "AS_OF" and status == "AVAILABLE",
            status=status,
            reasons=reasons,
            bindings=bindings,
            facts=facts,
        )

    try:
        issues = _compatible(bundle)
    except ValueError as exc:
        return result("INVALID", (*notes, str(exc)))
    if issues:
        status: Literal["INSUFFICIENT", "INVALID"] = (
            "INSUFFICIENT"
            if any(
                token in x
                for x in issues
                for token in ("MISSING", "QUALITY", "UNPROVEN", "FUTURE_AVAILABILITY")
            )
            else "INVALID"
        )
        return result(status, (*notes, *issues))
    registry = load_event_registry(root, wheel=wheel)
    periods: dict[str, Period] = {}
    bindings: list[UpstreamBinding] = []
    for name, data in (("W1", bundle.w1), ("D1", bundle.d1), ("M30", bundle.m30)):
        assert data is not None
        structure = registry.structure(data, CONTEXT_ID, "1.0.1")
        event = registry.event(data, structure, EVENT_ID, "1.0.1")
        if structure.status != "AVAILABLE" or event.status != "AVAILABLE":
            failing = structure if structure.status != "AVAILABLE" else event
            reasons = tuple(f"{name}_{x}" for x in failing.document()["reason_codes"])
            condition = "INSUFFICIENT" in (structure.status, event.status)
            return result(
                "INSUFFICIENT" if condition else "INVALID", (*notes, *reasons), tuple(bindings)
            )
        sd, ed = structure.document(), event.document()
        context = ContextEvidence.model_validate_json(FrozenJSON.of(sd["evidence"]).data)
        events = tuple(
            EventEvidence.model_validate_json(FrozenJSON.of(record["record"]["evidence"]).data)
            for record in ed["records"]
        )
        periods[name] = Period(data, context, events)
        bindings.append(
            UpstreamBinding(
                timeframe=cast(Literal["W1", "D1", "M30"], name),
                input_hash=data.input_hash,
                structure_result_hash=structure.canonical_result_hash,
                event_result_hash=event.canonical_result_hash,
                structure_code_hash=sd["code_hash"],
                event_code_hash=ed["code_hash"],
                structure_config_hash=sd["config_hash"],
                event_config_hash=ed["config_hash"],
                structure_version="1.0.1",
                event_version="1.0.1",
            )
        )
    facts, reasons = Replay(bundle, periods).run()
    return result("AVAILABLE", (*notes, *reasons), tuple(bindings), facts)
