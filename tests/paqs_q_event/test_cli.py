import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ai_infra_quant.core.domain.paqs_q.canonical import canonical
from tools.research.event_engine.__main__ import run
from tools.research.event_engine.data import decode_input, demo_input, read_input

ROOT = Path(__file__).resolve().parents[2]


def test_cli_offline_exports_exact_payload_and_protects_outputs(tmp_path):
    output = tmp_path / "event-demo"
    result = subprocess.run(
        [sys.executable, "-m", "tools.research.event_engine", "--demo", "--output", str(output)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(ROOT)},
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((output / "summary.json").read_bytes())
    events = json.loads((output / "events.json").read_bytes())
    assert summary["event_hash"] == events["canonical_result_hash"]
    html = (output / "report.html").read_text(encoding="utf-8")
    embedded = html.split('<script id="payload" type="application/json">', 1)[1].split(
        "</script>", 1
    )[0]
    payload = json.loads(embedded)
    assert payload["events"] == events and payload["summary"] == summary
    assert "https://" not in html and "http://" not in html
    assert decode_input(json.loads((output / "input.json").read_bytes())) == demo_input()
    with pytest.raises(ValueError, match="OUTPUT_MUST_BE_NEW_DIRECTORY"):
        run(demo_input(), output)


def test_canonical_input_mode_is_explicit_and_version_is_verified(tmp_path):
    data = demo_input()
    path = tmp_path / "input.json"
    path.write_bytes(canonical(data.payload()))
    assert read_input(path, None, "AS_OF") == data
    with pytest.raises(ValueError, match="MODE_MUST_MATCH"):
        read_input(path, None, "OBSERVATIONAL")
    raw = json.loads(path.read_bytes())
    raw["bars"][0]["close"] = "100.01"
    with pytest.raises(ValueError, match="VERSION_MISMATCH"):
        decode_input(raw)


def test_report_escapes_input_controlled_script_text(tmp_path):
    from dataclasses import replace

    from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON

    data = replace(
        demo_input(), provenance=FrozenJSON.of({"note": "</script><script>alert(1)</script>"})
    )
    run(data, tmp_path / "escaped")
    html = (tmp_path / "escaped" / "report.html").read_text(encoding="utf-8")
    assert "</script><script>alert(1)" not in html
    assert "\\u003c/script>" in html


def test_existing_qstr_capture_adapter_preserves_halfday_and_unknown_history(tmp_path):
    from dataclasses import asdict, replace
    from datetime import datetime

    from ai_infra_quant.core.strategy.paqs_q.event_calendar import Insufficient, qualify
    from tools.research.paqs_q.io import write_dataset
    from tools.research.paqs_q.types import Bar, Dataset

    source = demo_input()
    first = source.bars[0]
    early = first.end.replace(hour=18)
    bar = replace(
        first, end=early, completed_at=early, available_at=None, adjustment="PROVIDER_QFQ_CURRENT"
    )
    data = Dataset(source.security, "D1", source.market_timezone, (Bar(**asdict(bar)),), "PARTIAL")
    prices = tmp_path / "prices.json"
    write_dataset(prices, data)
    calendar = tmp_path / "calendar.json"
    calendar.write_text(
        json.dumps(
            {
                "calendar": [
                    {
                        "market_date": "2025-01-06",
                        "market": "US",
                        "market_timezone": "America/New_York",
                        "day_type": "MORNING_ONLY",
                        "provider": "SYNTHETIC_ADAPTER_TEST",
                        "retrieved_at": "2025-01-08T00:00:00Z",
                        "session_segments": [{"start": "09:30:00", "end": "13:00:00"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    converted = read_input(prices, calendar, "OBSERVATIONAL")
    assert converted.bars == (bar,)
    assert converted.calendar[0].kind == "OPEN"
    assert converted.calendar[0].segments[0][1] == early
    assert converted.calendar[0].available_at is None
    assert converted.calendar[0].retrieved_at == datetime.fromisoformat("2025-01-08T00:00:00Z")
    assert not converted.calendar[0].complete
    assert qualify(converted)
    assert converted.provenance.document()["input_file_sha256"]
    with pytest.raises(Insufficient):
        qualify(read_input(prices, calendar, "AS_OF"))
