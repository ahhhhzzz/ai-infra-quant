from decimal import Decimal

import pytest
from sqlalchemy.dialects import postgresql, sqlite

from ai_infra_quant.core.domain.money import canonical_decimal_string, decimal_string, parse_decimal
from ai_infra_quant.database.types import ExactDecimal


def test_dialect_compilation() -> None:
    exact = ExactDecimal(38, 18)
    assert str(exact.compile(dialect=sqlite.dialect())) == "TEXT"  # type: ignore[no-untyped-call]
    assert str(exact.compile(dialect=postgresql.dialect())) == (  # type: ignore[no-untyped-call]
        "NUMERIC(38,18)"
    )


def test_canonical_fixed_scale_storage() -> None:
    assert ExactDecimal.canonical_storage(Decimal("100.000000000000000001")) == (
        "00000000000000000100.000000000000000001"
    )
    assert ExactDecimal.canonical_storage(Decimal("-1.5")) == (
        "-00000000000000000001.500000000000000000"
    )


@pytest.mark.parametrize(
    "value",
    [
        1.5,
        1,
        True,
        "1e2",
        "01.0",
        ".5",
        "1.",
        "NaN",
        "0.1234567890123456789",
        "100000000000000000000.000000000000000000",
    ],
)
def test_invalid_decimal_input_is_rejected(value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        parse_decimal(value)


@pytest.mark.parametrize(
    "zero",
    [Decimal("-0"), Decimal("-0.00"), Decimal("0.000000000000000000")],
)
def test_signed_zero_is_positive_in_domain_serialization_and_hashes(zero: Decimal) -> None:
    parsed = parse_decimal(zero)
    assert parsed == Decimal(0)
    assert not parsed.is_signed()
    assert not decimal_string(zero).startswith("-")
    assert canonical_decimal_string(zero) == "0"
