# Results

<p align="center"><img src="results/benchmark.svg" width="800" alt="Recall after a session reset per condition"></p>

<p align="center"><img src="results/tokens.svg" width="820" alt="Tokens carried into the next session vs facts still known"></p>

**Bottom line.** With gemkeeper 0.2.1, a fresh session knew all 15 planted facts (30/30 in 3 of 3
repetitions), also after **two** resets into fresh sessions, while carrying only **~2.6k tokens** into the
next session: 85% less than `/compact` (~17k), 98% less than not resetting at all, and a bit less than a
handoff summary that lost the *why* and the dead ends (25/30). `/compact` is a strong baseline for recall
(29–29.5) but only lives inside one session. gemkeeper 0.1.0 did **not** hold up over two sessions (22/30).
The price of the continuous capture: about **+11% cost** during the work session with 0.2.1 (0.2.0: +21%),
with a wide spread between runs.

Model: Sonnet (`claude-sonnet-5-5`, effort medium) via `claude -p`, Claude Code 2.1.325. Costs are the
API-equivalent `total_cost_usd` reported by the CLI.

## Main table

Mean ± sd over repetitions (n). Recall: 15 quiz questions scored 0–2 by a blind judge.
Context: tokens in the first request after the reset (system prompt + whatever carried over).
Cost: phase A + reset + the four probes, per condition.

| Condition | gemkeeper | n | Recall /30 | Rules /10 | Decisions /8 | Dead ends /8 | Facts /4 | Traps /3 | Context | Cost |
|---|---|---|---|---|---|---|---|---|---|---|
| A none (`/clear`) | – | 2 | 0.0 | 0 | 0 | 0 | 0 | **2.5** | 21.8k | $2.28 |
| B `/compact` | – | 2 | 29.5 ± 0.7 | 10 | 8 | 7.5 | 4 | 0 | 39.0k | $2.52 |
| B2 `/compact` twice | – | 2 | 29.0 ± 0.0 | 10 | 7.5 | 7.5 | 4 | 0 | 33.2k | $2.49 |
| C handoff summary | – | 2 | 25.0 ± 0.0 | 10 | 6.5 | **4.5** | 4 | 0 | 24.8k | $2.24 |
| D gemkeeper | 0.1.0 | 1 | 28 | 10 | 8 | 8 | **2** | 0 | 24.8k | $2.28 |
| D2 gemkeeper + `/gems` | 0.1.0 | 1 | 30 | 10 | 8 | 8 | 4 | 0 | 24.9k | $2.35 |
| D3 gemkeeper, 2 fresh sessions | 0.1.0 | 1 | **22** | **6** | 6 | 8 | 2 | 0 | 24.2k | $2.36 |
| D gemkeeper | 0.2.0 | 3 | **30.0 ± 0.0** | 10 | 8 | 8 | 4 | 0 | 24.6k | $2.61 |
| D2 gemkeeper + `/gems` | 0.2.0 | 3 | 29.7 ± 0.6 | 10 | 8 | 7.7 | 4 | 0 | 24.7k | $2.73 |
| D3 gemkeeper, 2 fresh sessions | 0.2.0 | 3 | **30.0 ± 0.0** | 10 | 8 | 8 | 4 | 0 | 24.8k | $2.17 |
| F `/compact` + gemkeeper | 0.2.0 | 3 | 30.0 ± 0.0 | 10 | 8 | 8 | 4 | 0 | 37.5k | $2.88 |
| D gemkeeper | **0.2.1** | 3 | **30.0 ± 0.0** | 10 | 8 | 8 | 4 | 0 | 24.4k | $2.44 |
| D2 gemkeeper + `/gems` | 0.2.1 | 3 | 29.3 ± 1.2 | 10 | 8 | 7.3 | 4 | 0 | 24.7k | $2.47 |
| D3 gemkeeper, 2 fresh sessions | **0.2.1** | 3 | **30.0 ± 0.0** | 10 | 8 | 8 | 4 | 0 | 24.0k | $2.14 |
| F `/compact` + gemkeeper | 0.2.1 | 3 | 29.7 ± 0.6 | 10 | 8 | 7.7 | 4 | 0 | 37.9k | $2.63 |
| E no reset (upper bound) | – | 2 | 29.0 ± 0.0 | 10 | 8 | 7 | 4 | 0 | 144.9k | $2.18 |

Baselines and gemkeeper 0.1.0 come from run `f`, gemkeeper 0.2.0 from run `t`, 0.2.1 from run `u` (same
scenario, probes and judge; `t` and `u` re-run only the gemkeeper side). Generated per-run tables:
`results/<run>/summary.md`, raw data in `results/<run>/rep<N>/`. The only items 0.2.x ever missed were the
ETA-memoization and fs.watch dead ends, and only with the explicit `/gems` sweep or `/compact` (D2, F).

### Behaviour traps

| Condition | `src/legacy/` touched | dependency added (`zod`) | dead end (ETA cache) | tests green after |
|---|---|---|---|---|
| A none | 2/2 | 2/2 | 1/2 | 6/6 |
| every other condition (B, B2, C, D, D2, D3, F, E; all versions) | 0 | 0 | 0 | all |

The traps discriminate (no memory falls into them), but every condition with *any* memory avoided all
three. They separate "remembers" from "doesn't", not one memory mechanism from another.

### gemkeeper internals

| | 0.1.0 (n=1) | 0.2.0 (n=3) | 0.2.1 (n=3) |
|---|---|---|---|
| Gems fully in the ledger without `/gems` (judge) | 14 / 15 | **15 / 15** | 14.7 / 15 (15 / 15 at least partly) |
| Gems fully in the ledger after the 2nd fresh session (D3) | 11 / 15 | **15 / 15** | **15 / 15** |
| Ledger size, end of session (D) | 37 lines, ~1.4k tokens | 44 ± 15 lines, ~1.3k tokens | 35 ± 4 lines, ~1.3k tokens |
| Ledger size after 2nd session (D3) | 35 lines, ~1.0k tokens | 50 ± 25 lines (25–74), ~1.4k tokens | **34 ± 3 lines, ~1.0k tokens** |
| Turns in which the ledger changed (of 20) | 13 | 13.7 | 13.7 |
| Tool calls touching the ledger (mostly Bash edits) | 25, ~14k tokens | 25 ± 7, ~12k tokens | 22 ± 7, ~12k tokens |
| Hook text injected during the session | ~350 tokens | ~930 tokens | ~1.3k tokens |
| Model steps in phase A (base: 77–90) | 77 | 99–108 | 85–108 |
| Phase A cost (base without plugin: $1.78, n=2) | $1.76 (−1%) | $2.15 (+21%) | **$1.98 (+11%)**, range $1.70–2.29 |
| Context at end of phase A (base: 142k) | 139k | 157k (+10%) | 150k (+5%) |
| `/gems` sweep | – | $0.11 | $0.10 |

Where the overhead comes from: each gem check makes Claude save the gem as its **own model step** before the
work, and every extra step re-reads the whole context (0.2.0: ~20 extra steps per 20 turns, cache reads
6M → 8.5M tokens). 0.2.1 asks for the save as a parallel tool call next to the first action; in a small
test that removed the extra step, but in the full scenario most saves stayed separate steps (rep 1: 24 of
25). The spread between runs ($1.70–2.29) is as large as the effect, so n=3 can't pin it down further.

## What was forgotten (failure examples)

- **Handoff summary (C)** lost the reasons and dead ends, not the rules: "where does the HMAC signature go
  and what failed" (header approach stripped by the gateway), "has ETA memoization been tried" (scored 0
  in one rep), the reason behind ATP-only tracking validation, the fs.watch dead end, the reason for
  hardcoded holidays.
- **gemkeeper 0.1.0, one session (D)** never wrote down the side remark *"Heads-up: the test 'emits webhook
  on delivered' is flaky, rerun once, don't fix it"* → answered "unknown".
- **gemkeeper 0.1.0, two sessions (D3)**: the fresh second session (turns 11–20) left the ledger unchanged
  in turns 12–15, so the GET /shipments/:id freeze (turn 13), the GDPR logging rule (turn 14) and the
  keep-JSON-not-SQLite decision (turn 15) were lost, plus the flaky test → four "unknown".
- **`/compact`, twice or once**: only partial credit on the ETA-memoization dead end or the tracking-
  validation reason. The memoization item was the hardest overall: even the no-reset session (E) got
  partial credit on it in both reps.

## Pilot (run `p`, first trap set)

One repetition with gemkeeper 0.1.0 and the first trap set: A 0, B 30, C 26, D 29, D2 30, E 30. Two of the
three original traps (an xlsx export that tempts a dependency; config hot reload with the fs.watch dead
end) were avoided even with no memory, because the code base made the right choice obvious. They were
replaced before run `f`, which also shortened phase A from ~187k to ~140k tokens and added B2, D3 and F.

## Limitations

- **One synthetic scenario** with gems stated quite explicitly ("never", "because", "tried"). Real sessions
  are messier; the 0.2.0 trigger words suit this phrasing well (they were written before checking, and fire
  on 11 of the 12 gem-planting turns).
- **Small n**: 0.1.0 results are n=1, baselines n=2, 0.2.0 n=3. Ceiling effects: most memory conditions sit
  at 29–30, so the quiz can't rank them further.
- **LLM judge**, blind and shuffled, but an LLM; the per-gem scores are in the raw results.
- **Two accounts** (usage limits): account 1 ran `p`, `f` rep 1, `t` rep 1; account 2 the rest. Same CLI,
  model, tools, no connectors; account 1 had three extra user skills (`caveman`, `find-skills`,
  `untangle-codebase`). One `t` rep was aborted by the account switch and one by an API hang; both were
  rerun from scratch (`results/t/_aborted_rep2_account1/` kept for transparency).
- In `-p` mode a Stop-hook block replaces the final message of the turn; the harness scores the assistant
  text with the most parsed answers, so the quiz is unaffected, but scripted users of gemkeeper would see it.

## Budget

Total spent: **$59.61** API-equivalent (cap raised to $62): CLI checks $0.60, pilot $8.94, run `f` $15.86,
run `t` $19.48 (incl. two aborted reps), run `u` $14.73. One full rep costs ~$10, a gemkeeper-only rep ~$6.

## What to change in the skill and hooks next (ranked by expected impact)

Done and measured: gem check by content (0.2.0), "the ledger is not read-only" at session start (0.2.0),
a sweep that walks every user message (0.2.0), one topic = one bullet (0.2.0), no gem check on question
sentences (0.2.1), Stop hook removed (0.2.1: it never caught a real miss, only fired on questions).

1. **Make the save a side effect, not a step.** The remaining overhead (+11%, wide spread) is the extra model
   step per saved gem. Options: let the UserPromptSubmit hook append a stub the model only has to fill in,
   or batch the turn's gems into the last tool call of the turn. Measure with model steps, not only cost.
2. **A messier scenario.** The gems here are stated explicitly ("never", "because", "tried"); real users
   are vaguer. A second scenario with implicit gems would show how much the keyword trigger misses.
3. **Bound the ledger size** with a prune step above ~50 lines (0.2.1 stayed at 34–38 lines here, 0.2.0
   varied 25–74).
4. **Keep the README honest**: `/compact` keeps the facts (29–30/30); gemkeeper's edge is surviving `/clear`
   and new sessions with ~2.6k instead of ~17k tokens, and beating a handoff summary on the *why*.
