# ema_vwap: Recreation package

Provenance: Source row in strategies/femto/femto-ema-vwap.md in this repo: Family Femto-lean; Source The old Alpaca swing desk, via Femto-lean; Asset US equities; Timeframe 1d (hourly checks); Universe 41-name old-desk basket; Style Mean reversion; Status live.

## What this sleeve is
This is a daily mean-reversion equity sleeve: it buys a basket name whose last close is well below its 20-day rolling VWAP and sells it when price reverts to the VWAP or a target, stop or time limit is hit. The v3 adapter additionally passes entries through the desk3/enhance15 entry filter. Sources: sleeves/ema_vwap.py and adapters3/ema_vwap.py on the desk.

## Full algorithm
Evaluation order in sleeves/ema_vwap.py signal(), per symbol in the universe (context.extra universe override, else the bars keys), with equity from the slice:

1. Held position first (exits need only the last close and session dates; the 30-bar warmup guards entries only). Exit the full qty when any of: the last close is at or above the 20-bar rolling VWAP (reverted_to_vwap, needs at least 21 bars); last close >= entry_px * 1.05 (+5% profit target, PROFIT_TARGET 0.05); last close <= entry_px * 0.92 (-8% hard stop, STOP_LOSS 0.08); or sessions held >= 5 trading days (TIME_STOP_DAYS 5, counted as delivered dates strictly after the entry date).
2. Entry gate: at least 30 bars (WARMUP_BARS 30); fewer than 8 open positions (MAX_POSITIONS 8); equity > 0.
3. Entry signal: deviation_below: at least 21 bars, a valid 20-bar rolling VWAP, and last close strictly below VWAP * (1 - 0.02) (DEV_PCT 0.02). The rolling VWAP is the 20-bar sum of typical price (h+l+c)/3 times volume divided by the 20-bar volume sum; any zero or missing volume bar inside the 20-bar window makes the VWAP None and there is no signal.
4. Enhancement gate (ENH, on by default; switched by context.extra["ema_vwap_improve"]["deviation_geometry_gate"]): refuse the entry when (VWAP - close) / close < STOP_LOSS 0.08, that is when the full reversion gain is smaller than the coded stop; in deviation terms only entries about 7.4% or more below the anchor are taken. Each qualifier records a paired control/treatment record.
5. Sizing: qty = floor(min(equity * 0.0025 / (0.08 * ref_px), equity * 0.05 / ref_px)) (RISK_FRACTION 0.0025, POS_NOTIONAL_CAP 0.05); qty <= 0 skips the entry, with no 1-share minimum. The entry is also skipped when sleeve notional after it would exceed 25% of equity (SLEEVE_NOTIONAL_CAP 0.25).
6. Entry intent: buy at the last close (price_hint rounded to 2dp), with a disaster stop at entry * (1 - 0.25) (DISASTER_STOP 0.25) and exit rules stop at that disaster price, target at entry * 1.05, and time_bars 5.

## Files in this repo
- Sleeve module: sleeves/ema_vwap.py (the strategy logic; CONFIG sleeve_id=ema_vwap).
- v3 adapter: adapters3/ema_vwap.py (evaluate(view, ctx), delegating through adapters3/_snapshot_ctx.evaluate_ported; that shared helper is named in the audit record as missing shared code in this repo).
- Existing strategy doc: strategies/femto/femto-ema-vwap.md.
- Shared engine file: engines/desk3/enhance15.py (desk3/enhance15.py; the adapters3 module applies enhance15.filter_entries to entries for ema_vwap and free_kraken_ada_basis; the other ported adapters in this batch delegate without that filter unless their adapter text says so).
- Config: engines/config/sleeves.json (row id=ema_vwap).
- The enhance15 filter is applied by adapters3/ema_vwap.py, not by the other ported adapters in this batch.

## Configuration
Module adapters3.ema_vwap; cadence_s 300; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [bars, positions]; parked false. Source: muse-desk-v3/config/sleeves.json row id=ema_vwap.

## Data inputs
Daily bars (dicts with t, o, h, l, c, v, ascending) for the universe symbols, supplied through the snapshot / adapter bar cache (1Day, 400 bars requested by the v2 adapter, warmup 30); positions and sleeve_state ({SYM: {position: {entry_px, entry_date, qty}}}) from the desk's position records; equity from the slice. The existing doc lists split-adjusted daily bars (120). No data is fetched during evaluation.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (engines/ paths map back to the desk paths of the same relative name, for example engines/desk3/enhance15.py is desk3/enhance15.py on a fresh desk).
2. Register the config row for `ema_vwap` from engines/config/sleeves.json (repo copy of config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides: the roster row carries params {} for this sleeve unless stated otherwise there.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot / context.extra in the shapes the algorithm section describes.
4. Run the desk cycle; the entry point is the adapter module's evaluate(view, ctx), which rebuilds the strategy context from the snapshot and delegates to the sleeve module's signal(bars, slice_state, context).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing.

## Verification
- Fixture A (entry): 30 or more daily bars whose last close is about 8% or more below a valid 20-bar VWAP (no zero-volume bar in the window) produces one buy intent sized by the 0.25% risk / 5% notional formula; the same fixture with the close only 3% below the VWAP produces no entry while the enhancement gate is on, and one entry with the gate switched off in context.extra.
- No intent is emitted when a required input is missing, stale, crossed or malformed: the code fails closed and never raises.
- Quantity, price hint and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- Exit fixtures for each exit rule in the Full algorithm section each produce exactly one exit intent for the full held quantity (or the stated trim quantity), and no exit fires when no exit rule is met.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
