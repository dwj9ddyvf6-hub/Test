# rsi_meanrev_options: Recreation package

Provenance: Source row in strategies/femto/femto-rsi-meanrev-options.md in this repo: The old Alpaca swing desk, via Femto-lean.

## What this sleeve is
This sleeve takes the rsi_meanrev equity signal (RSI(2) below 10 with the close above the 200-day SMA) and expresses it as a 14 to 30 DTE call debit spread instead of stock: the long leg is the highest strike at or below spot and the short leg the first strike at least 8 percent higher. It exits at 50 percent of maximum profit, at 7 DTE, or when RSI(2) snaps back above 70. Sources: sleeves/rsi_meanrev_options.py and desk_sleeves/rsi_meanrev_options.py on the desk.

## Full algorithm
Constants (sleeves/rsi_meanrev_options.py): RSI_PERIOD 2, RSI_OVERSOLD 10.0, RSI_OVERBOUGHT 70.0, MA200_PERIOD 200, RISK_FRACTION 0.0025, MAX_POSITIONS 5, SPREAD_WIDTH_PCT 0.08, PROFIT_TARGET_FRAC 0.50, EXIT_DTE 7, LIQ_GATE_FRAC 0.10, DTE_MIN 14, DTE_MAX 30, DEBIT_CAP_FRAC 0.5. CONFIG: cadence_s 300, universe (), risk_pct 0.0025. The signal is exactly the stock sleeve's, using the stock sleeve's ewm-seeded Wilder RSI imported from sleeves/rsi_meanrev.py.
Evaluation order in signal(), per symbol (universe override, else the bars keys):
1. Held spread first: compute the spread's close value from the live leg quotes, then exit_due in this order: close value - entry debit >= 0.50 x max profit (profit_target_50pct); remaining DTE <= 7 (dte_time_stop); RSI(2) > 70 (snapback done). Any one exits the full qty.
2. Entry gates: at most 5 open positions and equity above 0; rsi_signal requires at least 200 closes, RSI(2) strictly below 10, and the last close above the 200-day SMA.
3. Spread selection (select_debit_spread, target = spot): consider only the earliest expiration with DTE in 14..30; the long leg is the highest strike at or below spot (the lowest strike when none qualifies); the short leg is the first strike at or above long strike x 1.08, else no spread. Liquidity gate: the long leg's (ask - bid) / mid must be at most 0.10 when a bid exists; the long ask must be positive. Debit = long ask - short bid; refuse when debit <= 0 or debit >= width (a guaranteed-loss structure).
4. Enhancement gate (switch context.extra["rsi_meanrev_options_enhance"]["debit_cap"], default ON): refuse a spread whose debit exceeds half its width (max profit smaller than the amount risked). Every selected spread records a paired control/treatment decision in the sleeve's enhance journal.
5. Sizing: qty = floor(equity x 0.0025 / (debit x 100)); qty 0 skips. The enter intent is on the underlying with the long and short OCC symbols, strikes, expiry, width and debit named in the reason.
The v3 adapter universe is the 41-name basket (AEHR, NBIS, SKYQ, SHAZ, LITE, SOXL, WYFI, CRML, AAOI, WDC, VELO, ANF, SATL, ASPI, IREN, AG, AXTI, LASR, ARQQ, OUST, ALAB, CRDO, FCEL, HIVE, POET, SNDK, TEM, CORZ, HUT, TSEM, ARM, KEEL, FFIV, MU, CLS, TE, TTMI, CVNA, VRT, OKLO, USAR) plus the bridge CANDIDATES, roster additions and held symbols, with 200 1-day warmup bars requested; entries then pass desk3/enhance18.filter_entries.

## Files in this repo
- Strategy module (desk sleeves/rsi_meanrev_options.py): `sleeves/rsi_meanrev_options.py` in this repo (the strategy logic; CONFIG sleeve_id=rsi_meanrev_options).
- v3 adapter (desk desk_sleeves/rsi_meanrev_options.py): `integration/rsi_meanrev_options_adapter.py` in this repo; the adapter re-shapes the snapshot via the port bridge and applies the enhance18 entry filter to entries.
- Shared engine files (engines_map.json): `engines/desk3/enhance18.py` (desk desk3/enhance18.py, vendored; filter_entries) and `engines/desk3/bridge.py` (desk desk3/bridge.py, vendored; the port bridge).
- Sleeve contract used by the strategy: `sleeves/muse/core/sleeve.py` (desk core/sleeve.py).
- Config: engines/config/sleeves.json (row id=rsi_meanrev_options); also config/sleeves.json.
- Existing strategy doc: see the Provenance line.

## Configuration
Module rsi_meanrev_options; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et None; params {}; inputs ['bars_1day', 'positions', 'options_chains', 'options_quotes']; parked false. Source: muse-desk-v3/config/sleeves.json row id=rsi_meanrev_options (repo copy: engines/config/sleeves.json).

## Data inputs
Daily bars for the underlying symbols; call chains {SYM: [{symbol, strike, expiration}]} and option quotes {OCC: {bid, ask}} via context.extra (roster inputs options_chains and options_quotes); sleeve_state {SYM: {position}} with the recorded spread (legs, expiry, entry debit, max profit); equity from the slice.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance18.py is desk3/enhance18.py on a fresh desk).
2. Register the config row for `rsi_meanrev_options` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the v3 wrapper module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo unless named under Files in this repo):
- Check the signal: RSI(2) of exactly 10.0, a close below the SMA200, and fewer than 200 closes each produce no entry.
- Check selection: an expiration at 13 or 31 DTE is ignored; the long leg is the highest strike at or below spot and the short leg the first strike at or above 1.08 x the long strike; a long-leg spread wider than 10 percent of mid, a non-positive debit, and a debit at or above the width each produce no spread.
- Check the debit cap: a debit of 0.51 x width is refused with the gate ON and taken with it OFF; 0.50 x width is taken either way.
- Check exits in order: 50 percent of max profit exits before the 7-DTE stop, which exits before the RSI(2) above 70 check on a fixture where more than one applies.
- Check sizing: qty equals floor(equity x 0.0025 / (debit x 100)) and the 6th position is refused.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
