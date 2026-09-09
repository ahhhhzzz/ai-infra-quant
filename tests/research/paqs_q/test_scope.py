"""No product wiring; universe denominators survive absent research inputs."""

import ast
import json
from pathlib import Path

from tools.research.paqs_q.study import coverage
from tools.research.paqs_q.verify import allowed


def test_fixed_universe_coverage_denominators_and_unavailable_members() -> None:
    manifest = json.loads(Path("docs/evidence/TASK_006B_Q/universe.json").read_text())
    members = manifest["members"]
    assert len(members) == len({m["security"] for m in members}) == 40
    assert sum(m["market"] == "US" for m in members) == 24
    assert sum(m["market"] == "HK" for m in members) == 16
    assert {"US.AVGO", "US.VRT", "US.NVDA", "HK.09698", "HK.00700"} <= {
        m["security"] for m in members
    }
    result = coverage(members, [{"security": "US.AVGO", "timeframe": "D1", "cutoffs": 100}])
    assert result["real_market_gate"] == "INCOMPLETE"
    d1 = next(r for r in result["denominators"] if r["timeframe"] == "D1" and r["market"] == "ALL")
    assert (d1["valid_100"], d1["unavailable"], d1["target_cutoffs"]) == (1, 39, 4000)


def test_product_never_imports_prototype_and_engine_is_independent() -> None:
    for path in Path("src").rglob("*.py"):
        assert "tools.research.paqs_q" not in path.read_text(encoding="utf-8")
    for filename in ("engine.py", "zones.py", "types.py"):
        tree = ast.parse((Path("tools/research/paqs_q") / filename).read_text(encoding="utf-8"))
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        assert all(not name or not name.startswith("ai_infra_quant") for name in imports)
    for forbidden in ("src/new.py", "tests/unit/new.py", "pyproject.toml", "docs/ROADMAP.md"):
        assert not allowed(forbidden)
    assert allowed("tools/research/paqs_q/engine.py")
