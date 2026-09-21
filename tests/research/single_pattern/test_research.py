"""Bounded causal/accounting checks; all market paths here are synthetic."""

import json
from dataclasses import replace
from decimal import Decimal, localcontext

import pytest

from tools.research.paqs_q.io import write_dataset
from tools.research.paqs_q.types import CONTEXT
from tools.research.single_pattern.integrations.local import calendar, demo, load, validate
from tools.research.single_pattern.model import Config
from tools.research.single_pattern.report import run, write_report
from tools.research.single_pattern.simulation import simulate
from tools.research.single_pattern.strategy import signals

D = Decimal


@pytest.fixture
def sample(tmp_path):
    source, cal = demo(tmp_path / "input")
    return load(source, cal, "America/New_York", "USD"), cal


def test_hand_fixed_signal_times_and_prefix_invariance(sample):
    source, _ = sample
    full = signals(source.data, Config())
    assert [
        (
            s["index"],
            s["level_extreme_index"],
            s["level_known_index"],
            s["breakout_index"],
            s["touch_index"],
        )
        for s in full["signals"]
    ] == [(23, 18, 19, 21, 22), (50, 45, 46, 48, 49), (76, 71, 72, 74, 75)]
    for count in range(1, len(source.data.bars) + 1):
        prefix = replace(source.data, bars=source.data.bars[:count])
        result = signals(prefix, Config())
        for key, clock in (("signals", "index"), ("events", "index"), ("points", "known_index")):
            assert result[key] == [r for r in full[key] if r[clock] < count]
    bars = list(source.data.bars)
    bars[-1] = replace(bars[-1], high=D("10000"), close=D("9999"))
    assert signals(replace(source.data, bars=tuple(bars)), Config())["signals"] == full["signals"]


def test_confirmation_not_backfilled_and_no_same_bar_hold(sample):
    source, _ = sample
    bars = list(source.data.bars[:24])
    assert not signals(replace(source.data, bars=tuple(bars[:19])), Config())["points"]
    assert (
        signals(replace(source.data, bars=tuple(bars[:20])), Config())["points"][0]["known_index"]
        == 19
    )
    # A strong retest bar cannot confirm its own retest. Later flat bar cannot trigger.
    bars[22] = replace(bars[22], open=D("104"), high=D("108"), low=D("103.8"), close=D("107.5"))
    bars[23] = replace(bars[23], open=D("107"), high=D("108"), low=D("106"), close=D("107"))
    assert not signals(replace(source.data, bars=tuple(bars)), Config())["signals"]


def test_deadline_equality_failure_and_no_duplicate_signal(sample):
    source, _ = sample
    data = replace(source.data, bars=source.data.bars[:27])
    assert len(signals(data, Config(retest_window=2))["signals"]) == 1  # deadline accepted
    short = signals(data, Config(retest_window=1))
    assert not short["signals"]
    assert [e["type"] for e in short["events"]][-1] == "RETEST_EXPIRED"
    bars = list(data.bars)
    bars[22] = replace(bars[22], open=D("104"), high=D("105"), low=D("99"), close=D("100"))
    failed = signals(replace(data, bars=tuple(bars)), Config())
    assert not failed["signals"]
    assert any(e["type"] == "RETEST_FAILED" for e in failed["events"])
    bars = list(data.bars)
    bars[23] = replace(bars[23], open=D("102"), high=D("104"), low=D("101"), close=D("104"))
    assert not signals(replace(data, bars=tuple(bars[:24])), Config())["signals"]  # C=P


def test_bad_input_and_missing_sessions_are_rejected(sample):
    source, cal = sample
    schedule, _ = calendar(cal)
    data = source.data
    for change, message in (
        ({"completed": False}, "UNFINISHED"),
        ({"coverage": "PARTIAL"}, "INCOMPLETE"),
        ({"close": D("NaN")}, "NONFINITE"),
        ({"high": D("1")}, "OHLC"),
        ({"adjustment": "UNADJUSTED"}, "ADJUSTMENT"),
        ({"security": "HK.00001"}, "IDENTITY"),
        ({"start": data.bars[0].start.replace(tzinfo=None)}, "OFFSET"),
    ):
        changed = replace(data, bars=(replace(data.bars[0], **change), *data.bars[1:]))
        with pytest.raises(ValueError, match=message):
            validate(changed, schedule)
    with pytest.raises(ValueError, match="MISSING_SCHEDULED"):
        validate(replace(data, bars=data.bars[:20] + data.bars[21:]), schedule)
    with pytest.raises(ValueError, match="DUPLICATE"):
        validate(replace(data, bars=(data.bars[0], *data.bars)), schedule)


def test_existing_json_format_retains_observation_limitations(sample, tmp_path):
    source, cal = sample
    data = replace(
        source.data,
        bars=tuple(
            replace(b, adjustment="PROVIDER_QFQ_CURRENT", available_at=source.data.bars[-1].end)
            for b in source.data.bars
        ),
        quality="PARTIAL",
    )
    path = tmp_path / "observations.json"
    write_dataset(path, data)
    result = load(path, cal, "America/New_York", "USD")
    assert result.metadata["mode"] == "EXPLORATORY_NOT_POINT_IN_TIME"
    assert result.metadata["late_historical_availability"] == len(data.bars) - 1
    assert result.metadata["original_quality"] == "PARTIAL"
    assert result.data.bars[0].available_at == data.bars[0].available_at


def scenario(source, rows):
    bars = tuple(
        replace(b, open=D(o), high=D(h), low=D(low), close=D(c))
        for b, (o, h, low, c) in zip(source.data.bars, rows, strict=False)
    )
    data = replace(source.data, bars=bars)
    signal = {
        "signal_id": "TEST",
        "index": 0,
        "signal_time": bars[0].end,
        "level": D("9"),
        "stop": D("8"),
    }
    return data, signal


def test_cash_fees_pnl_drawdown_and_gap_stop_exact(sample):
    data, signal = scenario(
        sample[0], [("10", "11", "9", "10"), ("10", "11", "9", "10"), ("7", "9", "6", "8")]
    )
    config = Config(initial_cash=D("100"), allocation=D("1"), fee_rate=D("0.01"), slippage=D("0.1"))
    result = simulate(data, [signal], config)
    trade = result["trades"][0]
    assert (trade["entry_index"], trade["entry_price"], trade["quantity"], trade["entry_fee"]) == (
        1,
        D("11"),
        9,
        D("0.99"),
    )
    assert (trade["exit_reason"], trade["exit_price"], trade["exit_fee"], trade["pnl"]) == (
        "GAP_STOP",
        D("6.3"),
        D("0.567"),
        D("-43.857"),
    )
    assert result["summary"]["final_equity"] == D("56.143")
    assert result["summary"]["max_drawdown"] == D("0.43857")
    assert result["equity"][0]["quantity"] == 0
    assert all(row["cash"] >= 0 for row in result["equity"])


@pytest.mark.parametrize(
    "row,reason,price,phase",
    [
        (("10", "15", "7", "11"), "STOP_FIRST", "8", "INTRABAR_UNKNOWN"),
        (("10", "14", "9", "11"), "TARGET", "14", "INTRABAR_UNKNOWN"),
        (("10", "11", "8", "10"), "STOP", "8", "INTRABAR_UNKNOWN"),
    ],
)
def test_entry_bar_conservative_conflict_and_equal_touches(sample, row, reason, price, phase):
    data, signal = scenario(sample[0], [("10", "11", "9", "10"), row])
    result = simulate(data, [signal], Config(fee_rate=D("0"), slippage=D("0")))
    trade = result["trades"][0]
    assert (trade["entry_index"], trade["exit_index"]) == (1, 1)
    assert (trade["exit_reason"], trade["exit_price"], trade["exit_phase"]) == (
        reason,
        D(price),
        phase,
    )
    assert trade["exit_time"] is None


def test_invalid_open_cash_lot_and_end_sample(sample):
    data, signal = scenario(sample[0], [("10", "11", "9", "10"), ("9", "10", "8", "9")])
    assert simulate(data, [signal], Config())["decisions"][-1]["status"] == "CANCELLED_OPEN_INVALID"
    data = replace(
        data, bars=(data.bars[0], replace(data.bars[1], open=D("10"), high=D("11"), low=D("9")))
    )
    insufficient = simulate(data, [signal], Config(initial_cash=D("5"), lot_size=100))
    assert insufficient["decisions"][-1]["status"] == "INSUFFICIENT_CASH"
    last = simulate(replace(data, bars=data.bars[:1]), [signal], Config())
    assert last["pending_signal"] == signal
    assert last["summary"]["win_rate"] is None
    assert last["summary"]["entries"] == 0


def test_hold_signals_not_queued_time_exit_and_open_position(sample):
    data, signal = scenario(sample[0], [("10", "11", "9", "10")] * 5)
    second = {**signal, "signal_id": "IGNORED", "index": 1, "signal_time": data.bars[1].end}
    config = Config(max_hold=2, fee_rate=D("0"), slippage=D("0"))
    prefix = simulate(replace(data, bars=data.bars[:3]), [signal, second], config)
    assert prefix["open_position"] is not None and not prefix["trades"]
    full = simulate(data, [signal, second], config)
    assert full["trades"][0]["exit_index"] == 3
    assert full["trades"][0]["exit_reason"] == "TIME_EXIT"
    assert full["summary"]["entries"] == 1
    assert prefix["equity"] == full["equity"][:3]
    assert prefix["decisions"] == full["decisions"]


def test_gap_target_is_capped_not_optimistic(sample):
    data, signal = scenario(
        sample[0], [("10", "11", "9", "10"), ("10", "11", "9", "10"), ("20", "21", "7", "8")]
    )
    result = simulate(data, [signal], Config(fee_rate=D("0"), slippage=D("0")))
    assert result["trades"][0]["exit_price"] == D("14")
    assert result["trades"][0]["exit_reason"] == "TARGET_GAP_CAPPED"


def test_end_to_end_exact_exports_and_inert_html(sample, tmp_path):
    source, _ = sample
    result = run(source, Config())
    assert len(result["strategy"]["signals"]) == 3
    assert [t["exit_reason"] for t in result["trades"]] == ["TARGET", "GAP_STOP"]
    assert result["open_position"] is not None
    with localcontext(CONTEXT):
        assert D(result["summary"]["final_equity"]) == (
            D("100000")
            + D(result["summary"]["realized_pnl"])
            + D(result["open_position"]["unrealized_pnl_net_entry_fee"])
        )
    result["security"] = "</script><script>alert('x')</script>"
    destination = tmp_path / "report"
    write_report(result, destination)
    html = (destination / "report.html").read_text(encoding="utf-8")
    assert "</script><script>alert" not in html
    assert "\\u003c/script" in html
    assert json.loads((destination / "results.json").read_text(encoding="utf-8")) == result
    assert all(
        (destination / name).exists() for name in ("trades.csv", "signals.csv", "equity.csv")
    )
    with pytest.raises(FileExistsError):
        write_report(result, destination)


def test_invalid_config_and_decimal_context_independence(sample):
    for values in (
        {"allocation": D("1.01")},
        {"fee_rate": D("NaN")},
        {"slippage": D("1")},
        {"initial_cash": D("0")},
        {"lot_size": 0},
    ):
        with pytest.raises(ValueError):
            Config(**values)
    ordinary = run(sample[0], Config())
    with localcontext() as context:
        context.prec = 6
        assert run(sample[0], Config()) == ordinary
