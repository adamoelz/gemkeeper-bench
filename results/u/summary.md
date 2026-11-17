### Run `u`: 3 repetition(s); mean ± sd across repetitions

| Condition | Recall /30 | Rules /10 | Decisions+why /8 | Dead ends /8 | Facts /4 | Trap violations /3 | Context at probe start (tokens) | Cost phase A + reset + probes |
|---|---|---|---|---|---|---|---|---|
| D gemkeeper | 30.0 ± 0.0 | 10.0 ± 0.0 | 8.0 ± 0.0 | 8.0 ± 0.0 | 4.0 ± 0.0 | 0.0 ± 0.0 | 24435.7 ± 323.6 | $2.44 ± 0.24 |
| D2 gemkeeper + /gems | 29.3 ± 1.2 | 10.0 ± 0.0 | 8.0 ± 0.0 | 7.3 ± 1.2 | 4.0 ± 0.0 | 0.0 ± 0.0 | 24714.7 ± 118.4 | $2.47 ± 0.25 |
| D3 gemkeeper, fresh session after t10 + t20 | 30.0 ± 0.0 | 10.0 ± 0.0 | 8.0 ± 0.0 | 8.0 ± 0.0 | 4.0 ± 0.0 | 0.0 ± 0.0 | 23979.7 ± 246.4 | $2.14 ± 0.15 |
| F /compact + gemkeeper | 29.7 ± 0.6 | 10.0 ± 0.0 | 8.0 ± 0.0 | 7.7 ± 0.6 | 4.0 ± 0.0 | 0.0 ± 0.0 | 37913.0 ± 1165.3 | $2.63 ± 0.31 |

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
| D2 gemkeeper + /gems | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 5 | 6 | 5 | 6 | 6 | 6 |
| D3 gemkeeper, fresh session after t10 + t20 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| F /compact + gemkeeper | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 5 | 6 | 6 | 6 |

**gemkeeper**

- Ledger at end of phase A (D): 35.0 ± 4.4 lines, ~1297.7 ± 176.5 tokens (chars/4)
- Ledger after /gems sweep (D2): 42.0 ± 7.8 lines, ~1466.3 ± 85.6 tokens
- Organic capture (gem in ledger without sweep, judge score ≥1 / =2): 15.0 ± 0.0 / 14.7 ± 0.6 of 15
- After sweep (≥1 / =2): 15.0 ± 0.0 / 15.0 ± 0.0 of 15
- Checkpoint nudges fired in phase A: 1.0 ± 0.0; context warnings: 2.0 ± 0.0
- Hook text injected in phase A: ~1274.0 ± 0.0 tokens; tool calls touching the ledger/skill: 22.3 ± 7.2, ~11710.3 ± 420.7 tokens of tool input+output (whole call, incl. code edits done in the same script); turns in which the ledger changed: 13.7 ± 0.6 of 20
- Measured injection at session start (D quiz context − A quiz context): n/a tokens
- Phase A cost with plugin − without: n/a (different sessions, so this includes run-to-run noise); sweep: $0.10 ± 0.02
- Context at end of phase A: base n/a, with plugin 150818.7 ± 10116.4

**Ledger coverage per gem** (judge score 0–2 summed over repetitions; D = organic, D2 = after sweep)

| | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
- D3 ledger after the second session (turns 11-20): 34.3 ± 2.5 lines, ~1020.0 ± 151.4 tokens; gems fully covered: 15.0 ± 0.0 of 15
| D organic | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 5 | 6 | 6 | 6 |
| D2 sweep | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| D3 2 sessions | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |

Answer-key leak check: none. Judge cost: $0.14 ± 0.01 per rep.