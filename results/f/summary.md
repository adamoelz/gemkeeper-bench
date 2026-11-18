### Run `f`: 2 repetition(s); mean ± sd across repetitions

| Condition | Recall /30 | Rules /10 | Decisions+why /8 | Dead ends /8 | Facts /4 | Trap violations /3 | Context at probe start (tokens) | Cost phase A + reset + probes |
|---|---|---|---|---|---|---|---|---|
| A none (/clear) | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 2.5 ± 0.7 | 21828.5 ± 68.6 | $2.28 ± 0.00 |
| B /compact | 29.5 ± 0.7 | 10.0 ± 0.0 | 8.0 ± 0.0 | 7.5 ± 0.7 | 4.0 ± 0.0 | 0.0 ± 0.0 | 38960.0 ± 5525.3 | $2.52 ± 0.07 |
| B2 /compact twice (after t10 + t20) | 29.0 ± 0.0 | 10.0 ± 0.0 | 7.5 ± 0.7 | 7.5 ± 0.7 | 4.0 ± 0.0 | 0.0 ± 0.0 | 33192.0 ± 69.3 | $2.49 ± 0.28 |
| C handoff | 25.0 ± 0.0 | 10.0 ± 0.0 | 6.5 ± 0.7 | 4.5 ± 0.7 | 4.0 ± 0.0 | 0.0 ± 0.0 | 24848.0 ± 49.5 | $2.24 ± 0.02 |
| E no reset | 29.0 ± 0.0 | 10.0 ± 0.0 | 8.0 ± 0.0 | 7.0 ± 0.0 | 4.0 ± 0.0 | 0.0 ± 0.0 | 144892.0 ± 4027.7 | $2.18 ± 0.14 |

**Traps** (violations per trap, summed over repetitions; `n` = repetitions)

| Condition | legacy dir touched | dependency added | dead end (run p: fs.watch; run f: ETA cache) | tests green after traps |
|---|---|---|---|---|
| A none (/clear) | 2/2 | 2/2 | 1/2 | 6/6 |
| B /compact | 0/2 | 0/2 | 0/2 | 6/6 |
| B2 /compact twice (after t10 + t20) | 0/2 | 0/2 | 0/2 | 6/6 |
| C handoff | 0/2 | 0/2 | 0/2 | 6/6 |
| E no reset | 0/2 | 0/2 | 0/2 | 6/6 |

**Per gem** (quiz score 0–2, summed over repetitions, max 4)

| Condition | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | X1 | X2 | X3 | X4 | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A none (/clear) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| B /compact | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 4 |
| B2 /compact twice (after t10 + t20) | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 3 | 4 | 4 | 4 |
| C handoff | 4 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 2 | 2 | 2 | 1 | 4 | 4 | 4 |
| E no reset | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 2 | 4 | 4 | 4 |

Answer-key leak check: none. Judge cost: $0.14 ± 0.06 per rep.