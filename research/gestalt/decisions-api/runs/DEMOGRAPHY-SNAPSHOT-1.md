# DEMOGRAPHY SNAPSHOT 1 (Level 8): THE FLEET'S FIRST AGE-STRUCTURE READ

Computed Sat 2026-11-14 from runs/attribution_ledger_v1.json
(all 339 sleeves; Lens T seeded over 8,928 fills per
runs/ATTRIBUTION-LEDGER-V1.md) and
research_notes/sleeve-activation-calibration-20261111/execution_board.csv
(339 sleeve rows). This is a snapshot of a population, not a set
of verdicts on sleeves.

## HEADLINE

A population of 339 with 13 lifetime own closes, 0 clean
verdict-grade members, and 81.7 percent of members having never
closed a trade. The fleet is not aging into senescence; it has
not yet reached childhood's end. Every demographic ratio below
is downstream of that one fact.

## State distribution (ledger klass, Lens T source classes)

- NOT FIRED: 223 of 339 (65.8 percent).
- PARKED: 54 of 339 (15.9 percent).
- LOW SAMPLE: 62 of 339 (18.3 percent).
Note on the face: the ledger's klass is the Lens T source class;
the execution board's live states supersede for operations
(ATTRIBUTION-LEDGER-V1.md). The board carries the operational
states (for example ARMED-PROVEN rows) that the ledger classes
do not express. A demography that conflates the two would be
wrong in both directions, so both are named and neither is
silently substituted.

## Closes distribution

- 0 own closes: 336 sleeves (99.1 percent).
- 2 own closes: 1 (bta_onebar_qqq: 2 losses, expectancy
  minus 150.25 dollars).
- 3 own closes: 1 (bta_onebar_rth: 3 wins, expectancy
  +220.45 dollars, flag NETTED).
- 8 own closes: 1 (aster_trader_donchian55: 8 wins, expectancy
  +686.17 dollars, realized +5,489.35 dollars, flags
  NETTED;SCALE).
- Total own closes, fleet lifetime: 13.
- Sleeves with any closes: 3 of 339 (0.88 percent).
- Sleeves at or above the 3-own-close FREQUENCY bar: 2.
- Sleeves at verdict grade (bar met AND exits not consumed by
  the shared book): 0 clean. Both bar-meeting sleeves carry the
  NETTED flag. THE HONEST NUMBER IS 0.
- Fills without closes: 62 sleeves carry all 7,766 fills; fills
  are activity, not life outcomes, and the gap between 7,766
  fills and 13 own closes is the population's defining number.

## Age structure (sessions on the board, the only age proxy in the record)

Sessions per sleeve (ledger sessions field): 14 sessions: 135
sleeves; 13: 107; 12: 21; 11: 3; 10: 9; 8: 17; 7: 11; 6: 2; 5: 5;
3: 1; 2: 1; 1: 1; 0: 26. The population is a single cohort, not a
layered age structure: 242 of 339 sleeves (71.4 percent) sit at
13 to 14 sessions. There is no prime-aged stratum distinct from
the newborn stratum, because there has been no time and no
selective survival to create one. GAP NAMED: sessions is an
exposure count, not a birth date; the ledger carries no birth
timestamp per sleeve, so true age, and any median-age figure,
cannot be computed from v1. Birth dates must be a v1.1 field.

## Birth and death accounting (as the record supports)

- Population of record: 339 sleeves (execution board total,
  matching the ledger count exactly).
- Births: the board is a current-state census, not a birth
  register; cumulative promotions to date cannot be counted from
  it. GAP NAMED: no promotion log with dates was found in the
  artifacts read for this snapshot.
- Deaths: no kill register with dates was found either; the
  PARKED class (54) is a state, not a death count, and counting
  it as deaths would fabricate a mortality rate. GAP NAMED.
- What can be said honestly: net population change is
  unmeasurable from the current artifacts; the conveyor's birth
  and death rates, and median age at death (a Level 4 dashboard
  metric), are UNMEASURED until a dated birth/death register
  exists. Building that register is a one-table job and is the
  snapshot's first instrumentation demand.

## What the demography instrumentation still lacks

1. Lifetime expectancy per sleeve from replay civilizations
   (fixture drives at scale that let a sleeve live a simulated
   lifetime in a day): this is W20's build, named here as the
   missing instrument. Without it, birth decisions use a single
   backtest window and the Level 8 comparison cannot be run.
2. Birth timestamps and a dated promotion register.
3. A dated kill register with kill reason (the Level 4 death
   rules: forward Sharpe CI excluding the haircut budget, DSR
   below 0.5 on forward data, or mechanism invalidation).
4. Per-sleeve capital over time (needed for percent of capital
   in prime sleeves, the Level 8 headline ratio; today capital
   shares cannot be computed, only headcounts).
5. Pre-registered half-life per sleeve (needed for the percent
   past half-life dashboard metric).

## Falsifier

Ascension Level 8 falsifier, verbatim: "Falsifier:
lifetime-expectancy ranking from replay civilizations does not
beat single-window ranking on forward sleeve performance within
two quarters."

STATUS: PARTIAL for the snapshot as scoped (state, closes and
cohort structure computed from the final ledger; birth and death
rates and lifetime expectancy named as instrumentation gaps, not
estimated). EVIDENCE: attribution_ledger_v1.json counts computed
directly from the file; execution_board.csv row count.
