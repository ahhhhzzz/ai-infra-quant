"""F01: public evaluator and JSON inputs cannot turn bad bar quality into clean facts."""

import json
import subprocess
import sys
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from tools.research.paqs_q.engine import evaluate, prepare
from tools.research.paqs_q.fixtures import synthetic
from tools.research.paqs_q.io import read_dataset, write_dataset
from tools.research.paqs_q.types import Timeframe


@pytest.mark.parametrize("tf", ["D1", "W1", "M30"])
@pytest.mark.parametrize("coverage", ["INVALID", "BROKEN", "complete", "", None, 1, []])
def test_invalid_coverage_fails_public_and_wire(
    tf: Timeframe, coverage: Any, tmp_path: Path
) -> None:
    data = synthetic(tf, pattern="bull")
    bad = replace(data, bars=(*data.bars[:-1], replace(data.bars[-1], coverage=coverage)))
    path = tmp_path / "bad.json"
    write_dataset(path, bad)
    for item in (bad, read_dataset(path)):
        result = evaluate(item, data.bars[-1].completed_at).document()["decision"]
        assert result["input_status"] == "INVALID"
        assert result["regime"] == "UNCERTAIN"
        assert result["reasons"] == ["BAR_COVERAGE_INVALID"]
        assert result["active_pivots"] == [] and result["zones"] == []


@pytest.mark.parametrize(
    "aggregate,coverage,expected",
    [
        ("COMPLETE", "PARTIAL", "INVALID"),
        ("COMPLETE", "UNKNOWN", "INVALID"),
        ("PARTIAL", "UNKNOWN", "INVALID"),
        ("PARTIAL", "PARTIAL", "PARTIAL"),
        ("UNKNOWN", "PARTIAL", "UNKNOWN"),
        ("UNKNOWN", "UNKNOWN", "UNKNOWN"),
        ("PARTIAL", "COMPLETE", "PARTIAL"),
        ("UNKNOWN", "COMPLETE", "UNKNOWN"),
    ],
)
def test_aggregate_quality_never_upgrades(
    aggregate: str, coverage: str, expected: str, tmp_path: Path
) -> None:
    data = synthetic(pattern="bull")
    changed = replace(
        data, quality=aggregate, bars=(*data.bars[:-1], replace(data.bars[-1], coverage=coverage))
    )
    path = tmp_path / "quality.json"
    write_dataset(path, changed)
    for item in (changed, read_dataset(path)):
        result = evaluate(item, data.bars[-1].completed_at).document()["decision"]
        assert result["input_status"] == expected
        if expected == "INVALID":
            assert result["regime"] == "UNCERTAIN"
            assert result["reasons"] == ["AGGREGATE_BAR_QUALITY_CONFLICT"]


def test_cli_cannot_publish_complete_bull_from_invalid_coverage(tmp_path: Path) -> None:
    data = synthetic(pattern="bull")
    path, output = tmp_path / "input.json", tmp_path / "output.json"
    write_dataset(path, data)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["dataset"]["bars"][-1]["coverage"] = "INVALID"
    path.write_text(json.dumps(raw), encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.research.paqs_q",
            "analyze",
            str(path),
            "--cutoff",
            data.bars[-1].completed_at.isoformat(),
            "--output",
            str(output),
        ],
        check=True,
    )
    decision = json.loads(output.read_text(encoding="utf-8"))["decision"]
    assert (decision["input_status"], decision["regime"]) == ("INVALID", "UNCERTAIN")


@pytest.mark.parametrize("tf", ["D1", "W1", "M30"])
def test_future_unavailable_and_unfinished_bad_quality_cannot_leak(tf: Timeframe) -> None:
    data = synthetic(tf, pattern="bull")
    cutoff = data.bars[-1].completed_at
    unavailable = replace(
        data.bars[-4], coverage="INVALID", available_at=cutoff + timedelta(days=1)
    )
    unfinished = replace(data.bars[-3], coverage="INVALID", completed=False)
    future = replace(data.bars[-1], coverage="INVALID", completed_at=cutoff + timedelta(days=1))
    bad = replace(data, bars=(*data.bars, unavailable, unfinished, future))
    assert evaluate(bad, cutoff).decision_json == evaluate(data, cutoff).decision_json


@pytest.mark.parametrize("tf", ["W1", "M30"])
def test_derived_partial_revision_cannot_resurrect_older_complete_bar(tf: Timeframe) -> None:
    data = replace(synthetic(tf), quality="PARTIAL")
    revision = replace(data.bars[-4], coverage="PARTIAL", available_at=data.bars[-1].completed_at)
    changed = replace(data, bars=(*data.bars, revision))
    result = evaluate(changed, data.bars[-1].completed_at).document()["decision"]
    assert result["input_status"] == "PARTIAL"
    assert data.bars[-4].ref not in {p["extreme_ref"] for p in result["active_pivots"]}
    # The actual observation is absent from the calculation, not merely absent as a pivot.
    assert len(result["observations"]) == result["window"]["count"]
    assert data.bars[-4].start not in {
        b.start for b in prepare(changed, data.bars[-1].completed_at)
    }
