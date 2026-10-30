# R19_ETF_INTERVAL1_C098 - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `R19_ETF_INTERVAL1_C098`
- Canonical name: ETF leader confirmed across two sources · 98% exposure
- Aliases: R19_ETF_INTERVAL1_C098, ausar_pb89, ausar_r19_R19_ETF_INTERVAL1_C098
- Type: market timing and rotation; Family: etf; Algorithm grade in ALL-SLEEVES accounting: FULL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "ETF leader confirmed across two sources · 98% exposure" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "ETF leader confirmed across two sources · 98% exposure" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; femto land-wt config params; md2 catalog entry/exit/strategy text; alias record sources: ausar_deployed, femto_land_wt, md2_ausar_map, md2_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start, 4,430 entries; plus file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,441 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Accounting gaps: none listed. Where the accounting graded PARTIAL, those gaps are gaps of the accounting's consulted sources only; the Test strategy card and code cited below are the fuller record used here, and any remaining gap is marked 'not in the record' in place.

## What this strategy is

ETF leader confirmed across two sources · 98% exposure. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

## Full algorithm

Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_etf_interval1_c098

## What it is
A monthly Aster R19 ETF rotation sleeve (batch 9). The local core at sleeves/aster_etf_interval1_c098.py is a thin wrapper: it sets SLEEVE_ID to "aster_etf_interval1_c098", takes INPUTS from inputs_for(SLEEVE_ID), and delegates evaluate(view, ctx) to desk3/aster_etf_b9.evaluate. That shared engine is already saved in this repo at desk3/aster_etf_b9.py, and the same wrapper is saved as the integration adapter at integration/aster_etf_interval1_c098_adapter.py (byte-identical to the local adapters3 file).

## What it trades
One or more symbols from the 14-symbol ETF universe (see Common engine), selected monthly by the policy below. This sleeve's policy is INTERVAL1, gross target 0.98, source_id R19_ETF_INTERVAL1_C098.

## Indicators and parameters
- Policy: INTERVAL1
- Gross target: 0.98 (so a gross of 1.5 targets USD 15,000 of exposure on the USD 10,000 slice; the dispatcher's buying-power check, not the sleeve, governs execution)
- Source id: R19_ETF_INTERVAL1_C098

## Entry rules
Selection (INTERVAL policies in desk3/aster_etf_b9.py):
- Primary scores come from the primary bars (ALPACA daily histories) and secondary scores from bars_secondary (YAHOO daily histories).
- The secondary eligible set must equal the primary eligible set and must include QQQ, or the sleeve refuses and emits nothing (the archive PROVIDER_ELIGIBILITY_DISAGREEMENT condition). If bars_secondary is empty, the sleeve emits nothing. Note: no v3 producer produces bars_secondary yet, so INTERVAL sleeves are UNFED by design in the live registry and emit nothing until that input exists. The code does not fake-feed it.
- For each symbol the provider interval is [min(primary score, secondary score), max(primary score, secondary score)]. A robust leader is a symbol whose interval low is strictly above every other symbol's interval high. If there is exactly one robust leader, it is selected. Otherwise the incumbent is selected if it is still possible (its interval high is at or above the highest interval low); otherwise QQQ is selected.

- Weights: see the sizing note for this policy below.
- Intents are emitted only inside the execution window and only when the monthly guard does not already show this month's signal completed.

## Exit and rebalance rules
Sell-then-settle, as in the Common engine. There is no intraday, price-based, stop, or target exit.

## Sizing
NAV basis for this sleeve (ENH-NAVBASE, in ENH_NAVBASE_IDS): NAV is the slice capital (capital_usd when the slice row carries it, else the cash figure, which in v3 is the capital proxy). Held value is part of that budget and is never added on top. Desired shares = floor(weight x gross x NAV / price). Weights: 100% to the selected symbol, except INTERVAL_CORE25, which is stated separately for that sleeve.

## Session, cadence, and data inputs
- Data inputs declared by the wrapper: bars, bars_secondary, positions. Primary bars are daily histories keyed as "<symbol>|1Day", "<symbol>|1D", or the bare symbol.
Common engine (desk3/aster_etf_b9.py, batch 9):
- Universe: QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY.
- Score: 126-session log return, log(close[-1] / close[-127]). Eligibility requires at least 252 sessions of history and all closes in the last 252 sessions positive. Ties break alphabetically.
- Execution window: 09:35-09:40 America/New_York, when a clock time is known. Aware timestamps are converted to ET, naive timestamps are read as ET, and a date-only or midnight stamp is ungated.
- Monthly guard: if every held position carries signal_month equal to the latest bar month, no rebalance is emitted.
- Incumbent: a position flagged incumbent/selected, otherwise the holding with the largest held value at last close.
- Sizing: desired shares = floor(weight x gross x NAV / price), whole shares, never capped inside the sleeve. Price is the last close, falling back to the position average price for a held symbol with no bars. If any needed price is at or below zero, the sleeve emits nothing.
- Exits: sell-then-settle. When any holding is above its desired shares, only sell intents are emitted on that evaluation (kind exit, sell_to_close, market, day). Buys follow on a later evaluation. There is no price stop and no price target; the designed exit is the next monthly selection reducing or replacing a holding.
- Session and cadence (config row): cadence 300 s, session rth, slice capital USD 10,000 and cash USD 10,000, bp_buffer_frac 0.02, flat_by_close false, parked false.

## Ambiguities
- The wrapper itself implements no strategy logic; every rule above is read from the shared engine desk3/aster_etf_b9.py and from this sleeve's config row and engine SPECS row. Where the engine and the config row disagree on inputs, both are stated above.

Accounting record for this canonical strategy (verbatim fields from ALL-SLEEVES):
- Entry (accounting): [R19_ETF_INTERVAL1_C098] ausar variant: ETF leader confirmed across two sources · 98% exposure
- Entry (accounting): [ausar_pb89] Calculates each ETF’s completed 126-session return separately from Alpaca and Yahoo. The two values form a range. A new leader is chosen only when its lower return exceeds every competitor’s higher return. When ranges overlap, retain the incumbent if it is still a possible winner; otherwise select QQQ. Allocates to the selected fund. Targets ETF holdings worth 98% of the paper account's net value,
- Entry (accounting): [ausar_r19_R19_ETF_INTERVAL1_C098] Calculates each ETF’s completed 126-session return separately from Alpaca and Yahoo. The two values form a range. A new leader is chosen only when its lower return exceeds every competitor’s higher return. When ranges overlap, retain the incumbent if it is still a possible winner; otherwise select QQQ. Allocates to the selected fund. Targets ETF holdings worth 98% of the paper account's net value,
- Exit (accounting): [ausar_pb89] Reduce or replace holdings when the next monthly selection changes their target. This strategy has no price-based stop or profit target.
- Exit (accounting): [ausar_r19_R19_ETF_INTERVAL1_C098] Reduce or replace holdings when the next monthly selection changes their target. This strategy has no price-based stop or profit target.
- Filters/data (accounting): [ausar_pb89] data: Completed historical ETF bars for signals; separately labeled IEX quotes for execution. The two-source versions compare complete Alpaca and Yahoo histories without joining them.
- Filters/data (accounting): [ausar_r19_R19_ETF_INTERVAL1_C098] data: posted r19 data adapters
- Parameters (accounting): {'R19_ETF_INTERVAL1_C098': {'symbols': ['QQQ', 'SPY', 'SMH', 'XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY']}}

## Files in this repo

- This recreation doc: `docs/R19_ETF_INTERVAL1_C098-RECREATE.md`
- Strategy card (family): `strategies/ausar/r19-etf.md`
- Code in Test: `sleeves/aster_etf_interval1_c098.py`, `adapters3/aster_etf_interval1_c098.py`, `integration/aster_etf_interval1_c098_adapter.py`, shared engine `desk3/aster_etf_b9.py`
- Existing per-sleeve doc in Test: `docs/ASTER_ETF_INTERVAL1_C098-ALGORITHM.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family parity code in Test: `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py`, `packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py`
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

Config row for this sleeve is in `config/sleeves.json` (also `engines/config/sleeves.json`): see the Common engine session/cadence note in the algorithm text above (cadence 300 s, session rth, slice capital USD 10,000, cash USD 10,000, bp_buffer_frac 0.02, flat_by_close false, parked false) and the engine SPECS row naming policy and gross in the algorithm text.

Accounting parameters: {'R19_ETF_INTERVAL1_C098': {'symbols': ['QQQ', 'SPY', 'SMH', 'XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY']}}

## Data inputs

Data inputs are as stated in the algorithm text above: bars, bars_secondary (INTERVAL only), positions, with primary bars daily histories keyed '<symbol>|1Day', '<symbol>|1D', or the bare symbol.

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
