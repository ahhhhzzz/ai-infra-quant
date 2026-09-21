"""Frozen expected outputs predate the port. New identities remain separate."""

import json
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
from decimal import Decimal, localcontext

import pytest

from ai_infra_quant.application.paqs_q_artifacts import load_registry
from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON
from ai_infra_quant.core.domain.paqs_q.inputs import QInput
from tests.paqs_q.support import GOLDEN, ROOT, decode, read_golden, synthetic


@pytest.mark.parametrize("vector", read_golden()["vectors"], ids=lambda v: v["name"])
def test_full_frozen_projection(vector):
    data = decode(vector["input"])
    registry = load_registry(ROOT, include_experimental=True)
    for arm, version in (("B0", "1.0.0"), ("A1", "0.1.0")):
        result = registry.structure(
            data, "paqs-q-structure-" + arm.lower(), version, allow_experimental=arm == "A1"
        )
        expected = vector["expected"][arm]
        if expected["status"] == "VALID":
            assert result.status == "AVAILABLE"
            assert result.document()["evidence"] == expected
            assert len(result.document()["records"]) == len(expected["events"])
            assert all(
                r["record_id"] != r["record"]["legacy"]["identity"]
                for r in result.document()["records"]
            )
        else:
            assert result.status == "INSUFFICIENT"
            assert result.document()["reason_codes"] == [expected["reason"]]
            assert result.document()["evidence"] is None and result.document()["records"] == []


@pytest.mark.parametrize("chain", [False, True])
def test_hand_calculated_synthetic(chain):
    data = synthetic(chain=chain)
    registry = load_registry(ROOT, include_experimental=True)
    spec = json.loads((GOLDEN / "synthetic.json").read_text())["expected"][
        "chain" if chain else "flat"
    ]
    for arm, version in (("B0", "1.0.0"), ("A1", "0.1.0")):
        out = registry.structure(
            data, "paqs-q-structure-" + arm.lower(), version, allow_experimental=True
        )
        assert out.status == "AVAILABLE"
        events = out.document()["evidence"]["events"]
        assert [[e["index"], e["kind"], e["price"]] for e in events] == spec[arm]


def test_recursive_immutability_and_context_independence():
    data = synthetic()
    bars, facts = list(data.bars), list(data.calendar)
    original = {"nested": ["retained"]}
    frozen = replace(data, bars=bars, calendar=facts, provenance=FrozenJSON.of(original))  # type: ignore[arg-type]
    bars.clear()
    facts.clear()
    original["nested"].append("changed")
    registry = load_registry(ROOT)
    result = registry.structure(frozen)
    before = result.canonical_bytes
    result.document()["records"].clear()
    with pytest.raises(FrozenInstanceError):
        frozen.bars = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen.bars[0].close = Decimal("1")  # type: ignore[misc]
    with localcontext() as ctx:
        ctx.prec = 3
        ctx.rounding = "ROUND_DOWN"
        assert registry.structure(frozen).canonical_bytes == before
    assert (
        registry.structure(
            replace(
                frozen, bars=tuple(reversed(frozen.bars)), calendar=tuple(reversed(frozen.calendar))
            )
        ).canonical_bytes
        == before
    )


@pytest.mark.parametrize(
    "change,reason",
    [
        ("future_price", "FUTURE_PRICE_EVIDENCE"),
        ("future_calendar", "FUTURE_CALENDAR_EVIDENCE"),
        ("unfinished", "UNFINISHED_BAR"),
        ("duplicate_price", "CONFLICTING_TIME_VERSION"),
        ("duplicate_calendar", "CALENDAR_CONFLICT"),
        ("bad_price", "OHLC_INVALID"),
    ],
)
def test_invalid_input_never_leaks_success_evidence(change, reason):
    data = synthetic()
    if change == "future_price":
        data = replace(
            data,
            bars=(
                *data.bars[:-1],
                replace(data.bars[-1], available_at=data.as_of + timedelta(days=1)),
            ),
        )
    elif change == "future_calendar":
        data = replace(
            data,
            calendar=(
                replace(data.calendar[0], available_at=data.as_of + timedelta(days=1)),
                *data.calendar[1:],
            ),
        )
    elif change == "unfinished":
        data = replace(data, bars=(replace(data.bars[0], completed=False), *data.bars[1:]))
    elif change == "duplicate_price":
        data = replace(data, bars=(*data.bars, data.bars[0]))
    elif change == "duplicate_calendar":
        data = replace(data, calendar=(*data.calendar, data.calendar[0]))
    else:
        data = replace(data, bars=(replace(data.bars[0], high=Decimal("1")), *data.bars[1:]))
    result = load_registry(ROOT).structure(data).document()
    assert result["status"] == "INVALID" and result["reason_codes"] == [reason]
    assert result["records"] == [] and result["evidence"] is None


def test_strict_unknown_and_observational_distinction():
    data = synthetic()
    unknown = replace(data, bars=tuple(replace(b, available_at=None) for b in data.bars))
    registry = load_registry(ROOT)
    assert registry.structure(unknown).status == "INSUFFICIENT"
    observed = registry.structure(replace(unknown, mode="OBSERVATIONAL"))
    assert observed.status == "AVAILABLE"
    assert observed.document()["evidence"]["strict_confirmation"] is False
    assert any(
        r["record"]["legacy"]["available_at"] is None for r in observed.document()["records"]
    )
    for changed in (
        replace(data, quality="PARTIAL"),
        replace(data, bars=tuple(replace(b, adjustment="PROVIDER_QFQ_CURRENT") for b in data.bars)),
        replace(data, bars=data.bars[:-1]),
    ):
        assert registry.structure(changed).status == "INSUFFICIENT"


def test_canonical_input_rejects_bad_schema_and_float():
    data = synthetic()
    with pytest.raises(ValueError, match="FINITE_DECIMAL"):
        replace(data.bars[0], close=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="AWARE"):
        replace(data, as_of=data.as_of.replace(tzinfo=None))
    with pytest.raises(ValueError, match="INPUT_SCHEMA"):
        replace(data, schema_version="later")
    with pytest.raises(TypeError):
        QInput(**(data.payload() | {"invented": True}))
