# W2-6: THE FLEET ECONOMY, FIRST COMPUTATION (Alpha Hunt Wave 2, Sat 2026-11-14)

SCOPE: Surface, the decisions program home only (wave2/ records, tools/ additions); no desk tree edits, and iv_snapshot.py was never imported. Constraints, Design Rule 1 of designs/LEVEL4-FLEET-ECONOMY-DESIGN.md binds throughout: allocation, promotion, and killing must be computable from a table by a script, with no discretionary step anywhere; a human may change a formula in writing with a falsifier, never override an output. Outcome, the Level 4 GDP line computed for the first time, the fleet correlation tax computed from the dispatcher journal, and dated birth and death registers for all 339 sleeves. Proof, tools/fleet_economy.py run end to end (exit 0) and its three output artifacts read back after writing: wave2/fleet_economy_v1.json, wave2/birth_register_v1.json, wave2/death_register_v1.json. Edges, the Scharfstein and Stein warning from Deep Dive Two section 1 is the reason this record contains no narrative allocation judgment at all: every figure below is a formula output, and every gap prints UNMEASURED with its missing input named.

Population honesty, stated once and binding on every section: all GDP computations use ONLY the proven per-close population of attribution ledger v1.1 (13 own closes across 3 sleeves, preserved per-close in wave2/attribution_ledger_v1_1.json). The two v1 fields that failed reproduction in W2-2 are never used as inputs here: excess_vs_spy_as_recorded_v1 (built on shared-book marks including unrealized P and L, a different population from own closes) and ranking_realized_usd (the shared-book figure; for aster_trader_donchian55 it differs from own-close realized by 498.38, 5,987.73 against 5,489.35). R multiples remain null in v1.1 by honesty (no stop or risk amount preserved), so no R-based figure appears anywhere in this record.

## 1. THE GDP LINE, FIRST COMPUTATION

GDP_t = graded expectancy per unit of drawdown = Consumption / fleet drawdown, computed by script from ledger v1.1 and the desk warm bars.

### The line as printed

```text
GDP (Level 4, first computation, as of 2026-11-13 close record)
  Consumption (proven compounding)      $0.00
    provisional flagged subtotal beside it, never inside it: $5,850.22
  Investment (forward test)             60 sleeves, $657,000 paper capital, 7,713 fills
  Waste (idle-capital drag, signed)     -$6,811.03 on $2,290,192 idle capital (277 sleeves)
  Denominator (fleet drawdown)          $300.49
  GDP = 0.00 / 300.49 = 0.0000
```

A zero consumption line is the finding, not a failure of the report (design section 1, publication rule).

### Consumption

Formula: C = sum(realized_usd | own_closes >= 3 and NETTED not in flags) over the 339 per-sleeve rows of ledger v1.1.
Inputs: verdict-grade sleeves, 0. Both sleeves at or above the 3-close bar carry NETTED (aster_trader_donchian55, flags NETTED;SCALE, 8 closes; bta_onebar_rth, flags NETTED, 3 closes), so the clean count is 0 and C = $0.00 exactly.
Provisional flagged subtotal, printed beside C and never inside it: 5,489.35 (aster_trader_donchian55, 8 closes) + 661.36 (bta_onebar_rth, 3 closes) - 300.49 (bta_onebar_qqq, 2 closes, below the bar, no flag) = $5,850.22 across the only 3 sleeves with any own closes. This matches the v1.1 reproduced total to the cent.

### Investment

Formula (design section 1): sleeves in LOW SAMPLE klass with fills above 0 and own_closes below the bar (3).
Output: 60 sleeves, $657,000 summed allocated_capital_usd from the v1.1 real capital column, 7,713 fills.
Named difference from the design's Today line: the design text counted all 62 LOW SAMPLE sleeves ($677,000, 7,766 fills). The formula as written excludes the 2 sleeves at or above the bar (aster_trader_donchian55 and bta_onebar_rth, $10,000 each, 53 fills between them). The formula governs; the difference is named here, not smoothed.

### Waste

Formula (updated per the W2-6 brief, now that v1.1 carries a real capital column; the design's uniform proxy, fleet capital / 339 per sleeve, is retired): W = sum over sleeves in klass NOT FIRED or PARKED of allocated_capital_usd_i x SPY_return(window_i).
SPY window basis, stated in full: window_i is the sleeve's `sessions` most recent SPY daily sessions ending 2026-11-11, taken from the desk warm bars (warm_bars.json, the same tape the v1.1 builder used). The end date is the ranking census session end: ranking health_at is 2026-11-12T01:21:06Z, before the 2026-11-12 session opened, and the live_start arithmetic checks against it (live_start 2026-10-23 plus 14 sessions ends 2026-11-11; aster_trader_donchian55 live_start 2026-10-27 plus 12 sessions ends 2026-11-11). SPY_return = close on the last window session / close on the first window session - 1.
Inputs: 277 sleeves (223 NOT FIRED + 54 PARKED), summed allocated capital $2,290,192, which is 77.18 percent of the fleet total $2,967,192.
Output: W = -$6,811.03 over the 250 measurable sleeves. The sign is a computed result, not an error: SPY fell over most census windows (the 14-session window return is -1.99 percent on this basis, the 13-session window -2.32 percent), so idle capital avoided a decline and the signed opportunity drag is negative. Its magnitude is $6,811.03.
UNMEASURED, named, never zero-filled: 27 waste sleeves have sessions below 2 and therefore no SPY window (26 sleeves at 0 sessions, listed in full in fleet_economy_v1.json, plus shen_fade at 1 session). Their combined allocated capital is $69,055; the printed W excludes them.

### Denominator

Formula: fleet drawdown = max peak-to-trough decline of the summed realized_usd curve over the trailing quarter, built from the ledger's per-close rows grouped by close_date, curve starting at 0.
The record supports exactly 3 curve points, and no curve beyond them is invented:

| Close date | Day realized (USD) | Cumulative realized (USD) |
|---|---|---|
| 2026-10-30 | 5,489.35 | 5,489.35 |
| 2026-11-04 | -300.49 | 5,188.86 |
| 2026-11-05 | 661.36 | 5,850.22 |

Peak 5,489.35 (2026-10-30), trough after peak 5,188.86 (2026-11-04), max peak-to-trough decline $300.49. The trailing quarter contains no other own closes, so $300.49 is the whole denominator the record supports. It is thin (13 closes, 3 dates) and is printed as such; the design's v1 gap (no per-sleeve equity curve) is now closed only to this extent: a fleet summed curve exists, a per-sleeve daily curve still does not, and any finer drawdown figure is UNMEASURED.

GDP ratio: 0.00 / 300.49 = 0.0000. The provisional subtotal is not divided into the denominator anywhere in this record; doing so would put flagged money inside the line.

## 2. THE CORRELATION TAX

### Journal, located from the evidence trail

The execution board evidence (execution_board.csv, evidence_detail) cites "full dispatcher record 65203 rows (5 generations), window 2026-11-02 to 2026-11-13". The artifact is the 5 generations of the desk dispatcher journal at muse-desk-v3/state/dispatcher.jsonl plus dispatcher.jsonl.1 through .4, read read-only. At this run's read the files hold 65,607 rows total; the journal has grown since the board check, so this computation freezes its window at the cited dates (intent_id timestamps from 2026-11-02 to 2026-11-13) and reports what it used: 55,304 rows fall on the 10 window sessions, and 4,565 rows fall on the weekend dates 2026-11-07 and 2026-11-08 inside the window and are excluded from the session series (they are not sessions), named here rather than silently dropped.

### Method (design section 2, interim fire basis, exactly as the design specifies until closes exist)

- Sessions: the 10 Monday to Friday dates 2026-11-02, 03, 04, 05, 06, 09, 10, 11, 12, 13.
- Fire indicator: 1 on a session where the sleeve has at least one dispatcher row whose intent_id timestamp falls on that session (an intent reached the dispatcher), else 0.
- rho_ij: Pearson correlation of the two sleeves' fire indicator series over the 10 sessions.
- sigma_i: sample standard deviation (ddof=1) of the sleeve's daily distinct-intent count over the 10 sessions (the design's interim fire-count volatility).
- w_i: allocated_capital_usd_i / 2,967,192 (the v1.1 real capital column; fleet weights, not renormalized to the measurable subset).
- Pair contribution: c_ij = w_i x w_j x rho_ij x sigma_i x sigma_j. Fleet aggregate tax (the Deep Dive Two section 1 form, pairs counted once): lambda x sum over i<j of c_ij. Per-sleeve tax (design form): tax_i = lambda x sum over j != i of w_j x rho_ij x sigma_i x sigma_j, and sum_i w_i tax_i = 2 x the aggregate, printed as a cross-check.
- Lambda: printed at lambda = 1. The design calibrates lambda so a strategy duplicating an incumbent must earn about 2x the fleet hurdle, but no numeric fleet hurdle exists on record, so the calibration is UNMEASURED and every tax figure below is per unit lambda. Units are weighted squared distinct-intents-per-day on the interim fire basis, not return units; conversion to return units is UNMEASURED until a realized daily P and L series exists (13 closes cannot supply one).

### Spec status, named before the numbers

The design requires a minimum of 20 shared sessions per pair. This window holds 10. Every pair in this run is therefore below the design minimum, and every correlation below is labeled INTERIM, below-spec, a first computation and not a design-grade measurement. Pairs that cannot be computed at all are named, never filled; the design's median-rho fill for unmeasured pairs is NOT applied, per the brief (a thin pair is named, not filled):

- Measurable: 53 sleeves, 1,378 pairs.
- Zero variance, all-fire (indicator 1 on all 10 sessions, correlation undefined): 20 sleeves, named in fleet_economy_v1.json (includes aster_trader_donchian55, beatendown, capitulation, confluence, donchian, momentum, rsi_meanrev, ts_momentum_decile).
- Zero variance, no fire in window (indicator 0 on all 10 sessions, dated journal rows only outside the window): free_kraken_link_breakdown, s_mn_kronos.
- Undated only (appear in journal rows but never with a dated intent_id, so no fire series exists): 8 sleeves, named in fleet_economy_v1.json (aster_core_rsi2_long, aster_core_rsi2_vertical, aster_etf_drift1_m150, aster_etf_exsmh1_c098, aster_etf_exsmh1_m150, aster_etf_leader1_c098, s_cl_vmr_qqq, s_mn_hourly).
- Never in the journal at all: 264 of the 339 ledger sleeves, named in full in fleet_economy_v1.json. Their fire series is all zero by absence of record, which is a statement about the journal, not proof a sleeve never evaluated.

### Results (INTERIM, lambda = 1)

- Fleet aggregate tax: -0.97629861 (pairs counted once). Gross positive pair contributions sum to +2.42444846 and gross negative to -3.40074707, so the net is negative: on this fire basis the measurable fleet's weighted co-firing is net diversifying, not net crowding. Cross-check: sum_i w_i tax_i = -1.95259719 = 2 x the aggregate, to the digit.
- One sleeve dominates the net: pairs involving tensor_swing sum to -0.99750184, essentially the entire aggregate. tensor_swing has by far the largest fire-count volatility (sigma 771.4421 distinct intents per day), so its mostly negative weighted correlations set the fleet sign. Any reading of the aggregate that does not name this concentration would be a narrative, so it is named as arithmetic.
- Median pairwise rho: 0.1021. Hurdle dynamics (design rule: hurdle_t = base hurdle x (1 + median rho / 0.5), floored at base): the multiplier at the median is 1.2041. The base hurdle itself is UNMEASURED (no numeric base on record), so no hurdle level is printed.
- Effective N (design dashboard metric 1, interim fire basis): N_eff = (sum lambda_k)^2 / sum lambda_k^2 = 5.1808 over the 53 measurable sleeves. Largest eigenvalue 16.38, a 30.91 percent share (0.3091) of the trace. Reading, stated as arithmetic only: 53 measurable fire series carry about 5.2 independent fire dimensions on 10 sessions of evidence.
- Top taxed pairs (by c_ij, lambda = 1):

| Sleeve i | Sleeve j | rho | sigma_i | sigma_j | Contribution |
|---|---|---|---|---|---|
| aster_tensor_d20_tensor | tensor_swing | 0.5092 | 102.0912 | 771.4421 | 0.45547829 |
| aster_tensor_d20_pv | tensor_swing | 0.5092 | 61.1211 | 771.4421 | 0.27269071 |
| investandbefree_dmac_intraday | tensor_swing | 0.2722 | 45.7992 | 771.4421 | 0.10922022 |
| investandbefree_dmac_deep | tensor_swing | 0.5092 | 20.0280 | 771.4421 | 0.08935473 |
| grok_sr_spy | tensor_swing | 0.6667 | 15.2756 | 771.4421 | 0.08923177 |
| aster_rsi2_1d | po10_qqq | 1.0000 | 56.3320 | 9.1409 | 0.07310737 |
| aster_tensor_d20_pv | aster_tensor_d20_tensor | 1.0000 | 61.1211 | 102.0912 | 0.07087423 |
| teddy_orb_spy | tensor_swing | 0.5092 | 14.9086 | 771.4421 | 0.06651450 |
| po10_qqq | rsi_meanrev_options | 0.3563 | 9.1409 | 113.1614 | 0.05233347 |
| em_1587 | tensor_swing | 0.6667 | 8.4958 | 771.4421 | 0.04962752 |

Eight of the top ten taxed pairs involve tensor_swing, and the two rho = 1.0000 pairs (aster_rsi2_1d with po10_qqq; aster_tensor_d20_pv with aster_tensor_d20_tensor) are identical fire patterns on a 10-session binary series, which is what a 10-session window can and cannot distinguish. Both facts are properties of the window, printed so the next, longer window can falsify them.

- Top taxed sleeves (tax_i, lambda = 1): aster_tensor_d20_tensor 98.25281; aster_tensor_d20_pv 67.262492; grok_sr_spy 26.329031; teddy_orb_spy 24.309158; investandbefree_dmac_deep 17.503868. Full per-sleeve and per-pair tables are in fleet_economy_v1.json (top 15 pairs printed there; all 1,378 pair contributions are recomputed by the tool on every run).

### Dashboard metrics status (design section 4, updated by this run)

1. N_eff: computed INTERIM on the fire basis above (5.1808). Return-basis N_eff UNMEASURED (no per-sleeve daily P and L series).
2. Diversification ratio: UNMEASURED (needs fleet realized vol and stand-alone vols; 13 closes cannot supply them).
3. Median pairwise correlation: computed INTERIM (0.1021, fire basis). Tail correlation on worst-decile fleet days: UNMEASURED (no fleet daily P and L series to define worst-decile days).
4. Birth rate, death rate, median age at death, percent of capital past half-life: registers now exist (section 3). Birth and death counts over the census window are computable from them; median age at death is UNMEASURED (formal deaths, 0; see section 3); percent past half-life is UNMEASURED (no pre-registered half-life field exists for any sleeve).
5. Aggregate DSR distribution: UNMEASURED (the fleet does not yet log honest trial counts per sleeve).
6. Turnover-weighted spread cost: UNMEASURED (no spread cost field on record).
7. Allocation Gini versus return Gini: allocation Gini is now computable from the v1.1 capital column (input landed; the Gini computation itself is not part of this run and is rowed, not estimated). Return Gini UNMEASURED (only 3 sleeves have any realized return).

## 3. DEMOGRAPHY REGISTERS

Artifacts: wave2/birth_register_v1.json (339 rows) and wave2/death_register_v1.json (61 rows), both built by tools/fleet_economy.py from ranking_rows.json, ledger v1.1, the dispatcher journal, the execution board, and the desk config roster (read-only).

Update rule (stated in both artifacts and binding on future runs): the registers are append-only. An existing row is never edited in place. A first_seen_date marked UNKNOWN may be filled only by a dated primary record (ranking live_start, a journal intent timestamp, or a config commit) with its source named in the row's basis field. New sleeves append as new rows. A correction appends a superseding row naming the row it supersedes. No narrative discretion exists in either register: every field is copied or computed from a named source by the tool.

### Birth register

Fields per sleeve: first_seen_date, first_seen_basis, origin_module, registration_in_config_sleeves_json, allocated_capital_usd, klass, sessions, first_dispatcher_date, first_close_date.
Rules: first_seen_date = ranking_rows.json live_start where non-empty, else UNKNOWN. Origin = the ranking module string verbatim (the registration module, for example adapters3.laz_1d or aster_sleeves.aster_abs_base_ada_fullcash). Registration = presence of the sleeve id in muse-desk-v3/config/sleeves.json. first_dispatcher_date and first_close_date are corroborating columns from the journal and the per-close rows; they never substitute for live_start.

Counts:
- Rows: 339 (the full ledger population, matching the board census exactly).
- first_seen_date known: 313. UNKNOWN: 26. The 26 are exactly the 0-session PARKED sleeves (the mk_zerodte, przm, and s_q07w / s_78 families and peers, named in full in the register); none of them appears in the journal, and no dated record of their first sighting exists, so UNKNOWN is the honest entry.
- Origin module: recorded for all 339. Registration in config/sleeves.json: all 339.
- Corroboration present: first_dispatcher_date for 75 sleeves; first_close_date for 3 sleeves.
- Cohort structure (first_seen_date counts): 2026-10-23, 135; 2026-10-24, 107; 2026-10-27, 21; 2026-10-28, 3; 2026-10-29, 9; 2026-10-31, 1; 2026-11-02, 16; 2026-11-03, 11; 2026-11-04, 2; 2026-11-05, 5; 2026-11-09, 1; 2026-11-10, 1; 2026-11-11, 1; UNKNOWN, 26. The 2026-10-23 and 2026-10-24 cohorts total 242 sleeves, which is the single-cohort fact DEMOGRAPHY-SNAPSHOT-1 recorded as 242 of 339 at 13 to 14 sessions, now with the dates behind the session counts. The snapshot's named gap (no birth timestamp per sleeve) is closed for 313 sleeves by the ranking live_start field and stays open, as UNKNOWN, for 26.

### Death register

Formal deaths under the Level 4 death rules (forward Sharpe confidence interval excluding the haircut budget; DSR below 0.5 on forward data; mechanism invalidation): 0. No DSR, confidence interval, or invalidation record exists for any sleeve, so no sleeve can be recorded as formally dead, and none is. What the register records instead is operational cessation, under two script rules, never conflated with formal death (the DEMOGRAPHY-SNAPSHOT-1 warning, applied):

- D1_PARKED: klass PARKED in ledger v1.1, 54 sleeves. Date basis stated on every row: the state was observed at the ranking census (health_at 2026-11-12T01:21:06Z); the park date itself is not on record and no date is invented for it. Of the 54, 26 are the never-live UNKNOWN-birth sleeves above and 28 have a live_start.
- D2_CEASED_FIRING_IN_WINDOW: journal sleeves whose last fire session in the window is on or before 2026-11-06 (no dispatcher row in the final 5 sessions, 2026-11-09 to 2026-11-13), 9 sleeves: aster_r19_tensor_g4_hot_reserve_25 (last fire 2026-11-02), free_kraken_ada_breakdown (2026-11-03, also D1), free_kraken_link_crowded (2026-11-04, also D1), investandbefree_dmac_intraday (2026-11-06), qqq_put_ladder (2026-11-06), s_mn_faber (2026-11-02), s_mn_macd (2026-11-06), s_mn_opt_turtle (2026-11-06), s_mn_reversal (2026-11-04).
- Rows total: 61 (54 D1 + 9 D2 - 2 sleeves meeting both).
- Cause field: each row carries the execution board's trigger_or_blocker text verbatim, with its basis stated on the row (it is the closest cause text on record; where it does not state a park or cessation cause, that cause is UNKNOWN). Board state is printed beside it, and the tension is named rather than resolved: 5 of the 9 D2 sleeves are board-classed LIVE-FIRING, because the board's definition (order_submitted or fill in the last 10 sessions) is wider than this register's any-row final-5-sessions rule. Both definitions are script rules; the register records the narrower observation and does not override the board.
- Median age at death: UNMEASURED. With 0 formal deaths there is no age-at-death population; computing one from parked states would fabricate a mortality rate, which the snapshot explicitly forbade.

## 4. OPEN ROWS

1. Correlation window length: the design minimum is 20 shared sessions and the journal window of record holds 10. The interim tax and N_eff above must be recomputed when the journal carries 20 or more sessions in a trailing window; until then no allocation, promotion, or kill output may cite them as design-grade. Owner, fleet economy lane, at the first window that qualifies.
2. Lambda calibration: needs a numeric fleet hurdle on record. Until one is registered in writing with a falsifier, all tax figures print per unit lambda.
3. Return-basis dashboard metrics 1, 2, 3 (tail), 5, 6, and return Gini in 7: need a per-sleeve daily P and L series and per-sleeve trial counts, neither of which exists. The v1.1 per-close legs are the seed; the daily series build is rowed to the attribution lane.
4. Birth UNKNOWN 26: fillable only by a dated primary record under the register update rule (a config commit history pass over config/sleeves.json is the highest-confidence route; it was not run in this pass and no date is guessed here).
5. Park dates and park causes: no dated kill or park log exists. The death register's D1 rows carry census-observed dates until a dated log lands; building that log prospectively is a one-table job owned by the demography lane.
6. Pre-registered half-life per sleeve: absent for all 339, so dashboard metric 4's past-half-life share and the exploration subsidy ledger's sunset dates (design section 3) remain UNMEASURED. No subsidy figure is printed in this run for the same reason: the subsidy pool and half-lives are not on record, and inventing them would be a narrative allocation, which Design Rule 1 forbids.

STATUS: PARTIAL for W2-6 as scoped (GDP line, correlation tax, and both registers computed from the final artifacts by script; the correlation figures are INTERIM below the design's 20-session minimum, lambda is uncalibrated for want of a numeric hurdle, and the named dashboard metrics and register fields above remain UNMEASURED with their missing inputs named). EVIDENCE POINTER: wave2/fleet_economy_v1.json, wave2/birth_register_v1.json, wave2/death_register_v1.json, built by tools/fleet_economy.py from wave2/attribution_ledger_v1_1.json, ranking_rows.json, execution_board.csv, muse-desk-v3/state/dispatcher.jsonl generations .1 to .4, muse-desk-v3/state/warm_bars.json, and muse-desk-v3/config/sleeves.json, all read after the tool's final run.
