<p align="center">
  <img src="https://raw.githubusercontent.com/adamoelz/gemkeeper/main/.claude-plugin/icon.png" width="96" alt="gemkeeper">
</p>

<h1 align="center">gemkeeper-bench</h1>

<p align="center">
  The benchmark behind <a href="https://github.com/adamoelz/gemkeeper">gemkeeper</a>: does a fresh Claude Code
  session still know what matters after a reset?<br>
  <b>Results: <a href="RESULTS.md">RESULTS.md</a></b>
</p>

---

## How it works

A scripted 20-turn session on a small TypeScript service (`scenario/project`) does real work and plants
15 facts that can't be read from the code: 5 rules, 4 decisions with their reasons, 4 dead ends, 2 gotchas.
Then the session is reset in one of these ways:

| | Reset |
|---|---|
| **A** | none, fresh session (`/clear`) |
| **B** / **B2** | `/compact` once / twice (after turn 10 and 20) |
| **C** | handoff summary pasted into a fresh session |
| **D** / **D2** | gemkeeper, fresh session / after a `/gems` sweep |
| **D3** | gemkeeper, fresh session after turn 10 *and* turn 20 |
| **F** | `/compact` with gemkeeper |
| **E** | no reset (upper bound) |

Every condition gets the same probes in its own fork or fresh session:

- **Quiz:** one question per fact, scored 0–2 by a blind `claude -p` judge against `answer_key/gems.json`.
- **Three traps** run as real tasks and scored from the diff: touching `src/legacy/`, adding a dependency,
  taking a planted dead end.

Auto-memory, claude.ai connectors and the `Agent` tool are off; every log is checked for answer-key access.

## Run it

Requirements: Claude Code CLI (logged in), Node 24+, Python 3.12+, bash (Git Bash on Windows).

```bash
git clone --recurse-submodules https://github.com/adamoelz/gemkeeper-bench && cd gemkeeper-bench
git -C gemkeeper checkout <commit from results/<run>/plugin.json>    # plugin version to measure

python harness/run_all.py --run myrun --reps 1 2 3 --budget 40        # resumable, waits out usage limits
python harness/summarize.py --run myrun                               # tables -> results/myrun/summary.md
python harness/make_charts.py --gk-run myrun --gk-version <version>   # results/*.svg
```

`--lineages gk` measures only the gemkeeper side against the baselines of an earlier run. A full rep costs
about $10 (API-equivalent), a gemkeeper-only rep about $5. Env: `BENCH_MODEL` (`sonnet`), `BENCH_EFFORT`
(`medium`), `BENCH_CLAUDE_CONFIG_DIR` (which Claude config/account runs the sessions).

## Versions

`gemkeeper/` is a git submodule pinned to the last measured plugin commit. Each run records its plugin commit
in `results/<run>/plugin.json` and the account per rep in `runner.json`; the harness refuses uncommitted
plugin changes and mixing commits within a run.

```
harness/      run_all.py, run_rep.py, cc.py (claude -p), score.py, summarize.py, make_charts.py
scenario/     the toy project, the 20 user turns, quiz and traps
answer_key/   gems.json (never shown to the model under test)
results/      raw results and logs per run and rep
```

## License

MIT
