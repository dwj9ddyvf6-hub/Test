# bilbo_options: Recreation package

Provenance: Source row in strategies/femto/femto-bilbo-options.md in this repo: Milkman (milkmantrades.com) Bilbo Box v2 with Saty's Phase Oscillator; the old swing desk, via Femto-lean (family Femto-lean, asset equity options, timeframe 1h (5-minute exits), universe 20 large caps, style volatility breakout (options)).

## What this sleeve is
This sleeve watches 20 large caps for an hourly Saty Phase compression box, and when the first hourly bar out of compression closes above the box high it buys one call about 0.75 ATR out of the money expiring in about three to five weeks. Exits run on 5-minute bars: below the box low, a giveback rule once the stock has run, a 10-trading-day cap, and a 5-days-to-expiry rail. The v3 adapter rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/bilbo_options.py signal(bars, slice_state, context).

## Full algorithm
Constants (sleeves/bilbo_options.py): UNIVERSE = NVDA, NFLX, AMD, GOOGL, AAPL, AMZN, MSFT, AVGO, TSLA, PLTR, INTC, MU, JPM, UBER, BAC, DIS, META, SMCI, HOOD, COIN (20 names), MAX_POSITIONS = 5, WATCH_DAYS = 10, BOX_FREEZE = 5, MIN_GREY = 1, TIME_CAP_TRADING_DAYS = 10, EXPIRY_PROXIMITY_DTE = 5, GIVEBACK_ARM_ATR = 1.25, GIVEBACK_KEEP = 0.25, SPREAD_GATE = 0.05, STRIKE_ATR_MULT = 0.75, PREMIUM_FRACTION = 0.04. CONFIG: cadence_s 300, universe UNIVERSE, risk_pct PREMIUM_FRACTION. Engine flags from the module header: 5-minute bars resampled to 60-minute on the on-the-hour grid over extended hours 04:00 to 19:55 ET, minutes = 60, session eth, break_rule close, min_grey = 1, first_bar_only = True, stdev_ddof = 1.

Box construction, in code order: grey (compression) bars are hourly bars in Saty Phase compression (21-period Bollinger inside a 2 x ATR14 Keltner, except not-shrinking and inside the 1.854 x expansion zone, per phase_compression). The box is the high and low of the FIRST 5 grey hourly candles of a run, frozen after the 5th; the run stays live for WATCH_DAYS = 10 calendar days; one shot per run.

Entries, in code order:
1. Exits for held positions are evaluated first (below); a symbol with a position is not re-entered, and entries stop at MAX_POSITIONS = 5 open or when equity is at or below 0 or no 5-minute bars are served. At least 200 resampled hourly bars are required.
2. Trigger: the last detected episode must have broken out, its out-bar must be the last hourly bar (only the FIRST bar out counts, on its own bar), the first hourly bar out of compression CLOSES above the box high, and time_gate_ok requires the hourly close to land 10:00 to 15:00 ET Monday to Friday.
3. Trend gate: spot strictly above the daily 21 EMA at the prior completed regular-hours close (ema21_gate_ok over daily_rth bars).
4. Contract: expiries are selected with select_expiry inside the effective DTE window: with the enhancement on (ENH-BILBO-20261024, switch in extra, default ON) the window is MIN_DTE to MAX_DTE as defined in the module for the improved rule (the card records the improvement as expiries 15 to 21 days out); with it off the control window CONTROL_MIN_DTE to CONTROL_MAX_DTE applies (the frozen 21 to 37 DTE rule in the module header). A paired record of both selections is journaled. The strike is the nearest to spot + 0.75 x the prior day's ATR(14) (target_strike).
5. Quote gate and sizing: the call quote must be two-sided with (ask - bid) / mid at most SPREAD_GATE = 0.05 (spread_gate_ok). size_contracts spends PREMIUM_FRACTION = 4 percent of equity in premium with a 1-contract minimum. The entry is a limit at the mid per the card's execution summary (cancelled after 60 minutes in the old runner; the v3 intent carries the sleeve's limit construction in the module).

Exits (evaluate_exit over 5-minute bars at or after entry, first trigger wins, in per-bar order):
1. Expiry rail first (not hostage to bars): when the OCC expiry is at most EXPIRY_PROXIMITY_DTE = 5 days from the reference date (the last bar's ET date, else the context session date; with neither it fails closed), exit with reason expiry_proximity. A position flagged box_metadata_unknown, or missing entry_t, entry_spot, box_lo, datr14_prior or entry_date, returns no stock-keyed exit (the DTE rail has already run).
2. Time cap: TIME_CAP_TRADING_DAYS = 10 trading days after entry.
3. Box low: a 5-minute close under the box low.
4. Giveback: once the stock has run GIVEBACK_ARM_ATR = 1.25 x ATR from entry, a close at or below entry + GIVEBACK_KEEP = 25 percent of the peak gain.
Exit intents carry the full held qty with a price hint from the last 5-minute close (or the recorded entry premium when the expiry rail fired bars-less).

Position management: at most 5 open, one call per breakout run, no pyramiding.

## Files in this repo
- Sleeve module (desk sleeves/bilbo_options.py): `sleeves/bilbo_options.py`.
- v3 adapter (desk adapters3/bilbo_options.py): `adapters3/bilbo_options.py`; also present as `integration/bilbo_options_adapter.py`.
- Shared v3 entry glue used by the adapter: `adapters3/_snapshot_ctx.py` (desk source adapters3/_snapshot_ctx.py; named in the audit record as a shared dependency).
- No separate engine file: the full logic (phase compression, box detection, exit evaluation) is in `sleeves/bilbo_options.py` itself (audit engine_files_needed names only the shared desk3/enhance14.py filter in the wider adapter chain).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/femto/femto-bilbo-options.md`.

## Configuration
- Universe: the 20 names listed in the Full algorithm section. Asset: equity call options. Timeframe: 1h boxes from 5-minute extended-hours bars; 5-minute regular-hours exits.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; risk_pct 0.04 in CONFIG (4 percent of equity in premium per trade, 1-contract minimum).
- Cadence: 300 seconds. Session: rth. flat_by_close: true; flatten_time_et: 15:55; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, options, positions.

## Data inputs
- bars_5m: context.extra["bars_5m"] {symbol: [5-minute bars]} (the card's Data line: Yahoo 5-minute bars, 60 days); the sleeve resamples them to extended-hours hourly bars itself and requires bars closed at least 20 minutes before scan time in the desk's SIP convention for the history leg.
- chains and quotes: context.extra["chains"] {symbol: [call chain rows with expiration]} and context.extra["quotes"], covering 0 to 60 DTE on the desk door (the sleeve selects inside its DTE window).
- sleeve_state: context.extra["sleeve_state"] {symbol: {"position": {qty, occ, entry_t, entry_spot, box_lo, datr14_prior, entry_date, entry_px}}}; context.equity is the sizing basis; context.session is the reference date.

## Install and run
1. Place the sleeve module at sleeves/bilbo_options.py and the adapter at adapters3/bilbo_options.py (repo copies at the same paths). The module needs the desk BaseSleeve / SleeveConfig / Intent plumbing it imports in the fresh desk.
2. Register the roster row for `bilbo_options` exactly as in the Configuration section in config/sleeves.json (module adapters3.bilbo_options).
3. Wire the producers so every snapshot carries: 5-minute bars per universe symbol in extra bars_5m, call chains and quotes in extra chains/quotes, this sleeve's positions in extra sleeve_state, and context.equity and context.session.
4. First evaluation: call evaluate(view, ctx) on the adapter; it rebuilds the v2 SleeveContext from the snapshot and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (the desk blocker named in the adapter header is tests/test_port_batch1_blockers.py, which hash-pins the strategy and v2 adapter copies; no per-sleeve test file for this sleeve is present in this repo):
- Check the box: the box freezes after the first 5 grey hourly candles, a run older than 10 calendar days is dead, and only the first bar out of compression, when it is the last hourly bar and closes above the box high inside 10:00 to 15:00 ET on a weekday, can trigger.
- Check the gates: spot at or below the daily 21 EMA, a quote spread over 5 percent of mid, or 5 positions already open each produce no entry.
- Check the contract: the chosen expiry lies in the effective DTE window (improved window with the enhancement on, 21 to 37 control window with it off) and the strike is nearest spot + 0.75 x prior daily ATR(14); premium sizing is 4 percent of equity with at least 1 contract.
- Check exit precedence: the 5-DTE expiry rail fires even with no bars served; then the 10-trading-day cap, a close under the box low, and the giveback rule (armed at +1.25 ATR, exit at entry + 25 percent of peak gain) fire in that per-bar order.
