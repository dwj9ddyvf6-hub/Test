# VITAL SIGN 1: THE ORGANISM'S AGGREGATE CALIBRATION, FIRST COMPUTATION

Computed Sat 2026-11-14 from the files named per organ. Design:
designs/LEVEL7-VITAL-SIGN-DESIGN.md. Weighting: pooled,
count-weighted mean of per-call Brier scores; every resolved
probability-bearing call counts once; accuracy-only organs ride
in the annex and are never blended.

## HEADLINE

Aggregate Brier: 0.2145 on n=40 resolved probability-bearing
calls (the confirmed set: 37 forecast twin calls plus JR-1 to
JR-3). Sensitivity: if JR-4 (p 0.35) resolved FALSE, as staged in
personal-quant/closure-report-2026-11-13.md ("on the order's
current state it resolves FALSE unless the order terminates
today"), the pooled figure is 0.2123 on n=41. JR-4's own outcome
line was not found in the files read, so the headline stands on
the confirmed 40 and the sensitivity is printed, not hidden.

## Decomposition by organ

- Forecast twin organ (typed-layer/forecast_twin_ledger.jsonl,
  resolution rows written by resolve_forecast_twin.py): n=37,
  Brier 0.2197. Same-set climatology: 0.1695 (base rate 0.7838).
  Excess: minus 0.0503. The twin organ is currently WORSE than
  climatology. Weight in the aggregate: 37 of 40 (92.5 percent).
  Twin detail, computed from the ledger: above-direction calls
  0.1934 (n24); below-direction calls 0.2683 (n13). Worst symbol
  cells: ELF 0.6475 (n4), MO 0.4489 (n3); best: RKLB 0.0001 (n4).
- Joint round organ (personal-quant/b5-inputs-2026-11-13.md):
  n=3 scored predicates. JR-1 0.0900, JR-2 0.1600, JR-3 0.2025;
  mean 0.1508. Weight: 3 of 40 (7.5 percent). n=3 supports no
  skill claim; the organ is in the pool because its calls were
  sealed and resolved, and it will earn weight only by accrual.
- Midna organ: EXCLUDED from the pool. Midna's 37 joined calls
  carried word confidences, not sealed numeric probabilities.
  The convention-mapped estimate (0.1387 on 36 mappable calls,
  accuracy 32 of 37) is recorded in
  designs/COGNITION-MAP-DESIGN.md as an estimate. Blending an
  estimate into the vital sign would corrupt the one number this
  program exists to keep honest.
- Selfaudit organ: 0 resolved. selfaudit_resolutions.jsonl is
  empty (0 lines); the resolver reports 5 right_first rows
  waiting inside their horizon (HARVESTER-RUN-1.md). Contributes
  nothing; named so its silence is visible.

Pooled arithmetic, shown: (37 x 0.2197 + 3 x 0.1508) / 40 =
(8.1289 + 0.4524) / 40 = 8.5813 / 40 = 0.2145.

## Annex: accuracy-only organs (never blended)

- Typed canary (typed-layer/canary-run-2026-11-14.md, run
  2026-11-14T14:36:39Z, frozen 24-pack set): stage agreement
  0.875 (21 of 24), verdict agreement 0.5833 (14 of 24), identical
  to the 2026-11-10 baseline and the 2026-11-11 proving run. No
  drift at the 3-pack declaration bar. These are agreement rates
  against a frozen baseline, not probabilities; annex only.
- Book card theses: 4 closed trades, graded in
  runs/JOURNAL-GRADING-RUN-1.md. Outcomes graded, no
  probabilities stated at entry; annex by design until the G19
  Brier-scored card fields land.

## The unmeasured surface (named, with size)

- 339 of 339 desk sleeves emit no probabilities
  (attribution_ledger_v1.json). The fleet's largest organ is
  entirely outside the vital sign.
- All book cards emit no probabilities until the week of
  Mon 2026-11-16 (G19 registration).
- 206 bank v2 typed panel rows posed, 0 resolved.
- 48 ghost and expression shadow rows, 0 resolved until expiry
  (ghost 2026-11-27).
- Calibration hypotheses: 0 resolvable, time-locked, none
  overdue on their own terms.

## Reading

The organism's measured calibration is dominated (92.5 percent)
by its weakest measured organ, and that organ trails its own
climatology. Diagnosis under the Level 7 rule: the sample is too
small to declare either divergence state (n=40, one organ), and
the honest sentence is that the measured surface is 40 calls
wide while the unmeasured surface is the entire fleet. The vital
sign's first job is to make that ratio impossible to ignore.

Falsifier carried from the design (Ascension Level 7, verbatim):
"Falsifier: the aggregate calibration number shows no leading
relationship with forward P&L across four quarters; then it is a
vanity metric and gets demoted."

STATUS: GREEN for Vital Sign 1 as scoped (computed from the
final files, gaps named on the face). EVIDENCE:
forecast_twin_ledger.jsonl resolution rows;
b5-inputs-2026-11-13.md JR lines; canary-run-2026-11-14.md.
