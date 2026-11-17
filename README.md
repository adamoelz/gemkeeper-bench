<p align="center">
  <img src="https://raw.githubusercontent.com/adamoelz/gemkeeper/main/.claude-plugin/icon.png" width="96" alt="gemkeeper">
</p>

<h1 align="center">gemkeeper-bench</h1>

<p align="center">
  <b>Does <a href="https://github.com/adamoelz/gemkeeper">gemkeeper</a> really keep what matters across a session reset?</b><br>
  A reproducible benchmark against <code>/compact</code>, a handoff summary, and no memory at all.<br>
  Negative and mixed results are reported as they are.
</p>

<p align="center">
  <a href="RESULTS.md">Results</a> ·
  <a href="#what-it-measures">What it measures</a> ·
  <a href="#conditions">Conditions</a> ·
  <a href="#run-it-yourself">Run it yourself</a> ·
  <a href="#limitations">Limitations</a>
</p>

---

## TL;DR

<p align="center"><img src="results/tokens.svg" width="820" alt="Tokens carried into the next session vs facts still known"></p>

- **gemkeeper 0.2.1 kept all 15 planted facts** after a reset into a fresh session (30/30, 3 of 3 runs),
  also across **two** fresh sessions, carrying **~2.6k tokens** into the next session: −85% vs `/compact`,
  −98% vs not resetting. 0.1.0 managed only 22/30 over two sessions.
- **`/compact` is a strong baseline** for recall (29.5/30 once, 29/30 twice) but only inside one session.
  A handoff summary lost the *why* and the dead ends (25/30). No memory: 0/30 and 2.5 of 3 behaviour traps
  fallen into; every condition with memory avoided all traps.
- **The cost of continuous capture**: about +11% during the work session with 0.2.1 (0.2.0: +21%), with a
  wide spread between runs. Details: [RESULTS.md](RESULTS.md).

<p align="center"><img src="results/benchmark.svg" width="800" alt="Recall after a session reset per condition"></p>

## What it measures

A scripted 20-turn session on a small TypeScript service (`scenario/project`, ~15 files with tests) does
real work: holiday-aware ETAs, tracking-number validation, ERP webhook signing and retries, request
logging, a store refactor. Along the way the "user" plants **15 gems** that can't be derived from the code:

| Category | # | Example |
|---|---|---|
| Rules | 5 | never touch `src/legacy/` (a sync job overwrites it) |
| Decisions + why | 4 | keep the JSON store, because ops' rsync diffs plain text |
| Dead ends | 4 | ETA memoization served stale ETAs after new events |
| Non-obvious facts | 2 | a flaky test that must be rerun, not fixed |

Noise turns (large log and fixture reads, full test output) bring the context to ~140k tokens. Then the
session is reset in different ways, and every condition gets the same probes, each as the first message
in its own fork or fresh session, on a clean copy of the workspace:

- **Quiz:** 15 questions, one per gem, answered from memory ("unknown" instead of guessing). A separate,
  **blind** `claude -p` judge scores each answer 0–2 against a hidden answer key (`answer_key/gems.json`):
  condition labels stripped, answers shuffled per question, the words gemkeeper/ledger/handoff masked.
- **Three behaviour traps**, run as real tasks and scored deterministically from the diff: a bug fix that
  tempts editing `src/legacy/`, a request to use `zod` (rule: no new dependencies), and a "make the list
  fast" task whose obvious fix is the planted ETA-caching dead end.

## Conditions

| | Reset | Carries over |
|---|---|---|
| **A** none | fresh session | nothing (lower bound) |
| **B** compact | built-in `/compact` after turn 20 | the compaction summary |
| **B2** compact twice | `/compact` after turn 10, turns 11–20 continue, `/compact` again | two nested summaries |
| **C** handoff | "write a handoff summary", pasted into a fresh session | the summary |
| **D** gemkeeper | fresh session, plugin loaded | the ledger, captured organically (no `/gems` call) |
| **D2** gemkeeper + sweep | `/gemkeeper:gems` before the reset | the swept ledger |
| **D3** gemkeeper, two sessions | fresh session after turn 10 *and* after turn 20 | only the ledger + the code |
| **F** compact + gemkeeper | `/compact`, plugin re-injects the ledger | summary + ledger |
| **E** no reset | the original session continues | everything (upper bound) |

## Versions

gemkeeper is a **git submodule** in `./gemkeeper`, pinned to the commit that was benchmarked last. Every
run records the exact plugin commit in `results/<run>/plugin.json`, and the harness refuses to run with
uncommitted plugin changes or to mix two plugin commits within one run.

| Run | What | gemkeeper | Account (`results/<run>/rep*/runner.json`) |
|---|---|---|---|
| `p` | pilot, first trap set | 0.1.0 (`b7952b3`) | 1 |
| `f` | hardened scenario, all baselines | 0.1.0 (`b7952b3`) | rep 1: 1, rep 2: 2 |
| `t` | tuned plugin, gemkeeper conditions only | 0.2.0 (`bc3a01c`) | rep 1: 1, reps 2–3: 2 |
| `u` | release candidate, gemkeeper conditions only | 0.2.1 (`8979dab`) | 2 |

## Run it yourself

Requirements: Claude Code CLI (logged in), Node 24+, Python 3.12+, bash (Git Bash on Windows).

```bash
git clone --recurse-submodules https://github.com/adamoelz/gemkeeper-bench
cd gemkeeper-bench
git -C gemkeeper checkout <commit from results/<run>/plugin.json>   # the plugin version to measure

python harness/run_all.py --run myrun --reps 1 2 3 --budget 40       # waits out usage limits, resumable
python harness/summarize.py --run myrun                              # tables -> results/myrun/summary.md
python harness/make_chart.py --gk-run u --gk-label "gemkeeper 0.2.1"  # results/benchmark.svg
python harness/make_token_chart.py --gk-run u                        # results/tokens.svg
```

- `--budget` is a hard cap in USD (API-equivalent `total_cost_usd`) over everything in `results/costs.jsonl`.
  A step that already has a result file is skipped, so a crashed or rate-limited rep simply resumes.
- `--lineages gk` runs only the gemkeeper side (D, D2, D3, F) against baselines from an earlier run.
- Env: `BENCH_MODEL` (default `sonnet`), `BENCH_EFFORT` (`medium`), `BENCH_CLAUDE_CONFIG_DIR`
  (which Claude Code config/account runs the sessions; one rep never switches it).
- One full rep costs about $10 (API-equivalent); a gemkeeper-only rep about $6.

## Layout

```
harness/      run_rep.py (one repetition), run_all.py (driver), cc.py (claude -p wrapper),
              score.py (trap checks + blind judge), summarize.py, workspace.py, settings.bench.json
scenario/     project/ (the toy service), phase_a.json (20 user turns), probe.json (quiz + traps)
answer_key/   gems.json (never shown to the model under test)
results/      <run>/rep<N>/*.json (raw results), logs/*.jsonl.gz (full event streams), summary.md
gemkeeper/    the plugin under test (submodule)
```

## Isolation

- All sessions use `harness/settings.bench.json`: auto-memory off, a claude.ai-synced copy of the gems skill
  hidden, so nothing but the condition's own mechanism carries context across the reset. The plugin is
  loaded only via `--plugin-dir` in D, D2, D3 and F.
- claude.ai connectors are disabled (`ENABLE_CLAUDEAI_MCP_SERVERS=false`), the `Agent` tool is off, and child
  processes get a clean environment with explicit `--model` / `--effort`.
- Every event log is checked for accesses to the answer key (none so far).

## Limitations

- **One synthetic scenario.** Real sessions are messier, and the gems here are stated quite explicitly.
- **Small n** (0.1.0: 1, baselines: 2, 0.2.0 and 0.2.1: 3) and an **LLM judge** (blind, but still an LLM).
- The 0.2.0 trigger words were written before checking them against the scenario; they fire on 11 of the 12
  turns that plant a gem. Still, the scenario's phrasing ("never", "because", "tried") suits them well.
- Two Claude accounts were used (usage limits). They were aligned (same CLI, model, tools, no connectors),
  but account 1 had three extra user skills installed.
- Costs are API-equivalent numbers reported by the CLI, not what a subscription actually bills.

## License

MIT, like gemkeeper.
