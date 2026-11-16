# RESOLUTION HARVESTER, RUN 1 (Sat 2026-11-14)

Program: Execute Both Brainstorms (W1). Method: census of the estate's
settleable prediction corpus from the ledgers of record, then the two
existing mechanical resolvers run live in this pass.

## Corpus census (6 families)
| Family | Posed | Resolved before run | State |
|---|---|---|---|
| Forecast twin predicates (T1-5) | 37 | 0 | resolver run below |
| Bank v2 typed panels / upside_first predicates | 206 ledger rows | 0 | horizons ~10 sessions; resolver run below |
| Book FORECAST-LOG calls incl. JR rounds | file of record | graded in-file | JR-1..3 Brier 0.1508 (2026-11-13); JR-4 resolved at the 2026-11-13 close |
| Book card theses (closed trades) | 4 | 4 | graded in JOURNAL-GRADING-RUN-1.md |
| Calibration hypotheses | ledger of record | 0 | TIME-LOCKED on live weeks; 0 resolvable today, none overdue on its own terms |
| Ghost + expression shadow | 48 priced/drafted | 0 | resolve at expiry (ghost 2026-11-27); G4 exit leg starved at source (D10) |

## Resolver runs in this pass (exact outputs)
- resolve_forecast_twin.py: "resolved 37 new calls. resolved: 37 |
  base rate 0.784 | twin Brier 0.2197 | climatology Brier 0.1695 |
  excess -0.0503. count toward the 300-call falsifier: 37/300 resolved
  (0 still pending)". HEADLINE: at 37 resolved the twin is WORSE than
  climatology by 0.0503 Brier. The falsifier binds at 300; the sign at
  37 is recorded, not smoothed.
- resolve_selfaudit.py: "pending right_first rows: 5. resolved 0,
  censored 0, waiting 5". The upside_first family is still inside its
  horizon window.

## Verdict
Run 1 EXECUTED. The harvester's census leg and both resolver legs ran
on the final artifacts; the corpus's honest state is: most of the
estate's predictions are young, not lost. Cadence registered:
resolution-harvester-nightly (weekdays).
STATUS: GREEN for run 1 as scoped. EVIDENCE: runs/first_wave_deterministic.json,
typed-layer/forecast_twin_ledger.jsonl (resolution rows appended by the resolver).
