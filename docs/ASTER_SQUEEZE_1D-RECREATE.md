# aster_squeeze_1d - RECREATE

Provenance: trader.dev public strategy; LazyBear squeeze momentum; StockCharts TTM squeeze (Source row of the existing Test doc `strategies/ausar/public-squeeze20.md`); the per-sleeve behaviour doc `docs/ASTER_SQUEEZE_1D-ALGORITHM.md` states it was derived from the sleeve code on 2026-10-29 with no author spec on file; desk engine header in `desk3/aster_batch1.py` describes the frozen rule `trader_squeeze20_public_v1` ported function-for-function from the archive trader signals module.

## What this sleeve is

This sleeve is a daily volatility-squeeze breakout sleeve over 15 liquid US ETFs. It buys a name only on the bar where a Bollinger Band squeeze inside the Keltner Channel releases, with rising positive LazyBear momentum and a close above the prior 20-bar high. It is a thin wrapper: all logic lives in the shared engine `desk3/aster_batch1.py`.

## Full algorithm

Delegation and spec: the adapter `adapters3/aster_squeeze_1d.py` sets `SLEEVE_ID="aster_squeeze_1d"`, takes `INPUTS = inputs_for(SLEEVE_ID)` and `PRODUCERS` from `desk3/aster_batch1.py`, and delegates to `desk3.aster_batch1.evaluate(SLEEVE_ID, view, ctx)`. The SPECS row in that engine for this sleeve is exactly: `kind="squeeze", cadence_s=300, session="rth"`. Inputs for kind `squeeze` are `("bars", "positions")`.

Universe (engine constant `UNIVERSE15`, daily bars, keys `SYM|1Day` then `SYM|1D`): SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX.

Evaluation order in `_eval_trader` (the engine dispatch for kind `squeeze`):

1. Feature computation per symbol. A symbol is skipped unless at least 252 bars are available. Features need a positive Wilder ATR14 (RMA of true range, period 14) and a positive DV20 (mean of close times volume over the last 20 bars); otherwise the symbol is skipped.
2. Completed-bar enhancement (ENH-B11-TRADER-COMPLETEDBAR-20261024, applies to this sleeve, default ON; switch `extra["enh_aster_squeeze_1d"]` or `ctx["enhance"]["aster_squeeze_1d"]` key `completed_bar`, OFF restores the forming-bar rule exactly): bars dated the current ET session are dropped before features are computed, so only completed daily bars decide; a differing forming-bar decision is recorded as the paired shadow control.
3. Squeeze series (`_squeeze_series`, all periods 20): SMA20 of closes; EMA20 centre (seed is the first-period mean); ATR20 as RMA of true range with period 20. Bollinger Bands are SMA20 plus or minus 2.0 times the population standard deviation of the last 20 closes. Keltner Channel is EMA20 centre plus or minus 1.5 times ATR20. A bar is in squeeze when the Bollinger lower band is above the Keltner lower band and the Bollinger upper band is below the Keltner upper band. Delta for a bar is close minus the average of (the 20-bar high/low midpoint) and SMA20; momentum is the linear-regression endpoint of delta over the last 20 bars.
4. Entry condition for a symbol (all must hold on the last completed bar): squeeze was on at the previous bar and off at the current bar (a release); momentum > 0; momentum greater than the previous bar momentum; close greater than the prior 20-bar high (maximum high of `bars[i-20:i]`).
5. Exits are evaluated before entries, in sorted symbol order, for each held long position (quantity > 0). The first applicable reason wins:
   - Signal exit reasons from the current features: close < EMA20 centre gives `close_below_ema20`; momentum <= 0 gives `momentum_nonpositive`; both may be joined.
   - Initial stop: the stop recorded at entry (position `stop_price` or sleeve state) is entry close minus 2 times ATR14; if the last bar low is at or below the stop, exit with reason `observed_quote_initial_2atr_stop`.
   - Time exit: held bars (position `bars_held` / `sessions_held` / `held_bars`, else bars after `opened_at`, else sleeve state bar count) >= 20 gives `20_completed_holding_bars`.
   An exit sells the full integer quantity as a market order, side sell, time in force day, with the feature close as price hint, and removes the symbol from sleeve state. If any exit is emitted, no entry is evaluated in the same pass.
6. Entries (only when no exit was emitted): candidates are symbols whose entry condition holds and that are not already held, ranked by `(-momentum / ATR14, symbol ascending)`. At most 10 positions in total; entries fill free slots in rank order. Sizing per candidate: cap = min(0.10 times equity, 0.01 times DV20, remaining cash), where equity is the slice `capital_usd` (fallback ctx or view equity, default 10000.0) and cash is the slice `cash_usd` (fallback equity); shares = floor(cap / close); the risk cap also applies because this sleeve has a stop distance: shares = min(shares, floor(0.005 times equity / stop_distance)) with stop_distance = 2 times ATR14. Shares < 1 emits nothing. Cash is decremented by shares times close after each fill.
7. Entry intent: market buy, time in force day, quantity shares, price hint the feature close, stop price `round(close - stop_distance, 4)`, reason `aster_squeeze_1d:squeeze_breakout`. Sleeve state (file `aster_b1_aster_squeeze_1d.json` in the ctx state dir, when one is supplied) records per symbol the bar count, the stop price and the entry time.

There is no shorting, no options leg and no other exit in this engine path for this sleeve.

## Files in this repo

- Sleeve adapter (repo copies): `adapters3/aster_squeeze_1d.py`, `sleeves/aster_squeeze_1d.py`, and `integration/aster_squeeze_1d_adapter.py`. Desk original: `adapters3/aster_squeeze_1d.py`, delegating to `desk3/aster_batch1.evaluate`.
- Shared engine that runs the logic: `desk3/aster_batch1.py` (contains the SPECS row for this sleeve, `_squeeze_series`, `_trader_features`, `_eval_trader` and `evaluate`; engines map status already_present).
- Existing family card: `strategies/ausar/public-squeeze20.md`. Existing per-sleeve behaviour doc: `docs/ASTER_SQUEEZE_1D-ALGORITHM.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json` (the row for `aster_squeeze_1d`).

## Configuration

- Sleeve id: `aster_squeeze_1d`; module: `adapters3.aster_squeeze_1d` (roster row in desk `config/sleeves.json`).
- Universe: the 15 ETFs listed in the algorithm (engine `UNIVERSE15`). Asset: US ETFs / equities. Timeframe: 1d (daily bars). Session: `rth`. Cadence: 300 seconds (`cadence_s=300`).
- Sizing / slice: $10,000 capital and $10,000 cash in the roster slice; the engine sizing rule is the cap formula in step 6 (10 percent of equity, 1 percent of DV20, remaining cash, plus the 0.5 percent risk cap to the 2 times ATR14 stop). `bp_buffer_frac=0.02`.
- `flat_by_close=false`, `flatten_time_et=null`. Parked: false (`parked=false`).

## Data inputs

Inputs declared in the roster row and the engine (`INPUTS_BY_KIND["squeeze"] = ("bars", "positions")`): `bars`, `positions`.

Producers declared in `desk3/aster_batch1.py` (`PRODUCERS`): `bars` (outputs bars, freshness SLA 900s), `tensor_bundle` (outputs tensor, 86400s), `broker_readback` (outputs positions, 900s), `quotes` (outputs quotes, 60s), `options_chain` (outputs options, 300s), `opening_events` (outputs opening_events, 300s). This sleeve consumes only bars and positions: at least 252 daily bars per candidate symbol and the current positions. The existing card lists the underlying data as Yahoo daily bars; the v3 function itself reads only the bars and positions supplied in the view, plus the slice equity and cash and the current time.

## Install and run

1. Place `desk3/aster_batch1.py` in a fresh desk under `desk3/` (copy the repo file of that path).
2. Place the adapter as `adapters3/aster_squeeze_1d.py` (copy any repo copy listed above).
3. Register the roster row for `aster_squeeze_1d` from `config/sleeves.json` (module `adapters3.aster_squeeze_1d`, cadence 300, session rth, $10,000 slice, inputs bars/positions, parked false).
4. Wire inputs so the view contains daily `bars` under `SYM|1Day` or `SYM|1D` keys for the 15 universe symbols (at least 252 completed bars each), `positions` from broker readback, a `slice` with capital and cash, and a current time in the view or context. Supply a ctx `state_dir` if the stop and holding state file is to persist.
5. First evaluation: call `adapters3.aster_squeeze_1d.evaluate(view, ctx)`; it delegates to `desk3.aster_batch1.evaluate("aster_squeeze_1d", view, ctx)`. Run every 300 seconds in the rth session; the first check is the exit scan, then ranked entries into free slots.

## Verification

No per-sleeve test file for this sleeve was present in the fresh Test tree at build time. Prove a recreation with this behaviour checklist, each check derived from the algorithm above:

- Check the squeeze definition exactly: with Bollinger (20, 2.0, population stdev) inside Keltner (EMA20, 1.5 times ATR20) on the prior bar and outside on the current bar, momentum positive and rising, and close above the prior 20-bar high, an entry is produced; failing any one of those four conditions independently blocks the entry.
- Check that fewer than 252 bars, a non-positive ATR14, or a non-positive DV20 skips the symbol.
- Check exits in order: close below the EMA20 centre exits, non-positive momentum exits, a bar low at or below entry close minus 2 times ATR14 exits on the recorded stop, and 20 held bars exits; any exit in a pass blocks all entries in that pass.
- Check sizing: shares equal the smaller of floor(min(0.10 equity, 0.01 DV20, cash) / close) and floor(0.005 equity / (2 times ATR14)), the stop price on the intent equals round(close minus 2 times ATR14, 4), and at most 10 positions are ever held.
- Check ranking: among simultaneous candidates the larger momentum divided by ATR14 enters first, with symbol ascending as the tie break in the rank tuple.
- Check the completed-bar rule: with the enhancement ON (the default), a bar dated the current ET session does not change the decision; with it OFF, the forming bar is included.
