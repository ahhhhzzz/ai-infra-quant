"""Hand-computed sizing and causal compatibility; synthetic data only."""

import csv
import json
from dataclasses import replace
from decimal import Decimal, localcontext

import pytest

from tools.research.paqs_q.types import CONTEXT
from tools.research.single_pattern.comparison import compare, write_comparison
from tools.research.single_pattern.integrations.local import demo, load
from tools.research.single_pattern.model import Config
from tools.research.single_pattern.report import run
from tools.research.single_pattern.simulation import simulate
from tools.research.single_pattern.sizing import SizingConfig, plan_entry

D = Decimal


@pytest.fixture
def source(tmp_path):
    path, calendar = demo(tmp_path / "input")
    return load(path, calendar, "America/New_York", "USD")


def test_hand_costs_distance_and_lot_limits():
    config = Config()
    narrow = plan_entry(D(10000), D(100), D(90), 94, config, SizingConfig("fixed-risk"))
    wide = plan_entry(D(10000), D(100), D(80), 94, config, SizingConfig("fixed-risk"))
    assert narrow["expected_stop_fill"] == D("89.955")
    assert narrow["planned_loss_per_share"] == D("10.234955")
    assert narrow["risk_budget"] == D(100)
    assert narrow["quantity"] == 9 and wide["quantity"] == 4
    assert narrow["planned_stop_loss"] == D("92.114595")
    assert narrow["sizing_constraint"] == "RISK"
    lot = plan_entry(
        D(10000), D(100), D(90), 90, replace(config, lot_size=5), SizingConfig("fixed-risk")
    )
    assert lot["quantity"] == 5
    cash = plan_entry(D(10000), D(100), D("99.99"), 5, config, SizingConfig("fixed-risk"))
    assert cash["quantity"] == 5 and cash["sizing_constraint"] == "CASH"
    equal = plan_entry(D(10000), D(100), D(90), 9, config, SizingConfig("fixed-risk"))
    assert equal["sizing_constraint"] == "BOTH"
    assert narrow["planned_stop_loss"] <= narrow["risk_budget"]
    assert narrow["planned_loss_per_share"] * (narrow["risk_quantity"] + 1) > narrow["risk_budget"]


def test_invalid_sizing_and_nonfinite_inputs():
    for fraction in (0.01, D(0), D(-1), D("1.01"), D("NaN"), D("Infinity")):
        with pytest.raises(ValueError, match="INVALID_RISK_FRACTION"):
            SizingConfig("fixed-risk", fraction)
    with pytest.raises(ValueError, match="INVALID_SIZING_MODE"):
        SizingConfig("unknown")
    for cash, price, stop in (
        (D("NaN"), D(10), D(8)),
        (D(100), D("Infinity"), D(8)),
        (D(100), D(10), D("NaN")),
        (D(-1), D(10), D(8)),
        (D(100), D(10), D(10)),
        (D(100), D(10), D(0)),
    ):
        with pytest.raises(ValueError):
            plan_entry(cash, price, stop, 1, Config(), SizingConfig("fixed-risk"))


def small_scenario(source, rows):
    bars = tuple(
        replace(bar, open=D(o), high=D(h), low=D(low), close=D(c))
        for bar, (o, h, low, c) in zip(source.data.bars, rows, strict=False)
    )
    data = replace(source.data, bars=bars)
    signal = {
        "signal_id": "SYNTHETIC",
        "index": 0,
        "signal_time": bars[0].end,
        "level": D(9),
        "stop": D(8),
    }
    return data, signal


def test_pre_open_equity_gap_loss_and_exact_accounting(source):
    data, signal = small_scenario(
        source, [("10", "11", "9", "10"), ("10", "13", "9", "12"), ("7", "9", "6", "8")]
    )
    config = Config(initial_cash=D(1000), allocation=D(1), fee_rate=D(".01"), slippage=D(".1"))
    result = simulate(data, [signal], config, sizing=SizingConfig("fixed-risk"))
    t = result["trades"][0]
    assert (t["entry_index"], t["entry_price"], t["entry_equity"], t["quantity"]) == (
        1,
        D(11),
        D(1000),
        2,
    )
    assert t["planned_loss_per_share"] == D("3.982")
    assert t["risk_budget"] == D(10) and t["planned_stop_loss"] == D("7.964")
    assert (t["exit_reason"], t["exit_price"], t["pnl"]) == ("GAP_STOP", D("6.3"), D("-9.746"))
    # A deeper gap exceeds the planned budget without changing stop or fill rules.
    gap = replace(data, bars=(*data.bars[:2], replace(data.bars[2], open=D(4), low=D(3))))
    deeper = simulate(gap, [signal], config, sizing=SizingConfig("fixed-risk"))
    dt = deeper["trades"][0]
    assert dt["exit_price"] == D("3.6") and dt["pnl"] == D("-15.092")
    assert -dt["pnl"] > dt["risk_budget"]
    assert deeper["summary"]["total_fees"] == D(".292")
    assert deeper["summary"]["final_equity"] == D("984.908")
    with localcontext(CONTEXT):
        assert deeper["summary"]["max_drawdown"] == 1 - D("984.908") / D("1001.78")
    assert all(e["cash"] >= 0 for e in deeper["equity"])
    changed_close = replace(
        data, bars=(data.bars[0], replace(data.bars[1], close=D(9)), data.bars[2])
    )
    assert (
        simulate(changed_close, [signal], config, sizing=SizingConfig("fixed-risk"))["trades"]
        == result["trades"]
    )


def test_zero_quantity_cash_cap_and_conflict(source):
    data, signal = small_scenario(source, [("10", "11", "9", "10"), ("10", "15", "7", "11")])
    config = Config(initial_cash=D(100), fee_rate=D(0), slippage=D(0))
    zero = simulate(data, [signal], config, sizing=SizingConfig("fixed-risk"))
    assert zero["decisions"][-1]["status"] == "ZERO_RISK_QUANTITY"
    assert zero["decisions"][-1]["quantity"] == 0 and not zero["trades"]
    assert zero["summary"]["win_rate"] is None
    both = simulate(
        data, [signal], replace(config, lot_size=100), sizing=SizingConfig("fixed-risk")
    )
    assert both["decisions"][-1]["status"] == "ZERO_CASH_AND_RISK_QUANTITY"
    # Small allocation is the binding cap, with conservative entry-bar stop before target.
    capped = simulate(
        data,
        [signal],
        replace(config, initial_cash=D(10000), allocation=D(".01")),
        sizing=SizingConfig("fixed-risk"),
    )
    trade = capped["trades"][0]
    assert trade["quantity"] == 10 and trade["sizing_constraint"] == "CASH"
    assert trade["exit_reason"] == "STOP_FIRST" and trade["exit_price"] == D(8)
    assert trade["entry_index"] == trade["exit_index"] == 1


def project_like(new, old):
    if isinstance(old, dict):
        return {k: project_like(new[k], v) for k, v in old.items()}
    if isinstance(old, list):
        assert len(new) == len(old)
        return [project_like(a, b) for a, b in zip(new, old, strict=True)]
    return new


def test_cash_compatibility_shared_signals_fills_and_benchmark(source):
    legacy = run(source, Config())
    result = compare(source, Config(), D(".01"))
    assert result["strategy"] == legacy["strategy"]
    assert result["comparison"]["common_entries"] == 3
    assert not result["comparison"]["cash_only"] and not result["comparison"]["fixed_risk_only"]
    mode = result["modes"]["cash"]
    for key in ("trades", "decisions", "equity", "open_position", "pending_signal", "summary"):
        assert project_like(mode[key], legacy[key]) == legacy[key]
    for mode in result["modes"].values():
        with localcontext(CONTEXT):
            fees = sum((D(t["entry_fee"]) + D(t["exit_fee"]) for t in mode["trades"]), D(0))
            fees += D(mode["open_position"]["entry_fee"])
        assert D(mode["summary"]["total_fees"]) == fees
    changed_sizing = run(source, Config(), sizing=SizingConfig("fixed-risk", D(".02")))
    assert changed_sizing["strategy"] == legacy["strategy"]


def test_risk_decisions_prefix_and_decimal_context(source):
    config, sizing = Config(), SizingConfig("fixed-risk")
    full = run(source, config, sizing=sizing)
    for count in (24, 25, 51, 60, 77):
        prefix = run(
            replace(source, data=replace(source.data, bars=source.data.bars[:count])),
            config,
            sizing=sizing,
        )
        assert prefix["strategy"]["signals"] == [
            s for s in full["strategy"]["signals"] if s["index"] < count
        ]
        assert prefix["decisions"] == [d for d in full["decisions"] if d["index"] < count]
        assert prefix["trades"] == [t for t in full["trades"] if t["exit_index"] < count]
        assert prefix["equity"] == full["equity"][:count]
    with localcontext() as context:
        context.prec = 6
        assert run(source, config, sizing=sizing) == full


def test_comparison_exact_exports_and_no_overwrite(source, tmp_path):
    result = compare(source, Config(), D(".01"))
    result["security"] = "</script><script>alert('x')</script>"
    output = tmp_path / "comparison"
    write_comparison(result, output)
    assert json.loads((output / "results.json").read_text(encoding="utf-8")) == result
    html = (output / "report.html").read_text(encoding="utf-8")
    assert "</script><script>alert" not in html and "\\u003c/script" in html
    for filename, rows in (
        ("summary", [{"mode": name, **mode["summary"]} for name, mode in result["modes"].items()]),
        (
            "equity",
            [
                {"mode": name, **row}
                for name, mode in result["modes"].items()
                for row in mode["equity"]
            ],
        ),
    ):
        with (output / f"{filename}.csv").open(encoding="utf-8-sig", newline="") as stream:
            assert list(csv.DictReader(stream)) == [
                {k: "" if v is None else str(v) for k, v in row.items()} for row in rows
            ]
    with (output / "trades.csv").open(encoding="utf-8-sig", newline="") as stream:
        trades = list(csv.DictReader(stream))
    assert len(trades) == 6 and sum(row["status"] == "OPEN" for row in trades) == 2
    assert (
        trades[3]["planned_stop_loss"]
        == result["modes"]["fixed-risk"]["trades"][0]["planned_stop_loss"]
    )
    with pytest.raises(FileExistsError):
        write_comparison(result, output)
