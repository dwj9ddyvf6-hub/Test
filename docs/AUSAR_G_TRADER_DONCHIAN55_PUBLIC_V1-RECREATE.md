# ausar_g_trader_donchian55_public_v1: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "55-bar trend breakout · 1d", type breakout, family public_recipe. Algorithm grade PARTIAL, with the recorded gap: sizing not recorded in any consulted source. This canonical id is the alias `ausar_g_trader_donchian55_public_v1` itself (status in the accounting: md2_catalog "installed").
- Accounting algorithm text: Entry: close > max(previous_55_high) and close > sma200. Exit: close < min(previous_20_low) or close < sma200 or observed_quote_initial_2atr_stop or 126_completed_holding_bars. Sell below the prior twenty-bar low, below SMA200, at the initial two-ATR stop, or after 126 completed holding bars. Data per the accounting: posted Ausar runtime inputs.
- No Test catalog entry in the accounting (test_entries empty). The sizing the accounting lacked is held in the code in this repo (see Full algorithm); nothing beyond the record and that code is claimed.
- Supporting Test docs: the strategy card `strategies/ausar/public-donchian55.md` (status live; universe 15 liquid ETFs; data Yahoo daily bars; code named as `desk3/aster_batch16.py`) and the code-derived `docs/ASTER_TRADER_DONCHIAN55-ALGORITHM.md`.
- Code search: the fresh Test tree taken at batch start holds the sleeve wrapper and the shared engine (paths in Files). Silicon, quant-research-backup and Midna trees were searched for this sleeve id and Donchian code; no matching file for this canonical id was found there.

## What this strategy is

A daily Donchian 55/20 trend-following sleeve over a fixed 15-ETF universe: buy a close above the prior 55-day high while above the 200-day SMA, exit on a close below the prior 20-day low or below the 200-day SMA, an initial 2 x ATR14 stop, or 126 holding bars. Paper only, on a $10,000 slice.

## Full algorithm

From `sleeves/aster_trader_donchian55.py` delegating to `desk3/aster_batch16.py` `evaluate` with kind donchian (DONCHIAN_ID `aster_trader_donchian55`, inputs bars/positions, cadence 86400 seconds). Engine constants: universe SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX; minimum bars 252; entry channel 55; exit channel 20; SMA 200; maximum hold 126 bars; slots 10; notional fraction 0.10 of equity; dollar-volume fraction 0.01 of the 20-day average dollar volume; risk fraction 0.005 of equity; stop 2.0 x ATR14 (Wilder RMA); slice $10,000.

Evaluation order:

1. Exits first, per held position, in this order: (a) initial stop: if the last close is at or below the position's recorded stop_price (from the position or its meta), sell in full with the observed_quote_initial_2atr_stop reason; (b) timeout: if bars held >= 126, sell in full (126_completed_holding_bars); (c) signal exits, requiring at least 252 bars: sell in full if the last close is below the prior 20-day low and/or below the 200-day SMA, with the triggered conditions named in the reason. If any exit is emitted, return with no entry.
2. Entries: a candidate symbol is not held, has at least 252 daily bars, a positive ATR14 and a positive 20-day average dollar volume, and its last close is above the prior 55-day high (the maximum high of the 55 bars before the last bar) and above the 200-day SMA.
3. Ranking: candidates are ranked by (close - prior55_high) / ATR14 descending, symbol ascending on ties. Free slots are 10 minus the number held.
4. Sizing per candidate: cap = min(equity x 0.10, dollar_volume20 x 0.01, available cash), where available cash starts as the slice cash and is reduced by held positions at their average prices and by each new entry in this evaluation; shares = int(cap // price), then capped by the risk size int((equity x 0.005) // (2.0 x ATR14)); fewer than 1 share emits nothing.
5. Entry intent: market, day, buy_to_open, with stop_price = round(price - 2.0 x ATR14, 4) recorded on the intent.

## Files in this repo

- This doc: `docs/AUSAR_G_TRADER_DONCHIAN55_PUBLIC_V1-RECREATE.md`
- Sleeve code (already in Test): `sleeves/aster_trader_donchian55.py`, with copies at `adapters3/aster_trader_donchian55.py` and `integration/aster_trader_donchian55_adapter.py`.
- Shared engine that runs the logic: `desk3/aster_batch16.py` (kind donchian; `_don_features` and `_eval_donchian`).
- Strategy card: `strategies/ausar/public-donchian55.md`; code-derived algorithm doc: `docs/ASTER_TRADER_DONCHIAN55-ALGORITHM.md`; rule lines: `docs/verify/ausar.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json`, row `aster_trader_donchian55`.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`.

## Configuration

- Sleeve (engine) id: `aster_trader_donchian55`; roster module `adapters3.aster_trader_donchian55`.
- Universe: the 15 ETFs listed in Full algorithm. Asset: US ETFs. Timeframe: 1-day completed bars.
- Session rth; cadence 86400 seconds; slice capital and cash $10,000; `bp_buffer_frac` 0.02; `flat_by_close` false; parked false. Paper only.
- Declared producers in the engine: bars (900s freshness) and broker_readback positions (900s freshness).

## Data inputs

- Daily bars per universe symbol (at least 252 for signals), positions (broker readback), and the slice cash/capital. Accounting data note for this alias: posted Ausar runtime inputs.

## Install and run

1. Clone the Test repo.
2. Place `desk3/aster_batch16.py` under `desk3/` and the wrapper as `sleeves/aster_trader_donchian55.py` (or the `adapters3/` copy).
3. Register the roster row for `aster_trader_donchian55` from `config/sleeves.json` (module `adapters3.aster_trader_donchian55`, cadence 86400, session rth, $10,000 slice, inputs bars/positions, parked false).
4. Wire the view with daily `bars` for the 15-ETF universe, `positions`, and a `slice`.
5. Call the wrapper's `evaluate(view, ctx)` once per day in the regular session; it delegates to `desk3.aster_batch16.evaluate("aster_trader_donchian55", view, ctx)`. First check is the exit scan, then ranked entries.
6. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in the fresh Test tree. Behaviour checklist from the algorithm above:

- No entry with fewer than 252 bars, a non-positive ATR14 or dollar volume, a close at or below the prior 55-day high, or a close at or below SMA200.
- Ranking follows (close - prior55_high) / ATR14 descending with symbol-ascending ties, and no more than 10 positions are held.
- Shares equal the minimum of the notional, dollar-volume and cash caps, further capped by the 0.5%-risk size to the 2 x ATR14 stop; the recorded stop_price is round(price - 2 x ATR14, 4).
- Exits fire in the stated order: recorded stop first, then 126 completed holding bars, then close below the prior 20-day low and/or below SMA200.
