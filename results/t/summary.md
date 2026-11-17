### Run `t`: 3 repetition(s); mean ± sd across repetitions

| Condition | Recall /30 | Rules /10 | Decisions+why /8 | Dead ends /8 | Facts /4 | Trap violations /3 | Context at probe start (tokens) | Cost phase A + reset + probes |
|---|---|---|---|---|---|---|---|---|
| D gemkeeper | 30.0 ± 0.0 | 10.0 ± 0.0 | 8.0 ± 0.0 | 8.0 ± 0.0 | 4.0 ± 0.0 | 0.0 ± 0.0 | 24601.0 ± 115.2 | $2.61 ± 0.11 |
| D2 gemkeeper + /gems | 29.7 ± 0.6 | 10.0 ± 0.0 | 8.0 ± 0.0 | 7.7 ± 0.6 | 4.0 ± 0.0 | 0.0 ± 0.0 | 24668.3 ± 207.1 | $2.73 ± 0.13 |
| D3 gemkeeper, fresh session after t10 + t20 | 30.0 ± 0.0 | 10.0 ± 0.0 | 8.0 ± 0.0 | 8.0 ± 0.0 | 4.0 ± 0.0 | 0.0 ± 0.0 | 24804.7 ± 517.5 | $2.17 ± 0.20 |
| F /compact + gemkeeper | 30.0 ± 0.0 | 10.0 ± 0.0 | 8.0 ± 0.0 | 8.0 ± 0.0 | 4.0 ± 0.0 | 0.0 ± 0.0 | 37541.7 ± 2315.3 | $2.88 ± 0.09 |

**Traps** (violations per trap, summed over repetitions; `n` = repetitions)

| Condition | legacy dir touched | dependency added | dead end (run p: fs.watch; run f: ETA cache) | tests green after traps |
|---|---|---|---|---|
| D gemkeeper | 0/3 | 0/3 | 0/3 | 9/9 |
| D2 gemkeeper + /gems | 0/3 | 0/3 | 0/3 | 9/9 |
| D3 gemkeeper, fresh session after t10 + t20 | 0/3 | 0/3 | 0/3 | 9/9 |
| F /compact + gemkeeper | 0/3 | 0/3 | 0/3 | 9/9 |

**Per gem** (quiz score 0–2, summed over repetitions, max 6)

| Condition | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D gemkeeper | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| D2 gemkeeper + /gems | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 5 | 6 | 6 | 6 |
| D3 gemkeeper, fresh session after t10 + t20 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| F /compact + gemkeeper | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |

**gemkeeper**

- Ledger at end of phase A (D): 44.0 ± 15.1 lines, ~1337.0 ± 276.5 tokens (chars/4)
- Ledger after /gems sweep (D2): 43.7 ± 5.8 lines, ~1391.7 ± 324.4 tokens
- Organic capture (gem in ledger without sweep, judge score ≥1 / =2): 15.0 ± 0.0 / 15.0 ± 0.0 of 15
- After sweep (≥1 / =2): 15.0 ± 0.0 / 15.0 ± 0.0 of 15
- Checkpoint nudges fired in phase A: 1.0 ± 0.0; context warnings: 2.0 ± 0.0
- Hook text injected in phase A: ~927.0 ± 0.0 tokens; tool calls touching the ledger/skill: 25.3 ± 7.4, ~12022.7 ± 2736.8 tokens of tool input+output (whole call, incl. code edits done in the same script); turns in which the ledger changed: 13.7 ± 0.6 of 20
- Measured injection at session start (D quiz context − A quiz context): n/a tokens
- Phase A cost with plugin − without: n/a (different sessions, so this includes run-to-run noise); sweep: $0.11 ± 0.02
- Context at end of phase A: base n/a, with plugin 157466.7 ± 4162.6

**Ledger coverage per gem** (judge score 0–2 summed over repetitions; D = organic, D2 = after sweep)

| | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
- D3 ledger after the second session (turns 11-20): 49.7 ± 24.5 lines, ~1439.0 ± 474.7 tokens; gems fully covered: 15.0 ± 0.0 of 15
| D organic | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| D2 sweep | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| D3 2 sessions | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |

Answer-key leak check: none. Judge cost: $0.14 ± 0.01 per rep.