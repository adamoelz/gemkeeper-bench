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