from __future__ import annotations

import hashlib
import json
from decimal import Decimal, localcontext

import pytest

from ai_infra_quant.core.domain.money import (
    MAX_EXACT_DECIMAL,
    canonical_decimal_string,
    parse_decimal,
)
from ai_infra_quant.core.domain.paqs_e_ledger import verified_json
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json


@pytest.mark.parametrize("precision", [9, 28, 60])
def test_evidence_serialization_keeps_all_financial_digits_at_any_arithmetic_precision(
    precision: int,
) -> None:
    amount = Decimal("12345678901234567890.123456789012345678")
    expected = '{"amount":"12345678901234567890.123456789012345678"}'
    with localcontext() as context:
        context.prec = precision
        text = canonical_json({"amount": amount})
        assert text == expected
        assert Decimal(json.loads(text)["amount"]) == amount
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert verified_json(text, digest) == json.loads(expected)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("100", "100"), ("100.000", "100"), ("1.25000", "1.25"), ("-0.0", "0"), ("-10.20", "-10.2")],
)
def test_exact_serializer_preserves_existing_scale_insensitive_canonical_form(
    value: str,
    expected: str,
) -> None:
    assert canonical_decimal_string(Decimal(value)) == expected


@pytest.mark.parametrize("precision", [9, 28, 60])
def test_exact_decimal_bounds_do_not_round_before_comparison(precision: int) -> None:
    with localcontext() as context:
        context.prec = precision
        assert parse_decimal(MAX_EXACT_DECIMAL) == MAX_EXACT_DECIMAL
        assert parse_decimal(MAX_EXACT_DECIMAL.copy_negate()) == MAX_EXACT_DECIMAL.copy_negate()
        assert canonical_decimal_string(MAX_EXACT_DECIMAL) == format(MAX_EXACT_DECIMAL, "f")
        with pytest.raises(ValueError, match="precision 38"):
            parse_decimal(Decimal("100000000000000000000"))
