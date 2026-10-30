# R19_ETF_INTERVAL_DRIFT1_C098 - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `R19_ETF_INTERVAL_DRIFT1_C098`
- Canonical name: Two-source ETF leader with unchanged-share holding · 98% exposure
- Aliases: R19_ETF_INTERVAL_DRIFT1_C098, ausar_pb93, ausar_r19_R19_ETF_INTERVAL_DRIFT1_C098
- Type: market timing and rotation; Family: etf; Algorithm grade in ALL-SLEEVES accounting: FULL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Two-source ETF leader with unchanged-share holding · 98% exposure" (also `docs/ALL-SLEEVES.md`); local census copy at research_notes/sleeve-census-20261029/accounting.json. doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Two-source ETF leader with unchanged-share holding · 98% exposure" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; femto land-wt config params; md2 catalog entry/exit/strategy text; alias record sources: ausar_deployed, femto_land_wt, md2_ausar_map, md2_catalog
- Existing Test family doc: `strategies/ausar/r19-etf.md` (R19 ETF books card). A separate recreation package exists for the same code under the v3 sleeve id: `docs/ASTER_ETF_INTERVAL_DRIFT1_C098-RECREATE.md`.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus file reads of the sleeve wrappers, desk3/aster_etf.py, desk3/aster_etf_b9.py, desk3/aster_batch11.py, config/sleeves.json, strategies/ausar/r19-etf.md and the existing docs/ASTER_ETF_*-RECREATE.md packages for the same code); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no r19_etf or aster_etf path); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no r19_etf or aster_etf path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no r19_etf or aster_etf path). Code was found in Test, so nothing was vendored.
- Accounting algorithm record (verbatim fields): entry: ['[R19_ETF_INTERVAL_DRIFT1_C098] ausar variant: Two-source ETF leader with unchanged-share holding · 98% exposure', '[ausar_pb93] Calculates each ETF’s completed 126-session return separately from Alpaca and Yahoo. The two values form a range. A new leader is chosen only when its lower return exceeds every competitor’s higher return. When ranges overlap, retain the incumbent if it is still a possible winner; otherwise select QQQ. Allocates to the selected fund. If the same incumbent remains the winner and is still held, reta', '[ausar_r19_R19_ETF_INTERVAL_DRIFT1_C098] Calculates each ETF’s completed 126-session return separately from Alpaca and Yahoo. The two values form a range. A new leader is chosen only when its lower return exceeds every competitor’s higher return. When ranges overlap, retain the incumbent if it is still a possible winner; otherwise select QQQ. Allocates to the selected fund. If the same incumbent remains the winner and is still held, reta']; exit: ['[ausar_pb93] Reduce or replace holdings when the next monthly selection changes their target. This strategy has no price-based stop or profit target.', '[ausar_r19_R19_ETF_INTERVAL_DRIFT1_C098] Reduce or replace holdings when the next monthly selection changes their target. This strategy has no price-based stop or profit target.']; filters: ['[ausar_pb93] data: Completed historical ETF bars for signals; separately labeled IEX quotes for execution. The two-source versions compare complete Alpaca and Yahoo histories without joining them.', '[ausar_r19_R19_ETF_INTERVAL_DRIFT1_C098] data: posted r19 data adapters']; parameters: {'R19_ETF_INTERVAL_DRIFT1_C098': {'symbols': ['QQQ', 'SPY', 'SMH', 'XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY']}}; gaps: []

## What this strategy is

Two-source ETF leader with unchanged-share holding · 98% exposure. A fixed-portfolio / R19 ETF book: Classification 2026-10-30: market timing and rotation (code evidence): muse-desk-v3 desk3/aster_etf_b9.py read: INTERVAL_DRIFT1 policy computes each ETF's 126-session return separately from Alpaca and Yahoo and rotates monthly into the robust leader at 98% exposure, retaining the incumbent when return ranges overlap

In the v3 desk in Test it runs as sleeve `aster_etf_interval_drift1_c098`: a thin wrapper that sets SLEEVE_ID to "aster_etf_interval_drift1_c098" and delegates evaluate(view, ctx) to desk3/aster_etf_b9.py. Its own spec: SPECS["aster_etf_interval_drift1_c098"] = policy INTERVAL_DRIFT1, gross 0.98, source_id "R19_ETF_INTERVAL_DRIFT1_C098".

## Full algorithm

Sleeve-specific rules: Monthly guard plus the INTERVAL_DRIFT1 drift rule and sell-then-settle, all in the evaluation order below. This sleeve is UNFED in v3 until a bars_secondary producer exists; that is a recorded state, not a defect of this package.

Evaluation order in desk3/aster_etf_b9.py evaluate(sleeve_id, view, ctx):
1. Window: intents only inside 09:35-09:40 America/New_York when a clock time is known (aware stamps converted to ET; naive stamps read as ET; date-only or midnight stamps are ungated). Outside the window, emit nothing.
2. Primary scores: from view["bars"] (Alpaca daily histories) for the 14-fund universe QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY. A fund needs >= 252 sessions (MIN_SESSIONS) and all-positive closes in the last 252; score = log(close[-1] / close[-127]) (126-session log return).
3. Secondary scores: because the policy starts with INTERVAL, scores are recomputed from view["bars_secondary"] (Yahoo histories). If bars_secondary is empty, emit nothing. NOTE: no v3 producer produces bars_secondary yet, so INTERVAL sleeves land visibly UNFED in the registry and are never fake-fed (engine header).
4. Selection (select(), archive r19_etf.select in substance): if the secondary eligible set differs from the primary set, or QQQ is not in the primary set, the sleeve refuses (PROVIDER_ELIGIBILITY_DISAGREEMENT) and emits nothing. Bounds per fund are [min(primary, secondary), max(primary, secondary)]. A fund is robust only if its interval low beats every other fund's interval high; if exactly one robust fund exists it is selected. Otherwise the incumbent is kept if it is still possible (its interval high >= the highest interval low); otherwise QQQ is selected. The incumbent is the position flagged incumbent/selected, else the largest held position by value.
5. Monthly guard: signal_month is the latest bar month; if every position is already stamped with that signal_month, emit nothing.
6. Drift rule (INTERVAL_DRIFT1): if the selected fund equals the incumbent and shares of it are held, emit nothing (unchanged-share holding).
7. Weights: {selected: 1.0}. NAV basis for this sleeve: legacy basis in the engine, nav = slice cash_usd (default 10000.0) + held value at last close (INTERVAL_DRIFT1 sleeves are not in the ENH-NAVBASE treated set; the engine header records that their drift-retain and sell-then-settle rules pre-empt every NAV-sensitive emission). Desired shares = floor(weight x gross x nav / price) for every held or target symbol; if any needed price is <= 0, emit nothing.
8. Sell-then-settle: if any holding is above its desired shares, emit ONLY sell intents for the excess (kind exit, side sell, position_intent sell_to_close, order_type market, time_in_force day, price_hint = last close) and return; buys follow on a later evaluation. Otherwise emit buy intents for shortfalls (kind entry, side buy, position_intent buy_to_open).
No price stop and no price target: the designed exit is the next monthly selection reducing or replacing a holding.

Exit rules are the sell and rebalance rules above. There is no separate stop, target, trailing, or time-based exit in the engine, beyond the frequency guards stated for this sleeve.

## Files in this repo

- Sleeve wrapper: `sleeves/aster_etf_interval_drift1_c098.py` (in Test)
- Adapter: `adapters3/aster_etf_interval_drift1_c098.py` (in Test); repo mirror at `integration/aster_etf_interval_drift1_c098_adapter.py`
- Engine: `desk3/aster_etf_b9.py` (in Test)
- Config: `config/sleeves.json` (also `engines/config/sleeves.json`), row id `aster_etf_interval_drift1_c098`
- Family doc: `strategies/ausar/r19-etf.md` (in Test)
- Family code also in Test: `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py` and `packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py`

## Configuration

- Config row: id `aster_etf_interval_drift1_c098`, module `adapters3.aster_etf_interval_drift1_c098`, cadence_s 300, session rth, slice capital_usd 10000.0 / cash_usd 10000.0, bp_buffer_frac 0.02, flat_by_close false, flatten_time_et null, parked false, inputs ["bars", "bars_secondary", "positions"].
- params {"policy": "INTERVAL_DRIFT1", "gross_target": 0.98, "source_id": "R19_ETF_INTERVAL_DRIFT1_C098"} in config/sleeves.json; the same policy/gross/source_id are in desk3/aster_etf_b9.py SPECS.
- Gross exposure for this variant: 0.98 (C100 = 1.0, C098 = 0.98, M150 = 1.5 in the id suffixes).
- Target symbols (accounting parameters): {'R19_ETF_INTERVAL_DRIFT1_C098': {'symbols': ['QQQ', 'SPY', 'SMH', 'XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY']}}

## Data inputs

Bars: primary daily histories (Alpaca) keyed "<symbol>|1Day", "<symbol>|1D", or bare symbol, plus bars_secondary daily histories (Yahoo) for the INTERVAL selection; the engine uses the last 252 closes and close[-127]. Positions: held qty, symbol, average price, and signal_month / incumbent markers. Producers declared in desk3/aster_etf_b9.py: bars (freshness_sla_s 900) and broker_readback (positions, 900). bars_secondary has NO v3 producer yet, so this sleeve is UNFED by design.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and confirm the files listed in "Files in this repo" are present at the stated paths.
2. Confirm the config row for `aster_etf_interval_drift1_c098` in config/sleeves.json matches the Configuration section.
3. Wire the producers named in Data inputs so view contains the declared inputs at evaluation time; for this INTERVAL sleeve, a bars_secondary (Yahoo) producer must be supplied by the host desk, because v3 has none yet.
4. Register the sleeve with the desk cycle so evaluate(view, ctx) is called on the 300 s cadence in the rth session; the engine itself enforces the 09:35-09:40 ET window.
5. Run one evaluation on a flat book inside the window with the required daily bars and confirm the emitted intents match the Verification checks before enabling live dispatch.

## Verification

No per-sleeve test file for this v3 sleeve is present in the repo tree. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- Window check: an evaluation at 09:36 ET inside the window can emit; an evaluation at 09:41 ET emits nothing.
- Sizing check: desired shares equal floor(weight x 0.98 x equity-or-NAV / price) on the basis stated in the algorithm, whole shares only.
- Interval check: with two-source fixture scores where one fund's low beats every other fund's high, that fund is selected; with overlapping ranges the incumbent is kept if still possible, else QQQ; a primary/secondary eligible-set mismatch emits nothing.
- Drift check: when the selected fund equals the held incumbent, no intents are emitted.
- Sell-then-settle check: a holding above target produces only sell intents on that evaluation.
- Unfed check: empty bars_secondary produces an empty intent list, never a guessed trade.
- Missing-data check: empty bars or a non-positive target price produces an empty intent list, never a guessed trade.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
