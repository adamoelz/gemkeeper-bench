### Run `i`: 1 repetition(s); mean ± sd across repetitions

| Condition | Recall /30 | Rules /10 | Decisions+why /8 | Dead ends /8 | Facts /4 | Trap violations /3 | Context at probe start (tokens) | Cost phase A + reset + probes |
|---|---|---|---|---|---|---|---|---|
| A none (/clear) | 0 | 0 | 0 | 0 | 0 | 3 | 21829 | $2.29 |
| B /compact | 29 | 10 | 8 | 7 | 4 | 0 | 41171 | $2.59 |
| B2 /compact twice (after t10 + t20) | 30 | 10 | 8 | 8 | 4 | 0 | 40490 | $3.16 |
| C handoff | 26 | 10 | 6 | 6 | 4 | 0 | 25108 | $2.20 |
| C2 handoff skill (mattpocock) | 26 | 10 | 7 | 6 | 3 | 0 | 24076 | $2.75 |
| D gemkeeper | 29 | 10 | 8 | 7 | 4 | 0 | 25533 | $2.69 |
| D2 gemkeeper + /gems | 30 | 10 | 8 | 8 | 4 | 0 | 25329 | $2.80 |
| D3 gemkeeper, fresh session after t10 + t20 | 30 | 10 | 8 | 8 | 4 | 0 | 24336 | $2.15 |
| F /compact + gemkeeper | 29 | 10 | 8 | 7 | 4 | 0 | 46560 | $3.15 |
| E no reset | 28 | 10 | 8 | 6 | 4 | 0 | 143487 | $2.23 |

**Traps** (violations per trap, summed over repetitions; `n` = repetitions)

| Condition | legacy dir touched | dependency added | dead end (run p: fs.watch; run f: ETA cache) | tests green after traps |
|---|---|---|---|---|
| A none (/clear) | 1/1 | 1/1 | 1/1 | 3/3 |
| B /compact | 0/1 | 0/1 | 0/1 | 3/3 |
| B2 /compact twice (after t10 + t20) | 0/1 | 0/1 | 0/1 | 3/3 |
| C handoff | 0/1 | 0/1 | 0/1 | 3/3 |
| C2 handoff skill (mattpocock) | 0/1 | 0/1 | 0/1 | 3/3 |
| D gemkeeper | 0/1 | 0/1 | 0/1 | 3/3 |
| D2 gemkeeper + /gems | 0/1 | 0/1 | 0/1 | 3/3 |
| D3 gemkeeper, fresh session after t10 + t20 | 0/1 | 0/1 | 0/1 | 3/3 |
| F /compact + gemkeeper | 0/1 | 0/1 | 0/1 | 3/3 |
| E no reset | 0/1 | 0/1 | 0/1 | 3/3 |

**Per gem** (quiz score 0–2, summed over repetitions, max 2)

| Condition | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A none (/clear) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| B /compact | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 |
| B2 /compact twice (after t10 + t20) | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| C handoff | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 2 |
| C2 handoff skill (mattpocock) | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 |
| D gemkeeper | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 |
| D2 gemkeeper + /gems | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| D3 gemkeeper, fresh session after t10 + t20 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| F /compact + gemkeeper | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 |
| E no reset | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 0 | 2 | 2 | 2 |

**gemkeeper**

- Ledger at end of phase A (D): 48 lines, ~1961 tokens (chars/4)
- Ledger after /gems sweep (D2): 48 lines, ~1823 tokens
- Organic capture (gem in ledger without sweep, judge score ≥1 / =2): 15 / 14 of 15
- After sweep (≥1 / =2): 15 / 14 of 15
- Checkpoint nudges fired in phase A: 3; context warnings: 3
- Hook text injected in phase A: ~402 tokens; tool calls touching the ledger/skill: 26, ~12350 tokens of tool input+output (whole call, incl. code edits done in the same script); turns in which the ledger changed: 15 of 20
- Measured injection at session start (D quiz context − A quiz context): 3704 tokens
- Phase A cost with plugin − without: $0.51 (different sessions, so this includes run-to-run noise); sweep: $0.09
- Context at end of phase A: base 142145, with plugin 165098

**Ledger coverage per gem** (judge score 0–2 summed over repetitions; D = organic, D2 = after sweep)

| | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
- D3 ledger after the second session (turns 11-20): 44 lines, ~1182 tokens; gems fully covered: 15 of 15
| D organic | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 |
| D2 sweep | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 |
| D3 2 sessions | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |

Answer-key leak check: none. Judge cost: $0.21 per rep.