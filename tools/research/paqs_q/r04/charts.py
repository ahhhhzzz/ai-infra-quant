"""Reproducible cutoff-limited matplotlib candles from frozen deterministic cases."""

import argparse
import importlib
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .integrations.local import stamp
from .study import write_new


def render(case_path: Path, output: Path) -> dict[str, Any]:
    case = json.loads(case_path.read_text(encoding="utf-8"))
    bars, rows = case["bars"], case["rows"]
    cutoff = stamp(case["cutoff"])
    assert 0 < len(bars) <= 40
    assert all(stamp(b["completed_at"]) <= cutoff for b in bars)
    assert not output.exists()
    plt = importlib.import_module("matplotlib.pyplot")
    patches = importlib.import_module("matplotlib.patches")
    fig, ax = plt.subplots(figsize=(14, 7), layout="constrained")
    lows, highs = [float(b["low"]) for b in bars], [float(b["high"]) for b in bars]
    span = max(highs) - min(lows)
    span = span if span else 1.0
    for i, b in enumerate(bars):
        opened, closed = float(b["open"]), float(b["close"])
        color = "#176e57" if closed >= opened else "#b94b49"
        ax.vlines(i, lows[i], highs[i], color=color, linewidth=1)
        ax.add_patch(
            patches.Rectangle(
                (i - 0.3, min(opened, closed)),
                0.6,
                max(abs(closed - opened), span * 0.001),
                facecolor=color,
                edgecolor=color,
            )
        )
        if i and rows[i]["segment"] != rows[i - 1]["segment"]:
            ax.axvline(i - 0.5, color="#9b8bb0", alpha=0.25, linestyle=":")
        if rows[i]["reason"] == "PRIOR_RAW_VETO":
            ax.scatter(i, highs[i] + span * 0.035, marker="x", color="#d07400", s=40)
        elif rows[i]["support_hash"] is None:
            ax.scatter(i, lows[i] - span * 0.035, marker="|", color="#666666", s=45)
    left = case["first_window_index"]
    center = case["selected"]["index"] - left
    ax.axvspan(
        max(-0.5, center - 2.5),
        min(len(bars) - 0.5, center + 1.5),
        color="#9fc2e2",
        alpha=0.22,
        label="selected four-price support (eligible or rejected)",
    )
    for event in case["events"]:
        i = event["index"] - left
        ax.scatter(
            i,
            float(event["price"]),
            marker="v" if event["kind"] == "HIGH" else "^",
            color="#193f93",
            s=65,
            zorder=5,
        )
    ax.annotate(
        "selected center\n" + case["selected"]["reason"],
        (center, highs[center]),
        xytext=(center, max(highs) + span * 0.18),
        ha="center",
        fontsize=8,
        arrowprops={"arrowstyle": "->", "color": "#202020"},
    )
    if center + 1 < len(bars):
        ax.scatter(
            center + 1,
            float(bars[center + 1]["close"]),
            marker="s",
            color="#773399",
            s=55,
            label="next bar reversal check (not same-bar confirmation)",
        )
    zone = ZoneInfo("America/New_York" if case["security"].startswith("US.") else "Asia/Hong_Kong")
    ticks = list(range(0, len(bars), max(1, len(bars) // 8)))
    ax.set_xticks(
        ticks,
        [stamp(bars[i]["start"]).astimezone(zone).strftime("%Y-%m-%d\n%H:%M") for i in ticks],
        fontsize=8,
    )
    ax.set_ylim(min(lows) - span * 0.12, max(highs) + span * 0.30)
    ax.set_xlim(-1, len(bars))
    ax.set_ylabel("Observed current-QFQ price; no return / performance claim")
    ax.grid(axis="y", alpha=0.18)
    ax.legend(loc="upper left", fontsize=8)
    fig.suptitle(
        f"{case['security']} {case['timeframe']} | {case['category']} | cutoff {case['cutoff']}\n"
        f"OBSERVATIONAL / {case['quality']} / availability UNKNOWN | "
        f"futu_opend_quote Capture | {zone.key}\n"
        "R04-CALENDAR-LOCAL-1 | blue: accepted extrema; orange x: veto; gray: support rejected",
        fontsize=10,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        fig.savefig(stream, format="png", dpi=120)
    plt.close(fig)
    return {
        "case": case_path.name,
        "image": output.name,
        "candles": len(bars),
        "cutoff": case["cutoff"],
        "future_candles": 0,
        "selected_reason": case["selected"]["reason"],
        "selected_center": case["selected"]["center"],
        "support": case["selected"].get("price_support"),
        "conversion": "Float solely for plotting; metrics remain Decimal",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("FRESH_EXCLUSIVE_PLOT_DIRECTORY_REQUIRED")
    cases = sorted(args.cases.glob("*.json"))
    assert len(cases) <= 20
    records = [render(path, args.output / (path.stem + ".png")) for path in cases]
    write_new(args.output / "manifest.json", records)
