"""Runs several repetitions unattended: waits out the subscription's usage limit and resumes.

    python harness/run_all.py --run f --reps 1 2 3 --budget 40

- Each rep is resumable (finished steps are skipped), so after a rate limit the same rep simply restarts.
- Before a rep starts, the remaining budget must cover 1.1x the cost of the most expensive finished rep
  of this run; otherwise the driver stops instead of leaving a half-finished rep behind.
- Any error other than a rate limit stops the driver (exit code 2) so a human can look at it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_rep  # noqa: E402


def wait_for_reset(msg: str) -> None:
    now = dt.datetime.now()
    m = re.search(r"resets\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)", msg, re.I)
    if m:
        hour = int(m[1]) % 12 + (12 if m[3].lower() == "pm" else 0)
        target = now.replace(hour=hour, minute=int(m[2] or 0), second=0, microsecond=0)
        if target <= now:
            target += dt.timedelta(days=1)
        target += dt.timedelta(minutes=3)
    else:
        target = now + dt.timedelta(minutes=30)
    print(f"[driver] usage limit hit; sleeping until {target:%Y-%m-%d %H:%M}", flush=True)
    time.sleep(max(60.0, (target - now).total_seconds()))


def rep_cost(costs: Path, run: str, rep: int) -> float:
    if not costs.exists():
        return 0.0
    pre = f"{run}/rep{rep}/"
    return sum(json.loads(line)["cost"] or 0 for line in costs.read_text(encoding="utf-8").splitlines()
               if line.strip() and json.loads(line)["label"].startswith(pre))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--reps", type=int, nargs="+", required=True)
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--max-waits", type=int, default=8)
    ap.add_argument("--lineages", nargs="+", default=["base", "gk"], choices=["base", "gk"])
    ap.add_argument("--est", type=float, help="expected cost of one rep (default: 1.1x the most expensive finished rep)")
    a = ap.parse_args()
    (run_rep.BENCH / "results" / a.run).mkdir(parents=True, exist_ok=True)
    costs = run_rep.BENCH / "results" / "costs.jsonl"
    budget = run_rep.Budget(costs, a.budget)
    for rep in a.reps:
        rep_dir = run_rep.BENCH / "results" / a.run / f"rep{rep}"
        if (rep_dir / "summary.json").exists():
            print(f"[driver] rep{rep} already complete", flush=True)
            continue
        done = [rep_cost(costs, a.run, r) for r in a.reps
                if (run_rep.BENCH / "results" / a.run / f"rep{r}" / "summary.json").exists()]
        est = a.est if a.est is not None else (1.1 * max(done) if done else 0.0)
        need = est - rep_cost(costs, a.run, rep)
        if est and a.budget - budget.spent() < need:
            print(f"[driver] STOP before rep{rep}: ${a.budget - budget.spent():.2f} left, a rep needs ~${need:.2f}", flush=True)
            return 0
        for _ in range(a.max_waits + 1):
            errors = run_rep.Rep(a.run, rep, budget, a.lineages).run()
            if not errors:
                print(f"[driver] rep{rep} complete  cost=${rep_cost(costs, a.run, rep):.2f}  spent=${budget.spent():.2f}", flush=True)
                break
            limited = [e for e in errors.values() if "RateLimited" in e]
            if len(limited) != len(errors):
                print(f"[driver] STOP: non-rate-limit error in rep{rep}: {errors}", flush=True)
                return 2
            wait_for_reset(limited[0])
        else:
            print(f"[driver] STOP: rep{rep} still rate limited after {a.max_waits} waits", flush=True)
            return 2
    print(f"[driver] all done  spent=${budget.spent():.2f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
