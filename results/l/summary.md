### Run `l`: 3 repetition(s); mean ± sd across repetitions

| Condition | Recall /30 | Rules /10 | Decisions+why /8 | Dead ends /8 | Facts /4 | Trap violations /3 | Context at probe start (tokens) | Cost phase A + reset + probes |
|---|---|---|---|---|---|---|---|---|
| DL skill-only + /gemkeeper:resume | 29.3 ± 1.2 | 10.0 ± 0.0 | 8.0 ± 0.0 | 7.3 ± 1.2 | 4.0 ± 0.0 | 0.0 ± 0.0 | 27359.7 ± 1500.1 | $2.28 ± 0.21 |
| DL3 skill-only, 2 fresh sessions + /resume | 30.0 ± 0.0 | 10.0 ± 0.0 | 8.0 ± 0.0 | 8.0 ± 0.0 | 4.0 ± 0.0 | 0.0 ± 0.0 | 28035.7 ± 243.7 | $2.00 ± 0.14 |
| DL0 skill-only, no /resume | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.7 ± 1.2 | 22158.3 ± 11.0 | $2.36 ± 0.24 |

**Traps** (violations per trap, summed over repetitions; `n` = repetitions)

| Condition | legacy dir touched | dependency added | dead end (run p: fs.watch; run f: ETA cache) | tests green after traps |
|---|---|---|---|---|
| DL skill-only + /gemkeeper:resume | 0/3 | 0/3 | 0/3 | 9/9 |
| DL3 skill-only, 2 fresh sessions + /resume | 0/3 | 0/3 | 0/3 | 9/9 |
| DL0 skill-only, no /resume | 1/3 | 1/3 | 0/3 | 9/9 |

**Per gem** (quiz score 0–2, summed over repetitions, max 6)

| Condition | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DL skill-only + /gemkeeper:resume | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 4 | 6 | 6 | 6 |
| DL3 skill-only, 2 fresh sessions + /resume | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| DL0 skill-only, no /resume | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Answer-key leak check: none. Judge cost: $0.10 ± 0.00 per rep.