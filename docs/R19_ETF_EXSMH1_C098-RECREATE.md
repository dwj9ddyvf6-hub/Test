# R19_ETF_EXSMH1_C098 - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `R19_ETF_EXSMH1_C098`
- Canonical name: ETF leader excluding semiconductors · 98% exposure
- Aliases: R19_ETF_EXSMH1_C098, ausar_pb87, ausar_r19_R19_ETF_EXSMH1_C098
- Type: market timing and rotation; Family: etf; Algorithm grade in ALL-SLEEVES accounting: FULL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "ETF leader excluding semiconductors · 98% exposure" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "ETF leader excluding semiconductors · 98% exposure" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; femto land-wt config params; md2 catalog entry/exit/strategy text; alias record sources: ausar_deployed, femto_land_wt, md2_ausar_map, md2_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start, 4,430 entries; plus file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,441 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Accounting gaps: none listed. Where the accounting graded PARTIAL, those gaps are gaps of the accounting's consulted sources only; the Test strategy card and code cited below are the fuller record used here, and any remaining gap is marked 'not in the record' in place.

## What this strategy is

ETF leader excluding semiconductors · 98% exposure. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

## Full algorithm

Engine SPECS source_id: R19_ETF_EXSMH1_C098 (desk3/aster_etf_b9.py SPECS and config/sleeves.json params).

Sleeve-specific rules: EXSMH1 selection: SMH is excluded from scoring and selection. Select the highest-scoring remaining symbol. Weights: 100% to the selected symbol.

NAV basis: ENH-NAVBASE applies (this sleeve is in ENH_NAVBASE_IDS, default ON via extra['aster_etf_b9_enh']['nav_basis']): NAV = slice capital (capital_usd when present, else the cash figure as capital proxy); held value is part of that budget, never added on top. A shadow legacy cash-plus-held desired set is computed but never emits.

Evaluation order in desk3/aster_etf_b9.py evaluate():
1. Execution window: if a clock time is known, emit nothing outside 09:35-09:40 America/New_York. Aware timestamps are converted to ET, naive timestamps are read as ET, and a date-only or midnight stamp is ungated. If no time is supplied, the window check passes.
2. Build the primary bars map from view['bars'], keyed '<symbol>|1Day', '<symbol>|1D', or the bare symbol, for the universe. If the map is empty, emit nothing.
3. Score: for each symbol with at least 252 sessions and all closes in the last 252 sessions positive, score = log(close[-1] / close[-127]) (126-session log return). Symbols below 252 sessions are ineligible.
4. Selection for this sleeve's policy (see sleeve-specific rules below). Ties for non-interval policies break alphabetically (lowest symbol among highest scores).
5. Monthly guard: signal_month is the latest bar month (max last-bar date, first 7 characters). If positions exist and every held position carries signal_month equal to that month, emit nothing (this month's signal is already completed).
6. Incumbent (where needed): a position flagged incumbent or selected, otherwise the holding with the largest held value at last close (fallback average price).
7. Prices: last close for each held or target symbol, falling back to bars last close, then to the position average price. If any needed price is <= 0, emit nothing.
8. Desired shares: floor(weight x gross x NAV / price) for each symbol in held union target, whole shares, never capped inside the sleeve. The dispatcher buying-power check governs execution for gross above 1.0.
9. Sell-then-settle: if any holding is above its desired shares, emit ONLY sell intents on this evaluation (kind exit, side sell, qty held minus desired, order_type market, time_in_force day, position_intent sell_to_close), and return. Buys follow on a later evaluation.
10. Otherwise emit buy intents for desired minus held where positive (kind entry, side buy, order_type market, time_in_force day, position_intent buy_to_open, price_hint = last close). Intent id format: '<sleeve>-<signal_month>-<stamp last 4>-<n>-<symbol>-<side>'.
No price stop and no price target exist in this engine. The designed exit is the next monthly selection reducing or replacing a holding.

Exit rules are the sell and rebalance rules in the steps above. There is no separate stop, target, trailing, or time-based exit in the engine, except the BUY_HOLD / monthly guards stated for this sleeve where applicable.

Accounting record for this canonical strategy (verbatim fields from ALL-SLEEVES):
- Entry (accounting): [R19_ETF_EXSMH1_C098] ausar variant: ETF leader excluding semiconductors · 98% exposure
- Entry (accounting): [ausar_pb87] Excludes SMH, the semiconductor ETF, then ranks the remaining configured funds by completed 126-session price return; equal scores use alphabetical ticker order. Allocates to the selected fund. Targets ETF holdings worth 98% of the paper account's net value, rounded down to whole shares.
- Entry (accounting): [ausar_r19_R19_ETF_EXSMH1_C098] Excludes SMH, the semiconductor ETF, then ranks the remaining configured funds by completed 126-session price return; equal scores use alphabetical ticker order. Allocates to the selected fund. Targets ETF holdings worth 98% of the paper account's net value, rounded down to whole shares.
- Exit (accounting): [ausar_pb87] Reduce or replace holdings when the next monthly selection changes their target. This strategy has no price-based stop or profit target.
- Exit (accounting): [ausar_r19_R19_ETF_EXSMH1_C098] Reduce or replace holdings when the next monthly selection changes their target. This strategy has no price-based stop or profit target.
- Filters/data (accounting): [ausar_pb87] data: Completed historical ETF bars for signals; separately labeled IEX quotes for execution. The two-source versions compare complete Alpaca and Yahoo histories without joining them.
- Filters/data (accounting): [ausar_r19_R19_ETF_EXSMH1_C098] data: posted r19 data adapters
- Parameters (accounting): {'R19_ETF_EXSMH1_C098': {'symbols': ['QQQ', 'SPY', 'SMH', 'XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY']}}

## Files in this repo

- This recreation doc: `docs/R19_ETF_EXSMH1_C098-RECREATE.md`
- Strategy card (family): `strategies/ausar/r19-etf.md`
- Code in Test: `sleeves/aster_etf_exsmh1_c098.py`, `adapters3/aster_etf_exsmh1_c098.py`, `integration/aster_etf_exsmh1_c098_adapter.py`, shared engine `desk3/aster_etf_b9.py`
- Existing per-sleeve doc in Test: `docs/ASTER_ETF_EXSMH1_C098-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family parity code in Test: `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py`, `packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py`
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

- Universe: QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY
- Timeframe: 1d bars (daily), monthly selection / rebalance for this sleeve
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0, gross_target 0.98, bp_buffer_frac 0.02
- Cadence: cadence_s 300, session rth
- Parked: false (parked false in config/sleeves.json)
- flat_by_close: false, flatten_time_et: null
- Module: adapters3.aster_etf_exsmh1_c098
- Inputs (config row): bars, positions

Accounting parameters: {'R19_ETF_EXSMH1_C098': {'symbols': ['QQQ', 'SPY', 'SMH', 'XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY']}}

## Data inputs

Primary bars: daily histories for the universe, keyed '<symbol>|1Day', '<symbol>|1D', or bare symbol; the engine uses closes (field c) and last-bar timestamps (field t). Positions: held qty, symbol, average price, and where supplied incumbent/selected flags and signal_month.
Producers: bars producer (outputs bars, freshness_sla_s 900) and broker_readback producer (outputs positions, freshness_sla_s 900), as declared in desk3/aster_etf_b9.py PRODUCERS.
Freshness is as stated in the producer declarations above. Absent or stale bars produce no intents in the engine (empty bars map or missing target price returns an empty list).

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc, the strategy card / family card named in Files, and `docs/ALL-SLEEVES.json` for the accounting record.
3. Use the code files listed in Files as the runnable logic, preserving their exact delegation and parameter values.
4. Supply the data inputs named above in the shape the code expects.
5. Run on the cadence and in the window stated in Configuration / Full algorithm; exits / rebalances are evaluated in the order the algorithm states.
6. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behaviour checklist in the existing per-sleeve doc named in Files, derived only from the algorithm above.
- Checklist summary: (a) outside the 09:35-09:40 ET window (when a time is known) no intents; (b) eligibility and selection match the sleeve-specific rules exactly; (c) desired shares equal floor(weight x gross x NAV/equity / price) on the basis stated above, whole shares only; (d) sells precede buys / sell-then-settle as the engine states; (e) the monthly / buy-and-hold guard, where stated, suppresses a completed rebalance; (f) missing bars, missing bars_secondary for an INTERVAL sleeve, or a non-positive price produces an empty intent list; (g) no intent carries a price stop or profit target.
