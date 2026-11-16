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