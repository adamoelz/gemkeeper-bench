"""Renders results/tokens.svg: tokens carried into the next session vs facts still known, per method.

    python harness/make_token_chart.py --gk-run u --gk-label "gemkeeper 0.2.1"

"Carried" = context of the first request after the reset minus the no-memory baseline (A_none: system
prompt + the probe itself), so it is what each method adds to every request of the next session.
Baselines come from run f. Static SVG for READMEs, light/dark via prefers-color-scheme.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
RES = BENCH / "results"


def cond(run: str, c: str) -> list[dict]:
    out = []
    for p in sorted((RES / run).glob("rep*/summary.json")):
        v = json.loads(p.read_text(encoding="utf-8"))["conditions"].get(c)
        if v:
            out.append(v)
    return out


def mean(rows, key):
    return statistics.mean(r[key] for r in rows)


def collect(gk_run: str, gk_label: str):
    base = mean(cond("f", "A_none"), "ctx_probe_start")
    spec = [("Keep the whole session (no reset)", "f", "E_noreset", False),
            ("/compact", "f", "B_compact", False),
            ("/compact twice", "f", "B2_compact2", False),
            ("Handoff summary", "f", "C_handoff", False),
            (gk_label, gk_run, "D_gemkeeper", True),
            ("No memory (/clear)", "f", "A_none", False)]
    rows = []
    for label, run, c, hi in spec:
        r = cond(run, c)
        rows.append({"label": label, "hi": hi, "n": len(r), "recall": mean(r, "recall"),
                     "carried": max(0.0, mean(r, "ctx_probe_start") - base)})
    gk = next(r for r in rows if r["hi"])
    for r in rows:
        r["saving"] = (1 - gk["carried"] / r["carried"]) if not r["hi"] and r["carried"] > gk["carried"] else None
    return rows


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bar_path(x, y, w, h, r=4):
    if w <= 0:
        return ""
    r = min(r, w, h / 2)
    return (f"M{x:.1f},{y:.1f} H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
            f"V{y + h - r:.1f} Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} H{x:.1f} Z")


def k(v: float) -> str:
    return f"{v / 1000:.1f}k" if v < 10000 else f"{v / 1000:.0f}k"


def render(rows, gk_label: str) -> str:
    W, LX, BX, BW = 840, 24, 262, 300
    FX, SX = BX + BW + 84, BX + BW + 178      # columns: facts known, gemkeeper tokens vs. this row
    ROW, BAR, top = 34, 16, 116
    vmax = max(r["carried"] for r in rows)
    H = top + ROW * len(rows) + 56
    gk = next(r for r in rows if r["hi"])
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">',
         f'<title id="t">Tokens carried into the next session vs facts still known</title>',
         '<desc id="d">' + esc("; ".join(f"{r['label']}: {k(r['carried'])} tokens carried, {r['recall']:.1f} of 30"
                                     for r in rows)) + "</desc>",
         """<style>
  svg { --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#7a7974; --rule:#e6e5e1;
        --base:#8f8d88; --hi:#2a78d6; }
  @media (prefers-color-scheme: dark) {
    svg { --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#9a9990; --rule:#33332f;
          --base:#8a8984; --hi:#3987e5; } }
  text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: var(--ink2); font-size: 13px; }
  .title { fill: var(--ink); font-size: 17px; font-weight: 600; }
  .sub, .colhead, .note { fill: var(--muted); font-size: 12px; }
  .val { fill: var(--ink); font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; }
  .num { fill: var(--ink2); font-size: 13px; font-variant-numeric: tabular-nums; }
  .hi-label { fill: var(--ink); font-weight: 600; }
  .rule { stroke: var(--rule); stroke-width: 1; }
  .base { fill: var(--base); } .hi { fill: var(--hi); }
</style>""",
         f'<rect width="{W}" height="{H}" rx="8" fill="var(--surface)"/>',
         f'<text class="title" x="{LX}" y="34">What the next session starts with</text>',
         f'<text class="sub" x="{LX}" y="54">Tokens carried over after a reset, and how many of 15 planted facts (rules, decisions + why,</text>',
         f'<text class="sub" x="{LX}" y="70">dead ends, gotchas) the next session still knows. Mean of 2–3 runs, blind LLM judge.</text>',
         f'<text class="colhead" x="{BX}" y="{top - 12}">tokens carried into the next session</text>',
         f'<text class="colhead" x="{FX}" y="{top - 12}">facts known</text>',
         f'<text class="colhead" x="{SX}" y="{top - 12}">{esc(gk_label.split(" ")[0])} tokens</text>']
    for i, r in enumerate(rows):
        y = top + i * ROW
        cy = y + ROW / 2
        if i:
            p.append(f'<line class="rule" x1="{LX}" y1="{y:.1f}" x2="{W - LX}" y2="{y:.1f}"/>')
        cls = "hi-label" if r["hi"] else ""
        p.append(f'<text class="{cls}" x="{BX - 12}" y="{cy + 4.5:.1f}" text-anchor="end">{esc(r["label"])}</text>')
        w = r["carried"] / vmax * BW
        if r["carried"] > 0:
            w = max(w, 3)                        # keep tiny bars visible
            p.append(f'<path class="{"hi" if r["hi"] else "base"}" d="{bar_path(BX, cy - BAR / 2, w, BAR)}"/>')
        p.append(f'<text class="val" x="{BX + w + 8:.1f}" y="{cy + 4.5:.1f}">{k(r["carried"]) if r["carried"] else "0"}</text>')
        rec = f"{r['recall']:.1f}".rstrip("0").rstrip(".")
        p.append(f'<text class="{"val" if r["hi"] else "num"}" x="{FX}" y="{cy + 4.5:.1f}">{rec} / 30</text>')
        if r["saving"] is not None:
            p.append(f'<text class="num" x="{SX}" y="{cy + 4.5:.1f}">−{r["saving"] * 100:.0f}%</text>')
    yb = top + ROW * len(rows)
    p.append(f'<text class="note" x="{LX}" y="{yb + 26}">Carried = context of the first request after the reset minus a session with no memory. '
             f'{esc(gk_label)}: n={gk["n"]}, baselines n=2.</text>')
    p.append(f'<text class="note" x="{LX}" y="{yb + 42}">Sonnet via claude -p · one synthetic scenario · github.com/adamoelz/gemkeeper-bench</text>')
    p.append("</svg>")
    return "\n".join(p) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gk-run", default="u")
    ap.add_argument("--gk-label", default="gemkeeper 0.2.1")
    a = ap.parse_args()
    rows = collect(a.gk_run, a.gk_label)
    out = RES / "tokens.svg"
    out.write_text(render(rows, a.gk_label), encoding="utf-8")
    for r in rows:
        print(f"{r['label']:36s} carried {r['carried']:8.0f}  recall {r['recall']:4.1f}  saving {r['saving']}")
    print(out)
