# Results (interim)

> One repetition per run so far (repetitions 2–3 are running). Generated tables per run follow;
> the final version of this file will add means ± spread, failure examples and the change list for the skill.

## Headline so far

- Without any memory (A) the model fails every trap and knows none of the 15 gems: the scenario and traps work.
- `/compact` (B) kept 30/30 once and 29/30 twice (B2). It is a strong baseline here.
- The handoff summary (C) lost the *why* of several decisions and dead ends (25/30).
- gemkeeper 0.1.0: 28/30 in one fresh session (D), but only 22/30 across two fresh sessions (D3): the
  second session stopped adding gems, and a side remark (the flaky test) was never captured.
- gemkeeper 0.2.0 (gem check on the user's message + Stop-hook safety net + 'the ledger is not read-only'
  at session start): 30/30 in D, D2, D3 and F, with a smaller ledger (25 lines, ~930 tokens after D3).
- No gemkeeper condition fell into a trap; neither did B, C or E.

## Run `f`: Hardened scenario, all baselines, gemkeeper 0.1.0

### Run `f`: 1 repetition(s); mean ± sd across repetitions

| Condition | Recall /30 | Rules /10 | Decisions+why /8 | Dead ends /8 | Facts /4 | Trap violations /3 | Context at probe start (tokens) | Cost phase A + reset + probes |
|---|---|---|---|---|---|---|---|---|
| A none (/clear) | 0 | 0 | 0 | 0 | 0 | 3 | 21877 | $2.28 |
| B /compact | 30 | 10 | 8 | 8 | 4 | 0 | 35053 | $2.47 |
| B2 /compact twice (after t10 + t20) | 29 | 10 | 7 | 8 | 4 | 0 | 33143 | $2.68 |
| C handoff | 25 | 10 | 6 | 5 | 4 | 0 | 24813 | $2.25 |
| D gemkeeper | 28 | 10 | 8 | 8 | 2 | 0 | 24845 | $2.28 |
| D2 gemkeeper + /gems | 30 | 10 | 8 | 8 | 4 | 0 | 24919 | $2.35 |
| D3 gemkeeper, fresh session after t10 + t20 | 22 | 6 | 6 | 8 | 2 | 0 | 24222 | $2.36 |
| E no reset | 29 | 10 | 8 | 7 | 4 | 0 | 142044 | $2.28 |

**Traps** (violations per trap, summed over repetitions; `n` = repetitions)

| Condition | legacy dir touched | dependency added | dead end (run p: fs.watch; run f: ETA cache) | tests green after traps |
|---|---|---|---|---|
| A none (/clear) | 1/1 | 1/1 | 1/1 | 3/3 |
| B /compact | 0/1 | 0/1 | 0/1 | 3/3 |
| B2 /compact twice (after t10 + t20) | 0/1 | 0/1 | 0/1 | 3/3 |
| C handoff | 0/1 | 0/1 | 0/1 | 3/3 |
| D gemkeeper | 0/1 | 0/1 | 0/1 | 3/3 |
| D2 gemkeeper + /gems | 0/1 | 0/1 | 0/1 | 3/3 |
| D3 gemkeeper, fresh session after t10 + t20 | 0/1 | 0/1 | 0/1 | 3/3 |
| E no reset | 0/1 | 0/1 | 0/1 | 3/3 |

**Per gem** (quiz score 0–2, summed over repetitions, max 2)

| Condition | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A none (/clear) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| B /compact | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| B2 /compact twice (after t10 + t20) | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 |
| C handoff | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 2 |
| D gemkeeper | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 0 |
| D2 gemkeeper + /gems | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| D3 gemkeeper, fresh session after t10 + t20 | 2 | 2 | 0 | 2 | 0 | 2 | 2 | 0 | 2 | 2 | 2 | 2 | 2 | 2 | 0 |
| E no reset | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 |

**gemkeeper**

- Ledger at end of phase A (D): 37 lines, ~1419 tokens (chars/4)
- Ledger after /gems sweep (D2): 37 lines, ~1472 tokens
- Organic capture (gem in ledger without sweep, judge score ≥1 / =2): 14 / 14 of 15
- After sweep (≥1 / =2): 15 / 15 of 15
- Checkpoint nudges fired in phase A: 3; context warnings: 2
- Hook text injected in phase A: ~347 tokens; tool calls touching the ledger/skill: 25, ~13890 tokens of tool input+output (whole call, incl. code edits done in the same script); turns in which the ledger changed: 13 of 20
- Measured injection at session start (D quiz context − A quiz context): 2968 tokens
- Phase A cost with plugin − without: $0.02 (different sessions, so this includes run-to-run noise); sweep: $0.08
- Context at end of phase A: base 139818, with plugin 139372

**Ledger coverage per gem** (judge score 0–2 summed over repetitions; D = organic, D2 = after sweep)

| | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
- D3 ledger after the second session (turns 11-20): 35 lines, ~1022 tokens; gems fully covered: 11 of 15
| D organic | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 0 |
| D2 sweep | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| D3 2 sessions | 2 | 2 | 0 | 2 | 0 | 2 | 2 | 0 | 2 | 2 | 2 | 2 | 2 | 2 | 0 |

Answer-key leak check: none. Judge cost: $0.18 per rep.

## Run `t`: Tuned plugin, gemkeeper 0.2.0, gemkeeper conditions only

### Run `t`: 1 repetition(s); mean ± sd across repetitions

| Condition | Recall /30 | Rules /10 | Decisions+why /8 | Dead ends /8 | Facts /4 | Trap violations /3 | Context at probe start (tokens) | Cost phase A + reset + probes |
|---|---|---|---|---|---|---|---|---|
| D gemkeeper | 30 | 10 | 8 | 8 | 4 | 0 | 24468 | $2.71 |
| D2 gemkeeper + /gems | 30 | 10 | 8 | 8 | 4 | 0 | 24432 | $2.82 |
| D3 gemkeeper, fresh session after t10 + t20 | 30 | 10 | 8 | 8 | 4 | 0 | 24290 | $2.26 |
| F /compact + gemkeeper | 30 | 10 | 8 | 8 | 4 | 0 | 40174 | $2.98 |

**Traps** (violations per trap, summed over repetitions; `n` = repetitions)

| Condition | legacy dir touched | dependency added | dead end (run p: fs.watch; run f: ETA cache) | tests green after traps |
|---|---|---|---|---|
| D gemkeeper | 0/1 | 0/1 | 0/1 | 3/3 |
| D2 gemkeeper + /gems | 0/1 | 0/1 | 0/1 | 3/3 |
| D3 gemkeeper, fresh session after t10 + t20 | 0/1 | 0/1 | 0/1 | 3/3 |
| F /compact + gemkeeper | 0/1 | 0/1 | 0/1 | 3/3 |

**Per gem** (quiz score 0–2, summed over repetitions, max 2)

| Condition | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D gemkeeper | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| D2 gemkeeper + /gems | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| D3 gemkeeper, fresh session after t10 + t20 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| F /compact + gemkeeper | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |

**gemkeeper**

- Ledger at end of phase A (D): 27 lines, ~1024 tokens (chars/4)
- Ledger after /gems sweep (D2): 37 lines, ~1027 tokens
- Organic capture (gem in ledger without sweep, judge score ≥1 / =2): 15 / 15 of 15
- After sweep (≥1 / =2): 15 / 15 of 15
- Checkpoint nudges fired in phase A: 1; context warnings: 2
- Hook text injected in phase A: ~927 tokens; tool calls touching the ledger/skill: 17, ~9130 tokens of tool input+output (whole call, incl. code edits done in the same script); turns in which the ledger changed: 13 of 20
- Measured injection at session start (D quiz context − A quiz context): n/a tokens
- Phase A cost with plugin − without: n/a (different sessions, so this includes run-to-run noise); sweep: $0.11
- Context at end of phase A: base n/a, with plugin 162045

**Ledger coverage per gem** (judge score 0–2 summed over repetitions; D = organic, D2 = after sweep)

| | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
- D3 ledger after the second session (turns 11-20): 25 lines, ~929 tokens; gems fully covered: 15 of 15
| D organic | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| D2 sweep | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| D3 2 sessions | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |

Answer-key leak check: none. Judge cost: $0.14 per rep.

## Run `p`: Pilot (first trap set; two traps turned out not to discriminate and were replaced in run f)

### Run `p`: 1 repetition(s); mean ± sd across repetitions

| Condition | Recall /30 | Rules /10 | Decisions+why /8 | Dead ends /8 | Facts /4 | Trap violations /3 | Context at probe start (tokens) | Cost phase A + reset + probes |
|---|---|---|---|---|---|---|---|---|
| A none (/clear) | 0 | 0 | 0 | 0 | 0 | 1 | 21848 | $2.51 |
| B /compact | 30 | 10 | 8 | 8 | 4 | 0 | 38608 | $3.05 |
| C handoff | 26 | 9 | 7 | 6 | 4 | 0 | 25451 | $2.79 |
| D gemkeeper | 29 | 9 | 8 | 8 | 4 | 0 | 26807 | $2.72 |
| D2 gemkeeper + /gems | 30 | 10 | 8 | 8 | 4 | 0 | 24933 | $2.89 |
| E no reset | 30 | 10 | 8 | 8 | 4 | 0 | 187473 | $2.79 |

**Traps** (violations per trap, summed over repetitions; `n` = repetitions)

| Condition | legacy dir touched | dependency added | dead end (run p: fs.watch; run f: ETA cache) | tests green after traps |
|---|---|---|---|---|
| A none (/clear) | 1/1 | 0/1 | 0/1 | 3/3 |
| B /compact | 0/1 | 0/1 | 0/1 | 3/3 |
| C handoff | 0/1 | 0/1 | 0/1 | 3/3 |
| D gemkeeper | 0/1 | 0/1 | 0/1 | 3/3 |
| D2 gemkeeper + /gems | 0/1 | 0/1 | 0/1 | 3/3 |
| E no reset | 0/1 | 0/1 | 0/1 | 3/3 |

**Per gem** (quiz score 0–2, summed over repetitions, max 2)

| Condition | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A none (/clear) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| B /compact | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| C handoff | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 2 |
| D gemkeeper | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| D2 gemkeeper + /gems | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| E no reset | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |

**gemkeeper**

- Ledger at end of phase A (D): 52 lines, ~1589 tokens (chars/4)
- Ledger after /gems sweep (D2): 49 lines, ~1420 tokens
- Organic capture (gem in ledger without sweep, judge score ≥1 / =2): 15 / 15 of 15
- After sweep (≥1 / =2): 15 / 15 of 15
- Checkpoint nudges fired in phase A: 3; context warnings: 2
- Hook text injected in phase A: ~347 tokens; tool calls touching the ledger/skill: 18, ~11720 tokens of tool input+output (whole call, incl. code edits done in the same script); turns in which the ledger changed: 14 of 20
- Measured injection at session start (D quiz context − A quiz context): 4959 tokens
- Phase A cost with plugin − without: $0.02 (different sessions, so this includes run-to-run noise); sweep: $0.11
- Context at end of phase A: base 185197, with plugin 177341

**Ledger coverage per gem** (judge score 0–2 summed over repetitions; D = organic, D2 = after sweep)

| | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D organic | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| D2 sweep | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |

Answer-key leak check: none. Judge cost: $0.13 per rep.

