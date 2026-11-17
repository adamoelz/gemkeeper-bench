"""Per-repetition metrics and cross-repetition aggregation.

    python harness/summarize.py --run p        # (re)summarizes every rep of run p and prints tables
"""
from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score  # noqa: E402

BENCH = Path(__file__).resolve().parent.parent
CONDITIONS = ["A_none", "B_compact", "B2_compact2", "C_handoff", "C2_handoff_skill", "D_gemkeeper", "D2_gemkeeper_sweep",
              "D3_gemkeeper_2sess", "F_compact_gemkeeper", "DL_lite", "DL3_lite_2sess", "DL0_lite_noresume",
              "E_noreset"]
LABEL = {"A_none": "A none (/clear)", "B_compact": "B /compact", "B2_compact2": "B2 /compact twice (after t10 + t20)",
         "C_handoff": "C handoff", "C2_handoff_skill": "C2 handoff skill (mattpocock)", "D_gemkeeper": "D gemkeeper", "D2_gemkeeper_sweep": "D2 gemkeeper + /gems",
         "D3_gemkeeper_2sess": "D3 gemkeeper, fresh session after t10 + t20",
         "F_compact_gemkeeper": "F /compact + gemkeeper", "DL_lite": "DL skill-only + /gemkeeper:resume",
         "DL3_lite_2sess": "DL3 skill-only, 2 fresh sessions + /resume", "DL0_lite_noresume": "DL0 skill-only, no /resume",
         "E_noreset": "E no reset"}
SPLIT = 10
TRAPS = ["trap_legacy", "trap_dependency", "trap_deadend"]
CATS = {"rules": "Rules /10", "decisions": "Decisions+why /8", "dead_ends": "Dead ends /8", "facts": "Facts /4"}
N_TURNS = 20


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def tok(chars: int) -> int:
    return round(chars / 4)


def _ledger_tool_ids(log: Path) -> set[str]:
    """ids of tool calls whose FULL input touches the ledger or loads the gems skill."""
    ids: set[str] = set()
    if not log.exists():
        return ids
    with gzip.open(log, "rt", encoding="utf-8") as f:
        for line in f:
            if '"tool_use"' not in line:
                continue
            ev = json.loads(line)
            for b in ev.get("message", {}).get("content", []) or []:
                if b.get("type") == "tool_use":
                    full = json.dumps(b.get("input"), ensure_ascii=False)
                    if ".gemkeeper" in full or (b.get("name") == "Skill" and "gems" in full):
                        ids.add(b.get("id"))
    return ids


def summarize_rep(rep_dir: Path) -> dict:
    """Works for full reps and for one-sided reps (--lineages base | gk)."""
    def opt(name):
        f = rep_dir / f"{name}.json"
        return _load(f) if f.exists() else None

    jq = _load(rep_dir / "judge_quiz.json")
    if (rep_dir / "judge_quiz_extra.json").exists():
        ex = _load(rep_dir / "judge_quiz_extra.json")
        jq = {**jq, "scores": {**jq["scores"], **ex["scores"]}, "cost": (jq.get("cost") or 0) + (ex.get("cost") or 0)}
    cov = opt("judge_coverage")
    pa_base, pa_gk, pa_lite = opt("phaseA_base"), opt("phaseA_gk"), opt("phaseA_lite")
    l2 = opt("phaseA2_lite2sess")
    comp, ho = opt("prep_compact"), opt("prep_compact") and opt("prep_handoff")
    o = {n: opt(n) for n in ("prep_compact10", "phaseA2_compacted", "prep_compact2", "phaseA2_gk2sess", "prep_compact_gk")}

    conds = {}
    for c in CONDITIONS:
        if not (rep_dir / f"probe_{c}_quiz.json").exists():
            continue
        quiz = _load(rep_dir / f"probe_{c}_quiz.json")
        per_gem = {v["gem"]: v["score"] for v in jq["scores"][c].values()}
        for g in score.GEMS:
            per_gem.setdefault(g["id"], 0)
        by_cat = {cat: sum(per_gem[g["id"]] for g in score.GEMS if g["category"] == cat) for cat in CATS}
        traps = {t: _load(rep_dir / f"probe_{c}_{t}.json") for t in TRAPS}
        any_rule = {k: any(traps[t]["checks"][k]["violation"] for t in TRAPS) for k in ("legacy", "dependency", "deadend")}
        probe_cost = quiz["cost"] + sum(traps[t]["cost"] for t in TRAPS)
        if c in ("DL_lite", "DL0_lite_noresume"):
            phase_a, prep = pa_lite["cost_phase_a"], 0
        elif c == "DL3_lite_2sess":
            phase_a, prep = pa_lite["cost_turn10"] + l2["cost"], 0
        elif c == "B2_compact2":  # turns 1-10, /compact, turns 11-20 in the compacted session, /compact
            phase_a = pa_base["cost_a1"] + o["phaseA2_compacted"]["cost"]
            prep = o["prep_compact10"]["cost"] + o["prep_compact2"]["cost"]
        elif c == "D3_gemkeeper_2sess":  # turns 1-10 with plugin, fresh session for turns 11-20
            phase_a, prep = pa_gk["cost_turn10"] + o["phaseA2_gk2sess"]["cost"], 0
        elif c == "F_compact_gemkeeper":
            phase_a, prep = pa_gk["cost_phase_a"], o["prep_compact_gk"]["cost"]
        elif c.startswith("D"):
            phase_a = pa_gk["cost_phase_a"]
            prep = (pa_gk.get("cost_sweep") or 0) if c == "D2_gemkeeper_sweep" else 0
        else:
            phase_a = pa_base["cost"]
            ho2 = opt("prep_handoff_skill")
            prep = {"B_compact": comp["cost"] if comp else 0, "C_handoff": ho["cost"] if ho else 0,
                    "C2_handoff_skill": ho2["cost"] if ho2 else 0}.get(c, 0)
        conds[c] = {
            "recall": sum(per_gem.values()),
            "by_cat": by_cat,
            "per_gem": per_gem,
            "quiz_tool_calls": len(quiz.get("tool_calls", [])),
            "traps": {t: traps[t]["violation"] for t in TRAPS},
            "violations": sum(traps[t]["violation"] for t in TRAPS),
            "any_rule_violation_in_traps": any_rule,
            "tests_green_after_trap": {t: traps[t]["tests_after"]["exit_code"] == 0 for t in TRAPS},
            "ctx_probe_start": quiz["session"]["ctx_first"],
            "ctx_trap_start": {t: traps[t]["session"]["ctx_first"] for t in TRAPS},
            "cost": {"phase_a": phase_a, "prep": prep, "probes": round(probe_cost, 4),
                     "total": round(phase_a + prep + probe_cost, 4)},
        }

    # ---------------- gemkeeper-specific
    gk = None
    if pa_gk and cov:
        led = {e["turn"]: e["text"] or "" for e in pa_gk["ledger_by_turn"]}
        ledger_d, ledger_d2 = led.get(N_TURNS - 1, ""), led.get(N_TURNS, "")
        first_seen = {}
        for g in score.GEMS:
            first_seen[g["id"]] = next((t + 1 for t in sorted(led) if t < N_TURNS and score.keyword_hits(led[t])[g["id"]]), None)

        hooks = [h for h in pa_gk["hooks"] if h["turn"] < N_TURNS]
        checkpoints = sum(1 for h in hooks if "checkpoint" in h["output"])
        warnings = sum(1 for h in hooks if "Context is at" in h["output"])
        gem_checks = sum(1 for h in hooks if "gem check" in h["output"])
        stop_blocks = sum(1 for h in hooks if "did not change this turn" in h["output"])
        ledger_ids = _ledger_tool_ids(rep_dir / "logs" / "phaseA_gk.jsonl.gz")
        ledger_tools = [t for turn in pa_gk["turns"][:N_TURNS] for t in turn["tools"]
                        if t.get("mentions_ledger") or t["id"] in ledger_ids]
        # A ledger write = the ledger file changed during that turn (robust to Write/Edit/Bash/python edits).
        prev, turns_with_ledger_write = "", []
        for t in range(N_TURNS):
            cur = led.get(t, "")
            if cur != prev:
                turns_with_ledger_write.append(t + 1)
            prev = cur
        ctx_gk = [turn["ctx"][-1] if turn["ctx"] else None for turn in pa_gk["turns"]]
        ctx_base = [turn["ctx"][-1] if turn["ctx"] else None for turn in pa_base["turns"]] if pa_base else []
        cov_d, cov_d2, cov_d3 = cov["D"], cov["D2"], cov.get("D3")
        g2 = o["phaseA2_gk2sess"]
        ledger_d3 = ((g2["ledger_by_turn"][-1]["text"] if g2 and g2.get("ledger_by_turn") else None) or "")
        a_ctx = conds.get("A_none", {}).get("ctx_probe_start")
        gk = {
            "ledger_D": {"lines": len(ledger_d.splitlines()), "chars": len(ledger_d), "tokens_est": tok(len(ledger_d))},
            "ledger_D2": {"lines": len(ledger_d2.splitlines()), "chars": len(ledger_d2), "tokens_est": tok(len(ledger_d2))},
            "organic_capture_any": sum(1 for v in cov_d.values() if v["score"] >= 1),
            "organic_capture_full": sum(1 for v in cov_d.values() if v["score"] == 2),
            "sweep_capture_any": sum(1 for v in cov_d2.values() if v["score"] >= 1),
            "sweep_capture_full": sum(1 for v in cov_d2.values() if v["score"] == 2),
            "coverage_D": {k: v["score"] for k, v in cov_d.items()},
            "coverage_D2": {k: v["score"] for k, v in cov_d2.items()},
            "keyword_first_seen_turn": first_seen,
            "hooks": {"checkpoints_fired": checkpoints, "context_warnings_fired": warnings,
                      "gem_checks_fired": gem_checks, "stop_blocks": stop_blocks,
                      "injected_chars": sum(h["chars"] for h in hooks), "injected_tokens_est": tok(sum(h["chars"] for h in hooks))},
            "ledger_tool_calls": len(ledger_tools),
            "ledger_write_calls": len(turns_with_ledger_write),
            "turns_with_ledger_write": turns_with_ledger_write,
            "ledger_tool_tokens_est": tok(sum(t["input_chars"] + t["result_chars"] for t in ledger_tools)),
            "phase_a_cost": pa_gk["cost_phase_a"],
            "phase_a_cost_delta_vs_base": round(pa_gk["cost_phase_a"] - pa_base["cost"], 4) if pa_base else None,
            "sweep_cost": pa_gk.get("cost_sweep"),
            "ctx_end_phase_a": {"base": ctx_base[N_TURNS - 1] if len(ctx_base) >= N_TURNS else None,
                                "gk": ctx_gk[N_TURNS - 1] if len(ctx_gk) >= N_TURNS else None},
            "ctx_by_turn": {"base": ctx_base, "gk": ctx_gk},
            "injection_tokens_measured": (conds["D_gemkeeper"]["ctx_probe_start"] - a_ctx) if a_ctx and "D_gemkeeper" in conds else None,
        }
        if cov_d3 is not None:
            gk["ledger_D3"] = {"lines": len(ledger_d3.splitlines()), "chars": len(ledger_d3), "tokens_est": tok(len(ledger_d3))}
            gk["coverage_D3"] = {k: v["score"] for k, v in cov_d3.items()}
            gk["d3_capture_full"] = sum(1 for v in cov_d3.values() if v["score"] == 2)

    # ---------------- skill-only edition
    lite = None
    cov_l = opt("judge_coverage_lite")
    if pa_lite and cov_l:
        led_l = {e["turn"]: e["text"] or "" for e in pa_lite["ledger_by_turn"]}
        ld = led_l.get(N_TURNS - 1, "")
        ld3 = ((l2["ledger_by_turn"][-1]["text"] if l2 and l2.get("ledger_by_turn") else None) or "")
        lite = {"phase_a_cost": pa_lite["cost_phase_a"],
                "phase_a_steps": sum((t["result"] or {}).get("num_turns") or 0 for t in pa_lite["turns"][:N_TURNS]),
                "ledger_DL": {"lines": len(ld.splitlines()), "tokens_est": tok(len(ld))},
                "ledger_DL3": {"lines": len(ld3.splitlines()), "tokens_est": tok(len(ld3))},
                "organic_capture_any": sum(1 for v in cov_l["DL"].values() if v["score"] >= 1),
                "organic_capture_full": sum(1 for v in cov_l["DL"].values() if v["score"] == 2),
                "d3_capture_full": sum(1 for v in cov_l["DL3"].values() if v["score"] == 2),
                "coverage_DL": {k: v["score"] for k, v in cov_l["DL"].items()},
                "coverage_DL3": {k: v["score"] for k, v in cov_l["DL3"].items()},
                "turns_with_ledger_write": [t + 1 for t in range(N_TURNS) if led_l.get(t, "") != led_l.get(t - 1, "")]}

    # ---------------- leak check: did any model under test touch the answer key?
    leaks = []
    for p in (rep_dir / "logs").glob("*.jsonl.gz"):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            text = f.read()
        if "answer_key" in text or "gems.json" in text:
            leaks.append(p.name)

    summary = {
        "conditions": conds, "gemkeeper": gk, "lite": lite,
        "compact": comp.get("compact") if comp else None,
        "handoff_chars": len(ho.get("handoff_text") or "") if ho else None,
        "handoff_wrote_files": ho.get("handoff_wrote_files") if ho else None,
        "phase_a": {k: {"cost": v.get("cost_phase_a", v.get("cost")), "wall_s": v["wall_s"], "error": v["error"]}
                    for k, v in (("base", pa_base), ("gk", pa_gk), ("lite", pa_lite)) if v},
        "judge_cost": jq.get("cost", 0) + (cov.get("cost", 0) if cov else 0) + (cov_l.get("cost", 0) if cov_l else 0),
        "judge_missing": jq.get("missing"),
        "answer_key_leaks": leaks,
    }
    (rep_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def _ms(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return "n/a"
    m = statistics.mean(vals)
    if len(vals) == 1:
        return f"{m:.1f}" if isinstance(m, float) and m != int(m) else f"{m:g}"
    return f"{m:.1f} ± {statistics.stdev(vals):.1f}"


def _money(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return "n/a"
    m = statistics.mean(vals)
    return f"${m:.2f}" if len(vals) == 1 else f"${m:.2f} ± {statistics.stdev(vals):.2f}"


def aggregate(run: str) -> str:
    run_dir = BENCH / "results" / run
    reps = sorted(p for p in run_dir.glob("rep*") if (p / "summary.json").exists())
    S = [_load(p / "summary.json") for p in reps]
    n = len(S)
    CONDS = [c for c in CONDITIONS if all(c in s["conditions"] for s in S)]
    out = [f"### Run `{run}`: {n} repetition(s); mean ± sd across repetitions\n"]
    out.append("| Condition | Recall /30 | " + " | ".join(CATS.values()) + " | Trap violations /3 | Context at probe start (tokens) | Cost phase A + reset + probes |")
    out.append("|---|---|" + "---|" * len(CATS) + "---|---|---|")
    for c in CONDS:
        rows = [s["conditions"][c] for s in S]
        out.append(f"| {LABEL[c]} | {_ms([r['recall'] for r in rows])} | "
                   + " | ".join(_ms([r['by_cat'][k] for r in rows]) for k in CATS)
                   + f" | {_ms([r['violations'] for r in rows])} | {_ms([r['ctx_probe_start'] for r in rows])} | {_money([r['cost']['total'] for r in rows])} |")
    out.append("\n**Traps** (violations per trap, summed over repetitions; `n` = repetitions)\n")
    out.append("| Condition | legacy dir touched | dependency added | dead end (run p: fs.watch; run f: ETA cache) | tests green after traps |")
    out.append("|---|---|---|---|---|")
    for c in CONDS:
        rows = [s["conditions"][c] for s in S]
        cells = [f"{sum(r['traps'][t] for r in rows)}/{n}" for t in TRAPS]
        green = sum(sum(r["tests_green_after_trap"].values()) for r in rows)
        out.append(f"| {LABEL[c]} | " + " | ".join(cells) + f" | {green}/{3 * n} |")
    out.append("\n**Per gem** (quiz score 0–2, summed over repetitions, max " + str(2 * n) + ")\n")
    gem_ids = [g["id"] for g in score.GEMS]
    out.append("| Condition | " + " | ".join(gem_ids) + " |")
    out.append("|---|" + "---|" * len(gem_ids))
    for c in CONDS:
        out.append(f"| {LABEL[c]} | " + " | ".join(str(sum(s["conditions"][c]["per_gem"][g] for s in S)) for g in gem_ids) + " |")
    G = [s["gemkeeper"] for s in S if s.get("gemkeeper")]
    if len(G) != n:
        G = []
    if G:
        out.append("\n**gemkeeper**\n")
        out.append(f"- Ledger at end of phase A (D): {_ms([g['ledger_D']['lines'] for g in G])} lines, ~{_ms([g['ledger_D']['tokens_est'] for g in G])} tokens (chars/4)")
        out.append(f"- Ledger after /gems sweep (D2): {_ms([g['ledger_D2']['lines'] for g in G])} lines, ~{_ms([g['ledger_D2']['tokens_est'] for g in G])} tokens")
        out.append(f"- Organic capture (gem in ledger without sweep, judge score ≥1 / =2): {_ms([g['organic_capture_any'] for g in G])} / {_ms([g['organic_capture_full'] for g in G])} of 15")
        out.append(f"- After sweep (≥1 / =2): {_ms([g['sweep_capture_any'] for g in G])} / {_ms([g['sweep_capture_full'] for g in G])} of 15")
        out.append(f"- Checkpoint nudges fired in phase A: {_ms([g['hooks']['checkpoints_fired'] for g in G])}; context warnings: {_ms([g['hooks']['context_warnings_fired'] for g in G])}")
        out.append(f"- Hook text injected in phase A: ~{_ms([g['hooks']['injected_tokens_est'] for g in G])} tokens; tool calls touching the ledger/skill: {_ms([g['ledger_tool_calls'] for g in G])}, ~{_ms([g['ledger_tool_tokens_est'] for g in G])} tokens of tool input+output (whole call, incl. code edits done in the same script); turns in which the ledger changed: {_ms([g['ledger_write_calls'] for g in G])} of 20")
        out.append(f"- Measured injection at session start (D quiz context − A quiz context): {_ms([g['injection_tokens_measured'] for g in G])} tokens")
        out.append(f"- Phase A cost with plugin − without: {_money([g['phase_a_cost_delta_vs_base'] for g in G])} (different sessions, so this includes run-to-run noise); sweep: {_money([g['sweep_cost'] for g in G])}")
        out.append(f"- Context at end of phase A: base {_ms([g['ctx_end_phase_a']['base'] for g in G])}, with plugin {_ms([g['ctx_end_phase_a']['gk'] for g in G])}")
        out.append("\n**Ledger coverage per gem** (judge score 0–2 summed over repetitions; D = organic, D2 = after sweep)\n")
        out.append("| | " + " | ".join(gem_ids) + " |")
        out.append("|---|" + "---|" * len(gem_ids))
        if all("coverage_D3" in g for g in G):
            out.append(f"- D3 ledger after the second session (turns 11-20): {_ms([g['ledger_D3']['lines'] for g in G])} lines, ~{_ms([g['ledger_D3']['tokens_est'] for g in G])} tokens; gems fully covered: {_ms([g['d3_capture_full'] for g in G])} of 15")
        rows_cov = [("coverage_D", "D organic"), ("coverage_D2", "D2 sweep")] + ([("coverage_D3", "D3 2 sessions")] if all("coverage_D3" in g for g in G) else [])
        for key, lab in rows_cov:
            out.append(f"| {lab} | " + " | ".join(str(sum(g[key].get(i, 0) for g in G)) for i in gem_ids) + " |")
    leaks = [l for s in S for l in s["answer_key_leaks"]]
    out.append(f"\nAnswer-key leak check: {'none' if not leaks else leaks}. Judge cost: {_money([s['judge_cost'] for s in S])} per rep.")
    md = "\n".join(out)
    (run_dir / "summary.md").write_text(md, encoding="utf-8")
    return md


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--no-resummarize", action="store_true")
    a = ap.parse_args()
    if not a.no_resummarize:
        for rep in sorted((BENCH / "results" / a.run).glob("rep*")):
            if (rep / "judge_coverage.json").exists():
                summarize_rep(rep)
    print(aggregate(a.run))
