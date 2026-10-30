# capitulation_options: Recreation package

Provenance: Source row in strategies/femto/femto-capitulation-options.md in this repo: The old Alpaca swing desk, via Femto-lean (family Femto-lean, asset equity options, timeframe 1h with 1d filters, universe 41-name old-desk basket, style mean reversion (options)).

## What this sleeve is
This sleeve expresses the same hourly capitulation signal as the equity capitulation sleeve as a single long call: the nearest expiry inside a week, the first strike at least 2 percent out of the money, sized at 0.10 percent of the book in premium. Exits are +75 percent on premium, 1 day to expiry, or the underlying 3 percent under its entry price. The v3 adapter rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/capitulation_options.py signal(bars, slice_state, context), with entry filtering through desk3/enhance14.py in the adapter path recorded in the audit chain.

## Full algorithm
Constants (sleeves/capitulation_options.py): RISK_FRACTION = 0.001 (0.10 percent), MAX_POSITIONS = 5, OTM_PCT = 0.02, PROFIT_TAKE_MULT = 1.75 (+75 percent premium), EXIT_DTE = 1, THESIS_BREAK_PCT = 0.03, QUOTE_GATE_FRAC = 0.15, plus the mirrored signal constants RSI_PERIOD = 14, RSI_OVERSOLD = 20, VOL_CLIMAX_MULT = 2.0, VOL_LOOKBACK = 20, EMA200_PERIOD = 200, EMA_TOLERANCE = 0.02, ATR_PCT_FILTER = 0.05, ATR_PERIOD = 14, BLACKOUT_DAYS_BEFORE = 3. CONFIG: cadence_s 300, universe (), risk_pct RISK_FRACTION. ENH_DTE_MIN = 2 for the enhancement below.

Signal: the same 5-part capitulation signal as the equity sleeve, mirrored verbatim in this module (detect_capitulation): 1-hour RSI(14) below 20, climax volume over 2 x the 20 bars before it, climax low within 2 percent of the daily EMA200, first green bar with RSI turning up, and daily ATR(14) over 5 percent of close.

Entries, in code order:
1. Fear gate: entries defer exactly as the equity sleeve unless extra["fear_ok"] is served (fail-closed when absent). The earnings veto refuses entries within 3 days before earnings.
2. Contract selection (select_long_call): ONE long call on the nearest expiry in the 0 to 7 DTE window, the first strike at or above spot x 1.02; the quote gate requires ask above 0 and (ask - bid) / mid at most QUOTE_GATE_FRAC = 0.15. Enhancement (ENH-CAPOPT-20261024, on by default; switch extra["capitulation_options_improve"] {"dte_min_2": bool}): the nearest expiry with DTE at least 2 is selected (0 to 1 DTE skipped, since they are born due under the EXIT_DTE = 1 law); OFF restores DTE-min-0 selection exactly.
3. Order and sizing: a DAY limit at the ask per the card's execution summary; quantity from qty_for_risk: premium budget = RISK_FRACTION = 0.10 percent of the book per trade (premium paid is the max loss; there is no disaster stop). At most MAX_POSITIONS = 5 live positions.

Exits (exit_due, first trigger wins): premium at or above PROFIT_TAKE_MULT = 1.75 x the entry premium (+75 percent); DTE at or below EXIT_DTE = 1 (never hold into expiry); underlying at or below entry x (1 - 0.03) (thesis broken). Exits are sold with a DAY limit at the bid per the card's execution summary.

Position management: at most 5 live, one call per signal, no stop on premium beyond the three exit rules above.

## Files in this repo
- Sleeve module (desk sleeves/capitulation_options.py): `sleeves/capitulation_options.py`.
- v3 adapter (desk adapters3/capitulation_options.py): `adapters3/capitulation_options.py`; also present as `integration/capitulation_options_adapter.py`.
- Shared v3 entry glue used by the adapter: `adapters3/_snapshot_ctx.py` (desk source adapters3/_snapshot_ctx.py; named in the audit record as a shared dependency).
- Shared entry filter in the adapter delegation path: `engines/desk3/enhance14.py` (desk source desk3/enhance14.py, vendored in this repo per engines_map.json).
- Signal mirror source: `sleeves/capitulation.py` (the equity sleeve whose 5-part signal this module mirrors).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/femto/femto-capitulation-options.md`.

## Configuration
- Universe: the 41-name old-desk basket (served as the bars keys; CONFIG universe is ()). Asset: equity call options, 0 to 7 DTE (at least 2 DTE with the enhancement on). Timeframe: 1h signal with 1d filters.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk_pct 0.001 in CONFIG (0.10 percent of the book in premium per trade).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, options, positions.

## Data inputs
- bars_1h: context.extra["bars_1h"] {symbol: [closed 1-hour bars]} and daily bars (260) for EMA200 and ATR, per the module header's input list.
- chains: context.extra["chains"] {symbol: [chain rows]} for the 0 to 7 DTE call selection, with bid/ask quotes for the 15 percent spread gate (the card's Data line: the desk's 0 to 7 DTE call chains and quotes).
- fear_ok: context.extra["fear_ok"] (fail-closed when absent); the earnings calendar for the 3-day veto; sleeve_state positions with entry premium, entry spot and expiry.

## Install and run
1. Place the sleeve module at sleeves/capitulation_options.py and the adapter at adapters3/capitulation_options.py (repo copies at the same paths). The adapter path also places the shared filter at desk3/enhance14.py (repo copy at engines/desk3/enhance14.py).
2. Register the roster row for `capitulation_options` exactly as in the Configuration section in config/sleeves.json (module adapters3.capitulation_options).
3. Wire the producers so every snapshot carries: daily and 1-hour bars per basket symbol in extra bars_1h and bars, call chains in extra chains, this sleeve's positions, and extra fear_ok.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch1_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check the signal mirror: the same 5-part fixtures as the equity sleeve produce a signal here, and removing any part produces none.
- Check contract selection: the expiry is the nearest inside 0 to 7 DTE (at least 2 DTE with the enhancement on), the strike is the first at or above spot x 1.02, and a spread over 15 percent of mid or a non-positive ask refuses the trade.
- Check sizing and limits: premium per trade is at most 0.10 percent of the book and the 6th live position is refused.
- Check exits: premium at 1.75 x entry, DTE at or below 1, or the underlying 3 percent under entry each close the position, first trigger wins.
