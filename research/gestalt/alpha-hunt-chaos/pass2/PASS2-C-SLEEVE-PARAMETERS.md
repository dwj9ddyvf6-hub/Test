# PASS 2, LANE C — ALL SLEEVES: VARIABLES, PARAMETERS, AND COMBINATIONS

Coverage, counted at build time from the artifacts: 339 of 339 sleeve parents extracted through the adapter seam (10447 parameter rows, every constant with its value and source line in pass2/work/param_maps.json); 24 of 339 sleeves variation-graded on data the sleeve itself produced (2 SCORED at the pre-registered bar, 22 INDICATIVE below it); 315 of 339 UNGRADABLE-BLOCKED, each with the specific missing datum named in its own register row, never as a class verdict.

## Method

Extraction (the Pass 1 wall, cured): Pass 1's prototype extractor read only module-level UPPERCASE numeric assignments in a sleeve's own module file and covered 84 of 339 parents; 268 sleeves are adapters3 shims whose parameters live behind the adapter seam. The Pass 2 extractor (pass2/work/build_param_maps.py, AST only, no desk module imported) follows the seam: config row (params, cadence, capital, costs), the sleeve's own module, the delegated engine's per-sleeve SPECS entry keyed by SLEEVE_ID plus engine-level constants (desk3/lazarus.py, the aster batch engines, q07), subscript overrides on SPECS entries, call-site kwargs in delegating evaluate() calls (the laz_sleeves seam), and the ported sleeves' same-stem v2 adapter and strategy copies under adapters/ and sleeves/ reached through the adapters3._snapshot_ctx bridge. Tuple assignments (SLOTS, SLOT_USD, HOLD_SESSIONS = ...) and arithmetic literals (60*48) are evaluated statically.

Variation (pass2/work/run_variations.py): on each sleeve's own recorded entry fills (state/dispatcher.jsonl*, 6,708 entry fills in total) priced forward on stored daily bars (cache/bars, 51 symbols; QQQ is the benchmark of record because the SPY/IWM/DIA caches end 2026-10-31, Campaign 1's recorded substitution): BASE hold profile at 1/3/5/10 sessions (the horizon_sessions parameter varied over its range), INVERT_SIGNAL, TIME_OF_DAY split, and, where the extracted map carries exit-path parameters, an exit-path simulation walking stored closes from each entry: EXIT_BASE at the sleeve's own stop_pct/target_pct/horizon, PARAM_JITTER (x0.8 and x1.2 singly; horizon x0.5 and x2), PARAM_EXTREME (stop x0.25, target x3, horizon x4), GATE_DROP (each gate dropped singly), net of the 6bp exit haircut. Scoring bar (Campaign 1, pre-registered): at least 10 priceable events on at least 3 distinct entry dates = SCORED; any priced variation below the bar = INDICATIVE. Signal-side parameters inside evaluate() (thresholds, windows) do not transform the recorded stream and are not pretend-varied; they are in the map for the seat read and for the replay-harness queue. Nothing in production sleeve code or the Tensor engine was edited; all variation ran in this research tree.

## Extraction results

Parameter rows by layer: config 3602, engine 4348, own 532, strategy 1965. Total 10447 rows over 339 maps (median 28 per sleeve). Extraction failures: 0. Sleeves whose map carries at least one exit-path parameter (stop_pct, target_pct, or horizon): 61 of 339.

## Variation results: the 24 graded sleeves

| sleeve | tier | entries (priceable/dates) | fwd5 raw bp | fwd5 excess bp | invert fwd5 bp | exit base bp | best exit variation |
|---|---|---|---|---|---|---|---|
| aster_etf_qqq_monthly_c098 | SCORED | 49 (46/8) | 147.9 | -51.8 | -147.9 | no exit params |  |
| aster_etf_qqq_monthly_m150 | SCORED | 15 (13/5) | 279.6 | -64.2 | -279.6 | no exit params |  |
| aster_core_rsi2_long | INDICATIVE | 2 (2/2) | -128.9 | -220.4 | 128.9 | no exit params |  |
| aster_core_rsi2_vertical | INDICATIVE | 2 (2/2) | -124.9 | -216.4 | 124.9 | no exit params |  |
| aster_etf_core25_c098 | INDICATIVE | 2 (1/1) | -170.4 | -16.9 | 170.4 | no exit params |  |
| aster_etf_core25_m150 | INDICATIVE | 2 (1/1) | -167.3 | -13.8 | 167.3 | no exit params |  |
| aster_saty_research | INDICATIVE | 7 (1/1) | -1455.8 | -501.2 | 1455.8 | no exit params |  |
| beatendown | INDICATIVE | 17 (2/2) | 488.2 | 969.5 | -488.2 | no exit params |  |
| bta_onebar_basket | INDICATIVE | 12 (6/4) | -220.6 | -549.5 | 220.6 | no exit params |  |
| bta_onebar_qqq | INDICATIVE | 7 (7/4) | -188.4 | -446.9 | 188.4 | -10.8 | stop_x0.8 -7.4 |
| bta_onebar_rth | INDICATIVE | 5 (5/3) | -294.6 | -740.6 | 294.6 | no exit params |  |
| capitulation | INDICATIVE | 14 (1/1) | 445.9 | 909.8 | -445.9 | no exit params |  |
| confluence | INDICATIVE | 17 (2/1) | 251.0 | 749.8 | -251.0 | no exit params |  |
| donchian | INDICATIVE | 13 (2/1) | 246.1 | 744.8 | -246.1 | no exit params |  |
| leaps_momentum | INDICATIVE | 16 (6/1) | None | None | None | no exit params |  |
| momentum | INDICATIVE | 7 (2/1) | 239.8 | 738.5 | -239.8 | no exit params |  |
| morning_dip | INDICATIVE | 1 (1/1) | 443.7 | 942.4 | -443.7 | no exit params |  |
| red_day_reversal | INDICATIVE | 164 (69/2) | -900.1 | -839.3 | 900.1 | -206.0 | stop_x0.25_extreme -56.0 |
| rsi_meanrev | INDICATIVE | 8 (1/1) | 37.1 | 535.8 | -37.1 | no exit params |  |
| s_cl_vmr_qqq | INDICATIVE | 3 (3/3) | -238.3 | 22.4 | 238.3 | -57.5 | horizon_x0.5 -53.3 |
| s_mn_macd | INDICATIVE | 177 (172/1) | 31.1 | 529.9 | -31.1 | no exit params |  |
| t_cci_corr | INDICATIVE | 27 (1/1) | None | None | None | no exit params |  |
| tensor_swing | INDICATIVE | 3633 (86/2) | None | None | None | no exit params |  |
| ts_momentum_decile | INDICATIVE | 14 (2/1) | 245.6 | 744.3 | -245.6 | no exit params |  |

Horizon note, leaps_momentum: no fwd5 read (its priceable entries sit too close to the end of the stored series); priced horizons: fwd1 71.9 bp (n=6).
Horizon note, t_cci_corr: no fwd5 read (its priceable entries sit too close to the end of the stored series); priced horizons: fwd1 -37.6 bp (n=1).
Horizon note, tensor_swing: no fwd5 read (its priceable entries sit too close to the end of the stored series); priced horizons: fwd1 79.7 bp (n=86).

Exit-path parameters: 61 of 339 maps carry at least one of stop_pct, target_pct, horizon; of those, 3 sleeves also hold a priceable record, and the full jitter/extreme/gate-drop set ran on them (bta_onebar_qqq, red_day_reversal, s_cl_vmr_qqq). The other exit-parameter sleeves are record-blocked like the rest; their variation set is fully specified in their maps and runs the moment their entries price.

The two SCORED sleeves are the same two Campaign 1 scored, the aster_etf_qqq_monthly arms (c098 and m150): benchmark-self sleeves whose entries are QQQ itself, so their excess-over-QQQ profile is degenerate by construction and the raw profile is the read. No other sleeve in the fleet reaches the bar on its own record; that is a statement about the stored record (435 of 6,708 entry fills priceable forward under this lane's definition: entry date resolvable in the symbol's stored daily series with forward bars after it), not about the sleeves' live behaviour.

## Joint variation: families, arm groups, mirror twins

Joint runs pool the recorded entries of every member of the group and vary the pool (hold profile + inversion), with the per-arm fwd5 contrast printed so the arm constant is read on identical footing. Groups with no member record cannot be pooled; they are counted, not silently dropped.

| unit (arm group) | members | members with records | pooled entries | pooled fwd5 raw bp | pooled invert bp |
|---|---|---|---|---|---|
| Aster ENJ nfs arms | 7 | 0 | 0 | no member record | |
| Aster ETF arms c098/m150 | 26 | 4 | 61 | 177.1 | -177.1 |
| Aster PEAD options | 4 | 0 | 0 | no member record | |
| Aster RSI2 recovery/core | 12 | 2 | 4 | -126.9 | 126.9 |
| Aster absorption | 8 | 0 | 0 | no member record | |
| Aster breakout arms | 2 | 0 | 0 | no member record | |
| Aster native SMA200 crypto | 2 | 0 | 0 | no member record | |
| Aster opening gamma | 2 | 0 | 0 | no member record | |
| Aster other batch sleeves | 60 | 0 | 0 | no member record | |
| Aster pub arms | 2 | 0 | 0 | no member record | |
| Aster trader/saty research | 2 | 1 | 1 | -1455.8 | 1455.8 |
| BTA onebar family | 3 | 3 | 18 | -225.7 | 225.7 |
| ChartsLector fire consumers (rule_*) | 5 | 0 | 0 | no member record | |
| DMAC family | 5 | 0 | 0 | no member record | |
| Fires singles | 38 | 9 | 19 | 319.3 | -319.3 |
| Free Kraken family | 7 | 0 | 0 | no member record | |
| Free opt family | 6 | 0 | 0 | no member record | |
| Fwd port sleeves | 4 | 0 | 0 | no member record | |
| Lazarus catalog singles | 13 | 1 | 3 | -238.3 | 238.3 |
| Lazarus fire consumers | 5 | 0 | 0 | no member record | |
| MN catalog | 18 | 1 | 172 | 31.1 | -31.1 |
| Q07 catalog | 49 | 0 | 0 | no member record | |
| Saty family | 6 | 0 | 0 | no member record | |
| Spec singles | 12 | 2 | 70 | -886.7 | 886.7 |
| Tensor D20/H1 model sleeves | 6 | 1 | 1 | None | None |
| Tensor batch13 C1/beta consumers | 10 | 0 | 0 | no member record | |
| Tensor batch14/15 G4 consumers | 12 | 0 | 0 | no member record | |
| Tensor producers | 2 | 1 | 86 | None | None |
| Trullas family | 11 | 0 | 0 | no member record | |

Unit joint runs executed: 10 of 29 multi-member units; the rest have no member with a priceable record. Mirror-twin stem groups where at least two twins hold priceable records: 2 (aster_etf_core25, aster_etf_qqq_monthly). The c098/m150 ETF arms are the twin pair with a SCORED read on both sides; their contrast sits in the graded table above.

## Decisions API seat over the parameter maps (lens only; seats set no grades)

Bank pass2-lane-c-sleeve-parameters v1.0, model gpt-6-luna: 280 questions in 5 family packs, $0.005877. Per family: a load-bearing score (expected value of the seat's probability vector over the 0-100 bands) and an adversarial inherited-template probability for each of the family's 24 most-carried parameters, a seven-lens panel predicate on the family map, and one adversarial-null choice.

### Aster
Seat's most load-bearing parameters: session (72.8), flat_by_close (70.8), cadence_s (70.0), bp_buffer_frac (68.0), fill_timing (66.4). Most likely inherited-template values: session (0.81), flat_by_close (0.78), cadence_s (0.77), commission_per_share (0.76), parked_reason (0.75). Seven-lens panel on the family map (probability it encodes a capturable edge): mean 0.141, range 0.09 to 0.19. Adversarial-null argmax: measurement_blocked (0.85).

### Fires and singles
Seat's most load-bearing parameters: session (72.8), cadence_s (70.4), flat_by_close (67.6), capital_usd (66.8), bp_buffer_frac (66.0). Most likely inherited-template values: cadence_s (0.84), sell_to_close (0.83), session (0.82), min_commission_per_order (0.82), fill_timing (0.8). Seven-lens panel on the family map (probability it encodes a capturable edge): mean 0.159, range 0.12 to 0.19. Adversarial-null argmax: measurement_blocked (0.97).

### Lazarus/Q07/MN
Seat's most load-bearing parameters: flat_by_close (73.8), session (72.0), cadence_s (69.0), fill_timing (68.4), capital_usd (66.0). Most likely inherited-template values: flat_by_close (0.79), commission_per_share (0.79), midlarge (0.79), cadence_s (0.78), session (0.78). Seven-lens panel on the family map (probability it encodes a capturable edge): mean 0.157, range 0.11 to 0.19. Adversarial-null argmax: measurement_blocked (0.86).

### Spec-built
Seat's most load-bearing parameters: session (72.0), flat_by_close (70.6), cadence_s (68.6), capital_usd (65.0), bp_buffer_frac (64.0). Most likely inherited-template values: cadence_s (0.84), fill_timing (0.84), slippage_model (0.84), buy_to_close (0.83), flat_by_close (0.82). Seven-lens panel on the family map (probability it encodes a capturable edge): mean 0.146, range 0.12 to 0.17. Adversarial-null argmax: measurement_blocked (0.72).

### Tensor
Seat's most load-bearing parameters: session (69.0), flat_by_close (67.8), cadence_s (65.8), capital_usd (64.0), fill_timing (62.8). Most likely inherited-template values: session (0.83), commission_per_share (0.83), min_commission_per_order (0.83), flat_by_close (0.82), fill_timing (0.8). Seven-lens panel on the family map (probability it encodes a capturable edge): mean 0.149, range 0.12 to 0.17. Adversarial-null argmax: measurement_blocked (0.96).

Supplement (bank pass2-lane-c-strategy-parameters v1.0, 160 questions, $0.003442): the v1.0 ranking is dominated by config boilerplate carried by all 339 sleeves, so the seat was re-run per family over the 16 most-carried strategy-bearing parameters only (own/engine/strategy layers; numeric or bool values; UPPERCASE constants, SPECS-entry fields, and unit-suffixed fields; function-default argument names and flattening artifacts excluded — a first unfiltered supplement run is preserved in pass2/work/seat_runs2_noisy_pool.json and superseded by this one). That is the read that separates the family's actual trading parameters from its plumbing:

### Aster, strategy parameters
Most load-bearing: risk (42.0), ENTRY_WINDOW_S (41.8), dte (40.0), FEE (36.0), SLICE (35.2), hold (34.8). Most likely inherited-template: SLICE (0.68), gross (0.66), max_debit_width (0.66), lag_bars (0.66), FEE_PER_CONTRACT (0.66), ENTRY_FRESH_S (0.66).

### Fires and singles, strategy parameters
Most load-bearing: MAX_POSITIONS (44.4), RISK_FRACTION (42.4), CADENCE_S (39.4), BAR_SECONDS (37.8), _NBARS (35.8), NOTIONAL_FRACTION (33.2). Most likely inherited-template: BAR_SECONDS (0.77), BUDGET_USD (0.76), FUTURE_TOLERANCE_SECONDS (0.76), RECEIPT_MAX_SECONDS (0.75), STALE_BAR_DAYS (0.73), MAX_POSITIONS (0.72).

### Lazarus/Q07/MN, strategy parameters
Most load-bearing: parked (59.0), budget (55.0), STOP_FRAC (54.4), slots (53.8), WINDOW_SESSIONS (53.4), horizon_w (51.8). Most likely inherited-template: parked (0.74), slots (0.7), DEFAULT_EQUITY (0.7), XSTALE_MAX_LAG_DAYS (0.7), budget (0.69), SLOT_USD (0.69).

### Spec-built, strategy parameters
Most load-bearing: _BARS_N (48.6), SLICE_FALLBACK_USD (41.0), QUOTE_STALE_S (35.2), RISK_FRACTION (34.2), F_GATE (33.8), MAX_POSITIONS (32.8). Most likely inherited-template: SLICE_FALLBACK_USD (0.74), _BARS_N (0.72), QUOTE_STALE_S (0.71), F_TRIGGER (0.71), MAX_POSITIONS (0.7), F_GATE (0.69).

### Tensor, strategy parameters
Most load-bearing: HOLD_SESSIONS (69.4), slots (49.2), TICKET (47.0), ticket (45.8), SLOTS (43.6), SLICE (34.8). Most likely inherited-template: slots (0.73), STALE_BAR_DAYS (0.72), ticket (0.71), SLOTS (0.71), STALE_SIGNAL_DAYS (0.71), HOLD_SESSIONS (0.7).

## The 315 blocked sleeves, by missing datum (each named in its own register row)

- no fills of any kind recorded: 194
- no fills; upstream fire/signal stream produced no recorded entry: 80
- exit fills only, entry fills absent: 23
- entries recorded, none priceable on stored bars: 17
- entries at the end of the stored series, no forward bars: 1

The dominant class is the absence of any recorded fill: the dispatcher record is the only event stream most sleeves have, and a sleeve that has never recorded an entry has nothing of its own to vary. The cured intent records (symbol/side/ref_price stamped from 2026-11-15, desk commit 87a3956) are the accrual instrument that converts these rows session by session from Monday 2026-11-16. The second class is a data-coverage wall, not a sleeve property: 51 cached symbols against a fleet that trades the small-cap universe (aster_tensor_d20_tensor alone holds 684 recorded entries on uncached names).

STATUS: PARTIAL — extraction is GREEN and complete (339 of 339 parents, 10,447 parameter rows, counted in pass2/work/param_maps.json and recounted in the register); variation grading is bounded by the recorded stream (24 of 339 graded: 2 SCORED, 22 INDICATIVE; joint runs on 10 units and 2 twin groups), and the remaining 315 rows stand UNGRADABLE-BLOCKED each with its own missing datum named, converting only as forward records accrue and the bar cache widens beyond 51 symbols.
