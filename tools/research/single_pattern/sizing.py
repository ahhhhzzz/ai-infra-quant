"""Explicit experiment sizing, separate from the frozen v1 signal hash config."""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Any

from tools.research.paqs_q.types import CONTEXT

from .model import Config


@dataclass(frozen=True)
class SizingConfig:
    mode: str = "cash"
    risk_fraction: Decimal = Decimal("0.01")

    def __post_init__(self) -> None:
        if self.mode not in {"cash", "fixed-risk"}:
            raise ValueError("INVALID_SIZING_MODE")
        if (
            not isinstance(self.risk_fraction, Decimal)
            or not self.risk_fraction.is_finite()
            or not 0 < self.risk_fraction <= 1
        ):
            raise ValueError("INVALID_RISK_FRACTION:required finite Decimal in (0,1]")


def plan_entry(
    cash: Decimal,
    price: Decimal,
    stop: Decimal,
    cash_quantity: int,
    config: Config,
    sizing: SizingConfig,
) -> dict[str, Any]:
    """Called flat, before purchase. cash_quantity comes from the unchanged v1 buy()."""
    for value in (cash, price, stop):
        if not isinstance(value, Decimal) or not value.is_finite():
            raise ValueError("INVALID_SIZING_INPUT")
    if cash < 0 or not 0 < stop < price:
        raise ValueError("INVALID_ENTRY_EQUITY_OR_STOP")
    if type(cash_quantity) is not int or cash_quantity < 0 or cash_quantity % config.lot_size:
        raise ValueError("INVALID_CASH_QUANTITY")
    with localcontext(CONTEXT):
        stop_fill = stop * (1 - config.slippage)
        loss = price * (1 + config.fee_rate) - stop_fill * (1 - config.fee_rate)
        if not loss.is_finite() or loss <= 0:
            raise ValueError("INVALID_PLANNED_LOSS_PER_SHARE")
        budget = cash * sizing.risk_fraction if sizing.mode == "fixed-risk" else None
        risk_quantity = None
        quantity, constraint = cash_quantity, "CASH"
        if budget is not None:
            risk_quantity = int(budget / (loss * config.lot_size)) * config.lot_size
            # Guard a rounded division immediately next to an exact lot boundary.
            if risk_quantity * loss > budget:
                risk_quantity -= config.lot_size
            quantity = min(cash_quantity, risk_quantity)
            constraint = (
                "RISK"
                if risk_quantity < cash_quantity
                else ("CASH" if cash_quantity < risk_quantity else "BOTH")
            )
        planned = loss * quantity
        return {
            "sizing_mode": sizing.mode,
            "entry_equity": cash,
            "stop_distance": price - stop,
            "expected_stop_fill": stop_fill,
            "planned_loss_per_share": loss,
            "risk_budget": budget,
            "risk_fraction": sizing.risk_fraction if budget is not None else None,
            "cash_quantity": cash_quantity,
            "risk_quantity": risk_quantity,
            "quantity": quantity,
            "sizing_constraint": constraint,
            "planned_stop_loss": planned,
            "planned_loss_fraction": planned / cash if cash else None,
        }
