# R19_ETF_DRIFT1_C098 - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `R19_ETF_DRIFT1_C098`
- Canonical name: ETF leader with unchanged-share holding · 98% exposure
- Aliases: R19_ETF_DRIFT1_C098, ausar_pb85, ausar_r19_R19_ETF_DRIFT1_C098
- Type: market timing and rotation; Family: etf; Algorithm grade in ALL-SLEEVES accounting: FULL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "ETF leader with unchanged-share holding · 98% exposure" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "ETF leader with unchanged-share holding · 98% exposure" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; femto land-wt config params; md2 catalog entry/exit/strategy text; alias record sources: ausar_deployed, femto_land_wt, md2_ausar_map, md2_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start, 4,430 entries; plus file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,441 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Accounting gaps: none listed. Where the accounting graded PARTIAL, those gaps are gaps of the accounting's consulted sources only; the Test strategy card and code cited below are the fuller record used here, and any remaining gap is marked 'not in the record' in place.

## What this strategy is

ETF leader with unchanged-share holding · 98% exposure. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

## Full algorithm

Evaluation order in `desk3/aster_batch8.py` _etf(), as applied to ETF_SPECS['aster_etf_drift1_c098'] = policy 'DRIFT1', gross 0.98:

1. Timing: intents are emitted only inside the 09:35-09:40 America/New_York window. Aware clock stamps are converted to ET; naive stamps are read as ET (engine enhancement ENH-ETWIN8, on by default).
2. Monthly guard: when positions are held, no `rebalance_due` flag is set in extra, and every held position was entered in the current month, no intents are emitted.
3. Leader selection: basket = QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY. For each symbol with at least 127 daily bars and a positive close 127 bars back, score = close[-1] / close[-127] - 1 (the 126-session return). The leader is the best score; ties break alphabetically.
4. DRIFT1 weights: 100% of the target portfolio in the leader. DRIFT1 incumbent rule: if the leader is already held, its target is set to its existing share count unchanged, so no intent changes that holding.
5. Targets: whole shares, int(gross x equity x weight / price), where equity is account_value or net_value from extra when present, otherwise the slice capital (default $10,000), and price is the last daily close. A target price at or below zero emits nothing. Gross is applied as coded and never silently capped in the sleeve; for gross above 1 the dispatcher buying-power check governs execution.
6. Order of operations: sells first (held above target), then buys (target above held). Intents are market, day; entries are buy_to_open, reductions and full exits are sell_to_close.
7. Exits: no price stop and no price target. A holding above its new target is reduced; a holding with target zero is exited in full at the next monthly selection.

Accounting record for this canonical strategy (verbatim fields from ALL-SLEEVES):
- Entry (accounting): [R19_ETF_DRIFT1_C098] ausar variant: ETF leader with unchanged-share holding · 98% exposure
- Entry (accounting): [ausar_pb85] Ranks the configured ETF basket by its completed 126-session price return; equal scores use alphabetical ticker order. Allocates to the selected fund. If the same incumbent remains the winner and is still held, retain its existing share count instead of resizing it. Targets ETF holdings worth 98% of the paper account's net value, rounded down to whole shares.
- Entry (accounting): [ausar_r19_R19_ETF_DRIFT1_C098] Ranks the configured ETF basket by its completed 126-session price return; equal scores use alphabetical ticker order. Allocates to the selected fund. If the same incumbent remains the winner and is still held, retain its existing share count instead of resizing it. Targets ETF holdings worth 98% of the paper account's net value, rounded down to whole shares.
- Exit (accounting): [ausar_pb85] Reduce or replace holdings when the next monthly selection changes their target. This strategy has no price-based stop or profit target.
- Exit (accounting): [ausar_r19_R19_ETF_DRIFT1_C098] Reduce or replace holdings when the next monthly selection changes their target. This strategy has no price-based stop or profit target.
- Filters/data (accounting): [ausar_pb85] data: Completed historical ETF bars for signals; separately labeled IEX quotes for execution. The two-source versions compare complete Alpaca and Yahoo histories without joining them.
- Filters/data (accounting): [ausar_r19_R19_ETF_DRIFT1_C098] data: posted r19 data adapters
- Parameters (accounting): {'R19_ETF_DRIFT1_C098': {'symbols': ['QQQ', 'SPY', 'SMH', 'XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY']}}

## Files in this repo

- This recreation doc: `docs/R19_ETF_DRIFT1_C098-RECREATE.md`
- Strategy card (family): `strategies/ausar/r19-etf.md`
- Code in Test: `sleeves/aster_etf_drift1_c098.py`, `adapters3/aster_etf_drift1_c098.py`, `integration/aster_etf_drift1_c098_adapter.py`, shared engine `desk3/aster_batch8.py`
- Existing per-sleeve doc in Test: `docs/ASTER_ETF_DRIFT1_C098-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family parity code in Test: `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py`, `packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py`
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

- Universe: QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY. Timeframe: daily bars, monthly rebalance.
- Module: `adapters3.aster_etf_drift1_c098`; cadence_s 300; session 'rth'.
- Slice: capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}.
- Inputs declared in config: bars, positions, quotes. Parked: false.
- Engine spec: policy DRIFT1, gross 0.98.

Accounting parameters: {'R19_ETF_DRIFT1_C098': {'symbols': ['QQQ', 'SPY', 'SMH', 'XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY']}}

## Data inputs

Declared inputs: bars, positions, quotes (engine INPUTS_ETF). Producers named in the engine: bars (freshness_sla_s 900), broker_readback (900, outputs positions), quotes (60, outputs quotes).

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
