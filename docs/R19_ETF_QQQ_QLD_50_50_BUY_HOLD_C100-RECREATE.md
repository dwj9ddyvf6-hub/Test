# R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100 - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100`
- Canonical name: QQQ and QLD equal-weight buy and hold · 100% exposure
- Aliases: R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100, ausar_pb102, ausar_r19_R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100
- Type: buy and hold; Family: etf; Algorithm grade in ALL-SLEEVES accounting: FULL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "QQQ and QLD equal-weight buy and hold · 100% exposure" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "QQQ and QLD equal-weight buy and hold · 100% exposure" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; femto land-wt config params; md2 catalog entry/exit/strategy text; alias record sources: ausar_deployed, femto_land_wt, md2_ausar_map, md2_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start, 4,430 entries; plus file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,441 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Accounting gaps: none listed. Where the accounting graded PARTIAL, those gaps are gaps of the accounting's consulted sources only; the Test strategy card and code cited below are the fuller record used here, and any remaining gap is marked 'not in the record' in place.

## What this strategy is

QQQ and QLD equal-weight buy and hold · 100% exposure. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

## Full algorithm

This is a BUY_HOLD sleeve: it acts only on initial allocation (flat book). Buy-and-hold sleeves never rebalance and never exit by design. Evaluation order in desk3/aster_etf.py evaluate(): (1) read this sleeve's SPECS entry; (2) check the time gate: entry only 09:35-09:40 ET (aware timestamps are converted to America/New_York; naive stamps are read as ET); (3) if the book already holds the target, emit nothing; (4) otherwise emit buys for the target weights.
- Policy: QQQ_QLD_50_50_BUY_HOLD. Frequency: BUY_HOLD. Gross: 1.0. Weights: {"QQQ": 0.5, "QLD": 0.5}.
- Target sizing: whole shares, floor(weight x gross x equity / price) per symbol, where equity is the sleeve slice; sells are emitted before buys.
- No price stop and no profit target. The 15 bps per side figure (cost_bps 15) is source-book accounting, not an order field.
- Exit rules: none: buy-and-hold sleeves never sell by design.

Accounting record for this canonical strategy (verbatim fields from ALL-SLEEVES):
- Entry (accounting): [R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100] ausar variant: QQQ and QLD equal-weight buy and hold · 100% exposure
- Entry (accounting): [ausar_pb102] Uses a fixed portfolio: 50% QQQ and 50% QLD. It does not rank or switch between competing funds. Targets ETF holdings worth 100% of the paper account's net value, rounded down to whole shares. QLD targets twice the Nasdaq-100 daily return; its multi-day return compounds rather than staying exactly twice the index return.
- Entry (accounting): [ausar_r19_R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100] Uses a fixed portfolio: 50% QQQ and 50% QLD. It does not rank or switch between competing funds. Targets ETF holdings worth 100% of the paper account's net value, rounded down to whole shares. QLD targets twice the Nasdaq-100 daily return; its multi-day return compounds rather than staying exactly twice the index return.
- Exit (accounting): [ausar_pb102] Holds fixed share quantities after the initial allocation; this strategy has no scheduled profit target or calendar exit.
- Exit (accounting): [ausar_r19_R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100] Holds fixed share quantities after the initial allocation; this strategy has no scheduled profit target or calendar exit.
- Filters/data (accounting): [ausar_pb102] data: Verified ETF identities, the account cash and holdings, and separately labeled IEX execution quotes for the initial allocation.
- Filters/data (accounting): [ausar_r19_R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100] data: posted r19 data adapters
- Parameters (accounting): {'R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100': {'symbols': ['QLD', 'QQQ']}}

## Files in this repo

- This recreation doc: `docs/R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100-RECREATE.md`
- Strategy card (family): `strategies/ausar/r19-etf.md`
- Code in Test: `sleeves/aster_etf_qqq_qld_buy_hold.py`, `adapters3/aster_etf_qqq_qld_buy_hold.py`, `integration/aster_etf_qqq_qld_buy_hold_adapter.py`, shared engine `desk3/aster_etf.py`
- Existing per-sleeve doc in Test: `docs/ASTER_ETF_QQQ_QLD_BUY_HOLD-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family parity code in Test: `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py`, `packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py`
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

- Universe / weights: {"QQQ": 0.5, "QLD": 0.5} (policy QQQ_QLD_50_50_BUY_HOLD).
- Timeframe: 1d bars; rebalance frequency BUY_HOLD.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 (desk config/sleeves.json row); target shares = floor(weight x gross x equity / price), gross 1.0.
- Cadence: cadence_s 300. Session: rth. bp_buffer_frac 0.02. flat_by_close false; flatten_time_et null. params: {}.
- Inputs declared in config: bars, positions, quotes.
- Parked: false (parked flag in the desk config row).

Accounting parameters: {'R19_ETF_QQQ_QLD_50_50_BUY_HOLD_C100': {'symbols': ['QLD', 'QQQ']}}

## Data inputs

Producers declared by desk3/aster_etf.py PRODUCERS, consumed through the runtime view:
- bars (producer name: bars): daily bars keyed as `<SYM>|1Day`, `<SYM>|1D`, or `<SYM>`; freshness SLA 900 s. Absent bars means no intents (unfed upstream).
- positions (producer name: broker_readback): current holdings for this sleeve; freshness SLA 900 s.
- quotes (producer name: quotes): freshness SLA 60 s.

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
