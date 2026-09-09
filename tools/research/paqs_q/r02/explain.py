"""Separate actual event expiry from tiny ATR-driven geometry changes; diagnostic only."""

import argparse
import json
from datetime import datetime
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

from ..engine import atr_series, labels, prepare
from ..fixtures import synthetic
from ..types import CONTEXT, Bar, Parameters, canonical
from ..zones import build_zones, ranges, select_zones
from . import engine
from .phase_a import case, load_original, write_new


def geometry(
    bars: tuple[Bar, ...], atrs: tuple[Decimal | None, ...], params: Parameters
) -> dict[str, Any]:
    """Counterfactual ATR input is diagnostic-only; do not expose as evaluate."""
    with localcontext(CONTEXT):
        ps, _ = engine.pivots(bars, atrs, params)
        active = tuple(p for p in ps if p.extreme >= params.warm and p.confirmed >= params.warm)
        zones = build_zones(active, params, {})
        _, selected = select_zones(zones, len(bars) - 1, bars[-1].close, params)
        boxes = ranges(bars, atrs, selected, params, {})
        return {
            "zones": [
                (
                    z.role,
                    z.lower,
                    z.upper,
                    tuple((p.extreme_ref, p.confirmed_ref) for p in z.touches),
                )
                for z in selected
            ],
            "range": (boxes[0].lower, boxes[0].upper) if boxes else None,
            "active_refs": [(p.kind, p.extreme_ref, p.confirmed_ref) for p in active],
            "labels": [(v.value, v.directional_eligible) for v in labels(ps, params.warm)],
        }


def run(data_dir: Path, comparison: Path, output: Path) -> None:
    data = load_original(data_dir)["D1"]
    params = Parameters.default("D1")
    out = []
    previous = json.loads((comparison / "US.AVGO.D1.material-causes.json").read_text())
    for record in previous:
        if record["algorithm"] != "H1":
            continue
        cutoff = datetime.fromisoformat(record["cutoff"])
        seq = prepare(data, cutoff)[-313:]
        old, left = seq[:-1], seq[1:-1]
        a, b = atr_series(old), atr_series(left)
        old_g = geometry(old, a, params)
        left_g = geometry(left, b, params)
        # Keep LEFT seed domain at local13 and shared OLD ATR values thereafter.
        held = tuple(None if i < 13 else a[i + 1] for i in range(len(left)))
        control = geometry(left, held, params)

        def same(x: dict[str, Any], y: dict[str, Any]) -> bool:
            return canonical((x["zones"], x["range"])) == canonical((y["zones"], y["range"]))

        cause = (
            "ATR_GEOMETRY_PROPAGATION"
            if same(old_g, control) and not same(old_g, left_g)
            else "UNRESOLVED_GEOMETRY"
        )
        out.append(
            {
                "cutoff": cutoff,
                "final_cause": cause,
                "previous_event_only_label": record["cause"],
                "diagnostic_only_hold_old_atr_restores_geometry": same(old_g, control),
                "OLD": old_g,
                "LEFT": left_g,
                "LEFT_WITH_OLD_ATR": control,
                "first_atr_common": {
                    "old": a[14],
                    "left": b[13],
                    "old_index": 14,
                    "left_index": 13,
                },
                "geometry_magnitudes": record["arm_evidence"]["geometry"],
                "event_diagnosis": case(data, cutoff, candidate=True)["cause"],
                "interpretation": (
                    "Exact range-bound comparison triggers inherited material flag even below "
                    ".5 ATR; not an unexplained large jump."
                ),
            }
        )
    write_new(output / "h1-geometry-causes.json", out)
    synthetic_data = synthetic("M30", 201, "path_lock")
    synth = case(synthetic_data, synthetic_data.bars[-1].completed_at, candidate=True)
    synth["label"] = "SYNTHETIC robustness rejection, not real-market evidence"
    write_new(output / "h1-rejection-counterexample.json", synth)
    print(
        canonical(
            {
                "geometry_causes": [r["final_cause"] for r in out],
                "synthetic_cause": synth["cause"],
                "synthetic_rediscovered": len(synth["rediscovered_still_eligible"]),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--comparison-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.data_dir, args.comparison_dir, args.output_dir)
