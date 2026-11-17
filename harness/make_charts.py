"""Renders the two README charts straight from the summaries (current gemkeeper vs the built-in options).

    python harness/make_charts.py --gk-run u --gk-version 0.2.1

results/benchmark.svg  facts still known after a reset (out of 30)
results/tokens.svg     tokens carried into the next session, with gemkeeper's saving in %
Baselines come from run f. Static SVGs, light/dark via prefers-color-scheme. Full numbers: RESULTS.md.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
RES = BENCH / "results"


def mean_of(run: str, cond: str, key: str) -> float:
    vals = [json.loads(p.read_text(encoding="utf-8"))["conditions"][cond][key]
            for p in sorted((RES / run).glob("rep*/summary.json"))
            if cond in json.loads(p.read_text(encoding="utf-8"))["conditions"]]
    return statistics.mean(vals)


STYLE = """<style>
  svg { --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#7a7974; --base:#8f8d88; --hi:#2a78d6; }
  @media (prefers-color-scheme: dark) {
    svg { --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#9a9990; --base:#8a8984; --hi:#3987e5; } }
  text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: var(--ink2); font-size: 14px; }
  .title { fill: var(--ink); font-size: 18px; font-weight: 600; }
  .sub, .src { fill: var(--muted); font-size: 12.5px; }
  .val { fill: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; }
  .pct { fill: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; }
  .hi-label { fill: var(--ink); font-weight: 600; }
  .base { fill: var(--base); } .hi { fill: var(--hi); }
</style>"""


def bar(x, y, w, h, r=4):
    r = min(r, w, h / 2)
    return (f"M{x:.1f},{y:.1f} H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
            f"V{y + h - r:.1f} Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} H{x:.1f} Z")


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chart(title: str, sub: str, rows: list[dict], vmax: float, alt: str, foot: str) -> str:
    """rows: label, value, text (value label), hi (bool), extra (optional right-hand text)."""
    W, LX, BX, BW, ROW, BH, top = 640, 24, 170, 300, 40, 18, 92
    H = top + ROW * len(rows) + 44
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(alt)}">',
         f"<title>{esc(alt)}</title>", STYLE,
         f'<rect width="{W}" height="{H}" rx="8" fill="var(--surface)"/>',
         f'<text class="title" x="{LX}" y="36">{esc(title)}</text>',
         f'<text class="sub" x="{LX}" y="58">{esc(sub)}</text>']
    for i, r in enumerate(rows):
        cy = top + i * ROW + ROW / 2
        p.append(f'<text class="{"hi-label" if r["hi"] else ""}" x="{BX - 14}" y="{cy + 5:.1f}" text-anchor="end">{esc(r["label"])}</text>')
        w = max(r["value"] / vmax * BW, 3) if r["value"] > 0 else 0
        if w:
            p.append(f'<path class="{"hi" if r["hi"] else "base"}" d="{bar(BX, cy - BH / 2, w, BH)}"/>')
        p.append(f'<text class="val" x="{BX + w + 10:.1f}" y="{cy + 5:.1f}">{esc(r["text"])}</text>')
        if r.get("extra"):
            p.append(f'<text class="pct" x="{BX + BW + 90}" y="{cy + 5:.1f}">{esc(r["extra"])}</text>')
    p.append(f'<text class="src" x="{LX}" y="{H - 16}">{esc(foot)}</text>')
    p.append("</svg>")
    return "\n".join(p) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gk-run", default="u")
    ap.add_argument("--gk-version", default="0.2.1")
    a = ap.parse_args()
    gk = ("u", "D_gemkeeper") if a.gk_run == "u" else (a.gk_run, "D_gemkeeper")

    foot = f"gemkeeper {a.gk_version} · Claude Sonnet · github.com/adamoelz/gemkeeper-bench"
    recall = {"No memory": mean_of("f", "A_none", "recall"), "Handoff summary": mean_of("f", "C_handoff", "recall"),
              "/compact": mean_of("f", "B_compact", "recall"), "gemkeeper": mean_of(*gk, "recall")}
    fmt = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")
    rows = [{"label": k, "value": v, "text": f"{fmt(v)} / 30", "hi": k == "gemkeeper"} for k, v in recall.items()]
    (RES / "benchmark.svg").write_text(chart(
        "Facts still known after a reset",
        "15 facts planted in a 20-turn Claude Code session, each scored 0–2 by a blind judge.",
        rows, 30, f"Facts still known after a reset (of 30): " + ", ".join(f"{k} {fmt(v)}" for k, v in recall.items()), foot),
        encoding="utf-8")

    base = mean_of("f", "A_none", "ctx_probe_start")       # system prompt + probe, nothing carried over
    carried = {"No reset": mean_of("f", "E_noreset", "ctx_probe_start") - base,
               "/compact": mean_of("f", "B_compact", "ctx_probe_start") - base,
               "Handoff summary": mean_of("f", "C_handoff", "ctx_probe_start") - base,
               "gemkeeper": mean_of(*gk, "ctx_probe_start") - base}
    g = carried["gemkeeper"]
    k = lambda v: f"{v / 1000:.1f}k" if v < 10000 else f"{v / 1000:.0f}k"
    rows = [{"label": n, "value": v, "text": k(v), "hi": n == "gemkeeper",
             "extra": None if n == "gemkeeper" else f"−{(1 - g / v) * 100:.0f}%"} for n, v in carried.items()]
    (RES / "tokens.svg").write_text(chart(
        "Tokens carried into the next session",
        "gemkeeper still knows all 15 planted facts, with fewer tokens than every alternative.",
        rows, max(carried.values()), "Tokens carried into the next session: " + ", ".join(f"{n} {k(v)}" for n, v in carried.items()), foot),
        encoding="utf-8")
    for n, v in carried.items():
        print(f"{n:16s} carried {v:8.0f}  recall {recall.get(n, '-')}")


if __name__ == "__main__":
    main()
