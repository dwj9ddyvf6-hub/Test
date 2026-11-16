# PROGRAM A — BEST SETUPS RECHECK

Owner program, Sun 2026-11-15: the entire corpus rechecked through the Decisions API for potential edge and alpha, all variables varied, all connections, nothing arbitrary, nothing assumed. Corpus: the Best Setups canon. Grading standard: potential edge (the measure set by the owner 2026-11-15 08:55-09:08 ET); tiers are graded from each item's own record; Decisions API seats are lens output only and never set a tier, gate, veto, or size.

Coverage: 264 of 264 located canon items received an itemized five-field read (variables enumerated and classified, evidence as printed in the item's own record, mechanism named or MECHANISM-ABSENT, decisive variations named, tier graded); 264 of 264 items carry a plausibility seat and an information score, 264 of 264 carry an adversarial-null seat, and 264 of 264 carry a full seven-lens panel (see the coverage table; the seated fractions are printed per section and nothing in this file claims a section more complete than the table shows).

## The located corpus

Located before grading, counted from the records themselves:

- S1, the consideration registry: 83 items, the femto-lean `core/consideration.py` registry as censused 2026-10-17 (`GESTALT-COVERAGE.md`, 115 briefs): 41 unconditional, 29 integrity-gated, 10 conditional, 3 never-firing. The registry is the desk's consideration surface: what a daily read is allowed to weigh, with evidence stances 0 (evidence-only), 1 (may nudge) and gated (a gate that only fires on verified integrity).
- S2, the curator's scoring rubric: 25 items, the 24 published factors of `scoring_method_table()` in `muse-desk-v3/best_setups/core/setups_curator.py`, verified verbatim against the golden `best_setups/golden/inputs/setups_latest.json` (scale 0-100, minimum_score 35, bands 75/55/35; board of record 11 setups, 4 considered, lector_top 10, 11 briefs), plus the bands/minimum item.
- S3, sleeve families: 7 (the FAMILIES map in the same curator; 33 member sleeves; DIP_FAMILIES = tensor, intraday_pullback, red_day, dip_event).
- S4, the canon-gap audit and build slate: 98 items. The audit (`ta-canon-gap-audit-20261020-2156/report.md`) lists 83 numbered gaps + 4 SMC rows + RS-L; the slate (`CANON-GAPS-STUDY.md`) reconciles 88 audit rows = 77 build-new + 8 already-present + 3 named-unavailable stamps, in 85 numbered slate rows + prerequisite P0, with grouped audit rows split where the slate splits them (row 8 into 4, row 23 into 2, row 49 into 4, row 74 into 4). Counted but not itemized as separate rows: audit row 70, folded by the slate into atr_trailing_levels (G033 carries the fold).
- S5, excluded by ruling: 7 items (audit section C), recorded with no recommendation, tier UNGRADABLE-BLOCKED by the owner's frozen-method ruling.
- S6, chart law: 22 items (register section G groupings L-54 to L-59, expanded to their constituent rules).
- S7, method laws: 13 items (register section 2's edge-bearing method subset).
- S8, lenses outside the registry: 9 (the weighed desk read, the Pass A/B/C read layers, Elliott, Echo, Lector, Tensor, Mood Ring).

Total located and itemized: **264 items**. Counted but deliberately not itemized here (named so the boundary is printed, not hidden): the register's remaining section-2 governance laws (identity, ledger, journal, calendar and cadence law) beyond the 13 edge-bearing method items, and the desk's 339 sleeves individually (their families are itemized in S3; the sleeves themselves are the sleeve-census corpus, graded in the Lane 7 sweep and the Potential-Edge Census).

### Findings printed before any grading

1. **Three HIGH/MEDIUM audit gaps have no slate row and no producer key.** A key grep over femto-lean `core/consideration.py` + `core/chart_read.py` (2026-11-15) finds every probed slate key present except `aroon`, and finds `cci`/`cmf` only as substrings inside other words. Audit rows 37 (CCI, MEDIUM), 41 (Aroon, MEDIUM) and 51 (CMF, MEDIUM-HIGH, called conspicuous by the audit itself) are absent from the slate's 85 rows and absent from the code. G041, G045 and G058 carry tier UNGRADABLE-BLOCKED with this named blocker. Three further audit gaps also have no slate row and no key: row 39 (ROC oscillator), row 40 (StochRSI), row 31's alt-MA-types/cross-events half (G034) and rows 4, 9 and 12 in part (G004, G009, G012) — all LOW by the audit's own materiality, all printed in their rows.
2. **No canon item carries a registered falsifier that has fired.** Tier RESOLVED-AGAINST is empty across all 264 items: the canon has machinery for calibration (M12/M13) but no item has yet been resolved against by its own falsifier. That is a statement about accrual, not quality: pattern-level resolution accrues through the Ghost Book and the pattern-resolution ledger (14 of 70 typed predicates resolved as of 2026-11-15), and the register's forward reads are the path by which this tier can ever populate.
3. **Exactly one canon item is a LIVE CANDIDATE**: the Tensor lens (N08), whose fires are priced, resolving forward, and first-graded (21 Ghost Book fires resolved 2026-11-15). Everything else edge-bearing is WATCH (armed or built, unproven as potential edge), machinery, or blocked with its blocker named.

## Coverage table

| Section | Located | Itemized reads | Plausibility + info seats | Null seats | Seven-lens panels |
|---|---|---|---|---|---|
| S1_registry | 83 | 83 | 83 | 83 | 83 |
| S2_rubric | 25 | 25 | 25 | 25 | 25 |
| S3_families | 7 | 7 | 7 | 7 | 7 |
| S4_canon_gaps | 98 | 98 | 98 | 98 | 98 |
| S5_excluded_by_ruling | 7 | 7 | 7 | 7 | 7 |
| S6_chart_law | 22 | 22 | 22 | 22 | 22 |
| S7_method_laws | 13 | 13 | 13 | 13 | 13 |
| S8_lenses | 9 | 9 | 9 | 9 | 9 |
| TOTAL | 264 | 264 | 264 | 264 | 264 |

Tier census (graded from the records): WATCH 161, MACHINERY 78, UNGRADABLE-BLOCKED 24, LIVE CANDIDATE 1.

## Per-item reads

Format per item: tier and kind; the evidence as printed in the item's own record; the mechanism (named or MECHANISM-ABSENT); the variables enumerated with each setting classified SOURCED / TESTED / ARBITRARY and its source; the variations that would most change the verdict and whether any record varies them; seat fields (plaus = mechanism-plausibility predicate probability; info = 0-100 marginal-information score; null = adversarial-null predicate probability; lenses = the seven lens probabilities HFM/SWING/GAME/GAMBLER/PREDMKT/DATA/QUANT with mean and spread). The machine-readable register (PROGRAM-A-BEST-SETUPS-REGISTER.jsonl) carries the identical rows.

### S1 - The consideration registry (femto-lean core/consideration.py; census 2026-10-17)

**R01 ad_line** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: A/D line direction as accumulation/distribution evidence in the volume family.
- Variables: inputs=daily OHLCV [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.6]; window=full brief history [ARBITRARY, no window stated in the record]
- Variations that would most change the verdict: Vary window (full-history vs 13-week): no record varies it.
- Seats: plaus 0.5; info 35.4; null 0.6; lenses 0.54/0.60/0.43/0.50/0.51/0.39/0.30 (mean 0.467, spread 0.3)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R02 adx** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: ADX/DMI trend-strength gauge (blessed addendum 3); separates trending from ranging names for family habitat calls.
- Variables: period=14 [SOURCED, Wilder canon via THE LIST (owner-dictated 2026-10-16, register L-35) addendum 3]; thresholds=none printed in the record [ARBITRARY]
- Variations that would most change the verdict: Vary period 14 vs 25 and the trend threshold: no record varies either.
- Seats: plaus 0.59; info 39.0; null 0.56; lenses 0.52/0.65/0.44/0.52/0.57/0.35/0.28 (mean 0.476, spread 0.37)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R03 atr** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: ATR is the desk's unit of distance: stops, zones, materiality floors and stretch are all denominated in it.
- Variables: period=14 [SOURCED, Wilder]; use=distance unit across plan law [SOURCED, register L-13/L-15]
- Variations that would most change the verdict: Vary ATR period or use true-range vs simple range: no record varies it; every ATR-denominated law inherits the choice.
- Seats: plaus 0.52; info 56.8; null 0.47; lenses 0.52/0.75/0.33/0.59/0.61/0.42/0.15 (mean 0.481, spread 0.6)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R04 averages** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Price position vs the 10/20/50/200-day averages: the trend skeleton of every read.
- Variables: periods=10/20/50/200 [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.4]; type=SMA/EMA not stated per average in the coverage record [ARBITRARY]
- Variations that would most change the verdict: Vary average type (EMA vs SMA) and the period set: no record varies them (audit row 31 names the same specification gap).
- Seats: plaus 0.55; info 54.4; null 0.61; lenses 0.61/0.73/0.45/0.66/0.55/0.42/0.21 (mean 0.519, spread 0.52)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R05 bollinger** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)); NOTE: the study found its squeeze test mislabels the canonical BB-inside-Keltner definition (CANON-GAPS-STUDY Flag O1, open defect)
- Mechanism: Bollinger width percentile and squeeze state as compression evidence (blessed addendum 4).
- Variables: period=20, mult=2 sigma [SOURCED, Bollinger canon]; squeeze test=BB width < 3*ATR/EMA20 [ARBITRARY desk proxy, found mislabelled vs canonical Keltner containment]
- Variations that would most change the verdict: Vary the squeeze definition to true BB-inside-Keltner: specified in slate row keltner, not yet the consumed definition in this item's record.
- Seats: plaus 0.44; info 39.2; null 0.69; lenses 0.35/0.48/0.43/0.34/0.34/0.26/0.24 (mean 0.349, spread 0.24)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R06 buy_zone_cap** — MACHINERY (machinery)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Plan geometry: buy zone, cap and distance-to-cap printed on every brief.
- Variables: zone=staged anchor +/-0.25xATR14 [SOURCED, register L-15]; cap=from the staged plan [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.11]
- Variations that would most change the verdict: Vary the 0.25xATR zone half-width: no record varies it.
- Seats: plaus 0.84; info 49.0; null 0.16; lenses 0.86/0.93/0.74/0.88/0.88/0.90/0.51 (mean 0.814, spread 0.42)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R07 candles** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: ~50 candlestick detectors, counted only at a key level (LIST fam.9): candle evidence is location-conditioned by law.
- Variables: detector set=~50 patterns [SOURCED, Nison canon via THE LIST (owner-dictated 2026-10-16, register L-35) fam.9]; gate=key level only [SOURCED, L-35]
- Variations that would most change the verdict: Vary the key-level gate (count everywhere vs at levels): no record varies it; the detector list itself was never itemised in the audited records (canon-gap audit caveat).
- Seats: plaus 0.39; info 38.4; null 0.66; lenses 0.54/0.63/0.45/0.48/0.41/0.35/0.33 (mean 0.456, spread 0.3)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R08 desk_book** — MACHINERY (machinery)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: The desk's existing exposure in the name and sector, stated on every brief including its absence.
- Variables: scope=name + sector exposure [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) addendum 9]
- Variations that would most change the verdict: Not an edge variable; variation not applicable.
- Seats: plaus 0.61; info 31.0; null 0.19; lenses 0.84/0.72/0.78/0.85/0.79/0.78/0.38 (mean 0.734, spread 0.47)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R09 desk_trades_it** — MACHINERY (machinery)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Which strategies hold the name and the desk's prior trade history in it.
- Variables: scope=desk ledger [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.11/13]
- Variations that would most change the verdict: Not an edge variable; variation not applicable.
- Seats: plaus 0.29; info 35.6; null 0.5; lenses 0.72/0.68/0.48/0.73/0.68/0.61/0.21 (mean 0.587, spread 0.52)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R10 div_battery** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: The divergence battery: 7 gauges on daily swings, grouped momentum vs volume (LIST fam.7).
- Variables: gauges=7 [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.7]; frames=daily (weekly is div_weekly) [SOURCED]; confirmation rules=register L-39 salience (confirmed > unconfirmed) [SOURCED]
- Variations that would most change the verdict: Vary gauge set and pivot-pairing rules: no record varies them; hidden divergences added by L-39 without a variation study.
- Seats: plaus 0.42; info 44.2; null 0.59; lenses 0.40/0.57/0.50/0.47/0.43/0.32/0.31 (mean 0.429, spread 0.26)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R11 div_weekly** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Weekly-frame divergences, the slower twin of the daily battery.
- Variables: gauges=7 on weekly swings [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.7]
- Variations that would most change the verdict: Vary weekly pivot parameters: no record varies them.
- Seats: plaus 0.49; info 46.6; null 0.53; lenses 0.47/0.58/0.44/0.38/0.41/0.42/0.25 (mean 0.421, spread 0.33)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R12 earnings** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Earnings dates on every brief (past reactions are the separate earnings_reactions item).
- Variables: scope=dates from the desk calendar [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.13]
- Variations that would most change the verdict: Not an edge variable by itself; variation not applicable.
- Seats: plaus 0.45; info 60.0; null 0.64; lenses 0.34/0.48/0.38/0.25/0.41/0.29/0.07 (mean 0.317, spread 0.41)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R13 econ_calendar** — MACHINERY (machinery)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Economic calendar context for the session.
- Variables: scope=desk calendar [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.13]
- Variations that would most change the verdict: Not an edge variable; variation not applicable.
- Seats: plaus 0.56; info 37.2; null 0.46; lenses 0.31/0.37/0.26/0.45/0.58/0.63/0.16 (mean 0.394, spread 0.47)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R14 elliott** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Elliott wave count + invalidation computed once per brief, stance 0 by ruling (register L-40): a lens that moves no number until validation + ruling.
- Variables: count=computed per brief [SOURCED, register L-40]; stance=0 [SOURCED, owner ruling 2026-10-16]
- Variations that would most change the verdict: Vary the count's weight (stance 0 vs any nonzero): barred by ruling until a pre-registered validation passes; no record varies it.
- Seats: plaus 0.23; info 26.2; null 0.71; lenses 0.19/0.26/0.15/0.18/0.19/0.13/0.07 (mean 0.167, spread 0.19)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R15 event_calendar_name** — MACHINERY (machinery)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)); its own fact states dividends/index/lockup ride on no desk calendar (sub-list class (c) inside an (a) item)
- Mechanism: Per-name event calendar: splits measured; dividends, index adds/drops and lockup expiries named as having no desk calendar product.
- Variables: scope=splits only in practice [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) addendum 10]; missing sub-list=no producer exists [ARBITRARY gap, named in the record]
- Variations that would most change the verdict: Variation blocked on a calendar product that does not exist.
- Seats: plaus 0.67; info 48.2; null 0.23; lenses 0.54/0.73/0.29/0.73/0.74/0.68/0.22 (mean 0.561, spread 0.52)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R16 fear_window** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: The fear-day timing window (red QQQ day, 3:20-3:50 PM ET) and the Mood Ring fear complex carried into the brief.
- Variables: window=3:20-3:50 PM ET [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.11]; fear test in scoring=SPY -1.5% or VIX +15%, desk additions VIX>=25 / red day + VIX>=20 [SOURCED/ARBITRARY mix, curator regime rows]
- Variations that would most change the verdict: Vary the window and the fear thresholds: no record varies them.
- Seats: plaus 0.33; info 30.8; null 0.75; lenses 0.33/0.39/0.38/0.29/0.29/0.26/0.18 (mean 0.303, spread 0.21)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R17 gaps** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Gaps counted only at key levels, with the gap taxonomy and unfilled gaps carried as levels (addendum 8).
- Variables: gate=key level only [SOURCED, L-35]; taxonomy=breakaway/runaway/exhaustion/common [SOURCED, canon via addendum 8]
- Variations that would most change the verdict: Vary the at-level gate: no record varies it.
- Seats: plaus 0.56; info 47.4; null 0.51; lenses 0.49/0.60/0.46/0.45/0.49/0.41/0.25 (mean 0.45, spread 0.35)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R18 high_low_52w** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: 52-week high/low: the inventory's outer supply frame (the audit's row 21 names the missing ATH leg, now ath_distance in the slate).
- Variables: window=52 weeks [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.3]
- Variations that would most change the verdict: Vary to ATH distance: built as a separate slate item (ath_distance); this item's window never varied.
- Seats: plaus 0.48; info 43.0; null 0.58; lenses 0.53/0.70/0.48/0.42/0.47/0.45/0.30 (mean 0.479, spread 0.4)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R19 higher_timeframe** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Monthly/weekly trend map: the daily setup's place inside the higher-timeframe structure (addendum 6).
- Variables: frames=monthly + weekly aggregates [SOURCED, addendum 6]
- Variations that would most change the verdict: Vary aggregation (calendar vs rolling): no record varies it.
- Seats: plaus 0.65; info 50.4; null 0.63; lenses 0.65/0.72/0.55/0.65/0.67/0.57/0.41 (mean 0.603, spread 0.31)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R20 iv_rank_hv** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)); prints HV on every brief but without the options product its IV side is absent and the fact says so
- Mechanism: IV rank + HV-vs-IV spread (addendum 5): separates 'IV high because the name moves' from 'IV high and the name is dead'.
- Variables: rank window=desk's own IV history (iv_history.jsonl) [SOURCED, coverage ledger]; HV windows=not stated in the coverage record [ARBITRARY]
- Variations that would most change the verdict: Vary the rank window and HV windows: no record varies them; the slate's hv_percentile item rebuilds the HV leg with stated windows (HV10/20/30/60 vs 1-yr).
- Seats: plaus 0.55; info 47.4; null 0.54; lenses 0.49/0.63/0.51/0.53/0.54/0.49/0.37 (mean 0.509, spread 0.26)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R21 lector_stage** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)); for names outside the replica's ranked universe the fact printed is the absence itself
- Mechanism: ChartsLector stage: an external expert's stage read, filed as testimony; coverage is the replica's own universe (ranks_top15 + curator lector_rank).
- Variables: universe=replica ranked set [SOURCED, coverage ledger]; stage taxonomy=Lector's own [SOURCED, replica]
- Variations that would most change the verdict: Vary universe or stage mapping: no record varies them; the curator's lector_tiers point mapping is desk-set (see B04).
- Seats: plaus 0.48; info 35.2; null 0.67; lenses 0.38/0.47/0.38/0.36/0.34/0.34/0.17 (mean 0.349, spread 0.3)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R22 liquidity** — MACHINERY (machinery)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Market cap, float, average dollar volume, typical spread (addendum 1).
- Variables: fields=cap/float/ADV/spread [SOURCED, addendum 1]
- Variations that would most change the verdict: Not an edge variable; variation not applicable.
- Seats: plaus 0.86; info 46.4; null 0.13; lenses 0.92/0.89/0.82/0.89/0.89/0.85/0.84 (mean 0.871, spread 0.1)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R23 macd_crossovers** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: MACD crossover events, one of the four items the owner marked NEW on THE LIST.
- Variables: params=12/26/9 [SOURCED, Appel canon via THE LIST (owner-dictated 2026-10-16, register L-35) fam.5]; event=cross of signal line [SOURCED]
- Variations that would most change the verdict: Vary MACD parameters: no record varies them.
- Seats: plaus 0.35; info 31.4; null 0.6; lenses 0.38/0.50/0.49/0.37/0.35/0.35/0.20 (mean 0.377, spread 0.3)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R24 market_breadth** — MACHINERY (machinery)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Breadth over an 1831-name scan (market_measurements EOD battery).
- Variables: universe=1831-name scan [SOURCED, coverage ledger]; series=% above 50/200 (values; the slate adds the filed series) [SOURCED]
- Variations that would most change the verdict: Not a per-name edge variable; variation not applicable.
- Seats: plaus 0.84; info 52.2; null 0.36; lenses 0.78/0.82/0.70/0.79/0.82/0.84/0.59 (mean 0.763, spread 0.25)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R25 market_rates_credit_dollar** — MACHINERY (machinery)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Rates/credit/dollar pair battery, the lean substitute for the old FRED feed (which is not itself consumed).
- Variables: pairs=desk battery in market_measurements [SOURCED, coverage ledger]
- Variations that would most change the verdict: Not an edge variable; variation not applicable.
- Seats: plaus 0.79; info 47.6; null 0.37; lenses 0.76/0.77/0.69/0.77/0.77/0.74/0.38 (mean 0.697, spread 0.39)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R26 market_regime** — MACHINERY (machinery)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Market regime label feeding the curator's regime factors (see B07-B13).
- Variables: taxonomy=desk regime states [ARBITRARY, no derivation in the record]; producer=market_measurements [SOURCED]
- Variations that would most change the verdict: Vary the regime taxonomy: no record varies it; the canon-gap audit (rows 71-74) names the rule-based internals the generic label cannot substitute for.
- Seats: plaus 0.81; info 50.0; null 0.26; lenses 0.79/0.79/0.64/0.77/0.69/0.79/0.73 (mean 0.743, spread 0.15)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R27 measured_move_pattern** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: The pattern's scaled measured-move objective, one of the ladder's two lawful objective pools (register L-12).
- Variables: objective=pattern height projected from breakout [SOURCED, Bulkowski canon via THE LIST (owner-dictated 2026-10-16, register L-35) fam.3]
- Variations that would most change the verdict: Vary projection convention (height from neckline vs from pattern extreme): no record varies it.
- Seats: plaus 0.47; info 30.6; null 0.53; lenses 0.34/0.53/0.34/0.36/0.43/0.32/0.16 (mean 0.354, spread 0.37)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R28 mfi** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Money Flow Index: volume-weighted RSI analogue in the volume family.
- Variables: period=14 [SOURCED, Quong/Soudack canon via THE LIST (owner-dictated 2026-10-16, register L-35) fam.6]
- Variations that would most change the verdict: Vary period: no record varies it.
- Seats: plaus 0.38; info 29.8; null 0.53; lenses 0.37/0.44/0.33/0.35/0.32/0.23/0.24 (mean 0.326, spread 0.21)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R29 momentum_6m** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)); its cross-stock rank is board-relative by construction (ranks against names briefed in the same build, not the market)
- Mechanism: 6-month momentum + cross-sectional rank (LIST fam.5).
- Variables: window=6 months [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.5]; rank universe=the same build's briefed names [ARBITRARY construction, named in the coverage record]
- Variations that would most change the verdict: Vary the rank universe to the full market: no record varies it; board-relative rank is the single most consequential quiet variable in this item.
- Seats: plaus 0.66; info 42.4; null 0.51; lenses 0.68/0.69/0.55/0.66/0.67/0.45/0.64 (mean 0.62, spread 0.24)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R30 obv** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: On-Balance Volume: cumulative signed volume as accumulation evidence.
- Variables: rule=Granville cumulative [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.6]
- Variations that would most change the verdict: Vary (e.g. OBV smoothing or divergence-only use): no record varies it.
- Seats: plaus 0.47; info 33.0; null 0.51; lenses 0.37/0.53/0.38/0.37/0.32/0.31/0.27 (mean 0.364, spread 0.26)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R31 relative_strength** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)); SPX leg always prints, sector leg only for names in the sector map
- Mechanism: RS vs S&P 500 and vs sector, one of the four owner-NEW items; the plotted RS line itself was the audit's HIGH gap (now rs_line, provisional).
- Variables: benchmarks=SPX + sector [SOURCED, L-35]; sector map=fixed ~48-name dict in core/m2_features.py [ARBITRARY coverage limit, named in the coverage ledger]
- Variations that would most change the verdict: Vary the sector map to a full-universe source: named as the cure in the coverage ledger, not landed in this record.
- Seats: plaus 0.61; info 49.8; null 0.5; lenses 0.67/0.71/0.61/0.68/0.64/0.47/0.54 (mean 0.617, spread 0.24)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R32 rsi** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: RSI: the momentum family's primary gauge and a divergence-battery member.
- Variables: period=14 [SOURCED, Wilder via THE LIST (owner-dictated 2026-10-16, register L-35) fam.5]
- Variations that would most change the verdict: Vary period (14 vs 2/3 for dip systems): the book's D3/E3 systems vary it outside Best Setups; inside the registry no record varies it.
- Seats: plaus 0.41; info 37.0; null 0.53; lenses 0.33/0.50/0.37/0.31/0.32/0.21/0.22 (mean 0.323, spread 0.29)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R33 scenarios** — MACHINERY (machinery)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Good/bad case scenarios printed with the plan (where the setup is wrong + good/bad case, LIST fam.11).
- Variables: form=plan law [SOURCED, register L-15/L-22]
- Variations that would most change the verdict: Not an edge variable; variation not applicable.
- Seats: plaus 0.69; info 38.6; null 0.34; lenses 0.60/0.71/0.58/0.65/0.70/0.58/0.23 (mean 0.579, spread 0.48)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R34 seasonality** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Seasonality context (plain seasonality is in the inventory; cycle methods are excluded by ruling, see X04).
- Variables: form=calendar seasonality [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.13]; windows=not stated [ARBITRARY]
- Variations that would most change the verdict: Vary seasonal windows: no record varies them.
- Seats: plaus 0.48; info 30.6; null 0.64; lenses 0.35/0.44/0.32/0.32/0.38/0.24/0.25 (mean 0.329, spread 0.2)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R35 sleeve_exits** — MACHINERY (machinery)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Which sleeve holds the name and that sleeve's exits/stops, stated for every name including absence.
- Variables: scope=desk sleeve records [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.11]
- Variations that would most change the verdict: Not an edge variable; variation not applicable.
- Seats: plaus 0.3; info 29.6; null 0.34; lenses 0.84/0.76/0.41/0.85/0.67/0.37/0.50 (mean 0.629, spread 0.48)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R36 stochastic** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Slow stochastic in the momentum family.
- Variables: params=slow stochastic, periods not stated in the coverage record [ARBITRARY]
- Variations that would most change the verdict: Vary %K/%D periods: no record varies them.
- Seats: plaus 0.34; info 25.8; null 0.69; lenses 0.31/0.37/0.24/0.25/0.21/0.21/0.18 (mean 0.253, spread 0.19)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R37 stretch_rank** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Distance from average in ATRs ranked vs the name's own 1-year history: the desk's statistical extension gauge.
- Variables: window=1-year own history [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.8]; unit=ATR [SOURCED]
- Variations that would most change the verdict: Vary the ranking window: no record varies it.
- Seats: plaus 0.56; info 46.2; null 0.52; lenses 0.48/0.57/0.42/0.40/0.42/0.30/0.27 (mean 0.409, spread 0.3)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R38 tensor_state** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)); prints on every brief including the honest silence fact; the engine itself runs only over its 41-name basket (Decision #38)
- Mechanism: Tensor slow/fast states and markers: the canonical engine's read on the name, or its stated silence.
- Variables: basket=41 names [SOURCED, Decision #38]; states=slow/fast + markers [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.10]
- Variations that would most change the verdict: Vary the basket: barred by Decision #38 in this record; the book's Ghost Book priced the engine's fires separately (census C10).
- Seats: plaus 0.49; info 37.2; null 0.59; lenses 0.38/0.50/0.30/0.39/0.40/0.29/0.23 (mean 0.356, spread 0.27)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R39 tensor_votes** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Tensor votes and trend strength as filed testimony in the synthesis.
- Variables: frames=weekly/daily/hourly per THE LIST [SOURCED, fam.10]; note=timeframe agreement is the separate tensor_timeframes item, class (c), R81
- Variations that would most change the verdict: Vary vote aggregation: no record varies it.
- Seats: plaus 0.48; info 33.0; null 0.5; lenses 0.40/0.48/0.28/0.35/0.41/0.26/0.19 (mean 0.339, spread 0.29)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R40 vwap_value_area** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: 20-day VWAP + volume-profile value area (VAH/VAL/POC): where value sits vs where price is.
- Variables: VWAP window=20 days [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.6]; VA=volume profile of the brief window [SOURCED]
- Variations that would most change the verdict: Vary the profile window and VA percentage (70% convention): no record varies either.
- Seats: plaus 0.58; info 49.4; null 0.51; lenses 0.54/0.63/0.47/0.50/0.54/0.42/0.32 (mean 0.489, spread 0.31)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R41 weinstein_stage** — WATCH (edge-bearing)
- Evidence (as printed): class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Weinstein stage: the cycle position of the name (basing/advancing/topping/declining).
- Variables: taxonomy=Weinstein 4-stage [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.4]; MA basis=30-week per canon, desk states its own in the item [ARBITRARY detail]
- Variations that would most change the verdict: Vary stage assignment rules: no record varies them.
- Seats: plaus 0.51; info 33.2; null 0.61; lenses 0.37/0.54/0.36/0.43/0.38/0.31/0.24 (mean 0.376, spread 0.3)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R42 abcd** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: AB=CD swing measured move: the one harmonic form the frozen method admits (full harmonics excluded, X01).
- Variables: ratio=1.0 AB=CD [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.3]; extensions 1.272/1.618 are R45
- Variations that would most change the verdict: Vary the equality tolerance for AB vs CD legs: no record varies it.
- Seats: plaus 0.36; info 29.4; null 0.52; lenses 0.31/0.46/0.26/0.31/0.32/0.24/0.22 (mean 0.303, spread 0.24)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R43 anchored_vwap** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Anchored VWAP from earnings date and major swing anchors (addendum 2); the slate extends the anchor set (IPO/ATH/gap/YTD/prior earnings cycle).
- Variables: anchors=earnings + major swings [SOURCED, addendum 2]; extension anchors=slate row 31 [SOURCED, CANON-GAPS-STUDY]
- Variations that would most change the verdict: Vary anchor choice: the extension is specified in the slate; no record compares anchor sets.
- Seats: plaus 0.57; info 49.0; null 0.5; lenses 0.55/0.65/0.51/0.41/0.55/0.41/0.44 (mean 0.503, spread 0.24)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R44 div_daily_core** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: The core daily divergence read sourced from the ta_read (R10 is the battery filing; this is the chart-read core with confirmation state).
- Variables: gauges=core set from chart_read [SOURCED, coverage ledger]; hidden+regular both in scope [SOURCED, register L-39]
- Variations that would most change the verdict: Vary pivot-pairing exhaustiveness: L-39 mandates every pivot pair; no record varies the pairing rule.
- Seats: plaus 0.42; info 35.0; null 0.5; lenses 0.40/0.52/0.41/0.39/0.42/0.30/0.26 (mean 0.386, spread 0.26)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R45 extensions** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: 1.272 and 1.618 Fibonacci extensions of the swing, ladder-eligible objectives.
- Variables: ratios=1.272/1.618 [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.3]
- Variations that would most change the verdict: Vary the ratio set: no record varies it.
- Seats: plaus 0.32; info 37.6; null 0.52; lenses 0.34/0.46/0.32/0.30/0.27/0.19/0.19 (mean 0.296, spread 0.27)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R46 fib_retracement** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Fibonacci retracement of the 1-year swing: band, give-back %, and whether the 200-day sits in the band.
- Variables: swing window=1 year [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.3]; levels=standard band incl. 50% [SOURCED]
- Variations that would most change the verdict: Vary the swing window (1-year vs the operative base): no record varies it.
- Seats: plaus 0.34; info 39.0; null 0.59; lenses 0.34/0.52/0.30/0.30/0.36/0.26/0.19 (mean 0.324, spread 0.33)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R47 level_confluence** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Level-confluence counts: how many independent level sources stack at one price. One of the four owner-NEW items; the count is the desk's core location statistic.
- Variables: sources=swings + volume profile + round numbers + trendlines [SOURCED, L-35]; independence rule=one vote per source family [ARBITRARY detail, no stated de-dup rule in the coverage record]
- Variations that would most change the verdict: Vary which sources count (add pivots/options walls per the slate): specified by slate rows pivot_points/gamma_walls_name feeding this count; no record yet varies the source set.
- Seats: plaus 0.61; info 45.0; null 0.5; lenses 0.54/0.63/0.46/0.58/0.53/0.33/0.37 (mean 0.491, spread 0.3)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R48 macd_state** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: MACD state (line/signal/histogram posture) from the ta_read, distinct from the crossover-events item R23.
- Variables: params=12/26/9 [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.5]
- Variations that would most change the verdict: Vary parameters: no record varies them.
- Seats: plaus 0.36; info 29.8; null 0.65; lenses 0.31/0.45/0.26/0.31/0.31/0.22/0.21 (mean 0.296, spread 0.24)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R49 pat_breakout** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Breakout/breakdown detection: the event the whole pattern family keys on.
- Variables: definition=close beyond the pattern boundary [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.1]; quality split is R50
- Variations that would most change the verdict: Vary the confirmation rule (close vs intraday breach): no record varies it.
- Seats: plaus 0.55; info 46.0; null 0.52; lenses 0.53/0.60/0.47/0.51/0.44/0.31/0.36 (mean 0.46, spread 0.29)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R50 pat_breakout_quality** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Breakout quality: closes held, stretched spike (LIST fam.1). Feeds the calibration layer's pattern base rates.
- Variables: quality terms=closes held + spike state [SOURCED, L-35]; base rates=pattern calibration (register L-42/43, n>=30 cells) [TESTED-adjacent: rates are measured on the 1,838-symbol census, span 2020-01-02 to 2026-10-16]
- Variations that would most change the verdict: Vary quality thresholds: no record varies them; the calibration cells are the only measured variation surface for the pattern family.
- Seats: plaus 0.64; info 47.6; null 0.52; lenses 0.59/0.66/0.51/0.60/0.59/0.38/0.44 (mean 0.539, spread 0.28)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R51 pat_channel** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Rising/falling channels as tradable structure.
- Variables: walls=confirmed pivots [SOURCED, register chart law item 7]
- Variations that would most change the verdict: Vary pivot confirmation count: no record varies it.
- Seats: plaus 0.52; info 37.8; null 0.54; lenses 0.51/0.57/0.47/0.46/0.49/0.41/0.28 (mean 0.456, spread 0.29)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R52 pat_cup** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Cup & handle: the O'Neil base shape, with depth/length discipline supplied by the slate's base items (base_metrics_stage).
- Variables: shape=cup + handle [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.1]; canon depth/length rules=absent at audit, built as slate rows base_flat/base_metrics_stage [SOURCED, CANON-GAPS-STUDY]
- Variations that would most change the verdict: Vary depth/length limits: the slate encodes canon limits (cup <=~33%); no record compares limits.
- Seats: plaus 0.5; info 33.4; null 0.66; lenses 0.54/0.65/0.43/0.56/0.48/0.51/0.32 (mean 0.499, spread 0.33)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R53 pat_cup_inverted** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Inverted cup & handle (bearish mirror).
- Variables: shape=mirror of R52 [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.1]
- Variations that would most change the verdict: As R52.
- Seats: plaus 0.34; info 31.2; null 0.5; lenses 0.47/0.55/0.38/0.43/0.42/0.34/0.30 (mean 0.413, spread 0.25)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R54 pat_double** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Double tops/bottoms incl. Adam & Eve refinements as sub-variants (audit section B).
- Variables: shape=two tests of one level [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.1]; calibration family=pattern census [TESTED-adjacent, L-42/43]
- Variations that would most change the verdict: Vary the two-test tolerance (how equal the extremes must be): no record varies it; the slate's liquidity_sweeps item builds the equal-extremes primitive for pools.
- Seats: plaus 0.48; info 37.2; null 0.53; lenses 0.51/0.61/0.48/0.52/0.47/0.37/0.30 (mean 0.466, spread 0.31)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R55 pat_flag_pennant** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Bull/bear flags & pennants; the slate adds the high-tight-flag detector into this item's slot (pole >=100% in <=8wk).
- Variables: shape=pole + consolidation [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.1]; HTF variant=slate row 10 [SOURCED]
- Variations that would most change the verdict: Vary pole/flag limits: canon limits encoded in the slate detector; no record compares them.
- Seats: plaus 0.51; info 35.6; null 0.59; lenses 0.55/0.63/0.55/0.51/0.58/0.45/0.38 (mean 0.521, spread 0.25)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R56 pat_head_shoulders** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Head & shoulders + inverse, incl. complex multi-head variants as a detector flag (audit section B).
- Variables: shape=three peaks + neckline [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.1]
- Variations that would most change the verdict: Vary neckline-break confirmation: no record varies it.
- Seats: plaus 0.41; info 31.2; null 0.63; lenses 0.53/0.58/0.48/0.51/0.50/0.40/0.32 (mean 0.474, spread 0.26)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R57 pat_rectangle** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Rectangles (the box family: Darvas box is this shape traded on breakout, audit section B).
- Variables: shape=horizontal range [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.1]; O'Neil flat-base rules are the separate slate item base_flat
- Variations that would most change the verdict: Vary range-length minimum: no record varies it.
- Seats: plaus 0.52; info 35.4; null 0.57; lenses 0.53/0.63/0.52/0.50/0.46/0.41/0.31 (mean 0.48, spread 0.32)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R58 pat_triangle** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Ascending/descending/symmetrical triangles.
- Variables: shape=converging walls on confirmed pivots [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.1]
- Variations that would most change the verdict: Vary wall-touch minimums: no record varies them.
- Seats: plaus 0.49; info 35.6; null 0.53; lenses 0.51/0.57/0.42/0.44/0.44/0.37/0.27 (mean 0.431, spread 0.3)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R59 pat_triple** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Triple tops/bottoms.
- Variables: shape=three tests [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.1]
- Variations that would most change the verdict: As R54.
- Seats: plaus 0.36; info 26.6; null 0.65; lenses 0.39/0.51/0.33/0.33/0.33/0.31/0.24 (mean 0.349, spread 0.27)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R60 pat_wedge** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Rising/falling wedges.
- Variables: shape=converging sloping walls [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.1]
- Variations that would most change the verdict: Vary slope/convergence rules: no record varies them.
- Seats: plaus 0.43; info 33.0; null 0.58; lenses 0.41/0.54/0.49/0.41/0.34/0.34/0.27 (mean 0.4, spread 0.27)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R61 pat_wedge_expanding** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Expanding wedges (both sides sloping). The slate's pat_broadening defers to this item's naming discipline: one geometry, one name (study section 7).
- Variables: shape=diverging walls [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.1]
- Variations that would most change the verdict: Vary the width-ratio threshold (slate sets >=1.3 for broadening): no record compares thresholds.
- Seats: plaus 0.32; info 30.6; null 0.75; lenses 0.34/0.47/0.32/0.33/0.32/0.27/0.21 (mean 0.323, spread 0.26)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R62 retests_reclaims** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Retests/reclaims of the 20-day and 50-day averages and of breakout levels. One of the four owner-NEW items.
- Variables: levels=20d/50d averages + breakout levels [SOURCED, L-35]
- Variations that would most change the verdict: Vary which levels count (add prior-period highs per slate): no record varies the set.
- Seats: plaus 0.68; info 48.8; null 0.53; lenses 0.68/0.72/0.64/0.66/0.64/0.60/0.50 (mean 0.634, spread 0.22)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R63 relative_volume** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Relative volume and breakout volume from the ta_read.
- Variables: basis=vs own average, window not stated in the coverage record [ARBITRARY]
- Variations that would most change the verdict: Vary the comparison window (20d vs 50d): no record varies it.
- Seats: plaus 0.55; info 44.0; null 0.52; lenses 0.63/0.70/0.55/0.64/0.63/0.45/0.40 (mean 0.571, spread 0.3)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R64 structure_state** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Structure intact/broken + warnings: the governing line of the read (the old desk's INTACT/BROKEN screen carried here).
- Variables: rule=swing structure breaks [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.2]; governing-line law=register L-30
- Variations that would most change the verdict: Vary break definition (close vs wick through the swing): no record varies it.
- Seats: plaus 0.56; info 44.6; null 0.5; lenses 0.53/0.69/0.46/0.62/0.60/0.45/0.23 (mean 0.511, spread 0.46)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R65 swings_dated** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Dated swing highs/lows: the pivot record every level and pattern is built from.
- Variables: pivot rule=shared PIVOTS primitive in the slate [SOURCED]; confirmation lag=not stated in the coverage record [ARBITRARY]
- Variations that would most change the verdict: Vary pivot strength (bars each side): no record varies it, and every pattern/level item inherits the choice.
- Seats: plaus 0.47; info 50.2; null 0.52; lenses 0.58/0.73/0.36/0.70/0.71/0.32/0.27 (mean 0.524, spread 0.46)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R66 trendlines** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Support/resistance trendlines from swings; fitted-line values expire under the distance/span law (register L-34).
- Variables: fit=through confirmed pivots [SOURCED]; expiry=distance/span bound [SOURCED, L-34]
- Variations that would most change the verdict: Vary the expiry bound: set by law A-21/A-22; no record varies it.
- Seats: plaus 0.44; info 41.6; null 0.66; lenses 0.48/0.61/0.44/0.51/0.50/0.36/0.29 (mean 0.456, spread 0.32)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R67 wyckoff** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Wyckoff phase & events: accumulation/distribution, springs, upthrusts, effort vs result.
- Variables: taxonomy=Wyckoff canon [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) addendum 7 names Wyckoff]; phase assignment=rules in chart_read [ARBITRARY detail]
- Variations that would most change the verdict: Vary phase-assignment rules: no record varies them.
- Seats: plaus 0.56; info 43.8; null 0.56; lenses 0.46/0.56/0.56/0.49/0.44/0.38/0.29 (mean 0.454, spread 0.27)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R68 zones_round** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Round-number S/R zones: the psychological level family in the confluence count.
- Variables: grid=round numbers [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.2]; granularity (whole/half/quarter dollars) not stated [ARBITRARY]
- Variations that would most change the verdict: Vary granularity by price level: no record varies it.
- Seats: plaus 0.36; info 30.8; null 0.67; lenses 0.37/0.44/0.28/0.35/0.35/0.30/0.19 (mean 0.326, spread 0.25)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R69 zones_swings** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: S/R zones built from swing extremes.
- Variables: zone width=not stated in the coverage record [ARBITRARY]
- Variations that would most change the verdict: Vary zone width (point level vs ATR-scaled band): no record varies it.
- Seats: plaus 0.57; info 45.4; null 0.69; lenses 0.59/0.71/0.55/0.56/0.59/0.47/0.31 (mean 0.54, spread 0.4)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R70 zones_volume_profile** — WATCH (edge-bearing)
- Evidence (as printed): class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: S/R zones from the volume profile (VAH/VAL/POC neighbourhoods).
- Variables: profile=brief window bars [SOURCED]; VA share=70% convention not stated [ARBITRARY]
- Variations that would most change the verdict: Vary the profile window: no record varies it.
- Seats: plaus 0.61; info 39.8; null 0.69; lenses 0.60/0.67/0.50/0.51/0.50/0.44/0.30 (mean 0.503, spread 0.37)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R71 iv_name** — WATCH (edge-bearing)
- Evidence (as printed): class (b) conditional, VAL 12/115 briefs; gate: fresh options gap product for the name; products build only for names on the board at build time (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Per-name IV from the chain snapshot: the options wing's raw observation.
- Variables: source=Alpaca chain snapshot [SOURCED]; TTL=3h in build_briefs [SOURCED, coverage ledger]
- Variations that would most change the verdict: Variation blocked on the product wing's timing: the named cure is build-on-board, not a parameter change.
- Seats: plaus 0.41; info 44.4; null 0.68; lenses 0.47/0.51/0.49/0.39/0.39/0.31/0.28 (mean 0.406, spread 0.23)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R72 options_positioning** — WATCH (edge-bearing)
- Evidence (as printed): class (b) conditional, VAL 6/115 briefs; gate: same options product as iv_name (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Per-name options positioning incl. largest-strike filing (extended by slate oi_concentration_name).
- Variables: source=chain snapshot [SOURCED]
- Variations that would most change the verdict: As R71.
- Seats: plaus 0.53; info 44.2; null 0.72; lenses 0.43/0.52/0.53/0.49/0.44/0.35/0.40 (mean 0.451, spread 0.18)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R73 short_interest** — WATCH (edge-bearing)
- Evidence (as printed): class (b) conditional, VAL 6/115 briefs; gate: shorts product (Reg SHO volume + FTDs landed; the item's % float and days-to-cover contents are class (c): FINRA public files refuse, Query API needs a credential the desk does not hold) (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Short interest, days to cover, short volume, FTDs (LIST fam.12): crowding evidence for both sides.
- Variables: contents landed=Reg SHO volume only in sampled builds [SOURCED, coverage ledger]; missing=SI% + days to cover [blocked, named NEEDS]
- Variations that would most change the verdict: Variation blocked on a FINRA developer credential the desk does not hold.
- Seats: plaus 0.53; info 40.8; null 0.59; lenses 0.47/0.58/0.60/0.45/0.46/0.40/0.42 (mean 0.483, spread 0.2)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R74 insider_buys** — WATCH (edge-bearing)
- Evidence (as printed): class (b) conditional, VAL 6/115 briefs; gate: EDGAR gap product (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Insider BUYS only (Form 4 code-P scan); selling is excluded by ruling (X06).
- Variables: source=EDGAR Form 4 [SOURCED, THE LIST (owner-dictated 2026-10-16, register L-35) fam.12]
- Variations that would most change the verdict: As R71 (product timing).
- Seats: plaus 0.61; info 37.6; null 0.71; lenses 0.62/0.59/0.47/0.59/0.48/0.47/0.45 (mean 0.524, spread 0.17)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R75 filings_8k** — MACHINERY (machinery)
- Evidence (as printed): class (b) conditional, VAL 6/115 briefs; gate: EDGAR gap product (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: 8-K filings as event evidence.
- Variables: source=EDGAR [SOURCED]
- Variations that would most change the verdict: Not an edge variable; product timing as R71.
- Seats: plaus 0.31; info 47.6; null 0.68; lenses 0.57/0.34/0.24/0.63/0.69/0.31/0.23 (mean 0.43, spread 0.46)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R76 earnings_reactions** — WATCH (edge-bearing)
- Evidence (as printed): class (b) conditional, VAL 6/115 briefs; gate: EDGAR gap product (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Past earnings reactions: 8-K 2.02 dates vs bars — the name's own event-response history.
- Variables: window=past reactions on file [ARBITRARY count]
- Variations that would most change the verdict: Vary the reaction window (1-day vs 5-day drift): no record varies it; the slate's power_earnings_gap builds the named setup form.
- Seats: plaus 0.61; info 45.0; null 0.71; lenses 0.56/0.61/0.47/0.49/0.54/0.48/0.31 (mean 0.494, spread 0.3)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R77 news_counts** — MACHINERY (machinery)
- Evidence (as printed): class (b) conditional, VAL 6/115 briefs; gate: news gap product (Alpaca News counts); headline content/geopolitics is not measured by design, stated on every brief (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: News counts as attention/event density.
- Variables: source=Alpaca News [SOURCED]
- Variations that would most change the verdict: Not an edge variable; variation not applicable.
- Seats: plaus 0.15; info 33.6; null 0.78; lenses 0.20/0.21/0.25/0.20/0.21/0.17/0.08 (mean 0.189, spread 0.17)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R78 attention** — WATCH (edge-bearing)
- Evidence (as printed): class (b) conditional, VAL 6/115 briefs; gate: attention gap product: Wikipedia only; Reddit is class (c), no credential-free route (403 on probe) (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Wikipedia attention as a crowding/interest gauge.
- Variables: source=Wikipedia pageviews [SOURCED]; Reddit=blocked [named NEEDS]
- Variations that would most change the verdict: Variation blocked on the Reddit route.
- Seats: plaus 0.26; info 25.4; null 0.73; lenses 0.29/0.29/0.26/0.22/0.26/0.19/0.13 (mean 0.234, spread 0.16)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R79 peers_21d** — WATCH (edge-bearing)
- Evidence (as printed): class (b) conditional, VAL 32/115 briefs; gate: name must be in the desk's sector map AND peer bars fetched (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Peer performance 21 days: the name vs its sector peers (LIST fam.13).
- Variables: window=21 days [SOURCED, L-35]; sector map=fixed ~48-name dict (core/m2_features.py SECTORS) [ARBITRARY coverage limit]
- Variations that would most change the verdict: Vary the sector source to a full-universe map: named cure in the coverage ledger, not landed in this record; the slate's peer_rs_trail extends the read to trajectory.
- Seats: plaus 0.65; info 47.2; null 0.55; lenses 0.59/0.63/0.53/0.55/0.51/0.45/0.25 (mean 0.501, spread 0.38)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R80 desk_history** — MACHINERY (machinery)
- Evidence (as printed): class (b) conditional, VAL 86/115 briefs; gate: family_record product present in the build's state (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: The family record: the selecting family's trades in the name (postmortem-refreshed nightly).
- Variables: source=state/live/family_record.json [SOURCED]
- Variations that would most change the verdict: Not an edge variable; variation not applicable.
- Seats: plaus 0.55; info 39.8; null 0.32; lenses 0.45/0.76/0.27/0.69/0.59/0.28/0.10 (mean 0.449, spread 0.66)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R81 tensor_timeframes** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): class (c), VAL 0/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: MECHANISM-ABSENT in production: Tensor timeframe agreement has no producer — the canonical engine publishes one series (Decision #108), memo rows carried no diagnostics in any sampled brief.
- Variables: frames=weekly/daily/hourly agreement [SOURCED as a LIST requirement, fam.10]; producer=NONE [blocker named in coverage ledger]
- Variations that would most change the verdict: Blocked: needs engine diagnostics + separate timeframe reads that do not exist; no variation is possible until a producer exists.
- Seats: plaus 0.13; info 11.6; null 0.58; lenses 0.05/0.01/0.05/0.00/0.05/0.04/0.05 (mean 0.036, spread 0.05)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R82 put_call_gamma** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): class (c), VAL 0/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: MECHANISM-ABSENT in production: market put/call + dealer gamma as a brief item has no product; CBOE's published statistics refused the desk's probes (AccessDenied, 2026-10-16), and dealer gamma is an inventory model, not an observation (NEEDS text).
- Variables: source=NONE [blocker: CBOE AccessDenied; the old desk's SPY GEX feed was never ported]
- Variations that would most change the verdict: Blocked on a data route; the slate's per-name gamma items (gamma_flip_name etc.) cover the per-name leg only.
- Seats: plaus 0.18; info 15.0; null 0.73; lenses 0.10/0.18/0.20/0.13/0.13/0.10/0.06 (mean 0.129, spread 0.14)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

**R83 fundamentals** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): class (c), VAL 0/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- Mechanism: Quarterly fundamentals never reach the brief BY THE ITEM'S OWN DESIGN ('deeper quarterly fundamentals ride with the sleeves, not the brief'); even its shares/market-value slice resolved 0/115 (needs a resolving CIK + mcap_facts cache).
- Variables: contents by design=shares outstanding + market value only [SOURCED, the item's own code]; quarterly fundamentals=excluded by design
- Variations that would most change the verdict: Blocked by design for the quarterly leg; the shares slice is blocked on the mcap cache route.
- Seats: plaus 0.32; info 23.6; null 0.51; lenses 0.05/0.12/0.10/0.06/0.13/0.05/0.05 (mean 0.08, spread 0.08)
- Source: femto-lean core/consideration.py registry; GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)

### S2 - The curator's scoring rubric (scoring_method_table, 24 published factors + the bands item)

**B01 family_confluence** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points={1:6, 2:16, 3:24, 4:30}, source tag 'desk', no citation (desk-set). Note as published: The rule that independent families each get one vote comes from the desk's combined read. The point steps are desk-set: the combined read gives no numbers.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: steps=6/16/24/30 for 1/2/3/4+ families [ARBITRARY, desk-set]; one-vote-per-family rule [SOURCED, Synthesis Parts V-VI]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.04; info 24.2; null 0.67; lenses 0.05/0.05/0.05/0.05/0.05/0.04/0.05 (mean 0.049, spread 0.01)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B02 tensor_confirmed** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=14 (fresh) / 4 (stale 4-10 sessions) / 0 (older), source tag 'method', citation DIP_SCORE_SPEC.md Component 4. Note as published: Tensor evidence graded by freshness: fresh trade 8 of 15, fresh watch 4, stale 2; the desk maps those proportions onto its scale where the fresh weight is 14.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: fresh weight=14 [ARBITRARY scale mapping of a SOURCED proportion]; age bands=<=3 / 4-10 / >10 sessions [SOURCED proportions, DIP_SCORE_SPEC]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.05; info 57.8; null 0.2; lenses 0.07/0.11/0.04/0.08/0.13/0.09/0.04 (mean 0.08, spread 0.09)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B03 tensor_context_only** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=7, source tag 'method', citation DIP_SCORE_SPEC.md Component 4. Note as published: Half the fresh confirmation weight, the same proportion the method gives a fresh watch.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=7 [SOURCED proportion of B02]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.01; info 20.6; null 0.32; lenses 0.05/0.05/0.04/0.06/0.06/0.05/0.01 (mean 0.046, spread 0.05)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B04 lector_tiers** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=tiers 75->10, 65->7, 55->4, 0->2; halved when ranks >3 sessions old, source tag 'desk', no citation (desk-set). Note as published: A context layer: it can add points but never creates a setup. The tier numbers are desk-set.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: tier breaks=75/65/55 [ARBITRARY]; points=10/7/4/2 [ARBITRARY]; staleness halving at >3 sessions [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.04; info 26.6; null 0.41; lenses 0.05/0.09/0.08/0.05/0.07/0.07/0.05 (mean 0.066, spread 0.04)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B05 entered** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=12, source tag 'desk', no citation (desk-set). Note as published: A filled entry is the desk's revealed conviction and outranks a plan that was only evaluated; held positions earn the same credit.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=12 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.01; info 24.8; null 0.15; lenses 0.05/0.06/0.05/0.05/0.06/0.05/0.05 (mean 0.053, spread 0.01)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B06 attempted_rejected** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=4, source tag 'desk', no citation (desk-set). Note as published: Paid only when the broker's own rejection says the account could not fund the order (buying power).
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=4 [ARBITRARY]; gate=capital-class rejection only [SOURCED, SA-4 2026-10-16]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.04; info 19.8; null 0.44; lenses 0.05/0.07/0.00/0.05/0.06/0.05/0.05 (mean 0.047, spread 0.07)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B07 regime_fear_dip_family** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=8, source tag 'desk', no citation (desk-set). Note as published: Recorded difference: the dip method's fear bonus is +10 inside a dip-depth measure this score does not compute; the desk merges fear into one market factor at 8. Fear test: SPY -1.5% or VIX +15%, desk additions VIX>=25 or red day with VIX>=20.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=8 [ARBITRARY vs method's +10]; fear thresholds=SPY -1.5% / VIX +15% [SOURCED, DIP method]; additions VIX>=25, red+VIX>=20 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.08; info 32.6; null 0.52; lenses 0.05/0.08/0.02/0.07/0.06/0.06/0.06 (mean 0.057, spread 0.06)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B08 regime_fear_other_family** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=3, source tag 'desk', no citation (desk-set). Note as published: Fear days are the dip buyers' validated habitat rather than this family's.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=3 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.02; info 24.4; null 0.43; lenses 0.05/0.05/0.04/0.05/0.07/0.05/0.05 (mean 0.051, spread 0.03)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B09 regime_uptrend_momentum** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=6, source tag 'desk', no citation (desk-set). Note as published: The dip method pays 10 in an uptrend and 0 in a downtrend without splitting by family; the desk splits by family habitat and sets its own numbers.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=6 [ARBITRARY vs method's 10]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.04; info 22.8; null 0.37; lenses 0.05/0.06/0.05/0.05/0.05/0.05/0.05 (mean 0.051, spread 0.01)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B10 regime_uptrend_dip** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=3, source tag 'desk', no citation (desk-set). Note as published: The desk's method buys dips inside uptrends, not against them. Desk-set number.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=3 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.06; info 14.0; null 0.26; lenses 0.05/0.06/0.05/0.05/0.05/0.05/0.05 (mean 0.051, spread 0.01)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B11 regime_downtrend_dip** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=2, source tag 'desk', no citation (desk-set). Note as published: Only reversal-class setups keep support in a downtrend; the dip method pays 0 in a downtrend and makes no exception.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=2 [ARBITRARY exception to the method]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.04; info 12.6; null 0.29; lenses 0.05/0.06/0.05/0.05/0.05/0.05/0.05 (mean 0.051, spread 0.01)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B12 regime_downtrend_other** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=-6, source tag 'desk', no citation (desk-set). Note as published: Trend-following entries are penalised until the regime turns.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=-6 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.07; info 20.2; null 0.23; lenses 0.05/0.05/0.04/0.04/0.05/0.05/0.05 (mean 0.047, spread 0.01)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B13 regime_chop** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=2, source tag 'desk', no citation (desk-set). Note as published: No tailwind either way; the setup stands on its own evidence.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=2 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.06; info 21.0; null 0.22; lenses 0.05/0.05/0.04/0.07/0.09/0.05/0.05 (mean 0.057, spread 0.05)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B14 reset_at_support** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=8, source tag 'method', citation DIP_SCORE_SPEC.md Component 2 (at the 20 EMA = 8, tolerance +/-1.0%). Note as published: Paid only when the close is within 1% of the 20-day average, the tolerance the method itself sets.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=8 [SOURCED, DIP_SCORE_SPEC]; tolerance=+/-1.0% of the 20 EMA [SOURCED]; tight test cured by SA-5 (the pre-cure code paid on a ~6x looser 1-ATR test)
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.02; info 31.0; null 0.5; lenses 0.10/0.14/0.07/0.10/0.09/0.05/0.07 (mean 0.089, spread 0.09)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B15 reset_near_support** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=4, source tag 'desk', no citation (desk-set). Note as published: A wider, weaker condition credited at half the method's route: close within about a day's range of the 20-day average, or reset onto the recent swing-low zone.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: points=4 [ARBITRARY]; condition=within 1 ATR of the 20-day average or the swing-low zone [ARBITRARY, the pre-SA-5 loose test kept as a lesser credit]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.01; info 29.0; null 0.5; lenses 0.08/0.11/0.03/0.06/0.07/0.05/0.05 (mean 0.064, spread 0.08)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B16 stop_ideal** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=8, source tag 'desk', citation bands per CHART_READING_METHOD section 7 (stops >=1.5 ATR; sub-1.5 ATR stops went 0W-3L in the read autopsies). Note as published: Stop distance 1.5-2.5x the daily range.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: band=1.5-2.5 ATR [SOURCED, CHART_READING_METHOD S7 + autopsy record]; points=8 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.01; info 37.2; null 0.27; lenses 0.09/0.16/0.05/0.12/0.17/0.05/0.06 (mean 0.1, spread 0.12)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B17 stop_wide_ok** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=5, source tag 'desk', citation bands per CHART_READING_METHOD S7. Note as published: Stop distance 2.5-4x the daily range.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: band=2.5-4 ATR [SOURCED]; points=5 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.02; info 26.2; null 0.45; lenses 0.07/0.12/0.05/0.11/0.07/0.06/0.05 (mean 0.076, spread 0.07)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B18 stop_tight** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=2, source tag 'desk', citation below the method's 1.5x floor. Note as published: Stop distance 1-1.5x the daily range: below the floor, noise can shake it out.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: band=1.0-1.5 ATR [SOURCED]; points=2 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.01; info 29.6; null 0.23; lenses 0.03/0.03/0.01/0.01/0.05/0.00/0.02 (mean 0.021, spread 0.05)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B19 stop_inside_noise** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=-4, source tag 'desk', no citation (desk-set). Note as published: A stop inside the normal daily range is very likely to be noise-stopped, so it deducts.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: band=<1 ATR [SOURCED concept]; points=-4 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.04; info 24.8; null 0.14; lenses 0.01/0.04/0.03/0.02/0.04/0.01/0.03 (mean 0.026, spread 0.03)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B20 stop_very_wide** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=1, source tag 'desk', no citation (desk-set). Note as published: Stop distance beyond 4x the daily range: the level is defined but a great deal of room sits between entry and exit.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: band=>4 ATR [ARBITRARY]; points=1 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.01; info 25.0; null 0.21; lenses 0.05/0.05/0.00/0.01/0.05/0.00/0.04 (mean 0.029, spread 0.05)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B21 extension_run_25** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=x0.7 multiplier, source tag 'method', citation DIP_SCORE_SPEC.md regime modifier (parabolic-spike guard). Note as published: Not a flat deduction: a name up 25%+ in 10 sessions has its finished score multiplied by 0.7.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: trigger=+25% in 10 sessions [SOURCED]; multiplier=0.7 [SOURCED]; pre-cure form was a flat -18, a conversion error cured by SA-3
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.0; info 30.6; null 0.48; lenses 0.03/0.01/0.00/0.02/0.01/0.01/0.00 (mean 0.011, spread 0.03)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B22 extension_run_15** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=-10, source tag 'desk', no citation (desk-set). Note as published: A lesser extension warning below the spike line; the method has no such tier.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: band=+15% to +25% in 10 sessions [ARBITRARY tier]; points=-10 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.02; info 26.8; null 0.5; lenses 0.04/0.01/0.02/0.05/0.01/0.00/0.01 (mean 0.02, spread 0.05)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B23 extension_above_ema** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=-8, source tag 'desk', no citation (desk-set). Note as published: Close more than 2.5x the daily range above the 20-day average: poor initiation quality even when the trend is intact.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: threshold=2.5 ATR above the 20-day average [ARBITRARY]; points=-8 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.01; info 31.8; null 0.35; lenses 0.05/0.00/0.01/0.02/0.00/0.00/0.01 (mean 0.013, spread 0.05)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B24 broken_structure** — MACHINERY (machinery)
- Evidence (as printed): Published rubric row: points=-15, source tag 'desk', no citation (desk-set). Note as published: Broken structure is one of the desk's named setup-ending faults (with heavy extension and no reset at support). The point value is desk-set.
- Mechanism: MECHANISM-ABSENT as an edge: a scoring weight inside the curator's 100-point composite; it ranks setups for the board and moves no number outside the score.
- Variables: event=close below the 20-session swing low [SOURCED concept, register L-30 family]; points=-15 [ARBITRARY]
- Variations that would most change the verdict: Vary this weight (half/double/zero ablation on the recorded boards): no record varies any rubric weight; the Stage D tests pin code-to-table consistency only, not edge.
- Seats: plaus 0.01; info 33.4; null 0.62; lenses 0.03/0.02/0.00/0.03/0.01/0.00/0.00 (mean 0.013, spread 0.03)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

**B25 tier_bands_and_minimum** — MACHINERY (machinery)
- Evidence (as printed): Published scoring_method: scale 0-100, minimum_score 35, bands 75 Top tier / 55 Strong / 35 Watch (DIP_SCORE_SPEC interpretation bands, renamed for the terminal).
- Mechanism: MECHANISM-ABSENT as an edge: publication bands over the composite score.
- Variables: MIN_SCORE=35 [ARBITRARY desk setting of a SOURCED band structure]; bands=75/55/35 [SOURCED, DIP_SCORE_SPEC interpretation bands]
- Variations that would most change the verdict: Vary MIN_SCORE or the band edges against recorded boards: no record varies them.
- Seats: plaus 0.19; info 16.0; null 0.23; lenses 0.07/0.07/0.03/0.21/0.13/0.09/0.05 (mean 0.093, spread 0.18)
- Source: muse-desk-v3 best_setups/core/setups_curator.py SCORE + scoring_method_table(); golden scoring_method in setups_latest.json

### S3 - Sleeve families (FAMILIES map; DIP_FAMILIES marked)

**F01 tensor** — WATCH (edge-bearing)
- Evidence (as printed): Family 'Tensor pattern engine': 2 member sleeves in the curator's FAMILIES map; habitat: dip-habitat (DIP_FAMILIES). One vote per family in the confluence factor (B01).
- Mechanism: The canonical Tensor engine's confirmed swings: the desk's single largest evidence item in the rubric (B02/B03) because 'Tensor + momentum are our strongest timing/selection edges' (DIP_SCORE_SPEC).
- Variables: members=tensor_swing, tensor_red_dip [SOURCED, FAMILIES map]; one-vote rule [SOURCED, Synthesis Part V]; habitat set DIP_FAMILIES membership as stated [SOURCED, Tensor selection doctrine 2026-10-08 + Decisions #75/#88]
- Variations that would most change the verdict: Vary family grouping (split/merge members, e.g. ema_vwap vs rsi_meanrev as separate votes): no record varies the grouping; Lane 3 of the Chaos Lab found mirror-twin sleeves with byte-identical journal counts inside the fleet, which is exactly the dependence this grouping exists to discount.
- Seats: plaus 0.58; info 55.4; null 0.54; lenses 0.63/0.52/0.51/0.61/0.59/0.55/0.40 (mean 0.544, spread 0.23)
- Source: muse-desk-v3 best_setups/core/setups_curator.py FAMILIES/FAMILY_LABELS/DIP_FAMILIES

**F02 intraday_pullback** — WATCH (edge-bearing)
- Evidence (as printed): Family 'intraday pullback': 6 member sleeves in the curator's FAMILIES map; habitat: dip-habitat (DIP_FAMILIES). One vote per family in the confluence factor (B01).
- Mechanism: EMA/VWAP + RSI mean-reversion entries from the same intraday/daily bar inputs: two sleeve sources, one family vote by design.
- Variables: members=ema_vwap, rsi_meanrev, ema_vwap_options, rsi_meanrev_options, morning_dip, snapback [SOURCED, FAMILIES map]; one-vote rule [SOURCED, Synthesis Part V]; habitat set DIP_FAMILIES membership as stated [SOURCED, Tensor selection doctrine 2026-10-08 + Decisions #75/#88]
- Variations that would most change the verdict: Vary family grouping (split/merge members, e.g. ema_vwap vs rsi_meanrev as separate votes): no record varies the grouping; Lane 3 of the Chaos Lab found mirror-twin sleeves with byte-identical journal counts inside the fleet, which is exactly the dependence this grouping exists to discount.
- Seats: plaus 0.53; info 32.6; null 0.52; lenses 0.53/0.56/0.46/0.46/0.52/0.42/0.30 (mean 0.464, spread 0.26)
- Source: muse-desk-v3 best_setups/core/setups_curator.py FAMILIES/FAMILY_LABELS/DIP_FAMILIES

**F03 red_day** — WATCH (edge-bearing)
- Evidence (as printed): Family 'red-day reversal': 1 member sleeves in the curator's FAMILIES map; habitat: dip-habitat (DIP_FAMILIES). One vote per family in the confluence factor (B01).
- Mechanism: Red-day reversal rules on daily bars, own logic: buys the first reversal attempt after a down day.
- Variables: members=red_day_reversal [SOURCED, FAMILIES map]; one-vote rule [SOURCED, Synthesis Part V]; habitat set DIP_FAMILIES membership as stated [SOURCED, Tensor selection doctrine 2026-10-08 + Decisions #75/#88]
- Variations that would most change the verdict: Vary family grouping (split/merge members, e.g. ema_vwap vs rsi_meanrev as separate votes): no record varies the grouping; Lane 3 of the Chaos Lab found mirror-twin sleeves with byte-identical journal counts inside the fleet, which is exactly the dependence this grouping exists to discount.
- Seats: plaus 0.46; info 33.8; null 0.59; lenses 0.49/0.44/0.45/0.44/0.42/0.46/0.25 (mean 0.421, spread 0.24)
- Source: muse-desk-v3 best_setups/core/setups_curator.py FAMILIES/FAMILY_LABELS/DIP_FAMILIES

**F04 dip_event** — WATCH (edge-bearing)
- Evidence (as printed): Family 'capitulation & fear events': 3 member sleeves in the curator's FAMILIES map; habitat: dip-habitat (DIP_FAMILIES). One vote per family in the confluence factor (B01).
- Mechanism: Capitulation / fear-event entries: buys disorderly selling events rather than structure.
- Variables: members=capitulation, capitulation_options, fear_premium [SOURCED, FAMILIES map]; one-vote rule [SOURCED, Synthesis Part V]; habitat set DIP_FAMILIES membership as stated [SOURCED, Tensor selection doctrine 2026-10-08 + Decisions #75/#88]
- Variations that would most change the verdict: Vary family grouping (split/merge members, e.g. ema_vwap vs rsi_meanrev as separate votes): no record varies the grouping; Lane 3 of the Chaos Lab found mirror-twin sleeves with byte-identical journal counts inside the fleet, which is exactly the dependence this grouping exists to discount.
- Seats: plaus 0.55; info 42.4; null 0.54; lenses 0.50/0.52/0.52/0.51/0.52/0.47/0.31 (mean 0.479, spread 0.21)
- Source: muse-desk-v3 best_setups/core/setups_curator.py FAMILIES/FAMILY_LABELS/DIP_FAMILIES

**F05 momentum_trend** — WATCH (edge-bearing)
- Evidence (as printed): Family 'momentum & trend': 12 member sleeves in the curator's FAMILIES map; habitat: continuation habitat (regime_uptrend_momentum). One vote per family in the confluence factor (B01).
- Mechanism: Trend and momentum continuation machinery: the family's edge claim is persistence of relative strength.
- Variables: members=momentum, momentum_rotation, ts_momentum_decile, legends_ema, leader_d, leader_sc, leaps_momentum, phase_daily, donchian, gate_1h, qullamaggie, qullamaggie_paper [SOURCED, FAMILIES map]; one-vote rule [SOURCED, Synthesis Part V]; habitat set DIP_FAMILIES membership as stated [SOURCED, Tensor selection doctrine 2026-10-08 + Decisions #75/#88]
- Variations that would most change the verdict: Vary family grouping (split/merge members, e.g. ema_vwap vs rsi_meanrev as separate votes): no record varies the grouping; Lane 3 of the Chaos Lab found mirror-twin sleeves with byte-identical journal counts inside the fleet, which is exactly the dependence this grouping exists to discount.
- Seats: plaus 0.67; info 42.6; null 0.51; lenses 0.67/0.69/0.66/0.68/0.68/0.66/0.51 (mean 0.65, spread 0.18)
- Source: muse-desk-v3 best_setups/core/setups_curator.py FAMILIES/FAMILY_LABELS/DIP_FAMILIES

**F06 gbm_rules** — WATCH (edge-bearing)
- Evidence (as printed): Family 'rule-score models': 6 member sleeves in the curator's FAMILIES map; habitat: not in DIP_FAMILIES. One vote per family in the confluence factor (B01).
- Mechanism: The frozen GBM / cyan rule-score family: six sleeves sharing one model, hence one vote.
- Variables: members=daily_cyan_gbm, rule_1d_cyan_smallcap, rule_1d_green_tom, rule_1h_cyan_raw, rule_1w_cyan_mom_adx, rule_1w_swing_beta_wt [SOURCED, FAMILIES map]; one-vote rule [SOURCED, Synthesis Part V]; habitat set DIP_FAMILIES membership as stated [SOURCED, Tensor selection doctrine 2026-10-08 + Decisions #75/#88]
- Variations that would most change the verdict: Vary family grouping (split/merge members, e.g. ema_vwap vs rsi_meanrev as separate votes): no record varies the grouping; Lane 3 of the Chaos Lab found mirror-twin sleeves with byte-identical journal counts inside the fleet, which is exactly the dependence this grouping exists to discount.
- Seats: plaus 0.49; info 29.6; null 0.5; lenses 0.42/0.47/0.35/0.46/0.46/0.46/0.22 (mean 0.406, spread 0.25)
- Source: muse-desk-v3 best_setups/core/setups_curator.py FAMILIES/FAMILY_LABELS/DIP_FAMILIES

**F07 m2_event** — WATCH (edge-bearing)
- Evidence (as printed): Family 'qualifier & event screens': 3 member sleeves in the curator's FAMILIES map; habitat: not in DIP_FAMILIES. One vote per family in the confluence factor (B01).
- Mechanism: M2-qualifier driven sleeves: beaten-down, winner-confluence, and earnings/buyback event screens.
- Variables: members=beatendown, confluence, earnings_buyback [SOURCED, FAMILIES map]; one-vote rule [SOURCED, Synthesis Part V]; habitat set DIP_FAMILIES membership as stated [SOURCED, Tensor selection doctrine 2026-10-08 + Decisions #75/#88]
- Variations that would most change the verdict: Vary family grouping (split/merge members, e.g. ema_vwap vs rsi_meanrev as separate votes): no record varies the grouping; Lane 3 of the Chaos Lab found mirror-twin sleeves with byte-identical journal counts inside the fleet, which is exactly the dependence this grouping exists to discount.
- Seats: plaus 0.56; info 39.4; null 0.51; lenses 0.48/0.50/0.49/0.49/0.51/0.49/0.38 (mean 0.477, spread 0.13)
- Source: muse-desk-v3 best_setups/core/setups_curator.py FAMILIES/FAMILY_LABELS/DIP_FAMILIES

### S4 - The canon-gap audit and build slate (audit 2026-10-20; CANON-GAPS-STUDY)

**G001 diamond_top_bottom** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 1 (Visual pattern, materiality MEDIUM): A broadening formation that narrows into a symmetrical triangle; one of the few named major-top shapes that is neither H&S nor double top, with its own measured move. Slate: row 11 pat_diamond: two-phase diverge-converge slopes, containment >=80%, prior move >=15%. Femto-lean key presence (grep 2026-11-15): pat_diamond present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=containment >=80%, prior move >=15% [SOURCED, canon as cited in the audit row]; materiality seat=70 @ confirmed break <=5 sessions [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.48; info 37.6; null 0.76; lenses 0.35/0.42/0.37/0.33/0.38/0.29/0.24 (mean 0.34, spread 0.18)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G002 broadening_formations** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 2 (Visual pattern, materiality MEDIUM): Expanding range with one horizontal boundary and one sloping boundary (right-angled ascending/descending, broadening tops & bottoms); the inventory's expanding wedges (both sides sloping) are not the same geometry. Slate: row 12 pat_broadening: extends the diverging branch, width ratio >=1.3. Femto-lean key presence (grep 2026-11-15): pat_broadening present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=width ratio >=1.3 [SOURCED, canon as cited in the audit row]; materiality seat=66 @ flat-side break <=5 sessions [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.43; info 36.8; null 0.71; lenses 0.34/0.44/0.34/0.32/0.32/0.25/0.25 (mean 0.323, spread 0.19)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G003 island_reversal** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 3 (Visual pattern, materiality MEDIUM-HIGH): Price gaps away, trades isolated 1+ days, gaps back: a self-contained reversal that can occur away from any drawn level, esp. on earnings/news. Slate: row 13 island_reversal in candles_gaps: aligned gap zones <=0.5 ATR, gaps >=0.75 ATR only. Femto-lean key presence (grep 2026-11-15): island_reversal present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=gap >=0.75 ATR, zone alignment <=0.5 ATR [SOURCED, canon as cited in the audit row]; materiality seat=74 @ completing gap <=3 sessions; 60 @ 4-10 [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.57; info 39.2; null 0.71; lenses 0.53/0.59/0.52/0.45/0.54/0.41/0.34 (mean 0.483, spread 0.25)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G004 rounding_bottom_top_saucer** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 4 (Visual pattern, materiality MEDIUM): Months-long gradual U (or inverted) where pressure slowly hands over; the canonical Stage-4-to-1-to-2 transition shape on weekly charts. Slate: NO slate row: the base engine rows (base_flat/base_ascending/base_on_base/base_ipo) do not name a saucer detector. Femto-lean key presence (grep 2026-11-15): no key found.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=none encoded [no producer]; seat=none
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.51; info 41.2; null 0.74; lenses 0.38/0.52/0.40/0.37/0.42/0.34/0.23 (mean 0.38, spread 0.29)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G005 bump_and_run_reversal** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 5 (Visual pattern, materiality MEDIUM): Lead-in trendline, steep parabolic bump departing it, then run back through the lead-in line: purpose-built for parabolic exhaustion reversals, with a defined trigger the inventory lacked. Slate: row 14 pat_bump_and_run: bump >=2x lead-in distance, run = close through line >=0.25 ATR. Femto-lean key presence (grep 2026-11-15): pat_bump_and_run present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=bump >=2x lead-in distance, run cross >=0.25 ATR [SOURCED, canon as cited in the audit row]; materiality seat=78 @ run_confirmed [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.54; info 36.0; null 0.77; lenses 0.41/0.47/0.46/0.46/0.47/0.41/0.30 (mean 0.426, spread 0.17)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G006 high_tight_flag** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 6 (Visual pattern, materiality HIGH): Stock rises >=100% in <=8 weeks, then flags sideways/down <=~25% for 3-5 weeks: not a bull flag; the prior doubling speed is the criterion, and the shape is rare but among the most powerful continuation bases. Slate: row 10 high_tight_flag inside the pat_flag_pennant slot: pole >=100% <=8wk (close-based >=90% floor), flag <=25% deep 1-5wk, flag RVOL < pole RVOL. Femto-lean key presence (grep 2026-11-15): high_tight_flag present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=pole >=100% (floor 90% close-based) <=8wk, flag <=25% deep, 1-5wk [SOURCED, canon as cited in the audit row]; materiality seat=72 @ HTF family & <=3% from flag pivot (the slate's only pattern-family-keyed seat, parent approval noted) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.7; info 61.2; null 0.55; lenses 0.63/0.67/0.62/0.63/0.64/0.59/0.39 (mean 0.596, spread 0.28)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G007 flat_base_oneil** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 7 (Visual pattern / structural, materiality HIGH): O'Neil flat base: >=5 weeks, <=15% deep (ideal <=10%), tight sideways after a >=30% prior advance; buy point = base high. The commonest second-stage continuation base in leaders; the shape overlaps rectangle but the rules and pivot did not exist. Slate: row 5 base_flat: prior advance >=30%, >=5wk, depth <=15%, weekly spread <=12%; near-miss files the failed rule. Femto-lean key presence (grep 2026-11-15): base_flat present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=depth <=15%, length >=5wk, prior advance >=30% [SOURCED, canon as cited in the audit row]; materiality seat=64 @ flat & <=3% from pivot [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.66; info 40.0; null 0.63; lenses 0.64/0.69/0.58/0.65/0.62/0.56/0.33 (mean 0.581, spread 0.36)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G008 ascending_base** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 8a (Visual pattern / structural, materiality MEDIUM): Three pullbacks 10-20% with higher lows over 9-16 weeks (O'Neil). Slate: row 6 base_ascending: exactly 3 pullbacks 8-22%, lows rising, 9-16wk. Femto-lean key presence (grep 2026-11-15): base_ascending present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=3 pullbacks 8-22%, 9-16wk [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.58; info 30.8; null 0.72; lenses 0.52/0.58/0.44/0.51/0.53/0.47/0.32 (mean 0.481, spread 0.26)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G009 base_on_base** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 8b (Visual pattern / structural, materiality MEDIUM): A new base forming on/just above a prior breakout (O'Neil). Slate: row 7 base_on_base: breakout + <20% advance + upper base >=3wk on the prior pivot. Femto-lean key presence (grep 2026-11-15): base_on_base present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=advance <20%, upper base >=3wk [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.63; info 34.6; null 0.7; lenses 0.55/0.63/0.52/0.55/0.55/0.52/0.35 (mean 0.524, spread 0.28)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G010 ipo_base** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 8c (Visual pattern / structural, materiality MEDIUM): First base after IPO, as short as ~7 days to 5 weeks (O'Neil). Slate: row 8 base_ipo: listing-age gate <=~18mo, base 2-7wk, depth <=35%; listing date from EDGAR or first-bar proxy, source filed. Femto-lean key presence (grep 2026-11-15): base_ipo present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=base 2-7wk, depth <=35%, listing age <=18mo [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.63; info 37.0; null 0.69; lenses 0.46/0.55/0.49/0.46/0.51/0.46/0.37 (mean 0.471, spread 0.18)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G011 cup_without_handle** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 8d (Visual pattern / structural, materiality MEDIUM): Cup-without-handle as a named variant of the cup family. Slate: row 9 cup_without_handle: _detect_cup returns variant cup_no_handle, one variant per segment. Femto-lean key presence (grep 2026-11-15): cup_without_handle present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=variant of the cup detector [SOURCED, canon as cited in the audit row]; materiality seat=60 @ fires & <=3% from rim [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.5; info 30.6; null 0.63; lenses 0.41/0.51/0.46/0.48/0.42/0.31/0.29 (mean 0.411, spread 0.22)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G012 rare_named_formations_group** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 9 (Visual pattern, materiality LOW (minor, grouped)): Three peaks & domed house (Lindsay), three falling peaks, tower top/bottom: rare, slow formations catalogued by Bulkowski (ch. 62). Slate: No dedicated slate row; the slate's micro_patterns row (G021) is the grouped micro-formation vehicle and does not name this group separately. Femto-lean key presence (grep 2026-11-15): no dedicated key found.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=none encoded separately [no producer]; seat=none
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.25; info 27.2; null 0.79; lenses 0.16/0.20/0.17/0.15/0.15/0.12/0.14 (mean 0.156, spread 0.08)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G013 micro_patterns_group** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 10 (Visual pattern, materiality LOW (minor, grouped)): Horn top/bottom, pipe top/bottom, scallops, roof/inverted roof, cloudbank, diving board, Big M/Big W as named spike variants: individually rare, often subsumed by doubles or flags; listed for census completeness. Slate: row 21 micro_patterns: _detect_micro (weekly for horn/pipe), one fire max by priority order, negative filing otherwise. Femto-lean key presence (grep 2026-11-15): micro_patterns present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=one fire max, priority order [SOURCED, canon as cited in the audit row]; materiality seat=none: considered-only (whole group) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.21; info 29.2; null 0.75; lenses 0.17/0.25/0.22/0.17/0.18/0.14/0.15 (mean 0.183, spread 0.11)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G014 v_top_v_bottom** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 11 (Visual pattern, materiality MEDIUM): Single-leg vertical reversal with no base: the anti-pattern that says there is no base, no pivot, and normal breakout entries do not apply. Slate: row 15 v_reversal: >=10% leg <=10 sessions, >=50% retrace <=10 sessions, no-base test. Femto-lean key presence (grep 2026-11-15): v_reversal present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=leg >=10% <=10 sessions, retrace >=50% [SOURCED, canon as cited in the audit row]; materiality seat=considered-only by design (a caution seat ~60 was proposed in the study and not enacted) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.52; info 40.6; null 0.63; lenses 0.38/0.56/0.45/0.45/0.39/0.31/0.36 (mean 0.414, spread 0.25)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G015 wolfe_wave** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 12 (Visual pattern, materiality LOW): 5-pivot converging structure; point 5 overshoots the 1-3 line; target on the 1-4 (EPA) line (Bulkowski chs. 75-76). Slate: NO slate row. Femto-lean key presence (grep 2026-11-15): no key found.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=5-pivot geometry per canon [SOURCED, audit row]; seat=none; producer=none
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.26; info 28.6; null 0.8; lenses 0.21/0.27/0.19/0.17/0.19/0.18/0.15 (mean 0.194, spread 0.12)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G016 dead_cat_bounce** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 13 (Visual pattern / event, materiality MEDIUM): Sharp decline, weak brief rally retracing ~20-50%, then resumption down through the prior low: the standard name for the commonest long-side trap in Stage 4 names. Slate: row 16 dead_cat_bounce: drop >=15% <=10 sessions + broken structure, bounce 20-50% on lighter volume, 3 states. Femto-lean key presence (grep 2026-11-15): dead_cat_bounce present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=drop >=15%, bounce 20-50% [SOURCED, canon as cited in the audit row]; materiality seat=72 @ confirmed_dead <=5 sessions; 58 @ bounce_forming (caution) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.64; info 42.2; null 0.7; lenses 0.59/0.66/0.54/0.55/0.54/0.41/0.49 (mean 0.54, spread 0.25)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G017 climax_top** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 14 (Visual pattern / structural, materiality HIGH (for exits / late longs)): After >=~18 weeks up from a base: near-vertical acceleration, largest gains of the move, exhaustion gaps: IBD's flagship sell signal. The desk's stretch measures flag extension statistically; the climax canon adds the behavioural sequence + time-from-base condition. Slate: row 17 climax_top: multi-component sequence detector; the selling side is a pointer to climax_base/wyckoff only (no second detector). Flag P1: read-depth ranking only, never wired to exits. Femto-lean key presence (grep 2026-11-15): climax_top present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=time-from-base >=~18wk + acceleration sequence [SOURCED, canon as cited in the audit row]; materiality seat=76 @ climax_run (read-depth ranking only, never exits) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.63; info 49.4; null 0.74; lenses 0.61/0.67/0.60/0.65/0.59/0.36/0.49 (mean 0.567, spread 0.31)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G018 trap_2b_reversal** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 15 (Structural concept, materiality MEDIUM): Sperandeo 2B: a new high/low marginally exceeds the prior one, fails, closes back inside; entry on the re-cross, stop beyond the trap extreme. A discrete, phase-free test at a prior swing extreme. Slate: row 18 trap_2b: prior >=20-session extreme, overshoot <=3%, close back inside <=3 sessions, first-fire latch. Femto-lean key presence (grep 2026-11-15): trap_2b present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=overshoot <=3%, return <=3 sessions [SOURCED, canon as cited in the audit row]; materiality seat=80 @ confirmed <=3 sessions; 63 @ unconfirmed [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.56; info 44.0; null 0.71; lenses 0.54/0.65/0.57/0.54/0.53/0.46/0.49 (mean 0.54, spread 0.19)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G019 range_events_nr4_nr7** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 16 (Visual pattern, materiality LOW): Key-reversal day, outside/inside day as pattern events; NR4/NR7 narrowest-range compression: range-statistic patterns, not candle shapes, and a standard pre-breakout compression tell. Slate: row 20 range_events: NR4/NR7, inside/outside, ID/NR4, key reversal (plain + strict), daily + weekly forms. Femto-lean key presence (grep 2026-11-15): range_events present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=NR4/NR7 windows 4/7 [SOURCED, canon as cited in the audit row]; materiality seat=58 @ ID/NR4 (or NR7+inside) at a pivot only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.55; info 36.2; null 0.61; lenses 0.47/0.61/0.37/0.44/0.40/0.44/0.33 (mean 0.437, spread 0.28)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G020 vcp_footprints** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 17 (Structural concept, materiality HIGH): Minervini VCP: 2-6 pullbacks inside a base, each shallower than the last (e.g. 25% -> 15% -> 8% -> 4%), tightening into a pivot: the modern canonical quality grade for the very bases the inventory lists by shape. Slate: row 1 vcp_footprints: _detect_vcp on BASESEG/CONTRACTIONS; files depths, ratio, footprint string, pivot, dist-to-pivot. Femto-lean key presence (grep 2026-11-15): vcp_footprints present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=2-6 contractions, each shallower [SOURCED, canon as cited in the audit row]; materiality seat=70 @ VCP & <=3% from pivot; 60 @ VCP any distance [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.69; info 59.2; null 0.57; lenses 0.68/0.70/0.66/0.69/0.68/0.65/0.65 (mean 0.673, spread 0.05)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G021 volume_dry_up** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 18 (Volume / structural, materiality HIGH): Volume falls to well below average (~40-60% below the 50-day, lowest in months) in the final contraction: Minervini/O'Neil's core supply-exhaustion tell and the reason a pivot can be bought with a tight stop. Slate: row 2 volume_dry_up: final-contraction window; min/mean vol vs VOL50, dry days, vol rank 120. Femto-lean key presence (grep 2026-11-15): volume_dry_up present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=vs VOL50, rank window 120 [SOURCED, canon as cited in the audit row]; materiality seat=65 @ dry-up inside a base [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.69; info 66.4; null 0.52; lenses 0.68/0.73/0.69/0.70/0.67/0.64/0.62 (mean 0.676, spread 0.11)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G022 pivot_tightness** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 19 (Structural concept, materiality MEDIUM-HIGH): Final area shows very narrow ranges and closes: 3-weeks-tight (weekly closes within ~1-1.5% for 3 weeks, an O'Neil add-on buy point), tight daily closes, shakeout+3. Slate: row 3 pivot_tightness: tight closes (10s spread <=3%), 3-weeks-tight, shakeout+3 (0.5-4% undercut + reclaim +3%). Femto-lean key presence (grep 2026-11-15): pivot_tightness present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=10-session close spread <=3%; undercut 0.5-4% [SOURCED, canon as cited in the audit row]; materiality seat=68 @ 3WT; 62 @ shakeout+3; tight closes considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.65; info 54.2; null 0.7; lenses 0.64/0.69/0.58/0.64/0.63/0.60/0.47 (mean 0.607, spread 0.22)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G023 base_metrics_stage** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 20 (Structural concept, materiality HIGH): Base depth, base length, and base-stage counting (1st/2nd vs 3rd/4th/late-stage) against canon limits: a Stage-2 name on its 4th base is a materially worse swing candidate than the same chart on its 1st, and the inventory could not express the difference. Slate: row 4 base_metrics_stage: walk over >=500 sessions; depth/length file always, count as lower bound when truncated. Femto-lean key presence (grep 2026-11-15): base_metrics_stage present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=history >=500 sessions; cup <=~33%, flat <=15% canon limits [SOURCED, canon as cited in the audit row]; materiality seat=66 @ late_stage (>=3rd base), direction-neutral caution [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.7; info 66.0; null 0.55; lenses 0.60/0.71/0.67/0.70/0.70/0.65/0.60 (mean 0.661, spread 0.11)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G024 ath_distance** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 21 (Structural concept, materiality MEDIUM): Distance to all-time high / blue-sky breakout: above ATH there is by definition no trapped overhead supply; the inventory stopped at the 52-week high. Slate: row 36 ath_distance (overlays cluster): % to ATH + blue-sky state; de-dup vs high_low_52w seat; files named-unavailable until the long-history product lands (Flag O3). Femto-lean key presence (grep 2026-11-15): ath_distance present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=long-history daily bars [SOURCED, canon as cited in the audit row]; materiality seat=65 @ within 3% of ATH or in blue sky [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.63; info 44.6; null 0.63; lenses 0.55/0.65/0.57/0.44/0.49/0.32/0.36 (mean 0.483, spread 0.33)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G025 smc_premium_discount** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 22 (Structural concept, materiality LOW-MEDIUM): Premium/discount & equilibrium of the dealing range (SMC): the swing range split at 50% as a standing location grade. Slate: Study section 7 resolution: ALREADY-PRESENT as fib_retracement (R46) — excluded from the slate; no second build. Femto-lean key presence (grep 2026-11-15): already present as fib_retracement.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=50% equilibrium [SOURCED, audit row: numerically the Fibonacci band's 50%]; seat=none (rides R46)
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.34; info 21.2; null 0.75; lenses 0.22/0.32/0.34/0.27/0.31/0.19/0.19 (mean 0.263, spread 0.15)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G026 andrews_pitchfork** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 23a (Overlay / structural, materiality LOW (minor)): Median line + parallels through 3 pivots (Murphy/Pring drawing-tool canon). Slate: row 33 andrews_pitchfork: from 3 confirmed pivots (shared PIVOTS). Femto-lean key presence (grep 2026-11-15): andrews_pitchfork present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=3 confirmed pivots [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.41; info 30.0; null 0.75; lenses 0.29/0.37/0.26/0.26/0.30/0.21/0.20 (mean 0.27, spread 0.17)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G027 regression_channel** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 23b (Overlay / structural, materiality LOW (minor)): Linear-regression / Raff channel: least-squares line with equidistant channels set by the furthest excursion; regression slope is the one genuinely new number. Slate: row 34 regression_channel: OLS/Raff over window +/- 2 sigma. Femto-lean key presence (grep 2026-11-15): regression_channel present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=channel +/-2 sigma [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.48; info 31.4; null 0.72; lenses 0.30/0.37/0.30/0.28/0.27/0.21/0.19 (mean 0.274, spread 0.18)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G028 ichimoku** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 24 (Overlay, materiality HIGH): Ichimoku Cloud: Tenkan (9), Kijun (26), Senkou A/B forward-plotted Cloud, Chikou: trend/support/momentum in one system, not reducible to the MA stack; price-in-cloud = no-trade is a decision the MA stack cannot make. The single biggest named-system absence at audit. Slate: row 22 ichimoku: standard spans; cloud state, TK-cross events + strength class. Femto-lean key presence (grep 2026-11-15): ichimoku present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=spans 9/26/52 standard [SOURCED, canon as cited in the audit row]; materiality seat=62 @ strong TK cross <=5 sessions; 60 @ cloud state change <=3 sessions [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.54; info 50.6; null 0.67; lenses 0.43/0.63/0.50/0.51/0.46/0.39/0.30 (mean 0.46, spread 0.33)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G029 donchian** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 25 (Overlay, materiality MEDIUM): Donchian channels (20/55-day): the Turtle breakout system; the canonical systematic N-day breakout/exit levels against the inventory's discretionary swing S/R. Slate: row 25 donchian: 20/55 highest-high/lowest-low, read-side only (the desk's donchian sleeve untouched). Femto-lean key presence (grep 2026-11-15): donchian present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=windows 20/55 [SOURCED, canon as cited in the audit row]; materiality seat=70 @ first 55-session break <=5 sessions; 60 @ 20-session [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.62; info 42.2; null 0.71; lenses 0.58/0.65/0.54/0.62/0.47/0.42/0.57 (mean 0.55, spread 0.23)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G030 keltner** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 26 (Overlay, materiality MEDIUM): Keltner channels: 20-day EMA +/- 2x ATR. The Bollinger/Keltner comparison is itself canonical: BB inside Keltner (TTM-style squeeze) is a standard squeeze definition the BB-width percentile alone does not give. Slate: row 26 keltner: EMA20 +/- 2xATR10; true squeeze_on + squeeze_fired; cure: bollinger consumes squeeze_on (Flags O1/O4: the seat move from bollinger is the parent's call; default keeps the existing bollinger seat). Femto-lean key presence (grep 2026-11-15): keltner present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=EMA20 +/- 2xATR10 [SOURCED, canon as cited in the audit row]; materiality seat=65 @ squeeze_fired <=3 sessions (seat move not enacted by default) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.55; info 42.2; null 0.73; lenses 0.47/0.62/0.39/0.36/0.33/0.28/0.33 (mean 0.397, spread 0.34)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G031 parabolic_sar** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 27 (Overlay, materiality LOW-MEDIUM): Wilder's accelerating trailing dots; flips = stop-and-reverse. Its one unique contribution is an accelerating trailing level. Slate: row 27 parabolic_sar: Wilder SAR (0.02/0.20), flip events, distance-to-SAR. Read-only (Flag O2). Femto-lean key presence (grep 2026-11-15): parabolic_sar present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=AF 0.02 step / 0.20 max [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.33; info 28.4; null 0.71; lenses 0.35/0.35/0.27/0.35/0.29/0.26/0.24 (mean 0.301, spread 0.11)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G032 supertrend** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 28 (Overlay, materiality MEDIUM): ATR-banded trailing line (commonly 10-period ATR x3) flipping side on close through it: a binary trend-state + trailing stop in one line, and an external reproducible benchmark of trend on/off. Slate: row 28 supertrend: ATR10 x3 final-band ratchet; flip events + age; read-side only. Femto-lean key presence (grep 2026-11-15): supertrend present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=ATR10 x3 [SOURCED, canon as cited in the audit row]; materiality seat=58 @ flip_age <=3 [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.48; info 30.2; null 0.64; lenses 0.39/0.51/0.33/0.40/0.37/0.29/0.28 (mean 0.367, spread 0.23)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G033 atr_trailing_levels** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 29_70 (Overlay / volatility, materiality MEDIUM): Chandelier Exit as a plotted level (22-period highest high - 3x ATR) plus Wilder volatility stop: converts ATR into the canonical trailing-stop price; slate row 29 folds audit row 70 (ATR trailing stops as a system) into this one item. Slate: row 29 atr_trailing_levels: Chandelier 22 / 3xATR22 + Wilder vol stop, filed as levels. Hard rule: never scored, never wired to exits/stops/dispatch (Flag O2). Femto-lean key presence (grep 2026-11-15): atr_trailing_levels present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=22-period, 3x ATR22 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only, never scored [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.34; info 28.8; null 0.69; lenses 0.54/0.61/0.42/0.57/0.43/0.31/0.31 (mean 0.456, spread 0.3)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G034 gmma** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 30 (Overlay, materiality LOW): Guppy GMMA: 6 short EMAs (3-15) + 6 long EMAs (30-60) read as two ribbons; compression/expansion = agreement/change. Information largely already carried by the MA stack + trend-strength system. Slate: row 32 gmma: EMA groups 3-15 vs 30-60, agreement/spread states, kernels named in data. Femto-lean key presence (grep 2026-11-15): gmma present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=EMA groups 3-15 / 30-60 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.19; info 13.0; null 0.79; lenses 0.23/0.33/0.23/0.24/0.21/0.16/0.21 (mean 0.23, spread 0.17)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G035 alt_ma_types_cross_events** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 31 (Overlay, materiality LOW (minor)): Alternate MA types as a stated choice (EMA vs SMA, Hull, weighted, McGinley) and MA slope/cross events beyond price-vs-MA (the 50/200 cross as a widely-watched regime event). Mostly a specification gap. Slate: NO slate row: the slate builds gmma (G034) but no MA-type/cross-event item. Femto-lean key presence (grep 2026-11-15): no key found.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=none encoded [no producer]; seat=none
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.14; info 20.6; null 0.83; lenses 0.19/0.27/0.17/0.20/0.20/0.14/0.14 (mean 0.187, spread 0.13)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G036 pivot_points** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 32 (Overlay / price level, materiality MEDIUM): Pivot point systems (floor, Fibonacci, Camarilla, Woodie, DeMark) + Central Pivot Range from prior-period H/L/C: a genuinely orthogonal, pre-computed S/R source for the confluence count. Slate: row 23 pivot_points: all five systems + CPR on completed weekly & monthly periods; feeds level_confluence. Femto-lean key presence (grep 2026-11-15): pivot_points present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=weekly & monthly completed periods [SOURCED, canon as cited in the audit row]; materiality seat=considered-only (feeds level_confluence R47) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.4; info 42.6; null 0.66; lenses 0.35/0.48/0.33/0.34/0.32/0.29/0.22 (mean 0.333, spread 0.26)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G037 prior_period_levels** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 33 (Structural / price level, materiality MEDIUM): Prior day/week/month high-low & open (PDH/PDL, PWH/PWL, PMH/PML) carried as lines: embarrassingly basic and absent at audit; a specific, dated, everyone-sees-it level that need not coincide with a swing zone. Slate: row 24 prior_period_levels: PDH/PDL/PDO, PWH/PWL, PMH/PML + break/retest event states. Femto-lean key presence (grep 2026-11-15): prior_period_levels present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=completed prior periods [SOURCED, canon as cited in the audit row]; materiality seat=68 @ wicked-through-closed-back at PWH/PMH <=3 sessions; 60 @ close cross [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.58; info 50.2; null 0.5; lenses 0.55/0.69/0.56/0.50/0.46/0.45/0.32 (mean 0.504, spread 0.37)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G038 vwap_bands** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 34 (Overlay / volume, materiality MEDIUM): VWAP standard-deviation bands (+/-1/2/3 sigma), session and anchored: converts above/below VWAP into how stretched vs fair value; anchored +/-2 sigma is a standard profit-taking/exhaustion reference. Slate: row 30 vwap_bands: 20-session + anchored VWAP +/-1/2/3 sigma, z filed; labelled as a daily-bar VWAP construction. Femto-lean key presence (grep 2026-11-15): vwap_bands present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=bands +/-1/2/3 sigma, z filed [SOURCED, canon as cited in the audit row]; materiality seat=60 @ |z| >=2.0 on a non-young anchor; 55 @ return inside +/-2 sigma <=3 sessions [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.52; info 40.2; null 0.69; lenses 0.56/0.64/0.57/0.59/0.58/0.43/0.37 (mean 0.534, spread 0.27)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G039 anchored_vwap_anchors_ext** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 35 (Volume / overlay, materiality LOW-MEDIUM): Additional AVWAP anchors: IPO date, all-time high, gap day, year-start/YTD, prior earnings cycle (earnings and major-swing anchors already present as R43). Slate: row 31: an extension of the existing anchored_vwap item, no new key. Femto-lean key presence (grep 2026-11-15): anchored_vwap present (extension).
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=anchors added: IPO, ATH, gap day, YTD, prior earnings cycle [SOURCED, canon as cited in the audit row]; materiality seat=considered-only (extends a considered-only item) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.28; info 29.4; null 0.78; lenses 0.33/0.45/0.29/0.32/0.31/0.23/0.27 (mean 0.314, spread 0.22)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G040 heikin_ashi** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 36 (Visual / chart type, materiality LOW (minor)): Heikin-Ashi chart view: averaged candles smoothing trend colour runs; a standard alternate view, not new information (it hides real opens/gaps, which this desk trades). Slate: row 35 heikin_ashi: HA series + streak/doji states; view-only characterisation. Femto-lean key presence (grep 2026-11-15): heikin_ashi present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=HA construction standard [SOURCED, canon as cited in the audit row]; materiality seat=considered-only, permanently [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.07; info 12.4; null 0.86; lenses 0.12/0.14/0.07/0.08/0.12/0.09/0.05 (mean 0.096, spread 0.09)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G041 cci** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 37 (Oscillator, materiality MEDIUM): CCI: (typical price - its SMA) / (0.015 x mean deviation); +/-100 = unusual strength. The most defensible oscillator gap at audit: catches trend-start thrusts differently from RSI's gain/loss ratio. Slate: NO slate row: the oscillators cluster's 22 rows do not include CCI, and the slate reconciliation does not name it. Femto-lean key presence (grep 2026-11-15): no key found (the string 'cci' matches only inside 'Fibonacci').
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=(TP-SMA)/(0.015 x MD), +/-100 zones [SOURCED, audit row]; seat=none; producer=none
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.32; info 30.4; null 0.69; lenses 0.37/0.50/0.37/0.32/0.34/0.32/0.29 (mean 0.359, spread 0.21)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G042 williams_r** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 38 (Oscillator, materiality LOW): Williams %R: the close's position in the N-day range, inverted 0 to -100; a near-duplicate of the stochastic (present). Completeness only. Slate: row 38 williams_r: %R(14) level + zone state. Femto-lean key presence (grep 2026-11-15): williams_r present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=%R(14) [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.16; info 10.4; null 0.86; lenses 0.14/0.17/0.09/0.14/0.15/0.13/0.10 (mean 0.131, spread 0.08)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G043 roc_oscillator** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 39 (Oscillator, materiality LOW): ROC as a plotted oscillator incl. 12-month ROC; 6-month momentum + rank (present) is ROC in substance. Slate: NO slate row as a standalone item (ROC lives inside the KST composite, G052). Femto-lean key presence (grep 2026-11-15): no standalone key found.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=N-period % change [SOURCED, audit row]; seat=none; producer=none as a standalone
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.17; info 13.0; null 0.75; lenses 0.18/0.23/0.16/0.17/0.17/0.14/0.15 (mean 0.171, spread 0.09)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G044 stoch_rsi** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 40 (Oscillator, materiality LOW): StochRSI: the stochastic formula applied to RSI values; faster/more extreme RSI, redundant for a desk running RSI + stochastic + a 7-gauge divergence set. Slate: NO slate row. Femto-lean key presence (grep 2026-11-15): no key found.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=stochastic of RSI [SOURCED, audit row]; seat=none; producer=none
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.11; info 10.2; null 0.85; lenses 0.14/0.15/0.10/0.11/0.13/0.08/0.09 (mean 0.114, spread 0.07)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G045 aroon** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 41 (Oscillator, materiality MEDIUM): Aroon Up/Down + Oscillator: % of time since the N-day high/low — a genuinely different input (time since extreme, not price change); the canonical how-fresh-is-this-trend gauge. Slate: NO slate row: absent from the oscillators cluster's 22 rows. Femto-lean key presence (grep 2026-11-15): aroon absent (the only slate-adjacent key the 2026-11-15 grep found missing).
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=25-day time-since-extreme [SOURCED, audit row]; seat=none; producer=none
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.41; info 39.2; null 0.7; lenses 0.42/0.55/0.36/0.42/0.35/0.36/0.30 (mean 0.394, spread 0.25)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G046 vortex** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 42 (Oscillator, materiality LOW): Vortex Indicator VI+/VI-: true-range-normalised up/down movement sums; crossovers mark trend starts; overlaps ADX/DMI (present). Slate: row 39 vortex: VI+/VI-(14) + cross state. Femto-lean key presence (grep 2026-11-15): vortex present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=period 14 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.27; info 20.8; null 0.73; lenses 0.28/0.35/0.26/0.24/0.25/0.21/0.18 (mean 0.253, spread 0.17)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G047 trix** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 43 (Oscillator, materiality LOW): TRIX: rate of change of a triple-smoothed EMA with signal line; slower than the MACD already present. Slate: row 40 trix: triple-EMA(15) ROC % + signal state. Femto-lean key presence (grep 2026-11-15): trix present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=triple EMA 15 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.19; info 11.4; null 0.75; lenses 0.20/0.29/0.17/0.18/0.19/0.15/0.14 (mean 0.189, spread 0.15)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G048 ultimate_oscillator** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 44 (Oscillator, materiality LOW): Ultimate Oscillator: buying pressure averaged over 3 windows (7/14/28); designed to fix single-window divergence flaws the desk's 7-gauge x 2-frame set already addresses. Slate: row 41 ultimate_oscillator: 7/14/28 BP/TR weighted 4/2/1. Femto-lean key presence (grep 2026-11-15): ultimate_oscillator present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=windows 7/14/28, weights 4/2/1 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.21; info 12.8; null 0.71; lenses 0.22/0.27/0.18/0.20/0.21/0.16/0.17 (mean 0.201, spread 0.11)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G049 awesome_oscillator** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 45 (Oscillator, materiality LOW): Awesome Oscillator: 5-period SMA of midpoints minus 34-period SMA of midpoints; a cruder MACD-histogram analogue. Slate: row 42 awesome_oscillator: SMA5-SMA34 median price + saucer state. Femto-lean key presence (grep 2026-11-15): awesome_oscillator present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=SMA 5/34 of midpoints [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.15; info 10.8; null 0.75; lenses 0.17/0.19/0.13/0.16/0.16/0.13/0.13 (mean 0.153, spread 0.06)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G050 cmo** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 46 (Oscillator, materiality LOW): CMO: (sum up - sum down)/(sum up + sum down) x 100; an RSI-like alternative answering no new question. Slate: row 43 cmo: CMO(14) up/down change sums. Femto-lean key presence (grep 2026-11-15): cmo present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=period 14 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.16; info 10.8; null 0.82; lenses 0.15/0.18/0.13/0.16/0.16/0.11/0.11 (mean 0.143, spread 0.07)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G051 kst** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 47 (Oscillator, materiality LOW-MEDIUM): KST (Pring): weighted sum of 4 smoothed ROCs (10/15/20/30) + signal line: the published canon for momentum across horizons in one line, esp. weekly KST for primary-trend turns. Slate: row 44 kst: ROC 10/15/20/30 smoothed, weighted 1/2/3/4 + signal. Study flag: weekly KST is the candidate if a composite-momentum seat is ever wanted; none proposed. Femto-lean key presence (grep 2026-11-15): kst present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=ROCs 10/15/20/30, weights 1/2/3/4 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.35; info 29.2; null 0.61; lenses 0.37/0.42/0.41/0.35/0.33/0.25/0.30 (mean 0.347, spread 0.17)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G052 coppock** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 48 (Oscillator, materiality LOW for swing): Coppock Curve: WMA of (14-mo ROC + 11-mo ROC), a long-term buy-signal oscillator built for monthly major-bottom identification — slower than this desk's holding horizon. Slate: row 45 coppock: WMA10 of ROC14+ROC11 on monthly closes. Study flag: the parent may rule Coppock belongs only in the market (SPY) record; per-name, expect a high fail-closed rate on history. Femto-lean key presence (grep 2026-11-15): coppock present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=monthly ROC 14 + 11, WMA 10 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.28; info 13.6; null 0.73; lenses 0.24/0.33/0.17/0.23/0.22/0.20/0.16 (mean 0.221, spread 0.17)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G053 elder_ray** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 49a (Oscillator, materiality LOW (grouped in audit row 49)): Elder-Ray Bull/Bear Power: high/low vs the 13-EMA as buyer/seller power; plus Elder Impulse colour. Slate: row 46 elder_ray: Bull/Bear Power vs EMA13 + Impulse colour. Femto-lean key presence (grep 2026-11-15): elder_ray present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=EMA 13 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.3; info 21.2; null 0.7; lenses 0.28/0.40/0.28/0.28/0.25/0.20/0.18 (mean 0.267, spread 0.22)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G054 mass_index** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 49b (Oscillator, materiality LOW (grouped in audit row 49)): Mass Index: range-expansion reversal warning (reversal bulge). Slate: row 47 mass_index: sum-25 EMA-ratio; bulge event >27 -> <26.5. Femto-lean key presence (grep 2026-11-15): mass_index present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=bulge >27 then <26.5 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.17; info 12.2; null 0.74; lenses 0.18/0.25/0.20/0.18/0.18/0.15/0.14 (mean 0.183, spread 0.11)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G055 choppiness** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 49c (Oscillator, materiality LOW (grouped in audit row 49)): Choppiness Index: a trending-vs-chopping gauge; ADX + BB-width + ATR already answer its main question for a swing desk. Slate: row 48 choppiness: Choppiness(14); >61.8 / <38.2 states. Femto-lean key presence (grep 2026-11-15): choppiness present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=period 14, states 61.8/38.2 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.23; info 14.6; null 0.74; lenses 0.18/0.29/0.18/0.22/0.18/0.17/0.13 (mean 0.193, spread 0.16)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G056 dpo** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 49d (Oscillator, materiality LOW (grouped in audit row 49)): Detrended Price Oscillator: cycle-length detrending. Slate: row 49 dpo: DPO(20) detrended close vs SMA. Femto-lean key presence (grep 2026-11-15): dpo present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=period 20 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.2; info 11.0; null 0.74; lenses 0.17/0.22/0.16/0.16/0.18/0.13/0.12 (mean 0.163, spread 0.1)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G057 td_sequential** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 50 (Oscillator / structural, materiality LOW-MEDIUM): TD Sequential / DeMark counts: consecutive closes vs the close 4 bars earlier to 9 (setup) and 13 (countdown) = an exhaustion count; a pure price-sequence count distinct from RSI/MACD overbought readings. Slate: row 50 td_sequential: Setup 9 + Countdown 13, perfection flags. Naming flag V2: 'TD Sequential'/'DeMark' are trademarks; the public-surface label is the parent's call. Femto-lean key presence (grep 2026-11-15): td_sequential present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=setup 9, countdown 13, lookback 4 [SOURCED, canon as cited in the audit row]; materiality seat=60 @ 13-count; 52 @ perfected 9 [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.33; info 30.4; null 0.69; lenses 0.33/0.35/0.30/0.29/0.28/0.25/0.19 (mean 0.284, spread 0.16)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G058 cmf** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 51 (Volume, materiality MEDIUM-HIGH): Chaikin Money Flow: money-flow volume summed over ~21 days / total volume, bounded and zero-centred: 'over the last month, has money flow been net positive, and how strongly?' — not the A/D line, MFI or OBV. Its absence from a volume section this detailed was conspicuous at audit. Slate: NO slate row: the oscillators/volume cluster's rows include the Chaikin Oscillator (G059) but not CMF itself. Femto-lean key presence (grep 2026-11-15): no key found (the string 'cmf' matches only inside other words).
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=21-day money-flow volume ratio [SOURCED, audit row]; seat=none; producer=none in femto-lean core. NOTE: the book's gestalt register (Lane 6) carries CMF as a Pass A volume variable with consumption unverified — the variable exists in the book's read set, its brief consumption does not.
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.39; info 48.6; null 0.52; lenses 0.55/0.60/0.37/0.54/0.44/0.31/0.34 (mean 0.45, spread 0.29)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G059 chaikin_oscillator** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 52 (Volume, materiality LOW): Chaikin Oscillator: MACD (3,10) of the Accumulation/Distribution Line; largely a faster CMF/A-D divergence tool. Slate: row 51 chaikin_oscillator: EMA3-EMA10 of the A/D line. Femto-lean key presence (grep 2026-11-15): chaikin_oscillator present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=EMA 3/10 of A/D [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.23; info 14.8; null 0.73; lenses 0.24/0.32/0.23/0.20/0.19/0.18/0.21 (mean 0.224, spread 0.14)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G060 force_index** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 53 (Volume, materiality MEDIUM): Force Index (Elder): (close - prior close) x volume, smoothed 2-day (timing) and 13-day (trend of force); the 2-day dips below zero in an uptrend are the standard buyable-pullback test no OBV/A-D/MFI replicates. Slate: row 52 force_index: EMA2/EMA13. Femto-lean key presence (grep 2026-11-15): force_index present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=EMA 2 / 13 [SOURCED, canon as cited in the audit row]; materiality seat=55 @ Elder pullback condition [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.46; info 41.8; null 0.56; lenses 0.40/0.54/0.38/0.42/0.35/0.31/0.25 (mean 0.379, spread 0.29)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G061 ease_of_movement** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 54 (Volume, materiality LOW): Ease of Movement (EMV/Arms): distance moved per unit of volume, scaled by range; conceptually adjacent to Wyckoff effort-vs-result (present). Slate: row 53 ease_of_movement: EMV 14-period smoothed. Femto-lean key presence (grep 2026-11-15): ease_of_movement present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=period 14 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.21; info 18.6; null 0.75; lenses 0.27/0.28/0.24/0.26/0.23/0.22/0.20 (mean 0.243, spread 0.08)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G062 klinger** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 55 (Volume, materiality LOW): Klinger Oscillator: difference of 34- and 55-period EMAs of volume force + 13 signal; a long-horizon money-flow oscillator. Slate: row 54 klinger: EMA34-EMA55 of force volume. Femto-lean key presence (grep 2026-11-15): klinger present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=EMA 34/55 + 13 signal [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.26; info 24.2; null 0.73; lenses 0.25/0.24/0.21/0.21/0.23/0.17/0.18 (mean 0.213, spread 0.08)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G063 vwma** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 56 (Volume / overlay, materiality LOW): VWMA(20): a volume-weighted moving average; AVWAP (present, R43) covers the concept in anchored form. Slate: row 55 vwma: VWMA(20) + price-vs-VWMA state. Femto-lean key presence (grep 2026-11-15): vwma present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=period 20 [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.2; info 12.8; null 0.77; lenses 0.30/0.34/0.21/0.26/0.25/0.18/0.17 (mean 0.244, spread 0.17)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G064 up_down_volume** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 57 (Volume, materiality MEDIUM): Up/down volume ratio (50-day) and accumulation-week counts per name: the classic O'Neil/IBD accumulation gauge as a quotable single number (>1.0 bullish, ~1.3+ strong), computable from data the desk already uses — a naming/computation gap, not a data gap. Slate: row 56 up_down_volume: 50d sum-up/sum-down ratio + accumulation-week counts. Femto-lean key presence (grep 2026-11-15): up_down_volume present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=window 50 days [SOURCED, canon as cited in the audit row]; materiality seat=55 @ ratio >=1.3 / <=0.7 [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.53; info 32.2; null 0.51; lenses 0.58/0.66/0.49/0.62/0.59/0.53/0.48 (mean 0.564, spread 0.18)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G065 volume_lines_alt** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 58 (Volume, materiality LOW (minor, grouped)): Negative/Positive Volume Index (NVI/PVI), Price-Volume Trend (PVT), Williams A/D: older-canon volume lines (Granville/Fosback era), grouped as one item. Slate: row 59 volume_lines_alt: NVI / PVI / PVT / Williams A/D in one item. Femto-lean key presence (grep 2026-11-15): volume_lines_alt present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=four legacy lines, one filing [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.22; info 18.2; null 0.76; lenses 0.22/0.28/0.24/0.19/0.20/0.18/0.17 (mean 0.211, spread 0.11)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G066 tpo_profile** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 59 (Volume / structural, materiality LOW): Market-profile time dimension beyond VA/POC: TPO distribution shape (P/b/D profiles), single prints, poor highs/lows; VAH/VAL/POC (present) carry most of the value. Slate: row 37 tpo_profile (overlays cluster): TPO counts/shape, single prints, poor highs/lows; files named-unavailable until the 30-min SIP bars product lands (Flag O3). Femto-lean key presence (grep 2026-11-15): tpo_profile present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=30-min SIP bars product [route named, product pending per Flag O3] [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.35; info 29.4; null 0.66; lenses 0.39/0.52/0.39/0.38/0.33/0.30/0.30 (mean 0.373, spread 0.22)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G067 expected_move** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 60 (Volatility / options-level, materiality HIGH): Expected move to expiry/earnings: ~0.85 x ATM straddle (or IV x spot x sqrt(T)) — the options market's 1-sigma range for the period; the canonical yardstick for whether a measured-move target sits inside or outside what is already priced, and for sizing an earnings hold. Slate: row 60 expected_move: ATM straddle (x0.85 stated) + IV x sqrt(T), to standing expiry and to next earnings; prerequisite P0 chain retention. Femto-lean key presence (grep 2026-11-15): expected_move present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=straddle x0.85 convention stated in the item [SOURCED, canon as cited in the audit row]; materiality seat=65 @ target-beyond-band / hold-spans-earnings [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.31; info 62.4; null 0.63; lenses 0.23/0.64/0.46/0.30/0.48/0.24/0.40 (mean 0.393, spread 0.41)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G068 hv_percentile** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 61 (Volatility, materiality MEDIUM): HV percentile/rank (HV10/20/30/60 vs own 1-yr): separates 'IV is high because the stock really is moving' from 'IV is high and the stock is dead'. Slate: row 57 hv_percentile (oscillators cluster; the duplicate claim by the options cluster resolved: built once, study section 7). Femto-lean key presence (grep 2026-11-15): hv_percentile present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=HV 10/20/30/60 vs trailing 1-yr [SOURCED, canon as cited in the audit row]; materiality seat=55 @ HV20 pct >=90 / <=10 [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.48; info 36.2; null 0.53; lenses 0.57/0.63/0.49/0.47/0.51/0.35/0.37 (mean 0.484, spread 0.28)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G069 gamma_flip_name** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 62 (Options-level, materiality MEDIUM-HIGH): Gamma flip / zero-gamma level per name: the price where aggregate dealer gamma changes sign; above = vol-suppressing/pinning, below = vol-amplifying/trending. Aggregate GEX (present) is a quantity; the flip is the level that belongs in the S/R confluence count. Slate: row 61 gamma_flip_name: compute_gex unchanged, per name, <=60d; liquidity floor >=50 contracts & >=5,000 total OI else unavailable with counts. Femto-lean key presence (grep 2026-11-15): gamma_flip_name present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=<=60d expiries; OI floor 50 contracts / 5,000 total [SOURCED, canon as cited in the audit row]; materiality seat=considered-only (by Ruling 1 in the study) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.48; info 49.8; null 0.63; lenses 0.48/0.58/0.61/0.42/0.52/0.37/0.57 (mean 0.507, spread 0.24)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G070 gamma_walls_name** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 63 (Options-level, materiality MEDIUM-HIGH): Call wall / put wall per name: the strikes with the largest call/put gamma — the most-quoted options-derived S/R levels in modern practice, and an independent level source for the confluence stack. Slate: row 62 gamma_walls_name: largest call-gamma / put-gamma strikes from the per-strike gamma map. Femto-lean key presence (grep 2026-11-15): gamma_walls_name present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=per-strike gamma map from the retained chain [SOURCED, canon as cited in the audit row]; materiality seat=55 @ wall coincides with a counted shelf [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.48; info 47.0; null 0.65; lenses 0.48/0.62/0.57/0.43/0.45/0.33/0.54 (mean 0.489, spread 0.29)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G071 max_pain_name** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 64 (Options-level, materiality MEDIUM (into expiry) / LOW otherwise): Max pain: the strike minimising total open-option value to buyers at expiry; a magnet mainly into a large expiry in a positive-gamma regime. Slate: row 63 max_pain_name: per-expiry payout-minimising strike from the full OI map. Femto-lean key presence (grep 2026-11-15): max_pain_name present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=per-expiry OI map [SOURCED, canon as cited in the audit row]; materiality seat=considered-only (optional 50 in OpEx conjunction — parent enacts) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.25; info 26.4; null 0.74; lenses 0.24/0.31/0.28/0.21/0.24/0.17/0.27 (mean 0.246, spread 0.14)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G072 oi_concentration_name** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 65 (Options-level / context, materiality MEDIUM): Open-interest strike concentration per name by expiry: the raw material behind the flip/walls/max-pain items and behind pin risk at a strike. Slate: row 64 oi_concentration_name: full strike x expiry OI map, top-strike share, volume-vs-OI read. Femto-lean key presence (grep 2026-11-15): oi_concentration_name present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=strike x expiry OI map [SOURCED, canon as cited in the audit row]; materiality seat=considered-only (optional 50 @ top-1 >=40% — parent enacts) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.51; info 47.6; null 0.67; lenses 0.59/0.66/0.58/0.60/0.62/0.39/0.67 (mean 0.587, spread 0.28)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G073 iv_skew_name** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 66 (Volatility / options, materiality MEDIUM): IV skew per name: which tail the market is paying for (25-delta put IV minus ATM IV); steepening put skew into an event is a hedging-demand warning a single ATM IV flattens away. Slate: row 65 iv_skew_name: 25d-put IV vs ATM at a stated expiry; BS-delta fallback if snapshot delta absent (Flag X3: greeks.delta not proven by any desk code read in the study pass). Femto-lean key presence (grep 2026-11-15): iv_skew_name present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=25-delta put vs ATM [SOURCED, canon as cited in the audit row]; materiality seat=60 @ own-history pct >=90 / <=10 (after 20 readings) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.5; info 46.6; null 0.56; lenses 0.62/0.66/0.45/0.62/0.57/0.41/0.55 (mean 0.554, spread 0.25)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G074 iv_term_name** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 67 (Volatility / options, materiality MEDIUM): IV term structure per name: contango vs backwardation — the fastest way to see when the market thinks the move happens and whether an event premium sits in the front expiry. Slate: row 66 iv_term_name: ATM IV by expiry; backwardation/contango with an earnings-kink explanation check. Femto-lean key presence (grep 2026-11-15): iv_term_name present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=ATM IV by expiry [SOURCED, canon as cited in the audit row]; materiality seat=60 @ unexplained backwardation [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.52; info 40.0; null 0.56; lenses 0.60/0.63/0.63/0.60/0.58/0.45/0.67 (mean 0.594, spread 0.22)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G075 options_flow_name** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 68 (Options-level / context, materiality MEDIUM): Unusual options flow (sweeps/blocks/opening size vs OI) per name: the desk had no flow input at all; the sources' caveat stands — flow is risk transfer as often as directional bets, a flag to investigate, not a signal. Slate: row S1 (8g): a NAMED-UNAVAILABLE STAMP, not a producer: 'no options trades tape reaches the desk'. NEEDS: an executed options trades tape (Alpaca v1beta1 options trades / OPRA feed) if the subscription admits it — unprobed as of 2026-10-20 — or a flow vendor subscription. Femto-lean key presence (grep 2026-11-15): stamp only (options_flow_name key is the stamp).
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=none [no tape]; seat=none; blocker=the unprobed Alpaca v1beta1 options/trades endpoint (study options Flag 1: one subscription probe converts the verdict from presumed-unavailable to measured)
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.27; info 33.6; null 0.68; lenses 0.21/0.29/0.28/0.24/0.27/0.19/0.29 (mean 0.253, spread 0.1)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G076 opex_calendar_name** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 69 (Context / options, materiality LOW-MEDIUM): Monthly OpEx timing & pin risk as a calendar item: third-Friday expiry (and quarterly witching) as a dated influence on range/pinning and post-expiry release. Slate: row 67 opex_calendar_name: third-Friday OpEx + witching dates; pin-risk conjunction (spot near a high-OI strike into OpEx). Femto-lean key presence (grep 2026-11-15): opex_calendar_name present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=calendar computed + retained OI map [SOURCED, canon as cited in the audit row]; materiality seat=55 @ 3-way conjunction [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.41; info 30.0; null 0.71; lenses 0.37/0.55/0.47/0.37/0.41/0.28/0.36 (mean 0.401, spread 0.27)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G077 market_distribution_days** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 71 (Market-internal, materiality HIGH): Distribution-day count (index): down >=~0.2% on higher volume; ~5-6 in ~25 sessions = uptrend under pressure. A regime label cannot substitute for the count: distribution clusters are O'Neil's canonical reason to de-gross swing longs before the index breaks. Slate: row 69 market_distribution_days: IBD count, 25-session window, >=6% early expiry, stalling days included. Femto-lean key presence (grep 2026-11-15): market_distribution_days present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=threshold -0.2% on rising volume, 25-session window [SOURCED, canon as cited in the audit row]; materiality seat=65 @ count >=5 [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.65; info 65.2; null 0.46; lenses 0.69/0.71/0.65/0.70/0.66/0.60/0.47 (mean 0.64, spread 0.24)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G078 market_follow_through** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 72 (Market-internal, materiality HIGH): Follow-through day: on day 4+ of a rally attempt, a major index rises >=~1.25-1.7% on higher volume — the canonical permission slip to press new swing longs after a correction, with a failure rule (undercutting the low cancels it). Slate: row 70 market_follow_through: rally-attempt state machine + FTD + failure on low undercut, in market_measurements. Femto-lean key presence (grep 2026-11-15): market_follow_through present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=day >=4, gain >=~1.25-1.7% on rising volume [SOURCED, canon as cited in the audit row]; materiality seat=70 @ live/failed FTD <=10 sessions [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.67; info 60.6; null 0.52; lenses 0.66/0.71/0.60/0.64/0.64/0.60/0.47 (mean 0.617, spread 0.24)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G079 market_mcclellan** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 73 (Market-internal, materiality MEDIUM): McClellan Oscillator & Summation Index: breadth momentum and its divergences at index highs — a classic topping tell behind most breadth-thrust/divergence commentary. Slate: row 71 market_mcclellan: FILING ONLY — an existing mcclellan() producer; the build adds the summary + consideration filing. Femto-lean key presence (grep 2026-11-15): market_mcclellan present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=19/39-day EMA of net advances [SOURCED, canon as cited in the audit row]; materiality seat=55 @ divergence [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.57; info 32.4; null 0.61; lenses 0.51/0.63/0.43/0.53/0.51/0.37/0.40 (mean 0.483, spread 0.26)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G080 market_breadth_thrust** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 74a (Market-internal, materiality LOW-MEDIUM (grouped in audit row 74)): Zweig Breadth Thrust: 10-day EMA of A/(A+D) from <0.40 to >0.615 in 10 days — a rare, famous thrust signal. Slate: row 72 market_breadth_thrust on the retained (adv, dec) series. Femto-lean key presence (grep 2026-11-15): market_breadth_thrust present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=EMA10 ratio <0.40 -> >0.615 within 10 sessions [SOURCED, canon as cited in the audit row]; materiality seat=65 @ signal <=20 sessions [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.49; info 29.2; null 0.65; lenses 0.49/0.59/0.42/0.48/0.45/0.43/0.44 (mean 0.471, spread 0.17)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G081 market_trin** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 74b (Market-internal, materiality LOW-MEDIUM (grouped in audit row 74)): Arms Index (TRIN): (A/D issues) / (A/D volume). Slate: row 73 market_trin: from adv/dec counts + adv/dec volume sums (new accumulation in build_breadth). Femto-lean key presence (grep 2026-11-15): market_trin present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=issue and volume advance/decline sums [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.33; info 28.0; null 0.58; lenses 0.44/0.46/0.32/0.37/0.34/0.24/0.28 (mean 0.35, spread 0.22)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G082 market_ad_line** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 74c (Market-internal, materiality LOW-MEDIUM (grouped in audit row 74)): Advance/Decline line as a plotted series with divergences (the audit's grouping also names % of stocks above 50/200-day, built as G083). Slate: row 74 market_ad_line: cumulative net-advances series + divergence checks on the shared retained series. Femto-lean key presence (grep 2026-11-15): market_ad_line present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=cumulative net advances [SOURCED, canon as cited in the audit row]; materiality seat=60 @ divergence [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.47; info 39.8; null 0.66; lenses 0.55/0.62/0.49/0.59/0.50/0.48/0.34 (mean 0.51, spread 0.28)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G083 market_breadth_series_ext** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 74d (Market-internal, materiality LOW-MEDIUM (grouped in audit row 74)): % of stocks above the 50-/200-day as named, filed series (the registry's market_breadth item R24 files the values; this extension files the per-session series alongside). Slate: row 80 (8e): an extension of the existing market_breadth key, no new key. Femto-lean key presence (grep 2026-11-15): market_breadth present (extension).
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=per-session % above 50/200 series [SOURCED, canon as cited in the audit row]; materiality seat=unchanged seat [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.33; info 28.4; null 0.7; lenses 0.30/0.39/0.21/0.35/0.43/0.24/0.21 (mean 0.304, spread 0.22)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G084 rrg_name** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 75 (Market-internal / relative-strength visual, materiality MEDIUM): Relative Rotation Graph per name/sector: RS-Ratio vs RS-Momentum scatter with a trail — catches rotation turns a static RS rank misses. Slate: row 75 rrg_name: files the existing _rrg_series per name (+ sector leg), labelled as the desk SMA variant (Flag M1: the desk series is an SMA-normalised variant of de Kempenaer's EMA formulation). Femto-lean key presence (grep 2026-11-15): rrg_name present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=desk SMA variant, labelled as such [SOURCED, canon as cited in the audit row]; materiality seat=60 @ trail transition [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.45; info 42.8; null 0.65; lenses 0.49/0.53/0.44/0.46/0.48/0.35/0.30 (mean 0.436, spread 0.23)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G085 sentiment_surveys** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 76 (Market-internal / context, materiality LOW): Sentiment/positioning surveys as named inputs (AAII, Investors Intelligence, NAAIM exposure), read contrarily at extremes; VIX, put/call and credit (present) carry most sentiment information. Slate: row S3 (8g): a NAMED-UNAVAILABLE STAMP: the desk holds no route to any of the three series (repo grep aaii|naaim|investors_intelligence = zero, slate 2026-10-20). Femto-lean key presence (grep 2026-11-15): stamp only (sentiment_surveys key is the stamp).
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=none [no feed]; seat=none; blocker=no feed, connector or file in the desk carries any of the three series
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.35; info 23.6; null 0.73; lenses 0.31/0.39/0.37/0.32/0.36/0.29/0.23 (mean 0.324, spread 0.16)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G086 beta_correlation** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 77 (Context, materiality MEDIUM): Beta & correlation to the index (and sector): converts 'the S&P falls 3% this week' into an expected path for the setup; low-correlation RS warns the name trades on idiosyncratic (event) risk, not trend. Slate: row 76 beta_correlation: beta/rho/R2 to SPY + sector SPDR; daily 252 primary, weekly 104 cross-check, raw labelled. Femto-lean key presence (grep 2026-11-15): beta_correlation present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=daily 252 + weekly 104 windows [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.67; info 49.8; null 0.51; lenses 0.58/0.70/0.52/0.57/0.69/0.26/0.18 (mean 0.5, spread 0.52)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G087 institutional_sponsorship** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 78 (Context, materiality MEDIUM): Institutional sponsorship trend: # funds owning, 13F change, quality of holders (IBD's 'I'): rising sponsorship into a base is the fundamental-side confirmation of the accumulation the volume section infers. Caveat: 13F data is lagged 45 days — it grades the base, it does not time the entry. Slate: row 77 institutional_sponsorship: EDGAR full-text 13F-HR by CUSIP, trailing 6 quarters -> quarterly gap_sponsorship product; lag printed; quality leg not filed (Flag M2: the cluster's only new crawl class). Femto-lean key presence (grep 2026-11-15): institutional_sponsorship present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=trailing 6 quarters of 13F-HR [SOURCED, canon as cited in the audit row]; materiality seat=considered-only [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.68; info 35.6; null 0.53; lenses 0.68/0.68/0.66/0.63/0.63/0.56/0.57 (mean 0.63, spread 0.12)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G088 industry_group_rank** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 79 (Context / relative-strength, materiality MEDIUM): Industry-group strength rank (group RS over ~6 months, group in top quartile): most of a leader's move is group + market; the same chart in a bottom-quartile group is a different proposition. Slate: row 78 industry_group_rank: desk GICS groups (sub-industry >=8 members), equal-weighted index, score = ret126, rank/percentile/quartile, nightly (Flag M3: only the headwind side is seated in v1). Femto-lean key presence (grep 2026-11-15): industry_group_rank present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=score = ret126, groups >=8 members [SOURCED, canon as cited in the audit row]; materiality seat=55 @ long setup & group percentile <=10 (headwind only) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.72; info 57.8; null 0.46; lenses 0.71/0.74/0.70/0.71/0.70/0.69/0.66 (mean 0.701, spread 0.08)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G089 ad_rating_grade** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 80 (Context / volume, materiality LOW): Accumulation/Distribution rating-style grade per name (13-week, A-E): substantively approximated by OBV/A-D/MFI + divergences (present) — a packaging gap. Slate: row 58 ad_rating_grade: a 13-week A-E grade packaged from OBV/A-D/MFI facts; the reader label must say 'desk accumulation grade', never 'IBD A/D rating' (Flag V1). Femto-lean key presence (grep 2026-11-15): ad_rating_grade present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=13-week window, A-E mapping published in the study [SOURCED, canon as cited in the audit row]; materiality seat=considered-only, explicitly [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.21; info 15.4; null 0.76; lenses 0.22/0.34/0.25/0.22/0.23/0.20/0.18 (mean 0.234, spread 0.16)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G090 buybacks_name** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 81 (Context, materiality LOW): Share-buyback authorisation & execution as a calendar catalyst: announced size / % of float, blackout windows, actual repurchase pace. Slate: row 68 buybacks_name: authorisation + execution from EDGAR 8-K/10-Q repurchase disclosures (a live producer replacing the dead old-desk reader). Femto-lean key presence (grep 2026-11-15): buybacks_name present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=EDGAR 8-K/10-Q disclosures [SOURCED, canon as cited in the audit row]; materiality seat=considered-only (optional 50 large-and-recent — parent enacts) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.46; info 29.2; null 0.7; lenses 0.48/0.54/0.46/0.50/0.48/0.35/0.47 (mean 0.469, spread 0.19)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G091 borrow_lending_name** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Audit row 82 (Context / positioning, materiality MEDIUM for short setups, LOW for longs): Securities-lending borrow fee, utilisation & shares available: a name can have modest short interest and a 40% borrow fee / 95% utilisation — a crowded, fragile short. Modern squeeze canon starts with borrow, not SI. Slate: row S2 (8g): a NAMED-UNAVAILABLE STAMP. NEEDS: a securities-lending feed (Ortex, Fintel, or IB's lending file/API); FINRA publishes none of these; the desk holds no lending subscription. Femto-lean key presence (grep 2026-11-15): stamp only (borrow_lending_name key is the stamp).
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=none [no feed]; seat=none; blocker=no lending subscription held
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.71; info 54.6; null 0.57; lenses 0.71/0.72/0.75/0.72/0.70/0.67/0.75 (mean 0.717, spread 0.08)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G092 power_earnings_gap** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 83 (Structural / context, materiality LOW-MEDIUM): Power Earnings Gap / post-earnings drift as a named pattern: an earnings gap up >=~10% on >=~2x volume that holds its gap/first days' range, entering a drift window (the study's built form: gap >=5%, near-miss 4-5% filed). Slate: row 19 power_earnings_gap: gap >=5% on >=1.5x VOL50, hold/fill/fail states, age + drift. Femto-lean key presence (grep 2026-11-15): power_earnings_gap present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=gap >=5% (near-miss 4-5%), volume >=1.5x VOL50 [SOURCED, canon as cited in the audit row]; materiality seat=64 @ PEG holding & age <=10 sessions [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.63; info 44.0; null 0.52; lenses 0.65/0.67/0.63/0.63/0.62/0.53/0.56 (mean 0.613, spread 0.14)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G093 fair_value_gap** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 22a (Structural concept (SMC), materiality MEDIUM): Fair Value Gap / imbalance: a 3-candle gap where candle 1's and candle 3's wicks do not overlap — untraded territory price often returns to mitigate. Practitioner-standard since ICT; evidence base is practitioner, not textbook. Slate: row 82 (8f) PROVISIONAL: 3-candle wick-non-overlap zones + mitigation state; no cluster-grade deep dive (study section 6). Femto-lean key presence (grep 2026-11-15): fair_value_gap present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=3-candle wick non-overlap [SOURCED, canon as cited in the audit row]; materiality seat=none proposed (provisional) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.32; info 34.6; null 0.68; lenses 0.39/0.43/0.40/0.35/0.37/0.33/0.24 (mean 0.359, spread 0.19)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G094 order_block** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 22b (Structural concept (SMC), materiality MEDIUM): Order block (incl. mitigation block): the last opposite-coloured candle before an impulsive displacement that broke structure, projected forward as a demand/supply zone — a different level generator feeding the same confluence stack. Slate: row 83 (8f) PROVISIONAL: origin-candle zone on confirmed structure breaks. Femto-lean key presence (grep 2026-11-15): order_block present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=origin candle of the displacement [SOURCED, canon as cited in the audit row]; materiality seat=none proposed (provisional) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.36; info 32.8; null 0.65; lenses 0.42/0.47/0.49/0.46/0.42/0.35/0.25 (mean 0.409, spread 0.24)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G095 liquidity_sweeps** — WATCH (edge-bearing)
- Evidence (as printed): Audit row 22c (Structural concept (SMC), materiality MEDIUM): Liquidity pools & sweeps / stop runs (EQH/EQL): resting stops above equal highs / below equal lows; a sweep = a wick through the pool that closes back inside. Phase-free, aimed at equal extremes and prior-period highs in trending names. Slate: row 84 (8f) PROVISIONAL: equal-high/low pools from the shared PIVOTS primitive + wick-through-close-back sweeps. Femto-lean key presence (grep 2026-11-15): liquidity_sweeps present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=equal extremes within a tight tolerance; sweep = wick beyond pool by a stated ATR fraction, close back inside [SOURCED, canon as cited in the audit row]; materiality seat=none proposed (provisional) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.52; info 46.6; null 0.59; lenses 0.49/0.56/0.50/0.46/0.45/0.41/0.36 (mean 0.461, spread 0.2)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G096 smc_labels** — MACHINERY (machinery)
- Evidence (as printed): Audit row 22d (Structural concept, LOW): displacement / inducement (SMC vocabulary) — useful labels for things the desk already describes in prose; the audit's own verdict: labels only, no new measurement. Slate row 85 (8f) PROVISIONAL: derived from existing facts, the builder must not introduce a new measurement under this key.
- Mechanism: MECHANISM-ABSENT: a vocabulary layer over existing facts (stretch/breakout items), by the audit's own framing.
- Variables: inputs=existing record facts only [SOURCED, slate row 85]; seat=none, ever [SOURCED, audit framing]
- Variations that would most change the verdict: No variation is meaningful: no measurement exists under this key by design.
- Seats: plaus 0.01; info 10.0; null 0.96; lenses 0.02/0.05/0.02/0.04/0.05/0.01/0.01 (mean 0.029, spread 0.04)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G097 rs_line** — WATCH (edge-bearing)
- Evidence (as printed): Audit row RS-L (Relative-strength visual, materiality HIGH (per the audit's section B note)): The plotted RS line (name / S&P 500, normalised) and its headline tell — the RS line makes a new high before or at the price breakout (the O'Neil/Minervini 'blue dot'): the inventory had numeric RS only (R31). Slate: row 81 (8f) PROVISIONAL: RS series (close / SPY, normalised to 100 at window start) + rs_line_new_high tell at/near the pivot; considered-only until a cluster-grade study calibrates it. Femto-lean key presence (grep 2026-11-15): rs_line present.
- Mechanism: Named in the canon audit as a missing consideration; mechanism as stated in the audit row's why-it-matters (carried in the definition above). No standalone falsifier or forward grade for this item exists in any record read for this recheck.
- Variables: parameters=RS = close/SPY normalised; new-high tell at/near pivot [SOURCED, canon as cited in the audit row]; materiality seat=none proposed (provisional) [ARBITRARY desk ranking score inside the stance-0 materiality mechanism, CANON-GAPS-STUDY slate]
- Variations that would most change the verdict: Vary its defining parameters against recorded reads: no record varies them; the slate encodes the canon parameters as built and no comparison run exists.
- Seats: plaus 0.57; info 60.2; null 0.5; lenses 0.61/0.68/0.60/0.62/0.66/0.46/0.35 (mean 0.569, spread 0.33)
- Source: ta-canon-gap-audit report.md (2026-10-20); CANON-GAPS-STUDY.md build slate (2026-10-20)

**G098 aggregate_chain_retention_P0** — MACHINERY (machinery)
- Evidence (as printed): Slate prerequisite P0 (8d head): the aggregate_chain retention change that rows 60-66 consume — additive, existing outputs byte-stable, product version bump. A product change, not a slate row.
- Mechanism: MECHANISM-ABSENT as an edge: the retained chain map is the data substrate for the whole per-name options-level family (G067, G069-G074).
- Variables: change=additive retention of the per-strike chain map [SOURCED, CANON-GAPS-STUDY 8d]
- Variations that would most change the verdict: Not an edge variable; variation not applicable.
- Seats: plaus 0.94; info 18.4; null 0.12; lenses 0.92/0.90/0.78/0.93/0.94/0.93/0.93 (mean 0.904, spread 0.16)
- Source: CANON-GAPS-STUDY.md build slate (2026-10-20)

### S5 - Excluded by ruling (audit section C; frozen method)

**X01 full_harmonics_beyond_abcd** — UNGRADABLE-BLOCKED (machinery)
- Evidence (as printed): Canon item recorded in the audit's section C 'Excluded by ruling' (Bulkowski 3rd ed. chs. 4-5, 16-20, 37-38: Gartley, Bat, Butterfly, Crab, Shark/Cypher); listed for completeness with no recommendation, per the frozen read method (THE LIST's own deliberately-out note).
- Mechanism: MECHANISM-ABSENT by ruling: the frozen method excludes it as a read input.
- Variables: status=excluded [SOURCED, owner frozen-method ruling]
- Variations that would most change the verdict: Blocked by ruling: reintroduction requires an owner ruling, not a variation study.
- Seats: plaus 0.01; info 11.4; null 0.92; lenses 0.02/0.03/0.01/0.02/0.04/0.00/0.04 (mean 0.023, spread 0.04)
- Source: ta-canon-gap-audit report.md section C; register L-35 deliberately-out list

**X02 point_and_figure_charts** — UNGRADABLE-BLOCKED (machinery)
- Evidence (as printed): Canon item recorded in the audit's section C 'Excluded by ruling' (Edwards & Magee / Murphy chart-type canon); listed for completeness with no recommendation, per the frozen read method (THE LIST's own deliberately-out note).
- Mechanism: MECHANISM-ABSENT by ruling: the frozen method excludes it as a read input.
- Variables: status=excluded [SOURCED, owner frozen-method ruling]
- Variations that would most change the verdict: Blocked by ruling: reintroduction requires an owner ruling, not a variation study.
- Seats: plaus 0.05; info 10.4; null 0.91; lenses 0.05/0.05/0.01/0.04/0.04/0.03/0.05 (mean 0.039, spread 0.04)
- Source: ta-canon-gap-audit report.md section C; register L-35 deliberately-out list

**X03 renko_charts** — UNGRADABLE-BLOCKED (machinery)
- Evidence (as printed): Canon item recorded in the audit's section C 'Excluded by ruling' (Japanese charting tradition, standard chart-type canon); listed for completeness with no recommendation, per the frozen read method (THE LIST's own deliberately-out note).
- Mechanism: MECHANISM-ABSENT by ruling: the frozen method excludes it as a read input.
- Variables: status=excluded [SOURCED, owner frozen-method ruling]
- Variations that would most change the verdict: Blocked by ruling: reintroduction requires an owner ruling, not a variation study.
- Seats: plaus 0.0; info 11.2; null 0.93; lenses 0.03/0.01/0.00/0.03/0.05/0.00/0.03 (mean 0.021, spread 0.05)
- Source: ta-canon-gap-audit report.md section C; register L-35 deliberately-out list

**X04 market_cycles** — UNGRADABLE-BLOCKED (machinery)
- Evidence (as printed): Canon item recorded in the audit's section C 'Excluded by ruling' (Pring / Hurst / Lindsay canon (plain seasonality is in the inventory as R34 and is not this item)); listed for completeness with no recommendation, per the frozen read method (THE LIST's own deliberately-out note).
- Mechanism: MECHANISM-ABSENT by ruling: the frozen method excludes it as a read input.
- Variables: status=excluded [SOURCED, owner frozen-method ruling]
- Variations that would most change the verdict: Blocked by ruling: reintroduction requires an owner ruling, not a variation study.
- Seats: plaus 0.04; info 19.4; null 0.93; lenses 0.04/0.01/0.03/0.05/0.06/0.03/0.03 (mean 0.036, spread 0.05)
- Source: ta-canon-gap-audit report.md section C; register L-35 deliberately-out list

**X05 level2_tape_reading** — UNGRADABLE-BLOCKED (machinery)
- Evidence (as printed): Canon item recorded in the audit's section C 'Excluded by ruling' (Elder / tape-reading canon (time & sales, depth of book)); listed for completeness with no recommendation, per the frozen read method (THE LIST's own deliberately-out note).
- Mechanism: MECHANISM-ABSENT by ruling: the frozen method excludes it as a read input.
- Variables: status=excluded [SOURCED, owner frozen-method ruling]
- Variations that would most change the verdict: Blocked by ruling: reintroduction requires an owner ruling, not a variation study.
- Seats: plaus 0.07; info 27.6; null 0.92; lenses 0.05/0.04/0.05/0.05/0.05/0.01/0.04 (mean 0.041, spread 0.04)
- Source: ta-canon-gap-audit report.md section C; register L-35 deliberately-out list

**X06 insider_selling_input** — UNGRADABLE-BLOCKED (machinery)
- Evidence (as printed): Canon item recorded in the audit's section C 'Excluded by ruling' (CAN SLIM-adjacent / event literature (the inventory uses insider buying only, by ruling)); listed for completeness with no recommendation, per the frozen read method (THE LIST's own deliberately-out note).
- Mechanism: MECHANISM-ABSENT by ruling: the frozen method excludes it as a read input.
- Variables: status=excluded [SOURCED, owner frozen-method ruling]
- Variations that would most change the verdict: Blocked by ruling: reintroduction requires an owner ruling, not a variation study.
- Seats: plaus 0.0; info 23.4; null 0.84; lenses 0.05/0.02/0.03/0.05/0.05/0.05/0.05 (mean 0.043, spread 0.03)
- Source: ta-canon-gap-audit report.md section C; register L-35 deliberately-out list

**X07 dilution_input** — UNGRADABLE-BLOCKED (machinery)
- Evidence (as printed): Canon item recorded in the audit's section C 'Excluded by ruling' (Event/fundamental canon adjacent to float & lockup analysis (ATM programmes, convertibles, warrant overhang as inputs)); listed for completeness with no recommendation, per the frozen read method (THE LIST's own deliberately-out note).
- Mechanism: MECHANISM-ABSENT by ruling: the frozen method excludes it as a read input.
- Variables: status=excluded [SOURCED, owner frozen-method ruling]
- Variations that would most change the verdict: Blocked by ruling: reintroduction requires an owner ruling, not a variation study.
- Seats: plaus 0.02; info 38.8; null 0.87; lenses 0.05/0.05/0.00/0.05/0.05/0.04/0.05 (mean 0.041, spread 0.05)
- Source: ta-canon-gap-audit report.md section C; register L-35 deliberately-out list

### S6 - Chart law (register section G; chart benchmark)

**C01 chart_law_item_1** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): Buy zone drawn as a shaded band, labeled with both prices.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: form=shaded band + both prices [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.57; info 27.8; null 0.51; lenses 0.84/0.85/0.01/0.83/0.85/0.42/0.41 (mean 0.601, spread 0.84)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C02 chart_law_item_2** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): Invalidation drawn as a line, labeled with its price: the line that ends the setup.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: form=line + price label [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.77; info 34.2; null 0.51; lenses 0.86/0.94/0.07/0.88/0.86/0.69/0.73 (mean 0.719, spread 0.87)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C03 chart_law_item_3** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): First + final targets drawn as lines, each labeled with its price; a measured level also carries its derivation (ratio + price).
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: form=lines + price + derivation labels [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.59; info 36.0; null 0.85; lenses 0.82/0.89/0.06/0.85/0.87/0.53/0.28 (mean 0.614, spread 0.83)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C04 chart_law_item_4** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): Every line labeled by its role (buy zone, trigger, stop, first target, target); never a trigger wearing a target's name.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: rule=role labels [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.7; info 28.2; null 0.61; lenses 0.91/0.94/0.21/0.88/0.93/0.86/0.88 (mean 0.801, spread 0.73)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C05 chart_law_item_5** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): Last close marked and priced.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: form=marker + price [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.58; info 28.0; null 0.69; lenses 0.53/0.78/0.01/0.80/0.81/0.22/0.36 (mean 0.501, spread 0.8)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C06 chart_law_item_6** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): R printed against the target on the plan chart.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: form=R beside target [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.35; info 24.6; null 0.89; lenses 0.75/0.83/0.07/0.85/0.83/0.66/0.24 (mean 0.604, spread 0.78)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C07 chart_law_item_7** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): The named pattern drawn on the price pane and labeled with its name; if no pattern is on the record, the operative trendlines draw instead.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: rule=pattern or trendlines drawn [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.32; info 29.4; null 0.82; lenses 0.72/0.86/0.06/0.81/0.85/0.20/0.20 (mean 0.529, spread 0.8)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C08 chart_law_item_8** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): The key averages the read uses, drawn, few and named.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: rule=few named averages [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.8; info 32.0; null 0.59; lenses 0.70/0.88/0.02/0.81/0.87/0.81/0.88 (mean 0.71, spread 0.86)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C09 chart_law_item_9** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): Reserved future space: roughly a quarter to a third of the price pane past the last bar.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: fraction=1/4 to 1/3 of the pane [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.22; info 23.2; null 0.85; lenses 0.40/0.82/0.01/0.55/0.69/0.04/0.39 (mean 0.414, spread 0.81)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C10 chart_law_item_10** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): The expected path drawn into the future space: dashed, thinner, desaturated, from last close through the plan's stages to the final target, move size printed at the end; the alternative scenario's line drawn too when the brief carries one.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: form=dashed path + size label [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.64; info 28.2; null 0.77; lenses 0.79/0.87/0.02/0.88/0.91/0.48/0.59 (mean 0.649, spread 0.89)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C11 chart_law_item_11** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): Volume pane under the price pane.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: form=pane order [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.31; info 25.2; null 0.77; lenses 0.76/0.83/0.14/0.78/0.80/0.64/0.73 (mean 0.669, spread 0.69)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C12 chart_law_item_12** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): RSI(14) pane and MACD pane under the volume pane.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: panes=RSI(14) + MACD [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.33; info 28.2; null 0.73; lenses 0.74/0.79/0.17/0.72/0.77/0.17/0.67 (mean 0.576, spread 0.62)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C13 chart_law_item_13** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): Divergences drawn where the record carries them, labeled, with matching price pivots marked; a spent divergence is never drawn.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: rule=record-gated drawing [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.23; info 29.8; null 0.77; lenses 0.85/0.87/0.53/0.84/0.86/0.79/0.84 (mean 0.797, spread 0.34)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C14 chart_law_item_14** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): Unobstructed: no label overlaps another label, a line, or the footnote; nothing truncated, ever.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: rule=renderer placement floors [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.79; info 27.6; null 0.72; lenses 0.85/0.88/0.81/0.85/0.90/0.83/0.85 (mean 0.853, spread 0.09)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C15 chart_law_item_15** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): No crowding at the decision zone: lines within ~1 ATR at the right edge compose into one stack label.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: threshold=~1 ATR stack rule [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.52; info 27.6; null 0.59; lenses 0.79/0.83/0.16/0.81/0.84/0.79/0.60 (mean 0.689, spread 0.68)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C16 chart_law_item_16** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): One fact once per surface (the plan strip restating drawn lines is the lawful second seat).
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: rule=single statement [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.31; info 16.2; null 0.78; lenses 0.79/0.81/0.24/0.81/0.80/0.72/0.76 (mean 0.704, spread 0.57)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C17 chart_law_item_17** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): Plain words only: the reader's vocabulary, no desk jargon on any chart.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: rule=vocabulary [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.11; info 25.2; null 0.54; lenses 0.74/0.82/0.16/0.70/0.76/0.36/0.63 (mean 0.596, spread 0.66)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C18 chart_law_item_18** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): The clock on the chart: the plan's expiry in the title/date.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: form=expiry printed [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.34; info 10.2; null 0.59; lenses 0.83/0.86/0.37/0.83/0.86/0.82/0.82 (mean 0.77, spread 0.49)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C19 chart_law_item_19** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): An explicit invalidation is never traded away (Echo implies his; ours prints).
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: rule=explicit invalidation [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.14; info 10.4; null 0.51; lenses 0.88/0.90/0.16/0.86/0.85/0.72/0.76 (mean 0.733, spread 0.74)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C20 chart_law_item_20** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): The expiry clock is never traded away (none of the four benchmark accounts print one).
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: rule=clock printed [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.06; info 10.0; null 0.75; lenses 0.81/0.92/0.09/0.86/0.84/0.36/0.84 (mean 0.674, spread 0.83)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C21 chart_law_item_21** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): R printed against the target is never traded away (none of the four print R).
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: rule=R printed [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.07; info 10.2; null 0.91; lenses 0.47/0.24/0.06/0.27/0.50/0.09/0.47 (mean 0.3, spread 0.44)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

**C22 chart_law_item_22** — MACHINERY (machinery)
- Evidence (as printed): Chart law (owner, 2026-10-18): The weighed opposition exists on the brief behind the chart: the chart never pretends the other side is not there.
- Mechanism: MECHANISM-ABSENT as an edge: a chart-production law; it governs whether the reader can see the plan honestly, not whether the plan has edge.
- Variables: rule=opposition on the brief [SOURCED, owner's LIST ratified 2026-10-18 + CHART-BENCHMARK.md]
- Variations that would most change the verdict: No record varies any chart-law item; the benchmark law (item L-54) re-compares against the four studied accounts every audit pass instead.
- Seats: plaus 0.14; info 14.2; null 0.76; lenses 0.80/0.81/0.29/0.79/0.79/0.69/0.69 (mean 0.694, spread 0.52)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section G (L-54..L-59), THE LIST (owner, 2026-10-18)

### S7 - Method laws (register section 2, edge-bearing subset)

**M01 logical_R_law** — MACHINERY (machinery)
- Evidence (as printed): Register L-10: A name whose honest ladder cannot reach R >= 1 does not board; headline R is computed to the FINAL objective, R to T1 also prints; a realized win rate is never a permission slip for illogical R/R (owner ruling 2026-10-16).
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: bar=R >= 1 to the final objective [SOURCED, owner ruling]; ladder=T1 + material structural objectives, origin-stamped [SOURCED]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.9; info 27.8; null 0.2; lenses 0.92/0.94/0.89/0.91/0.92/0.89/0.83 (mean 0.9, spread 0.11)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M02 ladder_construction** — MACHINERY (machinery)
- Evidence (as printed): Register L-12: Objective ladder = sleeve staged/exit target first, then every material structural objective above it from one price-ordered pool (chart_structure + chart_measured); one origin per rung; no objective is ever invented.
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: pools=chart_structure + chart_measured [SOURCED]; tie rule=tested level owns the rung [SOURCED]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.94; info 20.8; null 0.21; lenses 0.89/0.94/0.84/0.92/0.91/0.89/0.87 (mean 0.894, spread 0.1)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M03 materiality_floor** — MACHINERY (machinery)
- Evidence (as printed): Register L-13: A successive rung must clear max(0.5 x risk, 1 x ATR14) above the last accepted rung (cost term 0); nearer levels passed over are named in the targets note, never silent.
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: floor=max(0.5x risk, 1x ATR14) [ARBITRARY constants in a SOURCED rule form]; cost term=0 [ARBITRARY]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.89; info 16.8; null 0.58; lenses 0.89/0.90/0.74/0.87/0.89/0.83/0.91 (mean 0.861, spread 0.17)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M04 entry_zone_stop_backstop** — MACHINERY (machinery)
- Evidence (as printed): Register L-15: Entry zone = staged anchor +/- 0.25 x ATR14; stop = the trading stop from the curator's stop-role split; a disaster backstop is its own labeled field and never the plan's stop.
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: zone half-width=0.25 x ATR14 [ARBITRARY constant]; anchor sources=staged entry / Tensor staged / fill price [SOURCED]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.93; info 28.0; null 0.22; lenses 0.90/0.90/0.78/0.91/0.90/0.85/0.87 (mean 0.873, spread 0.13)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M05 conditional_doors_priced_at_trigger** — MACHINERY (machinery)
- Evidence (as printed): Register L-18: The R >= 1 boarding law binds the trade the door actually describes: entry at the trigger price, the brief's ends-line as stop, the brief's objective; a door paying under R 1 at its trigger files as a plain no-call with door_r on the record.
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: pricing point=trigger price [SOURCED, SPEC S41]; pattern-armed doors expressly NOT settled by this rule [open question, Ledger 4.9]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.92; info 20.2; null 0.25; lenses 0.94/0.93/0.92/0.93/0.91/0.92/0.90 (mean 0.921, spread 0.04)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M06 conviction_law** — MACHINERY (machinery)
- Evidence (as printed): Register L-22: Every boarded name gets a decisive, actionable setup: direction, objective, horizon, invalidation printed; conviction grades must discriminate; held names get a decisive management stance.
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: form=owner ruling 2026-10-17 [SOURCED]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.82; info 13.6; null 0.52; lenses 0.85/0.87/0.79/0.82/0.88/0.85/0.81 (mean 0.839, spread 0.09)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M07 tie_break_weighing** — MACHINERY (machinery)
- Evidence (as printed): Register L-23: 'Mixed' is banned as a call outcome: a mixed balance is resolved by explicit tie-break weighing, structure > volume-confirmed momentum > context, and the resolution prints in the basis.
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: order=structure > volume-confirmed momentum > context [SOURCED, owner 2026-10-17]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.88; info 19.6; null 0.62; lenses 0.86/0.92/0.85/0.85/0.89/0.84/0.82 (mean 0.861, spread 0.1)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M08 the_call** — MACHINERY (machinery)
- Evidence (as printed): Register L-26: Every boarded setup carries THE CALL: direction, the plan's final objective (origin-labeled), a horizon from the evidence's own timing; conviction word from the fixed ladder High conviction / Conviction / Lean / No call, mapped by stated rules to counted evidence; the family record may ride as a labeled base rate, never an input to the word.
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: word ladder=4 fixed words [SOURCED]; mapping=counted-evidence rules [SOURCED, SPEC S11]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.87; info 23.8; null 0.28; lenses 0.84/0.87/0.83/0.84/0.88/0.84/0.80 (mean 0.843, spread 0.08)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M09 conviction_caps** — MACHINERY (machinery)
- Evidence (as printed): Register L-29: Judgment ceilings: a counter-trend call cannot publish High on a momentum voice; a sole projected objective caps conviction; a trend shutout carries the counter-trend cap; a light-volume breakout cannot carry a call to High; the visual read never files HIGH on a single read.
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: caps=5 named ceilings [SOURCED, SPEC SS27/35/38 + buglogs]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.89; info 24.0; null 0.66; lenses 0.85/0.87/0.80/0.86/0.90/0.83/0.79 (mean 0.843, spread 0.11)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M10 one_governing_invalidation** — MACHINERY (machinery)
- Evidence (as printed): Register L-30: Each plan has exactly one governing invalidation line; it is the line the WHY leans on and the line drawn on every chart face (SA-14).
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: count=exactly one [SOURCED]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.89; info 14.8; null 0.61; lenses 0.92/0.94/0.88/0.89/0.88/0.90/0.91 (mean 0.903, spread 0.06)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M11 consideration_law_and_record** — MACHINERY (machinery)
- Evidence (as printed): Register L-35_L-36: Every synthesis must consider every item on THE LIST (~60 items, 15 families) plus the 10 blessed addenda; each brief carries one record with every registry item present as {key, family, label, status, fact, data}; a computation that cannot run lands UNAVAILABLE with the failure named, never faked; the material set is capped at six facts ranked by named deterministic rules; the record moves no desk number.
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: material cap=6 facts [ARBITRARY constant]; stance=0 [SOURCED, SPEC S13]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.94; info 27.4; null 0.2; lenses 0.94/0.95/0.94/0.94/0.95/0.94/0.94 (mean 0.943, spread 0.01)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M12 pattern_calibration_authorization** — MACHINERY (machinery)
- Evidence (as printed): Register L-42: For Best Setups only, the synthesis may be tuned on broad past results (pattern history calibrates reads: voice priors, base rates, horizon/objective realism); no backtests of the sleeves; census universe = the canonical genome roster of 1,838 symbols; span 2020-01-02 to 2026-10-16, detector + A7-constructed geometry (owner ruling 2026-10-19).
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: universe=1,838 symbols [SOURCED, owner ruling correcting the 903-name pool]; span=2020-01-02..2026-10-16 [SOURCED]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.82; info 32.4; null 0.38; lenses 0.81/0.82/0.48/0.85/0.85/0.78/0.83 (mean 0.774, spread 0.37)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

**M13 calibration_lookup_law** — MACHINERY (machinery)
- Evidence (as printed): Register L-43: Exactly one cell per pattern, finest lawful first: family x named slice (n>=30), family x direction, family alone; a cell is lawful only at measured n >= 30; rates are never averaged, pooled, or interpolated across cells.
- Mechanism: MECHANISM-ABSENT as an edge: a governing method law of the synthesis; it disciplines how evidence becomes a plan.
- Variables: n floor=30 [ARBITRARY constant in a SOURCED rule form]; lookup order=3 levels [SOURCED]
- Variations that would most change the verdict: No record varies this law's parameters; laws change by owner ruling or SPEC amendment only.
- Seats: plaus 0.82; info 20.4; null 0.53; lenses 0.87/0.88/0.59/0.85/0.88/0.87/0.83 (mean 0.824, spread 0.29)
- Source: BEST-SETUPS-REGISTER-2026-10-22.md section 2 (standing laws)

### S8 - Lenses outside the registry (weighed voices and read layers)

**N01 weighed_desk_read** — MACHINERY (machinery)
- Evidence (as printed): Runs on every sampled brief (class (a) outside the registry): ~40 voices (geometry, levels, pattern + base rates, divergences, Wyckoff, Tensor, Elliott, Lector, mood ring, breadth, theme rotation, index trend, risk appetite, regime, family agreement, curator score, conflicts).
- Mechanism: MECHANISM-ABSENT as an edge: the synthesis surface itself; its voices are the items graded elsewhere in this recheck.
- Variables: voices=~40 [SOURCED, coverage ledger]; salience rules=register L-39 (confirmed > unconfirmed; at a tested level > mid-range; independent agreement > single voice; proximity; recency) [SOURCED]
- Variations that would most change the verdict: Vary the salience order: set by L-39 doctrine; no record varies it.
- Seats: plaus 0.67; info 38.8; null 0.51; lenses 0.09/0.13/0.06/0.09/0.08/0.07/0.05 (mean 0.081, spread 0.08)
- Source: GESTALT-COVERAGE.md 'Outside the registry' table; BEST-SETUPS-REGISTER L-38/L-40/L-41

**N02 pass_b_perceptual_read** — WATCH (edge-bearing)
- Evidence (as printed): At the 2026-10-17 census: class (c) — charts are rendered for every brief but nothing read them back; the law (register L-38, owner 2026-10-17) since mandates the visual read as a weighed voice, hash-bound and fail-closed, its absence printed on the brief's face.
- Mechanism: The perceptual layer of the reading method (Grand Synthesis Parts II/III/VIII): render W/D/1H, look, judge shape/base/pattern quality — the half of the method that deterministic geometry cannot compute.
- Variables: frames=weekly/daily/1H renders [SOURCED, L-38]; confidence cap=never HIGH on a single read [SOURCED, L-29(v)]
- Variations that would most change the verdict: Vary frames or the single-read cap: no record varies them; the book's own Pass B reads (FULL-GESTALT-INVENTORY) are the running form.
- Seats: plaus 0.62; info 61.8; null 0.55; lenses 0.55/0.66/0.50/0.64/0.64/0.59/0.32 (mean 0.557, spread 0.34)
- Source: GESTALT-COVERAGE.md 'Outside the registry' table; BEST-SETUPS-REGISTER L-38/L-40/L-41

**N03 pass_a_1h_frame** — UNGRADABLE-BLOCKED (edge-bearing)
- Evidence (as printed): Class (c) at census: read_chart consumes daily bars only; hourly bars are fetched for rendering and the inputs hash, never read as TA.
- Mechanism: MECHANISM-ABSENT in production: intraday structure as its own read has no producer.
- Variables: frames=daily only in read_chart [blocker named in coverage ledger]
- Variations that would most change the verdict: Blocked: needs an hourly TA read path; no variation possible until it exists.
- Seats: plaus 0.31; info 29.6; null 0.81; lenses 0.13/0.27/0.22/0.27/0.40/0.20/0.18 (mean 0.239, spread 0.27)
- Source: GESTALT-COVERAGE.md 'Outside the registry' table; BEST-SETUPS-REGISTER L-38/L-40/L-41

**N04 pass_c_vision_proofread** — UNGRADABLE-BLOCKED (machinery)
- Evidence (as printed): Class (c) at census: no producer in the brief build; exists only as parent practice in the 20-setup audits.
- Mechanism: MECHANISM-ABSENT in production: a proofread pass over the finished card has no producer in the build.
- Variables: producer=NONE in build_brief [blocker named in coverage ledger]
- Variations that would most change the verdict: Blocked on a build slot; machinery when it exists.
- Seats: plaus 0.17; info 27.6; null 0.78; lenses 0.52/0.35/0.08/0.27/0.35/0.25/0.07 (mean 0.27, spread 0.45)
- Source: GESTALT-COVERAGE.md 'Outside the registry' table; BEST-SETUPS-REGISTER L-38/L-40/L-41

**N05 elliott_lens** — WATCH (edge-bearing)
- Evidence (as printed): Runs for every name (class (a) outside the registry): computed once per brief, shared by brief + voice; weighed as context, stance 0, moves no number until validation + ruling (register L-40). Lane 6's gestalt register graded the book's Elliott variables ARBITRARY-class with no ablation on record.
- Mechanism: A wave-count lens: proposes motive/corrective structure and an invalidation; its governing frame is a ruling, not a wiring gap.
- Variables: stance=0 [SOURCED, owner ruling]; promotion=pre-registered validation + owner ruling [SOURCED, L-40]
- Variations that would most change the verdict: Vary stance: barred by ruling until validation passes; no record varies it.
- Seats: plaus 0.29; info 30.2; null 0.74; lenses 0.27/0.35/0.25/0.25/0.31/0.24/0.18 (mean 0.264, spread 0.17)
- Source: GESTALT-COVERAGE.md 'Outside the registry' table; BEST-SETUPS-REGISTER L-38/L-40/L-41

**N06 echo_expert_lens** — WATCH (edge-bearing)
- Evidence (as printed): Echo Analysis's algorithm joined the record as a lens on 2026-10-18, filing as echo_expert testimony under the same stance discipline as other context/structure voices (register L-41); its trap screen must see the full path it claims to screen (buglog ECHO-1).
- Mechanism: An external expert's method coded as an algorithm: an independent read whose value is disagreement with the desk's own geometry (census bank K3 complex).
- Variables: source=Echo Analysis newsletter method, coded 2026-10-18 [SOURCED, register L-41]; stance=context/structure voice [SOURCED]
- Variations that would most change the verdict: Vary its weight in the synthesis: no record varies it; the Lane 7 sweep graded no Echo-axis cell (states never persisted per outcome).
- Seats: plaus 0.53; info 43.0; null 0.65; lenses 0.52/0.60/0.53/0.58/0.51/0.42/0.32 (mean 0.497, spread 0.28)
- Source: GESTALT-COVERAGE.md 'Outside the registry' table; BEST-SETUPS-REGISTER L-38/L-40/L-41

**N07 lector_lens** — WATCH (edge-bearing)
- Evidence (as printed): The ChartsLector replica: lector_stage files on every brief (R21) and lector_tiers scores its strength in the rubric (B04); coverage is the replica's ranked universe (lector_top 10 on the board of record).
- Mechanism: An external strength-ranking read (Lector Lab, live since 2026-10-06) used as context: it can add but never create a setup.
- Variables: universe=replica ranked set [SOURCED]; opportunity score=0-100 over its 55-name universe [SOURCED, curator note]
- Variations that would most change the verdict: Vary the replica's scoring: it is an external replica; no desk record varies it.
- Seats: plaus 0.45; info 33.0; null 0.69; lenses 0.39/0.53/0.47/0.46/0.49/0.36/0.25 (mean 0.421, spread 0.28)
- Source: GESTALT-COVERAGE.md 'Outside the registry' table; BEST-SETUPS-REGISTER L-38/L-40/L-41

**N08 tensor_lens** — LIVE CANDIDATE (edge-bearing)
- Evidence (as printed): The canonical Tensor engine as a lens over its 41-name basket (Decision #38): its states/votes file as R38/R39; its fires were priced by the book's Ghost Book (21 fires, 11 viable at R>=1.0) and first-resolved by the 2026-11-15 shadow resolver at 20 STOPPED_OUT / 1 TARGET_HIT on a daily-close intrinsic basis (census C10). Tier basis: the only canon item whose forward resolution is armed and accruing today — priced fires, a built resolver, first grades printed, and a named surviving form (the intraday-path redesign) carrying the candidate forward; the current daily-close construction's first grades are the C10 record, not a kill (n=21, one session's tape, per the resolver's own BUGLOG limits).
- Mechanism: Confirmed-swing timing/selection: the rubric's largest single evidence item (B02) rests on this engine's confirmed in-age swings.
- Variables: basket=41 names [SOURCED, Decision #38]; swing confirmation + age policy=core/tensor_feeds.py producer law [SOURCED]
- Variations that would most change the verdict: Vary the expression basis (daily-close first-touch vs intraday path): the census names the intraday-path redesign as the surviving form; the engine's own parameters were never varied in any record read for this recheck.
- Seats: plaus 0.47; info 54.2; null 0.79; lenses 0.46/0.49/0.43/0.40/0.42/0.37/0.31 (mean 0.411, spread 0.18)
- Source: GESTALT-COVERAGE.md 'Outside the registry' table; BEST-SETUPS-REGISTER L-38/L-40/L-41

**N09 mood_ring_sentiment** — MACHINERY (machinery)
- Evidence (as printed): Class (a) carried form of the old desk's sentiment composite: Mood Ring from VIX/VIX3M/VVIX/SKEW inside market_measurements, plus the fear_window item (R16).
- Mechanism: MECHANISM-ABSENT as an edge: a market-context composite feeding regime reads.
- Variables: inputs=VIX/VIX3M/VVIX/SKEW [SOURCED, coverage ledger]
- Variations that would most change the verdict: Not an edge variable; variation not applicable.
- Seats: plaus 0.29; info 30.8; null 0.52; lenses 0.14/0.18/0.11/0.20/0.15/0.16/0.11 (mean 0.15, spread 0.09)
- Source: GESTALT-COVERAGE.md 'Outside the registry' table; BEST-SETUPS-REGISTER L-38/L-40/L-41

## Connections (Bank D, connection hunting)

- **KA** (the level-confluence complex: the confluence count item, swing/volume/round zones, trendlines, plus the slate'...): choice = opt2 (several_objects: different level generators carry genuinely independent information and the count understates them) [seat probabilities: [{'value': 'opt1', 'probability': 0.45}, {'value': 'opt2', 'probability': 0.51}, {'value': 'opt3', 'probability': 0.04}]]; single registered variable captures most of the shared effect: seat refused (no probability returned); edge-share expected score (0-100): 34.2. Deciding check: accrue per-generator level tags on resolved reads (the step-13 axis-tag pattern) and test whether removing any one generator changes the confluence count's forward separation; the count is one object until a generator proves separable.
- **KB** (the base-discipline complex: VCP footprints, volume dry-up, pivot tightness, base depth/length/stage counting,...): choice = opt2 (several_objects: contraction, dry-up, tightness and stage are separable effects with separate failure modes) [seat probabilities: [{'value': 'opt1', 'probability': 0.39}, {'value': 'opt2', 'probability': 0.58}, {'value': 'opt3', 'probability': 0.03}]]; single registered variable captures most of the shared effect: probability 0.63; edge-share expected score (0-100): 52.2. Deciding check: the calibration layer already slices by pattern family; add base-quality sub-tags (contraction count, dry-up flag, tightness band) to the same cells and read which sub-tag carries the family's base rate.
- **KC** (the pattern complex: the registry's 17 pattern items, the slate's 21 pattern builds, and the pattern-calibrati...): choice = opt2 (calibration: the edge, if any, sits in the calibration layer's measured base rates; the detectors are interchangeable front-ends) [seat probabilities: [{'value': 'opt1', 'probability': 0.42}, {'value': 'opt2', 'probability': 0.44}, {'value': 'opt3', 'probability': 0.14}]]; single registered variable captures most of the shared effect: probability 0.5; edge-share expected score (0-100): 25.2. Deciding check: the calibration cells ARE the test: if family base rates at n>=30 separate resolved outcomes while detector variants do not, the calibration layer is the object; accrual via the pattern-resolution ledger.
- **KD** (the per-name options-level family built from the retained chain: expected move, gamma flip, gamma walls, max p...): choice = opt1 (one_object: the chain as a single information source about positioning and priced risk, read seven ways) [seat probabilities: [{'value': 'opt1', 'probability': 0.78}, {'value': 'opt2', 'probability': 0.21}, {'value': 'opt3', 'probability': 0.01}]]; single registered variable captures most of the shared effect: probability 0.53; edge-share expected score (0-100): 29.8. Deciding check: file the seven chain reads as axis tags on every priced expression from Mon 2026-11-16 and grade which tags separate resolved expression outcomes at n>=30; the expression-grading run is the instrument.
- **KE** (the market-internals complex: distribution-day count, follow-through day, McClellan, Zweig thrust, TRIN, the A...): choice = opt2 (several_objects: a de-grossing signal (distribution), a permission signal (FTD) and breadth-momentum divergences are different decisions) [seat probabilities: [{'value': 'opt1', 'probability': 0.15}, {'value': 'opt2', 'probability': 0.82}, {'value': 'opt3', 'probability': 0.03}]]; single registered variable captures most of the shared effect: seat refused (no probability returned); edge-share expected score (0-100): 23.2. Deciding check: the two seated items already carry ages (distribution count, FTD age); grade book-level de-grossing and pressing decisions against the counts forward, not against the regime label.
- **KF** (the two reading layers: Pass A deterministic geometry (the chart-read items: patterns, levels, divergences, Wy...): choice = opt2 (pass_b_distinct: the perceptual read carries information geometry cannot compute (base quality, shape gestalt), and its absence is a real evidence hole) [seat probabilities: [{'value': 'opt1', 'probability': 0.02}, {'value': 'opt2', 'probability': 0.88}, {'value': 'opt3', 'probability': 0.1}]]; single registered variable captures most of the shared effect: seat refused (no probability returned); edge-share expected score (0-100): 57.2. Deciding check: Pass B is mandated but unbuilt into the brief; the first 30 briefs carrying both a Pass A geometry read and a Pass B perceptual read, graded against outcomes, decide which layer carries the joint value.
- **KG** (the SMC structure family: fair value gaps, order blocks, liquidity pools/sweeps, displacement/inducement label...): choice = opt2 (vocabulary: new labels over the existing structure machinery; the only new measurement is the equal-extremes pool primitive) [seat probabilities: [{'value': 'opt1', 'probability': 0.06}, {'value': 'opt2', 'probability': 0.93}, {'value': 'opt3', 'probability': 0.01}]]; single registered variable captures most of the shared effect: probability 0.52; edge-share expected score (0-100): 17.8. Deciding check: the equal-extremes pool primitive is the only new measurement; tag sweeps on resolved reads and grade the pool-touch cell separately from the springs/upthrust cells it overlaps.
- **KH** (the curator's 100-point composite score: 24 published factors, of which family confluence (up to 30) and Tenso...): choice = opt2 (broad: the small factors jointly carry real discriminating information the two big blocks miss) [seat probabilities: [{'value': 'opt1', 'probability': 0.21}, {'value': 'opt2', 'probability': 0.78}, {'value': 'opt3', 'probability': 0.01}]]; single registered variable captures most of the shared effect: seat refused (no probability returned); edge-share expected score (0-100): 53.0. Deciding check: vary nothing in production; instead, score the same boards under ablated weight sets offline (drop all but confluence+Tensor; drop Tensor; drop confluence) and compare rank correlation with forward outcomes as they accrue.

Seat outputs above are lens readings, printed with their full probability vectors in the runs file; the deciding checks are the record-side instruments, and no cluster verdict above changes any item's tier.

## Potential-edge highlights (record first, seats as lens corroboration only)

- G091 borrow_lending_name [UNGRADABLE-BLOCKED]: lens mean 0.717, spread 0.08, info 54.6, null 0.57. Record basis: Audit row 82 (Context / positioning, materiality MEDIUM for short setups, LOW for longs): Securities-lending borrow fee, utilisation & shares available: a name can have modest short interest and a 40% borrow fee / 95% ut
- G088 industry_group_rank [WATCH]: lens mean 0.701, spread 0.08, info 57.8, null 0.46. Record basis: Audit row 79 (Context / relative-strength, materiality MEDIUM): Industry-group strength rank (group RS over ~6 months, group in top quartile): most of a leader's move is group + market; the same chart in a bottom-quartil
- G021 volume_dry_up [WATCH]: lens mean 0.676, spread 0.11, info 66.4, null 0.52. Record basis: Audit row 18 (Volume / structural, materiality HIGH): Volume falls to well below average (~40-60% below the 50-day, lowest in months) in the final contraction: Minervini/O'Neil's core supply-exhaustion tell and the reaso
- G020 vcp_footprints [WATCH]: lens mean 0.673, spread 0.05, info 59.2, null 0.57. Record basis: Audit row 17 (Structural concept, materiality HIGH): Minervini VCP: 2-6 pullbacks inside a base, each shallower than the last (e.g. 25% -> 15% -> 8% -> 4%), tightening into a pivot: the modern canonical quality grade for
- G023 base_metrics_stage [WATCH]: lens mean 0.661, spread 0.11, info 66.0, null 0.55. Record basis: Audit row 20 (Structural concept, materiality HIGH): Base depth, base length, and base-stage counting (1st/2nd vs 3rd/4th/late-stage) against canon limits: a Stage-2 name on its 4th base is a materially worse swing candi
- F05 momentum_trend [WATCH]: lens mean 0.65, spread 0.18, info 42.6, null 0.51. Record basis: Family 'momentum & trend': 12 member sleeves in the curator's FAMILIES map; habitat: continuation habitat (regime_uptrend_momentum). One vote per family in the confluence factor (B01).
- G077 market_distribution_days [WATCH]: lens mean 0.64, spread 0.24, info 65.2, null 0.46. Record basis: Audit row 71 (Market-internal, materiality HIGH): Distribution-day count (index): down >=~0.2% on higher volume; ~5-6 in ~25 sessions = uptrend under pressure. A regime label cannot substitute for the count: distribution
- R62 retests_reclaims [WATCH]: lens mean 0.634, spread 0.22, info 48.8, null 0.53. Record basis: class (a) integrity-gated, VAL 112/115 briefs; UNAVAIL only where read_chart withheld a discontinuous series (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))
- G087 institutional_sponsorship [WATCH]: lens mean 0.63, spread 0.12, info 35.6, null 0.53. Record basis: Audit row 78 (Context, materiality MEDIUM): Institutional sponsorship trend: # funds owning, 13F change, quality of holders (IBD's 'I'): rising sponsorship into a base is the fundamental-side confirmation of the accumula
- R29 momentum_6m [WATCH]: lens mean 0.62, spread 0.24, info 42.4, null 0.51. Record basis: class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)); its cross-stock rank is board-relative by construction (ranks against names briefed in the same build, not the market)
- G078 market_follow_through [WATCH]: lens mean 0.617, spread 0.24, info 60.6, null 0.52. Record basis: Audit row 72 (Market-internal, materiality HIGH): Follow-through day: on day 4+ of a rally attempt, a major index rises >=~1.25-1.7% on higher volume — the canonical permission slip to press new swing longs after a corre
- R31 relative_strength [WATCH]: lens mean 0.617, spread 0.24, info 49.8, null 0.5. Record basis: class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs)); SPX leg always prints, sector leg only for names in the sector map
- G092 power_earnings_gap [WATCH]: lens mean 0.613, spread 0.14, info 44.0, null 0.52. Record basis: Audit row 83 (Structural / context, materiality LOW-MEDIUM): Power Earnings Gap / post-earnings drift as a named pattern: an earnings gap up >=~10% on >=~2x volume that holds its gap/first days' range, entering a drift w
- G022 pivot_tightness [WATCH]: lens mean 0.607, spread 0.22, info 54.2, null 0.7. Record basis: Audit row 19 (Structural concept, materiality MEDIUM-HIGH): Final area shows very narrow ranges and closes: 3-weeks-tight (weekly closes within ~1-1.5% for 3 weeks, an O'Neil add-on buy point), tight daily closes, shakeo
- R19 higher_timeframe [WATCH]: lens mean 0.603, spread 0.31, info 50.4, null 0.63. Record basis: class (a) unconditional, VAL 115/115 briefs (GESTALT-COVERAGE.md census 2026-10-17 (115 briefs))

The ordering above is a lens sort for reading order only; it promotes nothing. The record-side highlights stand on their own: N08 (the only LIVE CANDIDATE, forward resolution running); G077/G078 (the two seated market-timing items the registry could not express); M12/M13 (the calibration layer, the canon's only self-grading machinery, lawful cells accruing); G067 (expected move, the yardstick every earnings hold is already judged against informally); G058 (CMF, the audit's most conspicuous gap, blocked by a slate omission, not by evidence).

## Spend and utilization

- Requests: 20 Decisions API calls (banks: best-setups-plausibility x4, best-setups-null x4, best-setups-lenses x11, best-setups-connections x1), all model gpt-6-luna, bank version 1.0, each pack hash recorded in the runs file. Questions: 2664. Answers recorded: 2664, of which 4 are seat refusals carrying no probability (the KA, KE, KF and KH single-variable predicates in Bank D; printed as refusals in the connections section, not silently dropped).
- Tokens (harness usage): input 630,632 (of which cache read 26,878, cache write 64,735), output 0 as reported by the API. Cost (harness-priced): $0.0623. The harness request-budget ledger is the system of record for the day count.
- Utilization choices (per the addendum): all three question types used where each fits (predicate for plausibility/nulls/lenses, score with 5-band levels for marginal information and cluster edge-share, choice for cluster structure); seven-lens panels at FULL width on every item (264 of 264), not a decile sample; the adversarial-null pass and the connection-hunting pass run as separate banks with separate ids; full probability vectors recorded in the runs file; the confidence field never consumed. Pack sizes were set at 132 questions (plausibility/null, 66 items) and 175 questions (lenses, 25 items x 7) — under the endpoint's 400-question cap by design, because the binding constraint in this run was the organization's shared tokens-per-minute ceiling (2,000,000 TPM, observed at 1,973,531 used when the first oversized pack was refused), and smaller packs fit the headroom other estate lanes left open.
- Rate-limit doctrine as corrected by the addendum: a 429 is backed off and resumed, never a stop order. In this run: the harness's internal retries (3 x 5/10/15s) plus a runner-level resume loop (60-second sleeps, same pack retried) carried every pack through repeated TPM walls; one runtime restart interrupted the run mid-backoff and the runner resumed from its saved state with zero repeated calls (15 packs skipped as already-done on relaunch). The only local limit is the 5,000 requests/day circuit breaker in request_budget.json. The brief's original stop-on-429 instruction was superseded by the addendum before any call ran.

## STATUS

STATUS: PARTIAL — the recheck itself is complete at its stated granularity (264 of 264 located items itemized and read; 264 of 264 seated on the plausibility, adversarial-null and full seven-lens banks; 2,664 of 2,664 questions answered, 4 of them seat refusals with no probability, named in the connections section), and the PARTIAL verdict names what the corpus itself leaves unproven, not unfinished work in this leg: (1) no canon item carries a registered falsifier that has fired, so the RESOLVED-AGAINST tier is empty and 161 WATCH items stand on mechanism and record, not on resolved forward grades — their resolution path is the named accrual machinery (calibration cells at n>=30, the Ghost Book pattern ledger, step-13 axis tags from Mon 2026-11-16); (2) six audit gaps have no slate row and no producer (CCI, Aroon, CMF at MEDIUM/MEDIUM-HIGH materiality; ROC and StochRSI standalone; the alt-MA half of row 31), blocked on a slate omission in the parent's build lane, named in G041/G045/G058/G043/G044/G034; (3) the three named-unavailable stamps (options flow, borrow/lending, sentiment surveys) stay UNGRADABLE-BLOCKED on the exact missing sources printed in G075/G091/G085; (4) the seven S5 items stay blocked by the owner's frozen-method ruling, recorded with no recommendation.

Evidence pointers: item table `programa_work/programa_items.py` (264 items, ids unique, counted by section); seat runs `programa_work/programa_seat_runs.json` (20 packs, per-pack hash/cost/usage, 2,664 answers with full probability vectors); register `PROGRAM-A-BEST-SETUPS-REGISTER.jsonl` (265 lines = 1 header + 264 rows); harness ledger `~/workspace/midna-book/typed-layer/request_budget.json` (day count 150 requests, $0.229836 all-estate at build time; this leg $0.062262 across 20 successful requests); corpus sources as cited per item (consideration registry census GESTALT-COVERAGE.md 2026-10-17; setups_curator.py + golden setups_latest.json; ta-canon-gap-audit report 2026-10-20; CANON-GAPS-STUDY; BEST-SETUPS-REGISTER-2026-10-22; slate key grep over femto-lean core/consideration.py + core/chart_read.py, 2026-11-15).

