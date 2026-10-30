# R19_ETF_SPY_MONTHLY_C098 - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `R19_ETF_SPY_MONTHLY_C098`
- Canonical name: S&P 500 ETF monthly rebalance · 98% exposure
- Aliases: R19_ETF_SPY_MONTHLY_C098, ausar_pb107, ausar_r19_R19_ETF_SPY_MONTHLY_C098
- Type: buy and hold; Family: etf; Algorithm grade in ALL-SLEEVES accounting: FULL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "S&P 500 ETF monthly rebalance · 98% exposure" (also `docs/ALL-SLEEVES.md`); local census copy at research_notes/sleeve-census-20261029/accounting.json. doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "S&P 500 ETF monthly rebalance · 98% exposure" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; femto land-wt config params; md2 catalog entry/exit/strategy text; alias record sources: ausar_deployed, femto_land_wt, md2_ausar_map, md2_catalog
- Existing Test family doc: `strategies/ausar/r19-etf.md` (R19 ETF books card). A separate recreation package exists for the same code under the v3 sleeve id: `docs/ASTER_ETF_SPY_MONTHLY_C098-RECREATE.md`.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus file reads of the sleeve wrappers, desk3/aster_etf.py, desk3/aster_etf_b9.py, desk3/aster_batch11.py, config/sleeves.json, strategies/ausar/r19-etf.md and the existing docs/ASTER_ETF_*-RECREATE.md packages for the same code); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no r19_etf or aster_etf path); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no r19_etf or aster_etf path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no r19_etf or aster_etf path). Code was found in Test, so nothing was vendored.
- Accounting algorithm record (verbatim fields): entry: ['[R19_ETF_SPY_MONTHLY_C098] ausar variant: S&P 500 ETF monthly rebalance · 98% exposure', "[ausar_pb107] Uses a fixed portfolio: 100% SPY. It does not rank or switch between competing funds. Targets ETF holdings worth 98% of the paper account's net value, rounded down to whole shares.", "[ausar_r19_R19_ETF_SPY_MONTHLY_C098] Uses a fixed portfolio: 100% SPY. It does not rank or switch between competing funds. Targets ETF holdings worth 98% of the paper account's net value, rounded down to whole shares."]; exit: ['[ausar_pb107] At each monthly rebalance, sell only holdings above the new fixed-portfolio target before buying any shortfall.', '[ausar_r19_R19_ETF_SPY_MONTHLY_C098] At each monthly rebalance, sell only holdings above the new fixed-portfolio target before buying any shortfall.']; filters: ['[ausar_pb107] data: Verified ETF identities and separately labeled IEX execution quotes. Monthly versions also use the prior signal-session closes to calculate share targets.', '[ausar_r19_R19_ETF_SPY_MONTHLY_C098] data: posted r19 data adapters']; parameters: {'R19_ETF_SPY_MONTHLY_C098': {'symbols': ['SPY']}}; gaps: []

## What this strategy is

S&P 500 ETF monthly rebalance · 98% exposure. A fixed-portfolio / R19 ETF book: Classification 2026-10-30: buy and hold (config evidence): accounting.json algorithm text for ausar_pb107 read: fixed portfolio of 100% SPY, explicitly does not rank or switch between funds, monthly rebalance only restores the fixed target at 98% exposure; none of the 12 types names a passive fixed holding and this slice holds 3 such fixed-portfolio books

In the v3 desk in Test it runs as sleeve `aster_etf_spy_monthly_c098`: a thin wrapper that sets SLEEVE_ID to "aster_etf_spy_monthly_c098" and delegates evaluate(view, ctx) to desk3/aster_etf.py + desk3/aster_batch11.py. Its own spec: Registered additively by desk3/aster_batch11.py into desk3/aster_etf.py SPECS: policy SPY_MONTHLY, freq MONTHLY, gross 0.98, weights {"SPY": 1.0}.

## Full algorithm

Sleeve-specific rules: MONTHLY guard: if positions exist and extra["rebalance_due"] is not set, emit nothing when every holding's entry month equals the session month; a flat book or a new month proceeds.

Evaluation order in desk3/aster_etf.py evaluate(sleeve_id, view, ctx):
1. Time gate: now is read from view["now"], ctx["now"], or ctx["session"]. Aware timestamps are converted to America/New_York (ENH-ETWIN, default ON via extra["aster_etf_enh"]["et_window"]); naive timestamps are read as ET. Emit nothing outside 09:35-09:40 ET, except that a MONTHLY sleeve with a due rebalance may use the same-session catch-up window 09:40-15:55 ET (ENH-B5-CATCHUP, default ON via extra["aster_etf_enh"]["catchup"]). If now cannot be parsed, emit nothing.
2. Equity basis: equity = extra["account_value"] or extra["net_value"] or slice capital_usd or 10000.0.
3. Positions: view["positions"] with non-zero qty, keyed by symbol.
4. Frequency guard for this sleeve (see sleeve-specific rules).
5. Target weights for this sleeve (see sleeve-specific rules). For a target leg, price is the last close of its bars ("<symbol>|1Day", "<symbol>|1D", or bare symbol key). If any target price is <= 0, refuse the whole rebalance and emit nothing.
6. Target shares: int(gross x equity x weight / price), floored to whole shares.
7. Sells first: for each held symbol in sorted order, if held > target (target 0 for non-target symbols), emit a sell intent for held minus target; kind is exit if target is 0 else rebalance, side sell, position_intent sell_to_close, order_type market, time_in_force day, price_hint = last close or position average price.
8. Buys: for each target symbol in sorted order, if target > held, emit a buy intent for target minus held (kind entry, side buy, position_intent buy_to_open, order_type market, time_in_force day, price_hint = last close). If the catch-up path served, each intent reason is suffixed with the catch-up experiment id and an enhance_exp record is attached.
No price stop and no price target exist in this engine. Source-book cost_bps 15 is accounting in the source book, not an order field (engine docstring).

Exit rules are the sell and rebalance rules above. There is no separate stop, target, trailing, or time-based exit in the engine, beyond the frequency guards stated for this sleeve.

## Files in this repo

- Sleeve wrapper: `sleeves/aster_etf_spy_monthly_c098.py` (in Test)
- Adapter: `adapters3/aster_etf_spy_monthly_c098.py` (in Test); repo mirror at `integration/aster_etf_spy_monthly_c098_adapter.py`
- Engine: `desk3/aster_etf.py` (in Test); registration module: `desk3/aster_batch11.py` (in Test)
- Config: `config/sleeves.json` (also `engines/config/sleeves.json`), row id `aster_etf_spy_monthly_c098`
- Family doc: `strategies/ausar/r19-etf.md` (in Test)
- Family code also in Test: `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py` and `packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py`

## Configuration

- Config row: id `aster_etf_spy_monthly_c098`, module `adapters3.aster_etf_spy_monthly_c098`, cadence_s 300, session rth, slice capital_usd 10000.0 / cash_usd 10000.0, bp_buffer_frac 0.02, flat_by_close false, flatten_time_et null, parked false, inputs ["bars", "positions", "quotes"].
- params {} in config/sleeves.json; the SPY spec is registered by desk3/aster_batch11.py (ETF_SPECS) into the batch-10 engine SPECS at import.
- Gross exposure for this variant: 0.98 (C100 = 1.0, C098 = 0.98, M150 = 1.5 in the id suffixes).
- Target symbols (accounting parameters): {'R19_ETF_SPY_MONTHLY_C098': {'symbols': ['SPY']}}

## Data inputs

Bars: daily histories keyed "<symbol>|1Day", "<symbol>|1D", or bare symbol; target pricing uses the last close. Positions: held qty, symbol, average price, and entry_date or opened_at for the monthly guard. Quotes are a declared input (freshness 60 s) though target pricing in evaluate() uses bar closes. Producers declared in desk3/aster_etf.py: bars (freshness_sla_s 900), broker_readback (positions, 900), quotes (60). Accounting data record: [ausar_pb107] data: Verified ETF identities and separately labeled IEX execution quotes. Monthly versions also use the prior signal-session closes to calculate share targets.; [ausar_r19_R19_ETF_SPY_MONTHLY_C098] data: posted r19 data adapters

## Install and run

1. Clone dwj9ddyvf6-hub/Test and confirm the files listed in "Files in this repo" are present at the stated paths.
2. Confirm the config row for `aster_etf_spy_monthly_c098` in config/sleeves.json matches the Configuration section.
3. Wire the producers named in Data inputs so view contains the declared inputs at evaluation time.
4. Register the sleeve with the desk cycle so evaluate(view, ctx) is called on the 300 s cadence in the rth session; the engine itself enforces the 09:35-09:40 ET window (and, for MONTHLY sleeves in desk3/aster_etf.py, the same-session catch-up).
5. Run one evaluation on a flat book inside the window with the required daily bars and confirm the emitted intents match the Verification checks before enabling live dispatch.

## Verification

No per-sleeve test file for this v3 sleeve is present in the repo tree. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- Window check: an evaluation at 09:36 ET inside the window can emit; an evaluation at 09:41 ET emits nothing (for a MONTHLY sleeve in desk3/aster_etf.py, a due rebalance may instead emit in the 09:40-15:55 ET catch-up with the catch-up marker).
- Sizing check: desired shares equal floor(weight x 0.98 x equity-or-NAV / price) on the basis stated in the algorithm, whole shares only.
- Frequency check: holdings whose entry month equals the session month emit nothing; a flat book or a new month can emit.
- Missing-data check: empty bars or a non-positive target price produces an empty intent list, never a guessed trade.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
