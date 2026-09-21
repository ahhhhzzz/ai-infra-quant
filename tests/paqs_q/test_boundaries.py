"""Closed imports, deterministic execution and calendar policy boundary tests."""

import ast
import builtins
import socket
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from ai_infra_quant.application.paqs_q_artifacts import FILES, load_registry
from ai_infra_quant.core.domain.paqs_q.inputs import Fact, bounded_prefix
from ai_infra_quant.core.strategy.paqs_q.calendar import slot, support
from tests.paqs_q.support import GOLDEN, ROOT, decode, read_golden, synthetic


def test_import_closure_and_pure_core_boundary():
    forbidden = {
        "os",
        "socket",
        "urllib",
        "httpx",
        "requests",
        "random",
        "time",
        "pathlib",
        "subprocess",
        "inspect",
        "importlib",
        "sqlite3",
        "sqlalchemy",
        "openai",
        "futu",
    }
    for logical in FILES:
        tree = ast.parse((ROOT / logical).read_text(encoding="utf-8"))
        module = logical.removeprefix("src/").removesuffix(".py").replace("/", ".")
        package = module.rsplit(".", 1)[0]
        pure = "/core/" in logical and ("/paqs_q/" in logical or logical.endswith("/paqs_q.py"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports = [x.name for x in node.names]
            elif isinstance(node, ast.ImportFrom):
                prefix = (
                    ".".join(package.split(".")[: len(package.split(".")) - node.level + 1])
                    if node.level
                    else ""
                )
                imports = [".".join(filter(None, (prefix, node.module)))]
            else:
                imports = []
            for name in imports:
                assert not name.startswith("tools.research")
                if pure:
                    assert name.split(".")[0] not in forbidden, (logical, name)
                    assert not any(
                        s in name
                        for s in (".database", ".integrations", ".backend", ".application")
                    )
                if name.startswith("ai_infra_quant"):
                    candidate = "src/" + name.replace(".", "/") + ".py"
                    assert candidate in FILES or candidate[:-3] + "/__init__.py" in FILES, (
                        logical,
                        candidate,
                    )
            if pure and isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert name not in {
                    "open",
                    "eval",
                    "exec",
                    "__import__",
                    "getenv",
                    "now",
                    "today",
                    "utcnow",
                }


def test_evaluation_has_no_file_network_or_environment_dependency(monkeypatch):
    registry = load_registry(ROOT, include_experimental=True)
    data = synthetic()
    expected = registry.structure(data).canonical_bytes

    def forbidden(*args, **kwargs):
        raise AssertionError("EXTERNAL_ACCESS")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setenv("PAQS_Q_UNTRUSTED", "ignored")
    assert registry.structure(data).canonical_bytes == expected
    assert (
        registry.structure(data, "paqs-q-structure-a1", "0.1.0", allow_experimental=True).status
        == "AVAILABLE"
    )


def test_calendar_support_hk_lunch_overnight_missing_and_dst():
    base = synthetic().bars[0]
    hk = ZoneInfo("Asia/Hong_Kong")

    def instant(hour: int, minute: int = 0) -> datetime:
        return datetime(2026, 1, 5, hour, minute, tzinfo=hk).astimezone(UTC)

    fact = Fact(
        date(2026, 1, 5),
        "HK",
        "Asia/Hong_Kong",
        "OPEN",
        ((instant(9, 30), instant(12)), (instant(13), instant(16))),
        "SYNTHETIC",
        instant(8),
        instant(8),
        True,
    )
    days = {fact.day: fact}
    morning = replace(
        base,
        security="HK.00001",
        start=instant(11, 30),
        end=instant(12),
        completed_at=instant(12),
        available_at=instant(12),
    )
    afternoon = replace(
        morning,
        start=instant(13),
        end=instant(13, 30),
        completed_at=instant(13, 30),
        available_at=instant(13, 30),
    )
    assert slot(morning, days, "AS_OF")[1].endswith(":0")
    assert slot(afternoon, days, "AS_OF")[1].endswith(":1")
    with pytest.raises(ValueError, match="PROHIBITED_SEGMENT_BOUNDARY"):
        support((morning, afternoon), days, "AS_OF")
    missing = replace(
        morning,
        start=instant(10, 30),
        end=instant(11),
        completed_at=instant(11),
        available_at=instant(11),
    )
    with pytest.raises(ValueError, match="MISSING_EXPECTED_BUCKET"):
        support((missing, morning), days, "AS_OF")
    early = replace(fact, segments=((instant(9, 30), instant(12)),))
    with pytest.raises(ValueError, match="OUTSIDE_REGULAR_SEGMENT"):
        slot(afternoon, {early.day: early}, "AS_OF")
    us = ZoneInfo("America/New_York")
    assert datetime(2026, 3, 6, 9, 30, tzinfo=us).astimezone(UTC).hour == 14
    assert datetime(2026, 3, 9, 9, 30, tzinfo=us).astimezone(UTC).hour == 13
    data = synthetic()
    with pytest.raises(ValueError, match="PROHIBITED_SEGMENT_BOUNDARY"):
        support(data.bars[12:14], {f.day: f for f in data.calendar}, "AS_OF")


def test_calendar_unknown_is_insufficient_not_empty_success_and_w1_geometry():
    data = synthetic()
    registry = load_registry(ROOT)
    for facts in ((), tuple(replace(f, available_at=None) for f in data.calendar)):
        result = registry.structure(replace(data, calendar=facts))
        assert result.status == "INSUFFICIENT"
        assert result.document()["evidence"] is None
    weekly = decode(
        next(
            v["input"] for v in read_golden()["vectors"] if v["name"].startswith("W1.OBSERVATIONAL")
        )
    )
    assert any(b.end > weekly.as_of >= b.completed_at for b in weekly.bars)
    assert registry.structure(weekly).status == "AVAILABLE"


def test_hash_seed_independence_subprocess():
    import os

    outputs = []
    for seed in ("1", "619"):
        env = dict(
            os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT)
        )
        script = (
            "from pathlib import Path; "
            "from ai_infra_quant.application.paqs_q_artifacts import load_registry; "
            "from tests.paqs_q.support import synthetic; "
            "print(load_registry(Path('.')).structure(synthetic()).canonical_result_hash)"
        )
        outputs.append(subprocess.check_output([sys.executable, "-c", script], cwd=ROOT, env=env))
    assert outputs[0] == outputs[1]


def test_golden_source_receipt_and_pre_port_commit():
    import hashlib

    golden = read_golden()
    assert golden["cases_verified"] == 14 and len(golden["vectors"]) == 12
    # Committed expected data is fixed independently of the port under test.
    assert (
        hashlib.sha256((GOLDEN / "r05.json").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        == "a441b129f6ea4c3cb9397e1093eda81f768cce08cf866978b95d022ab4dbc6ba"
    )
    for path, expected in golden["source_sha256"].items():
        raw = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(raw).hexdigest() == expected


def test_prefix_preparation_excludes_future_revisions_and_prices():
    data = synthetic()
    baseline = bounded_prefix(data, data.as_of)
    future = replace(data.bars[0], available_at=data.as_of + timedelta(days=1))
    newbar = replace(
        data.bars[-1],
        start=data.as_of,
        end=data.as_of + timedelta(minutes=30),
        completed_at=data.as_of + timedelta(minutes=30),
        available_at=data.as_of + timedelta(minutes=30),
    )
    calendar = replace(
        data.calendar[0], available_at=data.as_of + timedelta(days=1), complete=False
    )
    extended = replace(data, bars=(*data.bars, future, newbar), calendar=(*data.calendar, calendar))
    prefix = bounded_prefix(extended, data.as_of)
    assert prefix == baseline
    registry = load_registry(ROOT)
    assert (
        registry.structure(prefix).canonical_bytes == registry.structure(baseline).canonical_bytes
    )
