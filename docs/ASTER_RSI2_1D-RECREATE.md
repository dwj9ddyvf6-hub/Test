# aster_rsi2_1d: Recreation package

Provenance: Source row in strategies/ausar/public-rsi2.md in this repo: Larry Connors' RSI(2), via trader.dev, StockCharts and Tomazetti's Pine script; the old swing desk via Femto-lean; the per-sleeve algorithm doc docs/ASTER_RSI2_1D-ALGORITHM.md states it was derived from the sleeve code on 2026-10-29 (no author spec on file).

## What this sleeve is
This sleeve buys long US equity and ETF positions in a 15-symbol universe when a completed daily RSI2 dip occurs in a long-term uptrend (close above SMA200 and below SMA5), ranked by the depth of the dip, and sells when price closes back above SMA5 or after 10 completed holding bars. It is a thin adapter in adapters3/ whose evaluate(view, ctx) delegates to desk3/aster_batch1.py evaluate(SLEEVE_ID, view, ctx), kind rsi2. It implements no strategy math of its own; all rules below are the batch-1 trader engine rules as applied to this sleeve's SPECS entry.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_batch1.py): kind="rsi2", cadence_s=300, session="rth". Its frozen source rule is trader_rsi2_public_v1 (backend/trader_signals.py, indicator math ported function-for-function: Wilder RSI via RMA seed, EMA seed = first-period mean). No risk fraction, DTE, delta or options parameter applies to this equity sleeve.

Feature computation (engine _trader_features, kind rsi2), per symbol, on daily bars:
- At least 252 bars are required before features are computed at all in the evaluator (see the completed-bar rule below).
- ATR14 is the RMA (Wilder smoothing, seed = mean of the first 14 values) of true range; DV20 is the mean of close x volume over the last 20 bars. Features are refused when ATR14 is missing or at most 0, or DV20 is at most 0.
- RSI2 is the Wilder RSI of closes with period 2 (RMA-seeded gains and losses over close changes; 50 when gain and loss are both 0, 100 when loss is 0, 0 when gain is 0, else 100 - 100 / (1 + gain / loss)). SMA200 and SMA5 are simple means of the last 200 and last 5 closes. Any of RSI2, SMA200 or SMA5 missing refuses the symbol.
- Entry flag: RSI2 <= 5.0 and close > SMA200 and close < SMA5. Exit reasons: ["close_above_sma5"] when close > SMA5, otherwise none. Rank = (RSI2, -(SMA5 - close) / ATR14). Max hold = 10 completed holding bars. Stop distance = None: this sleeve has NO initial stop.
- Completed-bar enhancement (ENH-B11-TRADER-COMPLETEDBAR-20261024; this sleeve is in the engine ENH11_TRADER tuple, on by default; switch extra["enh_aster_rsi2_1d"] or ctx enhance {"completed_bar": bool}): bars dated the current ET session are dropped before features are computed, so the signal uses completed daily bars only; when the forming-bar and completed-bar decisions differ on entry or exit, a paired shadow record is written to the journal. With the switch off, the last (possibly forming) bar is used exactly as before.

Exits, evaluated first, for each held long position (qty > 0) in sorted symbol order:
1. If the symbol's features carry an exit reason (close > SMA5), exit the full qty, reason `aster_rsi2_1d:close_above_sma5`.
2. Otherwise, if bars held is at least max_hold = 10, exit the full qty, reason `aster_rsi2_1d:10_completed_holding_bars`. Bars held is taken from the position bars_held / sessions_held / held_bars field when present, otherwise the count of bars dated after opened_at, otherwise the difference between the current bar count and the bar_count stored in the sleeve state file (ctx state_dir / aster_b1_aster_rsi2_1d.json) at entry.
Exit intents are market sells, time_in_force day, price_hint = the feature close. If any exit intent is produced, the state entries for the exited symbols are removed, the state file is saved, and entries are not evaluated.

Entries, in code order:
1. Free slots = 10 minus the number of held positions; at most 10 positions. No free slot means no entry.
2. Candidates are symbols whose entry flag is true and which are not already held, sorted ascending by rank tuple (RSI2, -(SMA5 - close) / ATR14) and then symbol.
3. Sizing per candidate (per backend/trader_runtime.py as ported): cap = min(0.10 x equity, 0.01 x DV20, cash), where equity and cash come from view/ctx slice capital_usd / cash_usd (falling back to 10000.0). Shares = int(cap // close). Because stop_distance is None for rsi2, the additional risk cap floor(0.005 x equity / stop_distance) that the engine applies to risk sleeves does NOT apply here. Shares below 1 skips the candidate. Cash is decremented by shares x close after each fill of a slot.
4. Entry intent: market buy, time_in_force day, qty = shares, price_hint = close, stop_price = None, reason `aster_rsi2_1d:rsi2_pullback`. On entry the state file records bar_count (the number of bars supplied for the symbol), stop_price = None and entry_at = now.

Position management: at most 10 long positions, one per symbol, no pyramiding, no shorting, and no stop-loss for this sleeve.

## Files in this repo
- Sleeve adapter (desk adapters3/aster_rsi2_1d.py): `adapters3/aster_rsi2_1d.py`; also present as `sleeves/aster_rsi2_1d.py` and `integration/aster_rsi2_1d_adapter.py`.
- Shared engine: `desk3/aster_batch1.py` (desk source desk3/aster_batch1.py, SPECS entry for `aster_rsi2_1d`, inputs_for and _trader_features).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/ausar/public-rsi2.md`; existing per-sleeve algorithm doc: `docs/ASTER_RSI2_1D-ALGORITHM.md`.

## Configuration
- Universe: UNIVERSE15 in the engine: SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX. Asset: US equities and ETFs, long only. Timeframe: 1Day bars.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; the per-position cap rule in the Full algorithm applies (min of 10 percent of equity, 1 percent of DV20, cash).
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions. Engine inputs_for this kind: (bars, positions).

## Data inputs
- bars: view["bars"] keyed by `<symbol>|1Day` or `<symbol>|1D` or by symbol, rows with t, o, h, l, c, v; at least 252 rows per symbol are needed before features are computed, and with the completed-bar enhancement on, at least 252 completed rows. Producer: bars, freshness SLA 900 seconds (engine PRODUCERS in desk3/aster_batch1.py).
- positions: view["positions"] rows with symbol, qty, avg_price, opened_at and optionally bars_held / sessions_held / held_bars. Producer: broker_readback, freshness SLA 900 seconds.
- State: ctx state_dir holds aster_b1_aster_rsi2_1d.json with per-symbol bar_count, stop_price and entry_at written on entry and removed on exit.
- Clock: view now or ctx now (timezone-aware), or the ctx session date, supplies the current ET session for the completed-bar filter.

## Install and run
1. Place the engine at desk3/aster_batch1.py in the fresh desk (repo copy at the same path) and the adapter at adapters3/aster_rsi2_1d.py with SLEEVE_ID = "aster_rsi2_1d".
2. Register the roster row for `aster_rsi2_1d` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_rsi2_1d, cadence 300, session rth, $10,000 slice, inputs bars/positions).
3. Wire the producers so every snapshot carries daily bars for all 15 universe symbols and this sleeve's positions, plus a timezone-aware now and ctx state_dir for the state file.
4. First evaluation: call evaluate(view, ctx) on the adapter; it calls desk3.aster_batch1.evaluate("aster_rsi2_1d", view, ctx). Confirm a snapshot with fewer than 252 completed bars per symbol returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the entry flag on fixtures: RSI2 above 5.0, close at or below SMA200, or close at or above SMA5 each produce no entry; all three conditions together produce a candidate.
- Check the completed-bar rule: a bar dated the current ET session does not change the signal when the enhancement is on, and a paired record is written when the forming-bar decision would have differed; with the switch off the forming bar is used.
- Check ranking and slots: candidates fill in ascending (RSI2, -(SMA5 - close) / ATR14, symbol) order and never take the book above 10 positions or re-enter a held symbol.
- Check sizing: shares equal int(min(0.10 x equity, 0.01 x DV20, remaining cash) // close), with no stop-distance cap and stop_price absent on the entry intent.
- Check exits: close above SMA5 on a completed bar exits the full qty; otherwise the position exits exactly when bars held reaches 10; an exit suppresses entries in the same evaluation and removes the symbol from the state file.
