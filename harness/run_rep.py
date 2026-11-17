"""Runs one repetition of the benchmark.

    python harness/run_rep.py --run p --rep 1 --budget 15

Lineage "base" (no plugin):   phase A = turns 1-10 (session S1) + turns 11-20 (fork of S1 -> S)
                              forks of S: /compact (B), handoff (C); probes A (fresh), B, C (fresh + pasted handoff), E (fork of S)
                              B2 (two resets): fork S1 -> /compact -> turns 11-20 -> /compact -> probes
Lineage "gk" (plugin loaded): phase A (same 20 turns, one session) + "/gemkeeper:gems" as turn 21
                              probes for D (fresh, ledger as of turn 20) and D2 (fresh, ledger after the sweep)
                              D3 (two resets): workspace after turn 10 -> FRESH session for turns 11-20 -> fresh probe
                              F (/compact + gemkeeper): fork of the turn-20 session -> /compact (ledger re-injected) -> probes
                              (since run t the sweep runs in a fork of the turn-20 session, so F starts without it)
--lineages base|gk runs only one side (run t: tuned plugin, gk only; baselines come from run f).
Every step writes results/<run>/rep<N>/<step>.json and is skipped when that file exists (resumable).
Workspaces live in ./w/ (git-ignored, throwaway).
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cc  # noqa: E402
import score  # noqa: E402
import workspace as wsm  # noqa: E402

BENCH = Path(__file__).resolve().parent.parent
WORK = BENCH / "w"
PHASE_A = json.loads((BENCH / "scenario" / "phase_a.json").read_text(encoding="utf-8"))["turns"]
PROBE = json.loads((BENCH / "scenario" / "probe.json").read_text(encoding="utf-8"))

BASE_CONDS = ["A_none", "B_compact", "C_handoff", "E_noreset", "B2_compact2"]
GK_CONDS = ["D_gemkeeper", "D2_gemkeeper_sweep"]
CONDITIONS = ["A_none", "B_compact", "B2_compact2", "C_handoff", "D_gemkeeper", "D2_gemkeeper_sweep",
              "D3_gemkeeper_2sess", "F_compact_gemkeeper", "E_noreset"]
PROBES = ["quiz", "trap_legacy", "trap_dependency", "trap_deadend"]
N_TURNS = len(PHASE_A)
SPLIT = 10  # two-reset conditions (B2, D3) reset after this many turns


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    def __init__(self, path: Path, cap: float):
        self.path, self.cap, self.lock = path, cap, threading.Lock()

    def spent(self) -> float:
        if not self.path.exists():
            return 0.0
        return sum(json.loads(line)["cost"] or 0 for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip())

    def check(self, label: str) -> None:
        spent = self.spent()
        if spent >= self.cap:
            raise BudgetExceeded(f"budget cap ${self.cap:.2f} reached (${spent:.2f} spent) before {label}")

    def add(self, label: str, cost: float | None) -> None:
        with self.lock, open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"label": label, "cost": cost}) + "\n")


def plugin_info() -> dict:
    """The gemkeeper version the gk lineage runs against. Every result must map to one plugin commit."""
    import subprocess

    def git(*a):
        return subprocess.run(["git", "-C", str(cc.PLUGIN_DIR), *a], capture_output=True, text=True).stdout.strip()
    meta = json.loads((cc.PLUGIN_DIR / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    dirty = git("status", "--porcelain", "--", "hooks", "scripts", "skills", ".claude-plugin")
    return {"version": meta.get("version"), "commit": git("rev-parse", "HEAD"), "dirty": bool(dirty)}


def check_plugin(run_dir: Path) -> dict:
    """Refuses uncommitted plugin changes and mixing two plugin commits within one run."""
    info = plugin_info()
    if info["dirty"]:
        raise RuntimeError("gemkeeper has uncommitted changes in hooks/scripts/skills/.claude-plugin; "
                           "commit them first so the results map to a version")
    run_file = run_dir / "plugin.json"
    if run_file.exists():
        prev = json.loads(run_file.read_text(encoding="utf-8"))
        if prev["commit"] != info["commit"]:
            raise RuntimeError(f"run {run_dir.name} was measured with gemkeeper {prev['commit'][:8]}, "
                               f"the plugin is now at {info['commit'][:8]}: check out that commit or use a new run name")
    else:
        run_file.write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
    return info


def quiz_prompt() -> str:
    qs = "\n".join(f"{q['q']}. {q['text']}" for q in PROBE["quiz"]["questions"])
    return PROBE["quiz"]["intro"] + "\n\n" + qs


TRAP_TEXT = {t["id"]: t["text"] for t in PROBE["traps"]}


class Rep:
    def __init__(self, run: str, rep: int, budget: Budget, lineages=("base", "gk")):
        self.run_name, self.rep, self.budget, self.lineages = run, rep, budget, tuple(lineages)
        self.dir = BENCH / "results" / run / f"rep{rep}"
        self.logs = self.dir / "logs"
        self.logs.mkdir(parents=True, exist_ok=True)
        tag = f"{run}{rep}"
        self.ws_base = WORK / f"{tag}a" / "parcel-tracker"
        self.ws_gk = WORK / f"{tag}b" / "parcel-tracker"
        self.snap_base = WORK / f"{tag}a.snap"
        self.snap_gk = WORK / f"{tag}b.snap"
        self.snap_gk_sweep = WORK / f"{tag}b.sweep.snap"
        self.snap_base10 = WORK / f"{tag}a.snap10"
        self.snap_b2 = WORK / f"{tag}a.b2.snap"
        self.snap_gk10 = WORK / f"{tag}b.snap10"
        self.snap_gk2 = WORK / f"{tag}b.gk2.snap"

    # ------------------------------------------------------------ helpers
    def step(self, name: str, fn):
        f = self.dir / f"{name}.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
        self.budget.check(name)
        print(f"[rep{self.rep}] {name} ...", flush=True)
        try:
            res = fn()
        except cc.RateLimited as e:  # count what the aborted session already cost
            self.budget.add(f"{self.run_name}/rep{self.rep}/{name}#aborted", getattr(e, "cost", None))
            raise
        self.budget.add(f"{self.run_name}/rep{self.rep}/{name}", res.get("cost") if isinstance(res, dict) else None)
        err = (res.get("error") or (res.get("session") or {}).get("error")) if isinstance(res, dict) else None
        if err:  # never cache a failed step: a rerun must retry it
            raise RuntimeError(f"{name} failed: {err}")
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        cost = res.get("cost") if isinstance(res, dict) else None
        print(f"[rep{self.rep}] {name} done  cost=${cost}  budget spent=${self.budget.spent():.2f}", flush=True)
        return res

    # ------------------------------------------------------------ lineage: baseline
    def lineage_base(self):
        def phase_a():
            wsm.create(self.ws_base)
            prompts = [t["text"] for t in PHASE_A]
            s1 = cc.run_session(self.ws_base, prompts[:SPLIT], self.logs / "phaseA1_base.jsonl.gz")
            wsm.snapshot(self.ws_base, self.snap_base10)
            if s1.get("error"):
                return s1
            s2 = cc.run_session(self.ws_base, prompts[SPLIT:], self.logs / "phaseA_base.jsonl.gz",
                                resume=s1["session_id"], fork=True, parent_cost=s1["cost_cumulative"])
            wsm.snapshot(self.ws_base, self.snap_base)
            return {**s2, "turns": s1["turns"] + s2["turns"], "cost": round(s1["cost"] + (s2["cost"] or 0), 6),
                    "wall_s": s1["wall_s"] + s2["wall_s"], "session_id_a1": s1["session_id"],
                    "cost_a1": s1["cost"], "cost_cumulative_a1": s1["cost_cumulative"]}
        pa = self.step("phaseA_base", phase_a)
        if pa.get("error"):
            raise RuntimeError(f"phaseA_base failed: {pa['error']}")
        if not self.snap_base.exists():
            raise RuntimeError("baseline snapshot missing; delete phaseA_base.json to rerun phase A")

        # Order matters for cost: everything that forks the full phase-A context (E probes, handoff,
        # compaction) runs first, while the 1h prompt cache of that context is still warm.
        e_sess = {"resume": pa["session_id"], "fork": True, "parent_cost": pa["cost_cumulative"]}
        for probe in PROBES:
            self.step(f"probe_E_noreset_{probe}", lambda p=probe: self.run_probe(
                "E_noreset", p, self.ws_base, self.snap_base, e_sess))

        def handoff():
            wsm.restore(self.snap_base, self.ws_base)
            s = cc.run_session(self.ws_base, [PROBE["handoff_request"]], self.logs / "prep_handoff.jsonl.gz",
                               resume=pa["session_id"], fork=True, parent_cost=pa["cost_cumulative"])
            s["handoff_text"] = (s["turns"][0]["result"] or {}).get("text") if s["turns"] else None
            s["handoff_wrote_files"] = wsm.diff_trees(self.snap_base, self.ws_base)["added"]
            return s
        ho = self.step("prep_handoff", handoff)

        def compact():
            wsm.restore(self.snap_base, self.ws_base)
            return cc.run_session(self.ws_base, [PROBE["compact_command"]], self.logs / "prep_compact.jsonl.gz",
                                  resume=pa["session_id"], fork=True, parent_cost=pa["cost_cumulative"])
        comp = self.step("prep_compact", compact)

        # B2 step 1, while the prompt cache of S1's prefix is still warm: compact the session after turn 10
        def compact10():
            wsm.restore(self.snap_base10, self.ws_base)
            return cc.run_session(self.ws_base, [PROBE["compact_command"]], self.logs / "prep_compact10.jsonl.gz",
                                  resume=pa["session_id_a1"], fork=True, parent_cost=pa["cost_cumulative_a1"])
        c10 = self.step("prep_compact10", compact10)

        sessions = {
            "A_none": {},
            "B_compact": {"resume": comp["session_id"], "fork": True, "parent_cost": comp["cost_cumulative"]},
            "C_handoff": {},
        }
        for cond in ["B_compact", "C_handoff", "A_none"]:
            for probe in PROBES:
                self.step(f"probe_{cond}_{probe}", lambda c=cond, p=probe: self.run_probe(
                    c, p, self.ws_base, self.snap_base, sessions[c], handoff=ho.get("handoff_text")))

        # B2 steps 2-3: turns 11-20 in the compacted session, then compact again
        def a2_compacted():
            wsm.restore(self.snap_base10, self.ws_base)
            s = cc.run_session(self.ws_base, [t["text"] for t in PHASE_A[SPLIT:]], self.logs / "phaseA2_compacted.jsonl.gz",
                               resume=c10["session_id"], fork=True, parent_cost=c10["cost_cumulative"])
            wsm.snapshot(self.ws_base, self.snap_b2)
            return s
        a2c = self.step("phaseA2_compacted", a2_compacted)
        if a2c.get("error") or not self.snap_b2.exists():
            raise RuntimeError(f"phaseA2_compacted failed: {a2c.get('error')}")

        def compact2():
            wsm.restore(self.snap_b2, self.ws_base)
            return cc.run_session(self.ws_base, [PROBE["compact_command"]], self.logs / "prep_compact2.jsonl.gz",
                                  resume=a2c["session_id"], fork=True, parent_cost=a2c["cost_cumulative"])
        c2 = self.step("prep_compact2", compact2)
        b2_sess = {"resume": c2["session_id"], "fork": True, "parent_cost": c2["cost_cumulative"]}
        for probe in PROBES:
            self.step(f"probe_B2_compact2_{probe}", lambda p=probe: self.run_probe(
                "B2_compact2", p, self.ws_base, self.snap_b2, b2_sess))

    # ------------------------------------------------------------ lineage: gemkeeper
    def lineage_gk(self):
        def phase_a():
            wsm.create(self.ws_gk)
            ledger_by_turn = []

            def on_turn(i, _turn):
                p = self.ws_gk / ".gemkeeper" / "ledger.md"
                ledger_by_turn.append({"turn": i, "text": p.read_text(encoding="utf-8") if p.exists() else None})
                if i == SPLIT - 1:
                    wsm.snapshot(self.ws_gk, self.snap_gk10)
                if i == N_TURNS - 1:
                    wsm.snapshot(self.ws_gk, self.snap_gk)
                elif i == N_TURNS:
                    wsm.snapshot(self.ws_gk, self.snap_gk_sweep)

            s = cc.run_session(self.ws_gk, [t["text"] for t in PHASE_A], self.logs / "phaseA_gk.jsonl.gz",
                               plugin=True, on_turn=on_turn)
            costs = [t["result"]["total_cost_usd"] if t.get("result") else None for t in s["turns"]]
            s["cost_phase_a"] = costs[N_TURNS - 1] if len(costs) >= N_TURNS else None
            s["cost_turn10"] = costs[SPLIT - 1] if len(costs) >= SPLIT else None
            if not s.get("error") and s["cost_phase_a"] is not None:
                # the sweep runs in a fork, so the turn-20 session stays available for F (/compact + gemkeeper)
                sw = cc.run_session(self.ws_gk, [PROBE["sweep_command"]], self.logs / "phaseA_gk_sweep.jsonl.gz",
                                    plugin=True, resume=s["session_id"], fork=True, parent_cost=s["cost_cumulative"])
                on_turn(N_TURNS, None)
                s["sweep"] = {k: sw.get(k) for k in ("session_id", "cost", "error", "hooks")}
                s["turns"] = s["turns"] + sw["turns"]
                s["cost_sweep"] = sw["cost"]
                s["cost"] = round((s["cost"] or 0) + (sw["cost"] or 0), 6)
                s["error"] = sw.get("error")
            s["ledger_by_turn"] = ledger_by_turn
            return s
        pa = self.step("phaseA_gk", phase_a)
        if pa.get("error"):
            raise RuntimeError(f"phaseA_gk failed: {pa['error']}")
        # F: /compact the turn-20 session right away (prompt cache still warm); the plugin re-injects the ledger
        def compact_gk():
            wsm.restore(self.snap_gk, self.ws_gk)
            return cc.run_session(self.ws_gk, [PROBE["compact_command"]], self.logs / "prep_compact_gk.jsonl.gz",
                                  plugin=True, resume=pa["session_id"], fork=True, parent_cost=pa["cost_cumulative"])
        cg = self.step("prep_compact_gk", compact_gk)
        snaps = {"D_gemkeeper": self.snap_gk, "D2_gemkeeper_sweep": self.snap_gk_sweep}
        for cond in GK_CONDS:
            if not snaps[cond].exists():
                raise RuntimeError(f"snapshot for {cond} missing")
            for probe in PROBES:
                self.step(f"probe_{cond}_{probe}", lambda c=cond, p=probe: self.run_probe(
                    c, p, self.ws_gk, snaps[c], {"plugin": True}))

        # D3: the workspace (incl. ledger) after turn 10, then a FRESH session for turns 11-20, then a fresh probe
        def gk2():
            if not self.snap_gk10.exists():
                raise RuntimeError("snapshot after turn 10 missing")
            wsm.restore(self.snap_gk10, self.ws_gk)
            ledger_by_turn = []

            def on_turn(i, _turn):
                p = self.ws_gk / ".gemkeeper" / "ledger.md"
                ledger_by_turn.append({"turn": SPLIT + i, "text": p.read_text(encoding="utf-8") if p.exists() else None})
            s = cc.run_session(self.ws_gk, [t["text"] for t in PHASE_A[SPLIT:]], self.logs / "phaseA2_gk2sess.jsonl.gz",
                               plugin=True, on_turn=on_turn)
            wsm.snapshot(self.ws_gk, self.snap_gk2)
            s["ledger_by_turn"] = ledger_by_turn
            return s
        g2 = self.step("phaseA2_gk2sess", gk2)
        if g2.get("error") or not self.snap_gk2.exists():
            raise RuntimeError(f"phaseA2_gk2sess failed: {g2.get('error')}")
        for probe in PROBES:
            self.step(f"probe_D3_gemkeeper_2sess_{probe}", lambda p=probe: self.run_probe(
                "D3_gemkeeper_2sess", p, self.ws_gk, self.snap_gk2, {"plugin": True}))
        f_sess = {"plugin": True, "resume": cg["session_id"], "fork": True, "parent_cost": cg["cost_cumulative"]}
        for probe in PROBES:
            self.step(f"probe_F_compact_gemkeeper_{probe}", lambda p=probe: self.run_probe(
                "F_compact_gemkeeper", p, self.ws_gk, self.snap_gk, f_sess))

    # ------------------------------------------------------------ one probe
    def run_probe(self, cond: str, probe: str, ws: Path, snap: Path, sess: dict, handoff: str | None = None) -> dict:
        wsm.restore(snap, ws)
        prompt = quiz_prompt() if probe == "quiz" else TRAP_TEXT[probe]
        if cond == "C_handoff":
            prompt = PROBE["handoff_paste_template"].replace("<<<HANDOFF>>>", handoff or "").replace("<<<PROMPT>>>", prompt)
        s = cc.run_session(ws, [prompt], self.logs / f"probe_{cond}_{probe}.jsonl.gz", turn_timeout=1500, **sess)
        out = {"cost": s["cost"], "session": s}
        tools = [t for turn in s["turns"] for t in turn["tools"]]
        if probe == "quiz":
            # a Stop-hook continuation can replace the final result text, so take the assistant text
            # of this turn that parses into the most answers
            t0 = s["turns"][0] if s["turns"] else {}
            cands = [c for c in [(t0.get("result") or {}).get("text")] + t0.get("texts", []) if c]
            text = max(cands, key=lambda c: len(score.parse_quiz(c)), default=None)
            out["answer_texts_all"] = cands
            out["answer_text"] = text
            out["answers"] = score.parse_quiz(text)
            out["tool_calls"] = [t["name"] for t in tools]
        else:
            diff = wsm.diff_trees(snap, ws)
            out["checks"] = score.check_all(snap, ws, diff)
            out["violation"] = out["checks"][score.TRAP_PRIMARY[probe]]["violation"]
            out["diff"] = {k: diff[k] for k in ("added", "removed", "modified", "node_modules_created")}
            out["unified_diff"] = diff["unified"]
            out["tests_after"] = wsm.run_tests(ws)
            out["final_text"] = (s["turns"][-1]["result"] or {}).get("text") if s["turns"] else None
        wsm.restore(snap, ws)
        return out

    # ------------------------------------------------------------ scoring
    def scoring(self):
        quiz = {c: json.loads((self.dir / f"probe_{c}_quiz.json").read_text(encoding="utf-8")) for c in CONDITIONS
                if (self.dir / f"probe_{c}_quiz.json").exists()}

        def judge():
            res = score.judge_quiz({c: q["answers"] for c, q in quiz.items()}, self.dir, seed=1000 + self.rep)
            return res
        jq = self.step("judge_quiz", judge)

        if not (self.dir / "phaseA_gk.json").exists():  # base-only rep
            return quiz, jq, None, "", ""
        pa_gk = json.loads((self.dir / "phaseA_gk.json").read_text(encoding="utf-8"))
        led = {e["turn"]: e["text"] for e in pa_gk["ledger_by_turn"]}
        ledger_d = led.get(N_TURNS - 1) or ""
        ledger_d2 = led.get(N_TURNS) or ""
        g2_file = self.dir / "phaseA2_gk2sess.json"
        g2 = json.loads(g2_file.read_text(encoding="utf-8")) if g2_file.exists() else {}
        ledger_d3 = (g2["ledger_by_turn"][-1]["text"] if g2.get("ledger_by_turn") else None) or ""

        def coverage():
            out = {"cost": 0.0}
            for name, text in (("D", ledger_d), ("D2", ledger_d2)) + ((("D3", ledger_d3),) if g2 else ()):
                if text.strip():
                    r = score.judge_coverage(text, self.dir, name)
                    out[name] = r["scores"]
                    out["cost"] += r["cost"] or 0
                else:
                    out[name] = {g["id"]: {"score": 0, "why": "no ledger"} for g in score.GEMS}
            return out
        cov = self.step("judge_coverage", coverage)
        return quiz, jq, cov, ledger_d, ledger_d2

    def run(self):
        import os
        runner = {"config_dir": os.environ.get("BENCH_CLAUDE_CONFIG_DIR") or "default (~/.claude)", "model": cc.MODEL,
                  "effort": cc.EFFORT, "lineages": list(self.lineages)}
        rf = self.dir / "runner.json"
        if rf.exists() and json.loads(rf.read_text(encoding="utf-8"))["config_dir"] != runner["config_dir"]:
            raise RuntimeError(f"rep{self.rep} was started with another Claude config dir; sessions cannot be resumed across accounts")
        rf.write_text(json.dumps(runner, indent=1) + "\n", encoding="utf-8")
        if "gk" in self.lineages:
            info = check_plugin(self.dir.parent)
            (self.dir / "plugin.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
        errors = {}
        with ThreadPoolExecutor(2) as pool:
            futs = {n: pool.submit(getattr(self, f"lineage_{n}")) for n in self.lineages}
            for name, fut in futs.items():
                try:
                    fut.result()
                except Exception as e:  # keep the other lineage's results
                    errors[name] = f"{type(e).__name__}: {e}"
                    traceback.print_exc()
        err_file = self.dir / "errors.json"
        if errors:
            err_file.write_text(json.dumps(errors, indent=1), encoding="utf-8")
            print(f"[rep{self.rep}] lineage errors: {errors}", flush=True)
            return errors
        err_file.unlink(missing_ok=True)
        self.scoring()
        import summarize
        summarize.summarize_rep(self.dir)
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="run name, e.g. p (pilot) or f (full); also used in workspace paths")
    ap.add_argument("--rep", type=int, required=True)
    ap.add_argument("--budget", type=float, required=True,
                    help="hard cap in USD across ALL runs (pilot + full); spending is tracked in results/costs.jsonl")
    ap.add_argument("--lineages", nargs="+", default=["base", "gk"], choices=["base", "gk"])
    args = ap.parse_args()
    (BENCH / "results" / args.run).mkdir(parents=True, exist_ok=True)
    budget = Budget(BENCH / "results" / "costs.jsonl", args.budget)
    errors = Rep(args.run, args.rep, budget, args.lineages).run()
    print(f"done ok={not errors} spent=${budget.spent():.2f}")


if __name__ == "__main__":
    main()
