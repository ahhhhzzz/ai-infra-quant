"""Explicitly build only the newly versioned Event manifests; never touch B0/A1."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ai_infra_quant.application.paqs_q_event_artifacts import build_manifest  # noqa: E402
from ai_infra_quant.core.domain.paqs_q.canonical import canonical  # noqa: E402
from ai_infra_quant.core.strategy.paqs_q.event_context import VERSION  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-artifacts", action="store_true", required=True)
    parser.parse_args()
    for name in ("context", "event"):
        target = ROOT / f"src/ai_infra_quant/resources/paqs_q/event-{name}-{VERSION}.json"
        if target.exists():
            raise FileExistsError(f"REFUSE_TO_REWRITE_VERSIONED_ARTIFACT: {target}")
        target.write_bytes(canonical(build_manifest(ROOT, name)) + b"\n")
        print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
