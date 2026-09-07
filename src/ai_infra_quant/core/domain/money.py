from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

MAX_EXACT_DECIMAL = Decimal("99999999999999999999.999999999999999999")
SCALE = 18
_CANONICAL_INPUT = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$")


def parse_decimal(value: object) -> Decimal:
    if isinstance(value, bool | float | int):
        raise TypeError("financial values must be Decimal or canonical decimal strings")
    if isinstance(value, str):
        if not _CANONICAL_INPUT.fullmatch(value):
            raise ValueError("decimal string must use plain canonical notation")
        try:
            parsed = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("invalid decimal string") from exc
    elif isinstance(value, Decimal):
        parsed = value
    else:
        raise TypeError("financial values must be Decimal or canonical decimal strings")
    if not parsed.is_finite():
        raise ValueError("financial values must be finite")
    exponent = parsed.as_tuple().exponent
    if not isinstance(exponent, int):
        raise ValueError("financial values must be finite")
    if exponent < -SCALE:
        raise ValueError("financial value exceeds scale 18")
    if parsed.copy_abs() > MAX_EXACT_DECIMAL:
        raise ValueError("financial value exceeds precision 38")
    if parsed == 0:
        return parsed.copy_abs()
    return parsed


def decimal_string(value: Decimal) -> str:
    parsed = parse_decimal(value)
    return format(parsed, "f")


def canonical_decimal_string(value: Decimal) -> str:
    """Render a scale-insensitive decimal for hashes and idempotency keys."""
    parsed = parse_decimal(value)
    if parsed == 0:
        return "0"
    # Decimal.normalize() rounds through the ambient arithmetic context. Audit
    # serialization must retain every accepted digit even at a lower precision.
    rendered = format(parsed, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


@dataclass(frozen=True, slots=True)
class ExactValue:
    amount: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", parse_decimal(self.amount))

    def __str__(self) -> str:
        return decimal_string(self.amount)
