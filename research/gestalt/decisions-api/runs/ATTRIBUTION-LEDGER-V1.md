# VERDICT-GRADE ATTRIBUTION LEDGER, V1 (Sat 2026-11-14)

Program: Execute Both Brainstorms (W2). Basis: Lens T seeded rows
(build_lens_t_seeded.py over the durable fill ledger, 8,928 fills,
verified identical to the stock Lens T on all 339 sleeves), computed
in FIRING-BUT-LOSING-2026-11-14.md and re-emitted here as the ledger
of record: runs/attribution_ledger_v1.json (all 339 sleeves: own
closes, wins/losses, win rate, expectancy $, realized $, excess vs
SPY $, avg hold, sessions, fills, flags, class).

## HEADLINE COUNT
- Sleeves with any own closes: 3 of 339.
- Sleeves at or above the 3-own-close sample bar (FREQUENCY): 2
  (aster_trader_donchian55: 8 closes, +$686.17 expectancy, +$5,489.35
  realized, excess vs SPY +$11,923.30, flags NETTED;SCALE;
  bta_onebar_rth: 3 closes, +$220.45 expectancy, +$661.36 realized,
  excess vs SPY +$5.07, flag NETTED).
- CLEAN VERDICT-GRADE SLEEVES: 0. Both bar-meeting sleeves carry the
  NETTED flag (their exits are partly consumed by the shared book),
  so neither is clean attribution. bta_onebar_qqq (2 closes, -$150.25
  expectancy) stays on the WS3 watch; a third negative own close is
  its calibration trigger.
- Class counts: NOT FIRED 223, PARKED 54 (Lens T source classes;
  the board's live states supersede for operations), LOW SAMPLE 62.

## What unblocks the headline
The virtual-book fleet flip (VB-ENDGAME: criteria unmet on Friday's
6 residual symbols; proof = Mon 2026-11-16 full RTH census). Until
per-sleeve exits book against per-sleeve lots, attribution stays
starved at the source. This is now the program's named #1 data debt.
V1.1 items: a QQQ excess leg (source rows carry SPY only); per-sleeve
equity curves for W22 (meta-allocator design) once closes exist.
Cadence: recomputed nightly inside resolution-harvester-nightly.
STATUS: GREEN for v1 as scoped (the ledger exists and its headline
is the honest zero). EVIDENCE: runs/attribution_ledger_v1.json.
