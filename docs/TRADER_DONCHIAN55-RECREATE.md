# TRADER_DONCHIAN55: Recreation Package
Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "TRADER_DONCHIAN55", type trend following, family unrecorded. Sole alias `TRADER_DONCHIAN55`, recorded from ausar_deployed with status "mode=original_independent_local_paper running=False". The accounting records NO strategy description and NO algorithm (entry, exit, sizing all "not recorded in any consulted source"), and flags the strategy UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description".
- Evidence found in Test beyond the accounting: the strategy card `strategies/ausar/public-donchian55.md` ("Public Donchian 55 trend (daily)", source: trader.dev public strategy; StockCharts price channels), the v3 sleeve `sleeves/aster_trader_donchian55.py` (docstring: "Aster batch 16"), and the code-derived algorithm doc `docs/ASTER_TRADER_DONCHIAN55-ALGORITHM.md` (derived from the sleeve code on 2026-10-29). The algorithm below is taken from those two Test documents, which are the best evidence on file; the accounting's UNRESOLVED flag stands because the accounting itself never settled this id.

## What this strategy is

A Donchian 55/20 trend-following sleeve over a fixed 15-ETF universe: buy a close above the prior 55-day high while above the 200-day SMA; exit on a close below the prior 20-day low or below the 200-day SMA, an initial 2xATR14 stop, or 126 holding bars. Paper only, on a $10,000 slice.

## Full algorithm

From `docs/ASTER_TRADER_DONCHIAN55-ALGORITHM.md` (code-derived from `desk3/aster_batch16.py`, kind "donchian") and the strategy card, in evaluation order:

1. Exits are evaluated first; if any exit is emitted, the evaluation returns with no entry.
2. Exit, initial stop: a held position whose last close is at or below its recorded stop_price (the entry 2xATR14 stop, read from the position or its meta) is sold in full.
3. Exit, timeout: a position held at least 126 completed holding bars is sold in full (reason `126_completed_holding_bars`).
4. Exit, signals (requires at least 252 bars): a last close below the prior 20-day low and/or below the 200-day SMA sells the position in full, with the triggered conditions named in the reason. Exits are market, day, sell_to_close intents, in full.
5. Entry candidates need at least 252 daily bars, a positive ATR14, and a positive 20-day average dollar volume.
6. Entry condition: last close above the prior 55-day high (the maximum high of the 55 bars before the last bar) and last close above the 200-day SMA.
7. Candidates are ranked by (close - prior55_high) / ATR14 descending, symbol ascending on ties. Slots: 10.
8. Sizing: cap = min(equity x 0.10, dollar_volume20 x 0.01, available cash); shares = int(cap // price), then capped by the risk size int((equity x 0.005) // (2.0 x ATR14)); fewer than 1 share emits nothing.
9. The entry intent is market, day, buy_to_open, with stop_price = round(price - 2.0 x ATR14, 4) recorded on the intent. ATR14 is Wilder RMA.

## Files in this repo

- This package: `docs/TRADER_DONCHIAN55-RECREATE.md`
- Strategy card: `strategies/ausar/public-donchian55.md` (also `strategies/femto/femto-donchian.md` for the femto Donchian family)
- Code-derived algorithm doc: `docs/ASTER_TRADER_DONCHIAN55-ALGORITHM.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/aster_trader_donchian55.py` (wrapper; SLEEVE_ID `aster_trader_donchian55`)
  - `adapters3/aster_trader_donchian55.py` and `integration/aster_trader_donchian55_adapter.py` (same wrapper)
  - `desk3/aster_batch16.py` (shared engine, kind "donchian")

## Configuration

From the algorithm doc's spec section (engine `desk3/aster_batch16.py`): kind "donchian", inputs (bars, positions), cadence_s 86400, session rth, slice capital $10,000 (SLICE = 10000.0). Universe: SPY, QQQ, IWM, DIA, XLK, XLF, XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX (15 ETFs; the card says "15 liquid ETFs (as RSI2)"). Minimum bars 252; entry channel 55; exit channel 20; SMA 200; maximum hold 126 bars; slots 10; notional fraction 0.10 of equity; dollar-volume fraction 0.01 of the 20-day average dollar volume; risk fraction 0.005 of equity; stop 2.0 x ATR14 (Wilder RMA). Deployed status per the accounting: original_independent_local_paper, running=False.

## Data inputs

Declared inputs: bars, positions. Producers named in `desk3/aster_batch16.py`: bars (900s freshness), broker_readback (900s, positions). The strategy card records Yahoo daily bars as the data source for the original public strategy.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test) so that `desk3/` and `sleeves/` sit side by side; the wrapper imports the shared engine from `desk3/` by module path.
2. No third-party package beyond the desk3 runtime is required by the wrapper or the engine (standard library only, per the engine source).
3. Standalone evaluation: build a `view` dict carrying the declared inputs (see Data inputs) and call the wrapper: `from sleeves.aster_trader_donchian55 import evaluate; intents = evaluate(view, ctx)`. `ctx` may be None for a stateless read; the desk3 dispatcher supplies the snapshot view and context in production.
4. In the desk, the v3 dispatcher calls `evaluate` on the sleeve's cadence and routes the returned intent dicts (market, day, buy_to_open / sell_to_close) to the paper broker. Paper only.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A name with 252+ bars whose close crosses above its prior 55-day high while above its SMA200 produces a buy_to_open intent carrying stop_price = entry price - 2 x ATR14, rounded to 4 decimals.
- Position size never exceeds min(10% of equity, 1% of 20-day average dollar volume, cash) and never risks more than 0.5% of equity to the 2xATR14 stop.
- A held position closes in full on the first of: close at or below its stop_price, close below the prior 20-day low, close below the SMA200, or 126 completed holding bars.
- When an exit is emitted for a name, no entry for any name is emitted in the same evaluation.
- With fewer than 252 bars, or non-positive ATR14 or dollar volume, no entry is emitted.
