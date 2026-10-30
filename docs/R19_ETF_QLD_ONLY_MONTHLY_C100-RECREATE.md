# R19_ETF_QLD_ONLY_MONTHLY_C100 - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `R19_ETF_QLD_ONLY_MONTHLY_C100`
- Canonical name: QLD monthly rebalance · 100% exposure
- Aliases: R19_ETF_QLD_ONLY_MONTHLY_C100, ausar_pb98, ausar_r19_R19_ETF_QLD_ONLY_MONTHLY_C100
- Type: buy and hold; Family: etf; Algorithm grade in ALL-SLEEVES accounting: FULL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "QLD monthly rebalance · 100% exposure" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "QLD monthly rebalance · 100% exposure" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; femto land-wt config params; md2 catalog entry/exit/strategy text; alias record sources: ausar_deployed, femto_land_wt, md2_ausar_map, md2_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start, 4,430 entries; plus file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,441 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Accounting gaps: none listed. Where the accounting graded PARTIAL, those gaps are gaps of the accounting's consulted sources only; the Test strategy card and code cited below are the fuller record used here, and any remaining gap is marked 'not in the record' in place.

## What this strategy is

QLD monthly rebalance · 100% exposure. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

## Full algorithm

Config params are empty for this sleeve in config/sleeves.json; its policy, frequency, gross and weights come only from desk3/aster_etf.py SPECS.

Sleeve-specific rules: Frequency guard: MONTHLY. If positions exist and extra['rebalance_due'] is not set, compare holdings' entry months with the session month; if they equal the session month only, emit nothing. Flat is an initial allocation and proceeds. Weights: QLD 100% every rebalance.

Equity basis: see step 2 of the common evaluation order below; gross is applied to that equity, not to cash plus held value separately.

Evaluation order in desk3/aster_etf.py evaluate():
1. Time gate: now is read from view['now'], ctx['now'], or ctx['session']. Aware timestamps are converted to America/New_York (ENH-ETWIN, default ON via extra['aster_etf_enh']['et_window']); naive timestamps are read as ET. Emit nothing outside 09:35-09:40 ET, except that a MONTHLY sleeve with a due rebalance may use the same-session catch-up window 09:40-15:55 ET (ENH-B5-CATCHUP, default ON via extra['aster_etf_enh']['catchup']). If now cannot be parsed, emit nothing.
2. Equity basis: equity = extra['account_value'] or extra['net_value'] or slice capital_usd or 10000.0. Note the config slice is 10000.0 capital and 10000.0 cash.
3. Positions: view['positions'] with non-zero qty, keyed by symbol.
4. Frequency guard for this sleeve (see sleeve-specific rules below).
5. Target weights for this sleeve (see sleeve-specific rules below). For a target leg, price is the last close of its bars ('<symbol>|1Day', '<symbol>|1D', or bare symbol key). If any target price is <= 0, refuse the whole rebalance and emit nothing.
6. Target shares: int(gross x equity x weight / price), floored to whole shares.
7. Sells first: for each held symbol in sorted order, if held > target (target 0 for non-target symbols), emit a sell intent for held minus target; kind is exit if target is 0 else rebalance, side sell, position_intent sell_to_close, order_type market, time_in_force day, price_hint = last close or position average price.
8. Buys: for each target symbol in sorted order, if target > held, emit a buy intent for target minus held (kind entry, side buy, position_intent buy_to_open, order_type market, time_in_force day, price_hint = last close). If the catch-up path served, each intent reason is suffixed with the catch-up experiment id and an enhance_exp record is attached.
No price stop and no price target exist in this engine. Source-book cost_bps 15 is accounting in the source book, not an order field (engine docstring).

Exit rules are the sell and rebalance rules in the steps above. There is no separate stop, target, trailing, or time-based exit in the engine, except the BUY_HOLD / monthly guards stated for this sleeve where applicable.

Accounting record for this canonical strategy (verbatim fields from ALL-SLEEVES):
- Entry (accounting): [R19_ETF_QLD_ONLY_MONTHLY_C100] ausar variant: QLD monthly rebalance · 100% exposure
- Entry (accounting): [ausar_pb98] Uses a fixed portfolio: 100% QLD. It does not rank or switch between competing funds. Targets ETF holdings worth 100% of the paper account's net value, rounded down to whole shares. QLD targets twice the Nasdaq-100 daily return; its multi-day return compounds rather than staying exactly twice the index return.
- Entry (accounting): [ausar_r19_R19_ETF_QLD_ONLY_MONTHLY_C100] Uses a fixed portfolio: 100% QLD. It does not rank or switch between competing funds. Targets ETF holdings worth 100% of the paper account's net value, rounded down to whole shares. QLD targets twice the Nasdaq-100 daily return; its multi-day return compounds rather than staying exactly twice the index return.
- Exit (accounting): [ausar_pb98] At each monthly rebalance, sell only holdings above the new fixed-portfolio target before buying any shortfall.
- Exit (accounting): [ausar_r19_R19_ETF_QLD_ONLY_MONTHLY_C100] At each monthly rebalance, sell only holdings above the new fixed-portfolio target before buying any shortfall.
- Filters/data (accounting): [ausar_pb98] data: Verified ETF identities and separately labeled IEX execution quotes. Monthly versions also use the prior signal-session closes to calculate share targets.
- Filters/data (accounting): [ausar_r19_R19_ETF_QLD_ONLY_MONTHLY_C100] data: posted r19 data adapters
- Parameters (accounting): {'R19_ETF_QLD_ONLY_MONTHLY_C100': {'symbols': ['QLD']}}

## Files in this repo

- This recreation doc: `docs/R19_ETF_QLD_ONLY_MONTHLY_C100-RECREATE.md`
- Strategy card (family): `strategies/ausar/r19-etf.md`
- Code in Test: `sleeves/aster_etf_qld_monthly.py`, `adapters3/aster_etf_qld_monthly.py`, `integration/aster_etf_qld_monthly_adapter.py`, shared engine `desk3/aster_etf.py`
- Existing per-sleeve doc in Test: `docs/ASTER_ETF_QLD_MONTHLY-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family parity code in Test: `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_etf.py`, `packages/claude/master-desk-parity-tools/tools/parity/r19_etf.py`
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

- Universe: QLD only as a target; the b10 engine basket constant is still the 14-symbol list, but this sleeve's fixed weights use only QLD
- Timeframe: 1d bars (daily), monthly selection / rebalance for this sleeve (frequency MONTHLY)
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0, gross_target 1.0, bp_buffer_frac 0.02
- Cadence: cadence_s 300, session rth
- Parked: false (parked false in config/sleeves.json)
- flat_by_close: false, flatten_time_et: null
- Module: adapters3.aster_etf_qld_monthly
- Inputs (config row): bars, positions, quotes

Accounting parameters: {'R19_ETF_QLD_ONLY_MONTHLY_C100': {'symbols': ['QLD']}}

## Data inputs

Bars: daily histories keyed '<symbol>|1Day', '<symbol>|1D', or bare symbol; the engine uses the last close and, for LEADER1, close[-127]. Positions: held qty, symbol, average price, and entry_date or opened_at for the monthly guard. Quotes are a declared input (freshness 60 s) though target pricing in evaluate() uses bar closes.
Producers: bars producer (outputs bars, freshness_sla_s 900), broker_readback producer (outputs positions, freshness_sla_s 900), and quotes producer (outputs quotes, freshness_sla_s 60), as declared in desk3/aster_etf.py PRODUCERS. The evaluate() logic itself reads bars and positions (and ctx/view extras); quotes are a declared input of the sleeve.
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
