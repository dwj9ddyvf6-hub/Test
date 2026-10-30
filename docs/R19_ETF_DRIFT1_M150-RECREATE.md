# R19_ETF_DRIFT1_M150 - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `R19_ETF_DRIFT1_M150`
- Canonical name: ETF leader with unchanged-share holding · 150% exposure
- Aliases: R19_ETF_DRIFT1_M150, ausar_pb86, ausar_r19_R19_ETF_DRIFT1_M150
- Type: market timing and rotation; Family: etf; Algorithm grade in ALL-SLEEVES accounting: FULL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "ETF leader with unchanged-share holding · 150% exposure" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "ETF leader with unchanged-share holding · 150% exposure" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; femto land-wt config params; md2 catalog entry/exit/strategy text; alias record sources: ausar_deployed, femto_land_wt, md2_ausar_map, md2_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start, 4,430 entries; plus file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,441 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Accounting gaps: none listed. Where the accounting graded PARTIAL, those gaps are gaps of the accounting's consulted sources only; the Test strategy card and code cited below are the fuller record used here, and any remaining gap is marked 'not in the record' in place.

## What this strategy is

ETF leader with unchanged-share holding · 150% exposure. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

## Full algorithm

Evaluation order in `desk3/aster_etf_b9.py` evaluate(), as applied to SPECS['aster_etf_drift1_m150'] = policy 'DRIFT1', gross 1.5, source_id 'R19_ETF_DRIFT1_M150':

1. Timing: when a clock time is known, intents are emitted only inside 09:35-09:40 America/New_York (aware stamps converted to ET; naive stamps read as ET; a date-only or midnight stamp is ungated in the code).
2. Scores: universe = QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY. A symbol is eligible only with at least 252 sessions of history (MIN_SESSIONS) and all positive closes in the last 252; score = log(close[-1] / close[-127]), the 126-session log return. No eligible score emits nothing.
3. Selection (DRIFT1, non-interval): the selected symbol is the highest score; ties break alphabetically.
4. Incumbent: the position flagged incumbent / selected if present, otherwise the held symbol with the largest held value at last close.
5. Monthly guard: if positions are held and every held position's signal_month equals the latest bar month, no intents are emitted.
6. DRIFT1 rule: if the selected symbol equals the incumbent and shares of it are held, return nothing at all: the incumbent's shares are retained unchanged.
7. Targets and NAV: NAV for this sleeve is the legacy basis, slice cash (default $10,000) plus held value at last close, because this sleeve id is not in the engine's ENH-NAVBASE set. Desired shares for the selected symbol = floor(1.0 x 1.5 x NAV / price); desired for every other held symbol = 0. A price at or below zero for a held or target symbol emits nothing. Gross is never capped in the sleeve; the dispatcher buying-power check governs the 1.5 gross target.
8. Sell-then-settle: if any holding is above its desired target, emit only the sell intents (full exits where desired is 0) on this evaluation and no buys; buys to reach the target are emitted on a later evaluation when no sells remain. Intents are market, day; entries buy_to_open, exits sell_to_close.
9. Exits: no price stop and no price target. The designed exit is the next monthly selection reducing or replacing a holding under the sell-then-settle rule.

Accounting record for this canonical strategy (verbatim fields from ALL-SLEEVES):
- Entry (accounting): [R19_ETF_DRIFT1_M150] ausar variant: ETF leader with unchanged-share holding · 150% exposure
- Entry (accounting): [ausar_pb86] Ranks the configured ETF basket by its completed 126-session price return; equal scores use alphabetical ticker order. Allocates to the selected fund. If the same incumbent remains the winner and is still held, retain its existing share count instead of resizing it. Targets ETF holdings worth 150% of the paper account's net value, rounded down to whole shares. The excess uses simulated borrowing.
- Entry (accounting): [ausar_r19_R19_ETF_DRIFT1_M150] Ranks the configured ETF basket by its completed 126-session price return; equal scores use alphabetical ticker order. Allocates to the selected fund. If the same incumbent remains the winner and is still held, retain its existing share count instead of resizing it. Targets ETF holdings worth 150% of the paper account's net value, rounded down to whole shares. The excess uses simulated borrowing.
- Exit (accounting): [ausar_pb86] Reduce or replace holdings when the next monthly selection changes their target. This strategy has no price-based stop or profit target.
- Exit (accounting): [ausar_r19_R19_ETF_DRIFT1_M150] Reduce or replace holdings when the next monthly selection changes their target. This strategy has no price-based stop or profit target.
- Filters/data (accounting): [ausar_pb86] data: Completed historical ETF bars for signals; separately labeled IEX quotes for execution. The two-source versions compare complete Alpaca and Yahoo histories without joining them.
- Filters/data (accounting): [ausar_r19_R19_ETF_DRIFT1_M150] data: posted r19 data adapters
- Parameters (accounting): {'R19_ETF_DRIFT1_M150': {'symbols': ['QQQ', 'SPY', 'SMH', 'XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY']}}

## Files in this repo

- This recreation doc: `docs/R19_ETF_DRIFT1_M150-RECREATE.md`
- Strategy card (family): `strategies/ausar/r19-etf.md`
- Code in Test: `sleeves/aster_etf_drift1_m150.py`, `adapters3/aster_etf_drift1_m150.py`, `integration/aster_etf_drift1_m150_adapter.py`, shared engine `desk3/aster_etf_b9.py`
- Existing per-sleeve doc in Test: `docs/ASTER_ETF_DRIFT1_M150-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family parity code in Test: `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py`, `packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py`
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

- Universe: QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY. Timeframe: daily bars, monthly rebalance; eligibility requires 252 sessions.
- Module: `adapters3.aster_etf_drift1_m150`; cadence_s 300; session 'rth'.
- Slice: capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null.
- Config params: policy 'DRIFT1', gross_target 1.5, source_id 'R19_ETF_DRIFT1_M150'. Inputs declared in config: bars, positions. Parked: false.
- Engine spec: policy DRIFT1, gross 1.5, source_id R19_ETF_DRIFT1_M150.

Accounting parameters: {'R19_ETF_DRIFT1_M150': {'symbols': ['QQQ', 'SPY', 'SMH', 'XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY']}}

## Data inputs

Declared inputs for this sleeve: bars, positions (engine inputs_for for a non-INTERVAL policy). Producers named in the engine: bars (freshness_sla_s 900), broker_readback (900, outputs positions). No quotes input is declared for this b9 sleeve in its config row.

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
