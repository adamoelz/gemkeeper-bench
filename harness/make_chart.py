"""Renders results/benchmark.svg (recall after reset per condition) straight from the summaries.

    python harness/make_chart.py --gk-run u --gk-label "gemkeeper 0.2.1"   # baselines + 0.1.0 from run f

Static SVG for READMEs: light/dark via prefers-color-scheme, values labelled on every bar
(no hover in an <img>), the full numbers live in RESULTS.md.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
RES = BENCH / "results"

# (label, run, condition, group); group: base | v010 | v020
ROWS = [
    ("No memory (/clear)", "f", "A_none", "base"),
    ("Handoff summary", "f", "C_handoff", "base"),
    ("/compact", "f", "B_compact", "base"),
    ("/compact twice", "f", "B2_compact2", "base"),
    ("gemkeeper 0.1.0", "f", "D_gemkeeper", "v010"),
    ("gemkeeper 0.1.0, two fresh sessions", "f", "D3_gemkeeper_2sess", "v010"),
    ("{gk}", "{run}", "D_gemkeeper", "v020"),
    ("{gk}, two fresh sessions", "{run}", "D3_gemkeeper_2sess", "v020"),
    ("/compact + {gk}", "{run}", "F_compact_gemkeeper", "v020"),
    ("No reset (upper bound)", "f", "E_noreset", "base"),
]
LEGEND = [("base", "built-in / no plugin"), ("v010", "gemkeeper 0.1.0"), ("v020", "{gk}")]


def collect(gk_run: str, gk: str):
    out = []
    for label, run, cond, group in ROWS:
        label, run = label.format(gk=gk), run.format(run=gk_run)
        reps = [json.loads(p.read_text(encoding="utf-8"))["conditions"].get(cond)
                for p in sorted((RES / run).glob("rep*/summary.json"))]
        reps = [r for r in reps if r]
        out.append({"label": label, "group": group, "n": len(reps),
                    "recall": statistics.mean(r["recall"] for r in reps),
                    "ctx": statistics.mean(r["ctx_probe_start"] for r in reps),
                    "traps": statistics.mean(r["violations"] for r in reps)})
    return out


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bar_path(x: float, y: float, w: float, h: float, r: float = 4) -> str:
    """Bar anchored square at the baseline (left), 4px rounded data end (right)."""
    if w <= 0:
        return ""
    r = min(r, w, h / 2)
    return (f"M{x:.1f},{y:.1f} H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
            f"V{y + h - r:.1f} Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} H{x:.1f} Z")


def render(rows, gk: str) -> str:
    W, LX, BX, BW = 800, 24, 300, 300          # label column, bar origin, bar width for 30 points
    CX = BX + BW + 64                          # context column
    ROW, BAR = 30, 14
    top = 112
    y_rows, y = [], top
    prev = None
    for r in rows:
        if prev is not None and r["group"] != prev:
            y += 10                            # group gap
        y_rows.append(y)
        y += ROW
        prev = r["group"]
    axis_y = y + 4
    H = axis_y + 64
    scale = BW / 30

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">',
         '<title id="t">Recall after a Claude Code session reset, gemkeeper-bench</title>',
         '<desc id="d">' + esc("; ".join(f"{r['label']}: {r['recall']:.1f} of 30 (n={r['n']})" for r in rows)) + "</desc>",
         """<style>
  svg { --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#7a7974; --grid:#e6e5e1;
        --base:#8f8d88; --v010:#eb6834; --v020:#2a78d6; }
  @media (prefers-color-scheme: dark) {
    svg { --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#9a9990; --grid:#33332f;
          --base:#8a8984; --v010:#d95926; --v020:#3987e5; } }
  text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: var(--ink2); font-size: 13px; }
  .title { fill: var(--ink); font-size: 17px; font-weight: 600; }
  .sub, .tick, .note, .colhead { fill: var(--muted); font-size: 12px; }
  .val { fill: var(--ink); font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; }
  .ctx { fill: var(--ink2); font-size: 12px; font-variant-numeric: tabular-nums; }
  .grid { stroke: var(--grid); stroke-width: 1; }
  .base { fill: var(--base); } .v010 { fill: var(--v010); } .v020 { fill: var(--v020); }
</style>""",
         f'<rect width="{W}" height="{H}" rx="8" fill="var(--surface)"/>',
         f'<text class="title" x="{LX}" y="34">Recall after a session reset</text>',
         f'<text class="sub" x="{LX}" y="54">15 facts planted in a 20-turn Claude Code session (rules, decisions + why, dead ends, gotchas).</text>',
         f'<text class="sub" x="{LX}" y="70">Score out of 30, blind LLM judge, mean over n repetitions.</text>']
    lx = LX
    for key, text in LEGEND:                     # legend row
        text = text.format(gk=gk)
        p.append(f'<rect class="{key}" x="{lx}" y="84" width="12" height="12" rx="3"/>')
        p.append(f'<text x="{lx + 18}" y="94.5">{esc(text)}</text>')
        lx += 18 + len(text) * 7.1 + 22
    p.append(f'<text class="colhead" x="{CX}" y="{top - 8}">context after reset</text>')
    for v in (0, 10, 20, 30):                    # recessive hairline grid + ticks
        gx = BX + v * scale
        p.append(f'<line class="grid" x1="{gx:.1f}" y1="{top - 4}" x2="{gx:.1f}" y2="{axis_y}"/>')
        p.append(f'<text class="tick" x="{gx:.1f}" y="{axis_y + 16}" text-anchor="middle">{v}</text>')
    for r, ry in zip(rows, y_rows):
        cy = ry + ROW / 2
        n = f" (n={r['n']})"
        p.append(f'<text x="{BX - 12}" y="{cy + 4.5:.1f}" text-anchor="end">{esc(r["label"])}<tspan class="note">{n}</tspan></text>')
        w = r["recall"] * scale
        if w > 0:
            p.append(f'<path class="{r["group"]}" d="{bar_path(BX, cy - BAR / 2, w, BAR)}"/>')
        val = f"{r['recall']:.1f}".rstrip("0").rstrip(".") if r["recall"] != int(r["recall"]) else f"{int(r['recall'])}"
        p.append(f'<text class="val" x="{BX + w + 8:.1f}" y="{cy + 4.5:.1f}">{val}</text>')
        p.append(f'<text class="ctx" x="{CX}" y="{cy + 4.5:.1f}">{r["ctx"] / 1000:.0f}k tokens</text>')
    traps_a = next(r["traps"] for r in rows if r["label"].startswith("No memory"))
    p.append(f'<text class="note" x="{LX}" y="{axis_y + 40}">Behaviour traps: without memory the model fell into {traps_a:.1f} of 3 on average; '
             'every other condition into 0.</text>')
    p.append(f'<text class="note" x="{LX}" y="{axis_y + 56}">Sonnet via claude -p · one synthetic scenario · github.com/adamoelz/gemkeeper-bench</text>')
    p.append("</svg>")
    return "\n".join(p) + "\n"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--gk-run", default="u")
    ap.add_argument("--gk-label", default="gemkeeper 0.2.1")
    a = ap.parse_args()
    out = RES / "benchmark.svg"
    out.write_text(render(collect(a.gk_run, a.gk_label), a.gk_label), encoding="utf-8")
    print(out)
