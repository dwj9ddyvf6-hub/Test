# aster_pub_rsi2_ada - RECREATE

Provenance: Larry Connors' RSI(2), via trader.dev, StockCharts and Tomazetti's Pine script; the old swing desk via Femto-lean (Source row of the existing Test doc `strategies/ausar/public-rsi2.md`); the sleeve module header in desk `aster_sleeves/aster_pub_rsi2_ada.py` identifies this variant as public_recipe Filtered RSI2 dip rebound, ADAUSDT, TSV #46 / SM PUBLIC_TOMAZETTI_RSI2_SPOT100.

## What this sleeve is

This sleeve buys ADA crypto spot on an extreme 2 period RSI dip in an uptrend, on hourly bars, and sells when price closes back above the 5 bar average. This variant is the Tomazetti ADA hourly variant named in the existing card's Variants table for Midna v3 `aster_pub_rsi2_ada`. It is long only, with the source 10 percent stop disabled, on a $10,000 slice evaluated hourly.

## Full algorithm

Delegation: the sleeve module `aster_sleeves/aster_pub_rsi2_ada.py` imports `evaluate_rsi2` from `aster_sleeves._common` and calls it with `SLEEVE_ID="aster_pub_rsi2_ada"`. The shared engine fixes `SYMBOL = "ADAUSDT"`. All rules below are `evaluate_rsi2` in that engine as applied to this sleeve.

Evaluation order:

1. Current time is `view.now`, parsed as a timezone-aware timestamp (`_now`); a naive timestamp raises an error in `_stamp`.
2. Bars: `_bars(view, "1Hour")` reads only the key `ADAUSDT|1Hour` from the view `bars` dict, sorted by bar time. Closes are the close of each bar in order.
3. Position handling first: positions are filtered to `sleeve_id` equal to this sleeve or None, symbol `ADAUSDT`, quantity not zero.
   - If a position is held: compute SMA5 (simple mean of the last 5 closes, requiring at least 5 closes). If SMA5 exists and the last close > SMA5, exit the whole absolute quantity at the last close with reason `aster_rsi2_close_above_sma5`. Otherwise return no intents (a held position blocks any new entry, and there is no stop: the module header states stop disabled).
4. Entry gates (no position), in code order:
   - At least 200 bars are required; fewer returns no intents.
   - Decision window: the last bar completion time is its bar time plus 1 hour. `now - completion` must be between 0 and 300 seconds inclusive, otherwise no entry.
   - Installed window: the last bar time must be between 2009-01-01T19:00:00-05:00 and 2030-12-29T19:00:00-05:00 inclusive (engine constants `_WINDOW_START` / `_WINDOW_END`).
   - Indicators: Wilder RSI(2) via the engine `_rsi` / `_rma` helpers; SMA200 is the mean of the last 200 closes; SMA4 of RSI is the mean of the last 4 RSI(2) values. If RSI, SMA200 or SMA4 of RSI is None, no entry.
   - Signal: last RSI(2) < 10 AND last close > SMA200 AND SMA4(RSI(2)) < 30. All three must hold.
5. Sizing and entry intent: cash is `view.slice.cash_usd`, falling back to `capital_usd`, falling back to 10000. Quantity = `floor(cash / last close)`. Reject if quantity <= 0. Intent is a dict with `kind="entry"`, side buy, `order_type="market"`, `time_in_force="gtc"`, symbol `ADAUSDT`, price hint = last close, reason `aster_public_rsi2_filtered`. Exit intents use the same market / gtc shape with side sell.

Note on sizing versus the existing card: the card states the Binance book uses 100 percent of cash including 10 bps, lot-floored. The `evaluate_rsi2` path computes `floor(cash / close)` with no fee deduction (the engine fee constant is used in its separate crypto function, not in evaluate_rsi2); the code formula is the recreation standard here.

## Files in this repo

- Sleeve module (repo copies): `aster_sleeves/aster_pub_rsi2_ada.py`, `sleeves/aster/aster_pub_rsi2_ada.py`, and `integration/aster_pub_rsi2_ada_adapter.py`. Desk original: `aster_sleeves/aster_pub_rsi2_ada.py`, delegating to `aster_sleeves._common.evaluate_rsi2`.
- Shared engine that runs the logic: `engines/aster_sleeves/_common.py` (repo path for desk `aster_sleeves/_common.py`; contains `evaluate_rsi2`, `_rsi`, `_sma`, `_bars`, `_positions` and the ADAUSDT symbol constant).
- Existing family card: `strategies/ausar/public-rsi2.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_pub_rsi2_ada`).

## Configuration

- Sleeve id: `aster_pub_rsi2_ada`; module: `aster_sleeves.aster_pub_rsi2_ada` (roster row in desk `config/sleeves.json`; the module itself also declares `CADENCE_S = 3600` and `INPUTS = ('bars', 'positions')`).
- Universe: ADA (ADAUSDT) in the existing card's Variants table for this row. Asset: crypto spot.
- Timeframe: 1h (hourly, per the card variant and the `1Hour` bar key). Session: `24h`. Cadence: 3600 seconds.
- Sizing / slice: $10,000 capital and $10,000 cash; `bp_buffer_frac=0.02`; entry quantity is floor(cash / close) as above.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false.

## Data inputs

Inputs declared in the roster row and the module: `bars`, `positions`.

The code consumes `view.bars["ADAUSDT|1Hour"]`, `view.positions`, `view.slice`, and `view.now`. No producer tuple is declared in `aster_sleeves/_common.py` or the sleeve module, so no producer freshness SLA is stated in those files. The existing card lists the underlying data for the ADA variant as Binance 1 hour klines and Alpaca crypto bars; this v3 engine reads the bars supplied in the view.

## Install and run

1. Place the shared engine as `aster_sleeves/_common.py` in a fresh desk (from repo `engines/aster_sleeves/_common.py`) and the sleeve module as `aster_sleeves/aster_pub_rsi2_ada.py`.
2. Register the roster row for `aster_pub_rsi2_ada` from `config/sleeves.json` (module `aster_sleeves.aster_pub_rsi2_ada`, cadence 3600, session 24h, $10,000 slice, inputs bars/positions, parked false).
3. Wire inputs so the view contains `bars` under the exact key `ADAUSDT|1Hour` (at least 200 completed hourly bars for an entry), `positions` from broker readback, a `slice`, and a timezone-aware `now` within 300 seconds after a bar completes.
4. First evaluation: call `aster_sleeves.aster_pub_rsi2_ada.evaluate(view, ctx)`; it delegates to `evaluate_rsi2(view, ctx, "aster_pub_rsi2_ada")`. Run hourly at the bar completion plus the 300 second decision window.

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist:

- Check that a held position exits only when the last close is above SMA5, and otherwise produces no intent and no stop exit.
- Check that fewer than 200 bars, a decision time more than 300 seconds after the last bar completes, or a bar time outside the installed 2009 to 2030 window each block entry.
- Check that entry requires all three of RSI(2) < 10, close > SMA200, and the 4 bar mean of RSI(2) < 30; failing any one blocks entry.
- Check entry quantity equals floor(cash / last close), using cash_usd first, then capital_usd, then 10000.
- Check that a position whose symbol is not ADAUSDT or whose sleeve_id is a different sleeve is ignored by this sleeve.
