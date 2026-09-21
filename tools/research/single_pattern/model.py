"""Small immutable input/config records; financial arithmetic is Decimal."""

from dataclasses import dataclass, fields
from decimal import Decimal
from typing import Any

from tools.research.paqs_q.types import Dataset

STRATEGY = "local-high-retest-v1"


@dataclass(frozen=True)
class Config:
    initial_cash: Decimal = Decimal("100000")
    allocation: Decimal = Decimal("0.95")
    fee_rate: Decimal = Decimal("0.001")
    slippage: Decimal = Decimal("0.0005")
    lot_size: int = 1
    target_r: Decimal = Decimal("2")
    max_hold: int = 20
    breakout_buffer: Decimal = Decimal("0.15")
    outer: Decimal = Decimal("0.25")
    inner: Decimal = Decimal("0.20")
    failure_buffer: Decimal = Decimal("0.15")
    stop_buffer: Decimal = Decimal("0.15")
    retest_window: int = 15
    body_min: Decimal = Decimal("0.60")
    clv_min: Decimal = Decimal("0.75")
    range_min: Decimal = Decimal("0.80")

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name in {"lot_size", "max_hold", "retest_window"}:
                if type(value) is not int or not 1 <= value <= 100000:
                    raise ValueError(f"INVALID_CONFIG:{field.name}")
            elif not isinstance(value, Decimal) or not value.is_finite() or value < 0:
                raise ValueError(f"INVALID_CONFIG:{field.name}")
        if not (0 < self.initial_cash <= Decimal("1e18") and 0 < self.allocation <= 1):
            raise ValueError("INVALID_CAPITAL")
        if not (self.fee_rate < 1 and self.slippage < 1 and self.target_r > 0):
            raise ValueError("INVALID_COST_OR_TARGET")
        if not (0 <= self.body_min <= 1 and 0 <= self.clv_min <= 1):
            raise ValueError("INVALID_SIGNAL_RATIO")


@dataclass(frozen=True)
class Input:
    data: Dataset
    currency: str
    metadata: dict[str, Any]
