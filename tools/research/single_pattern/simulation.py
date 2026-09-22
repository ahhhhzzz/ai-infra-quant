"""One instrument, one cash-funded long. No broker, ledger or order interface."""

from decimal import Decimal, localcontext
from typing import Any

from tools.research.paqs_q.types import CONTEXT, Bar, Dataset

from .model import Config
from .sizing import SizingConfig, plan_entry


def buy(cash: Decimal, price: Decimal, config: Config) -> tuple[int, Decimal]:
    budget = cash * config.allocation
    lots = int(budget / (price * (1 + config.fee_rate) * config.lot_size))
    quantity = lots * config.lot_size
    return quantity, price * quantity * config.fee_rate


def exit_quote(
    bar: Bar, position: dict[str, Any], timed_exit: bool
) -> tuple[Decimal, str, str] | None:
    stop, target = position["stop"], position["target"]
    if bar.open <= stop:
        return bar.open, "GAP_STOP", "OPEN"
    if timed_exit:
        return bar.open, "TIME_EXIT", "OPEN"
    if bar.open >= target:
        return target, "TARGET_GAP_CAPPED", "OPEN"
    if bar.low <= stop:
        return stop, "STOP_FIRST" if bar.high >= target else "STOP", "INTRABAR_UNKNOWN"
    if bar.high >= target:
        return target, "TARGET", "INTRABAR_UNKNOWN"
    return None


def simulate(
    data: Dataset,
    signals: list[dict[str, Any]],
    config: Config,
    *,
    sizing: SizingConfig | None = None,
) -> dict[str, Any]:
    with localcontext(CONTEXT):
        return _simulate(data, signals, config, sizing)


def _simulate(
    data: Dataset,
    signals: list[dict[str, Any]],
    config: Config,
    sizing: SizingConfig | None,
) -> dict[str, Any]:
    cash = config.initial_cash
    position: dict[str, Any] | None = None
    trades: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    equity: list[dict[str, Any]] = []
    by_index = {signal["index"]: signal for signal in signals}
    if len(by_index) != len(signals):
        raise ValueError("DUPLICATE_SIGNAL_BAR")
    pending: dict[str, Any] | None = None
    peak = config.initial_cash
    max_drawdown = Decimal(0)
    first_price = data.bars[0].open * (1 + config.slippage)
    benchmark_qty, benchmark_fee = buy(config.initial_cash, first_price, config)
    benchmark_cash = config.initial_cash - first_price * benchmark_qty - benchmark_fee
    benchmark_peak = config.initial_cash
    benchmark_drawdown = Decimal(0)
    for i, bar in enumerate(data.bars):
        if pending is not None:
            if position is not None:
                raise ValueError("ENTRY_REQUIRES_FLAT_ACCOUNT")
            signal = pending
            pending = None
            if bar.open <= signal["stop"] or bar.open <= signal["level"]:
                decisions.append(
                    {
                        "signal_id": signal["signal_id"],
                        "index": i,
                        "status": "CANCELLED_OPEN_INVALID",
                    }
                )
            else:
                price = bar.open * (1 + config.slippage)
                quantity, fee = buy(cash, price, config)
                plan = {}
                if sizing is not None:
                    plan = plan_entry(cash, price, signal["stop"], quantity, config, sizing)
                    quantity = plan["quantity"]
                    fee = price * quantity * config.fee_rate
                if quantity == 0:
                    decisions.append(
                        {
                            "signal_id": signal["signal_id"],
                            "index": i,
                            "status": (
                                "ZERO_RISK_QUANTITY"
                                if plan.get("sizing_constraint") == "RISK"
                                else "ZERO_CASH_AND_RISK_QUANTITY"
                                if plan.get("sizing_constraint") == "BOTH"
                                else "INSUFFICIENT_CASH"
                            ),
                            **plan,
                        }
                    )
                else:
                    cash -= price * quantity + fee
                    position = {
                        **plan,
                        "signal_id": signal["signal_id"],
                        "signal_time": signal["signal_time"],
                        "signal_index": signal["index"],
                        "entry_index": i,
                        "entry_time": bar.start,
                        "entry_price": price,
                        "quantity": quantity,
                        "entry_fee": fee,
                        "stop": signal["stop"],
                        "target": price + config.target_r * (price - signal["stop"]),
                    }
                    decisions.append(
                        {"signal_id": signal["signal_id"], "index": i, "status": "ENTERED"}
                    )
        if position is not None:
            quote = exit_quote(bar, position, i - position["entry_index"] >= config.max_hold)
            if quote is not None:
                raw_price, reason, phase = quote
                price = raw_price * (1 - config.slippage)
                fee = price * position["quantity"] * config.fee_rate
                cash += price * position["quantity"] - fee
                pnl = (
                    (price - position["entry_price"]) * position["quantity"]
                    - fee
                    - position["entry_fee"]
                )
                trades.append(
                    {
                        **position,
                        "exit_index": i,
                        "exit_bar_start": bar.start,
                        "exit_bar_end": bar.end,
                        "exit_time": bar.start if phase == "OPEN" else None,
                        "exit_phase": phase,
                        "exit_price": price,
                        "exit_fee": fee,
                        "exit_reason": reason,
                        "pnl": pnl,
                        "return_on_cost": pnl
                        / (position["entry_price"] * position["quantity"] + position["entry_fee"]),
                        **(
                            {"pnl_fraction_of_entry_equity": pnl / position["entry_equity"]}
                            if sizing is not None
                            else {}
                        ),
                    }
                )
                position = None
        if i in by_index:
            signal = by_index[i]
            if position is None:
                pending = signal
                decisions.append(
                    {"signal_id": signal["signal_id"], "index": i, "status": "PENDING_NEXT_OPEN"}
                )
            else:
                decisions.append(
                    {"signal_id": signal["signal_id"], "index": i, "status": "IGNORED_WHILE_HELD"}
                )
        quantity = position["quantity"] if position is not None else 0
        nav = cash + quantity * bar.close
        peak = max(peak, nav)
        dd = 1 - nav / peak
        max_drawdown = max(max_drawdown, dd)
        bh = benchmark_cash + benchmark_qty * bar.close
        benchmark_peak = max(benchmark_peak, bh)
        bh_dd = 1 - bh / benchmark_peak
        benchmark_drawdown = max(benchmark_drawdown, bh_dd)
        equity.append(
            {
                "index": i,
                "time": bar.end,
                "cash": cash,
                "quantity": quantity,
                "equity": nav,
                "drawdown": dd,
                "buy_hold": bh,
                "buy_hold_drawdown": bh_dd,
            }
        )
    open_position = None
    if position is not None:
        open_position = {
            **position,
            "mark_price": data.bars[-1].close,
            "unrealized_pnl_net_entry_fee": (data.bars[-1].close - position["entry_price"])
            * position["quantity"]
            - position["entry_fee"],
        }
    realized = sum((trade["pnl"] for trade in trades), Decimal(0))
    extra_summary = {}
    if sizing is not None:
        extra_summary["total_fees"] = sum(
            (t["entry_fee"] + t["exit_fee"] for t in trades), Decimal(0)
        ) + (position["entry_fee"] if position is not None else Decimal(0))
        if open_position is not None:
            open_position["unrealized_pnl_fraction_of_entry_equity"] = (
                open_position["unrealized_pnl_net_entry_fee"] / open_position["entry_equity"]
            )
    return {
        "trades": trades,
        "decisions": decisions,
        "equity": equity,
        "open_position": open_position,
        "pending_signal": pending,
        "summary": {
            **extra_summary,
            "initial_cash": config.initial_cash,
            "final_equity": equity[-1]["equity"],
            "total_return": equity[-1]["equity"] / config.initial_cash - 1,
            "max_drawdown": max_drawdown,
            "closed_trades": len(trades),
            "open_positions": int(position is not None),
            "entries": len(trades) + int(position is not None),
            "win_rate": Decimal(sum(t["pnl"] > 0 for t in trades)) / len(trades)
            if trades
            else None,
            "realized_pnl": realized,
            "buy_hold_return": equity[-1]["buy_hold"] / config.initial_cash - 1,
            "buy_hold_max_drawdown": benchmark_drawdown,
            "buy_hold_quantity": benchmark_qty,
            "buy_hold_entry_fee": benchmark_fee,
            "metrics_basis": (
                "close-marked NAV; no final liquidation; no dividends; win rate closed trades only"
            ),
        },
    }
