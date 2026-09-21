"""Independent preimage vectors, Decimal/UTC/Unicode and artifact integrity."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, localcontext
from zipfile import ZipFile

import pytest

from ai_infra_quant.application.paqs_q_artifacts import (
    FILES,
    artifact_path,
    build_manifest,
    content_hash,
    load_registry,
    verify_manifest,
)
from ai_infra_quant.core.domain.paqs_q.canonical import FrozenJSON, canonical, digest
from ai_infra_quant.core.domain.paqs_q.results import Config, make_result, structure_config
from tests.paqs_q.support import GOLDEN, ROOT, synthetic


def test_independent_fixed_preimage_vectors():
    vectors = json.loads((GOLDEN / "canonical.json").read_text(encoding="utf-8"))
    for vector in vectors:
        value = vector["value"]
        assert canonical(value).decode() == vector["canonical"]
        assert digest(vector["tag"], value) == vector["sha256"]
    raw = {
        "unicode": "汉😀/\n\t\b\f\r\u0001",
        "decimal": Decimal("-0.000"),
        "long": Decimal("12345678901234567890.123456789012345678"),
        "instant": datetime(2026, 1, 2, 3, 4, 5, 6, timezone(timedelta(hours=8))),
    }
    with localcontext() as ctx:
        ctx.prec = 2
        assert canonical(raw).decode() == vectors[0]["canonical"]
    assert canonical(Decimal("1.00")) == canonical(Decimal("1.0")) == b'"1"'
    assert canonical(datetime(1, 1, 1, tzinfo=UTC)) == b'"0001-01-01T00:00:00.000000Z"'
    assert structure_config(coefficient=Decimal("1.00")) == structure_config()


@pytest.mark.parametrize(
    "bad",
    [
        1.0,
        Decimal("NaN"),
        Decimal("Infinity"),
        "\ud800",
        {"非": 1},
        {1: 1},
        {"a"},
        datetime(2026, 1, 1),
    ],
)
def test_reject_noncanonical_values(bad):
    with pytest.raises(ValueError):
        canonical(bad)


def test_duplicate_json_and_config_schema_rejection():
    for encoded in (b'{"a":1,"a":2}', b'{"a":1.0}', b'{ "a":1}', b'{"a":1}\n'):
        with pytest.raises(ValueError):
            FrozenJSON(encoded)
    for config in (
        {"unexpected": 1},
        {"coefficient": 1.0},
        {"coefficient": Decimal("2")},
        {"M30": [True, 160, 200]},
    ):
        with pytest.raises(ValueError):
            structure_config(**config)
    with pytest.raises(ValueError):
        digest("bad\0tag", {})


def test_identity_changes_and_old_result_stability():
    registry = load_registry(ROOT)
    plugin = registry.structures[0]
    d, config = plugin.descriptor, structure_config()
    data = synthetic()
    old = registry.structure(data)
    old_bytes = old.canonical_bytes
    changed_config = Config("test-config-v1", FrozenJSON.of({"coefficient": Decimal("2")}))
    assert changed_config.config_hash != config.config_hash
    assert d.binding_hash(config) != d.binding_hash(changed_config)
    assert d.binding_hash(config) != replace(d, strategy_version="1.0.1").binding_hash(config)
    assert d.binding_hash(config) != replace(d, code_hash="0" * 64).binding_hash(config)
    assert data.input_hash != replace(data, snapshot_identity="1" * 64).input_hash
    assert old_bytes == old.canonical_bytes
    original = make_result(data, d, config, "UNAVAILABLE", ("FIXTURE",))
    for descriptor, cfg in (
        (d, changed_config),
        (replace(d, strategy_version="1.0.1"), config),
        (replace(d, code_hash="0" * 64), config),
    ):
        assert (
            make_result(data, descriptor, cfg, "UNAVAILABLE", ("FIXTURE",)).canonical_result_hash
            != original.canonical_result_hash
        )


def test_artifact_content_inventory_and_portable_encoding(tmp_path):
    manifest = build_manifest(ROOT, "b0")
    expected = verify_manifest(ROOT, manifest, "b0")
    # A packaged tree with wheel layout, independent of repository/OS path spelling.
    for name in FILES:
        dest = tmp_path / name.removeprefix("src/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        raw = artifact_path(ROOT, name).read_bytes().replace(b"\r\n", b"\n")
        dest.write_bytes(raw.replace(b"\n", b"\r\n"))
    assert verify_manifest(tmp_path, manifest, "b0", wheel=True) == expected
    assert content_hash(b"a\r\nb\r", "utf8-lf") == content_hash(b"a\nb\n", "utf8-lf")
    assert content_hash(b"a\r\n", "binary") != content_hash(b"a\n", "binary")
    changed = json.loads(json.dumps(manifest))
    changed["files"].pop()
    with pytest.raises(ValueError, match="INVENTORY"):
        verify_manifest(tmp_path, changed, "b0", wheel=True)
    target = tmp_path / FILES[-1].removeprefix("src/")
    target.write_bytes(target.read_bytes() + b"# mutation\n")
    with pytest.raises(ValueError, match="CONTENT"):
        verify_manifest(tmp_path, manifest, "b0", wheel=True)
    changed_manifest = build_manifest(tmp_path, "b0", wheel=True)
    assert verify_manifest(tmp_path, changed_manifest, "b0", wheel=True) != expected
    for name in ("/absolute", "src/ai_infra_quant/../bad", "C:/bad", "src\\ai_infra_quant\\bad"):
        with pytest.raises(ValueError, match="PATH"):
            artifact_path(tmp_path, name)
    with pytest.raises(ValueError, match="BOM"):
        content_hash(b"\xef\xbb\xbftext", "utf8-lf")


def test_closed_manifest_matches_checked_in_artifact():
    for arm in ("b0", "a1"):
        actual = json.loads((ROOT / f"src/ai_infra_quant/resources/paqs_q/{arm}.json").read_text())
        assert actual == build_manifest(ROOT, arm)


def test_load_packaged_zip_and_crlf_manifest(tmp_path):
    """A real portable source artifact ZIP, not a claimed built distribution wheel."""
    archive = tmp_path / "paqs-q-artifact.zip"
    paths = (
        *FILES,
        "src/ai_infra_quant/resources/paqs_q/b0.json",
        "src/ai_infra_quant/resources/paqs_q/a1.json",
    )
    with ZipFile(archive, "w") as stream:
        for name in paths:
            raw = (ROOT / name).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            stream.writestr(name.removeprefix("src/"), raw)
    package = tmp_path / "extracted"
    with ZipFile(archive) as stream:
        stream.extractall(package)
    loaded = load_registry(package, include_experimental=True, wheel=True)
    source = load_registry(ROOT, include_experimental=True)
    data = synthetic()
    assert loaded.structure(data).canonical_bytes == source.structure(data).canonical_bytes
