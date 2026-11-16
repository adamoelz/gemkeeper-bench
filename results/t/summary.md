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