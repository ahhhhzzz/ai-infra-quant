"""Static local matplotlib rendering; conversion to floats occurs only for drawing."""

import argparse
from importlib import import_module
from pathlib import Path
from typing import Any

from ..r04.study import write_new
from .study import read


def render(case: dict[str, Any], path: Path) -> None:
    if path.exists():
        raise FileExistsError(path)
    plt = import_module("matplotlib.pyplot")
    patches = import_module("matplotlib.patches")
    bars = case["bars"]
    assert bars and all(b["completed_at"] <= case["cutoff"] for b in bars)
    fig, ax = plt.subplots(figsize=(16, 8))
    first = case["first_window_index"]
    for i, b in enumerate(bars):
        o, h, low, close = (float(b[k]) for k in ("open", "high", "low", "close"))
        color = "#258476" if close >= o else "#c85a52"
        ax.plot([i, i], [low, h], color=color, lw=1)
        ax.add_patch(
            patches.Rectangle(
                (i - 0.28, min(o, close)), 0.56, max(abs(close - o), (h - low) * 0.015), color=color
            )
        )
    bkeys = {e["key"] for e in case["events_B0"]}
    for event in case["events_A1"]:
        i = event["index"] - first
        shared = event["key"] in bkeys
        color = "#254fa5" if shared else "#d67500"
        ax.scatter(
            i,
            float(event["price"]),
            marker="^" if event["kind"] == "LOW" else "v",
            c=color,
            s=95,
            zorder=5,
        )
        if i + 1 < len(bars):
            ax.scatter(
                i + 1,
                float(bars[i + 1]["close"]),
                marker="s",
                facecolors="none",
                edgecolors=color,
                s=65,
            )
            ax.plot(
                [i, i + 1],
                [float(event["price"]), float(bars[i + 1]["close"])],
                ls=":",
                color=color,
            )
    rows = case["census_B0"]
    for i, r in enumerate(rows):
        if i and r["segment"] != rows[i - 1]["segment"]:
            ax.axvline(i - 0.5, ls="--", color="gray", alpha=0.5)
        if r["raw"] is not None and any(r["raw"]):
            ax.text(
                i,
                float(bars[i]["high"]),
                "D/U" if all(r["raw"]) else ("D" if r["raw"][0] else "U"),
                fontsize=8,
                va="bottom",
            )
        if r["support_hash"] is None:
            ax.scatter(i, float(bars[i]["low"]), marker="x", color="gray", s=30)
    for j in range(
        max(0, case["focus_first"] - 2 - first), min(len(bars), case["focus_last"] + 2 - first)
    ):
        ax.axvspan(j - 0.45, j + 0.45, color="#c2d9ed", alpha=0.15)
    ticks = list(range(0, len(bars), max(1, len(bars) // 12)))
    ax.set_xticks(
        ticks, [bars[i]["start"][:16] for i in ticks], rotation=35, ha="right", fontsize=8
    )
    ax.set_title(
        f"{case['security']} {case['timeframe']} | {', '.join(case['categories'])}\n"
        f"Cutoff {case['cutoff']} | OBSERVATIONAL / {case['quality']} / {bars[0]['adjustment']}"
    )
    ax.set_ylabel("Observed price (exact Decimal in case JSON)")
    ax.set_xlabel("UTC observation start; ordinal spacing, no missing-candle fill")
    ax.grid(alpha=0.15)
    fig.text(
        0.05,
        0.025,
        "Blue: shared B0/A1; orange: A1-only. Triangle: extreme; "
        "hollow square: next-bar confirmation.\n"
        "D/U: raw predicate. Shading: quartet span; dashed: segment boundary; "
        "gray x: unavailable support.\n"
        "Availability retained in case JSON. TRIPLE_ONLY is a non-event diagnostic. "
        "No candles after cutoff.",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        fig.savefig(stream, format="png", dpi=130)
    plt.close(fig)


def run(cases: Path, output: Path) -> None:
    from hashlib import sha256

    paths = sorted(p.as_posix() for p in cases.glob("*.json"))
    assert 0 < len(paths) <= 15
    manifest = []
    for name in paths:
        source = Path(name)
        target = output / (source.stem + ".png")
        render(read(source), target)
        manifest.append(
            {
                "case": source.as_posix(),
                "chart": target.as_posix(),
                "case_sha256": sha256(source.read_bytes()).hexdigest(),
                "chart_sha256": sha256(target.read_bytes()).hexdigest(),
            }
        )
    write_new(output / "manifest.json", manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.cases, args.output)
