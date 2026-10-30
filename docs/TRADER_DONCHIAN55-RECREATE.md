# TRADER_DONCHIAN55: recreation package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json): canonical name 'TRADER_DONCHIAN55', type trend following, algorithm grade PARTIAL, unresolved true, with the note: singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description. The accounting records no entry, exit, or sizing for this id. Test does hold a strategy card and code-derived algorithm doc for the corresponding Midna v3 sleeve aster_trader_donchian55: strategies/ausar/public-donchian55.md and docs/ASTER_TRADER_DONCHIAN55-ALGORITHM.md (algorithm derived from the sleeve code on 2026-10-29). This package records that Test evidence and does not claim the accounting is settled.

## What this strategy is

A daily Donchian 55/20 trend breakout sleeve over a fixed 15-ETF universe, as implemented by the Test code below: it buys a close above the prior 55-day high while above the 200-day SMA, and exits on a close below the prior 20-day low or below the 200-day SMA, an initial 2 x ATR14 stop, or 126 holding bars.

## Full algorithm

Evaluation order, from docs/ASTER_TRADER_DONCHIAN55-ALGORITHM.md (derived from desk3/aster_batch16.py) and strategies/ausar/public-donchian55.md:

1. Exits are evaluated first; if any exit is emitted, the evaluation returns with no entry.
2. Exit, initial stop: a held position whose last close is at or below its recorded stop price (entry price minus 2.0 x ATR14) is sold in full.
3. Exit, timeout: a position held at least 126 completed holding bars is sold in full.
4. Exit, signal: with at least 252 bars, a last close below the prior 20-day low and/or below the 200-day SMA sells the position in full. Exits are market, day, sell_to_close intents, in full.
5. Entry candidates need at least 252 daily bars, a positive ATR14, and a positive 20-day average dollar volume.
6. Entry condition: last close above the prior 55-day high (the maximum high of the 55 bars before the last bar) and last close above the 200-day SMA.
7. Ranking: candidates are ranked by (close minus prior 55-day high) / ATR14, descending, symbol ascending on ties. Slots: 10.
8. Sizing: cap = min(equity x 0.10, 20-day average dollar volume x 0.01, available cash); shares = int(cap // price), then capped by the risk size int((equity x 0.005) // (2.0 x ATR14)); fewer than 1 share emits nothing. Equity is the $10,000 slice (SLICE = 10000.0 in the algorithm doc).
9. The entry intent is market, day, buy_to_open, with stop_price = round(price minus 2.0 x ATR14, 4) recorded on the intent.

## Files in this repo

- This doc: docs/TRADER_DONCHIAN55-RECREATE.md
- Strategy card in Test: strategies/ausar/public-donchian55.md
- Code-derived algorithm doc in Test: docs/ASTER_TRADER_DONCHIAN55-ALGORITHM.md
- Accounting entry in Test: docs/ALL-SLEEVES.json, strategy 'TRADER_DONCHIAN55' (UNRESOLVED)
- Code in Test: sleeves/aster_trader_donchian55.py (wrapper, sleeve id aster_trader_donchian55) delegating to the shared engine desk3/aster_batch16.py (kind donchian); the same wrapper also appears at adapters3/aster_trader_donchian55.py and integration/aster_trader_donchian55_adapter.py
- No code was vendored for this package; all code above was already in Test.

## Configuration

- Universe (engine): SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX.
- Timeframe: daily. Minimum bars 252. Entry channel 55, exit channel 20, SMA 200, ATR 14 (Wilder RMA). Maximum hold 126 bars. Slots 10.
- Sizing: notional fraction 0.10 of equity, dollar-volume fraction 0.01 of the 20-day average dollar volume, risk fraction 0.005 of equity, stop 2.0 x ATR14. Slice capital $10,000.
- Cadence: 86400 seconds, session rth (engine). Paper only (algorithm doc).

## Data inputs

- Yahoo daily bars (card). Engine declared inputs: bars and positions; producers: bars at 900 second freshness and broker readback at 900 seconds (desk3/aster_batch16.py, per the algorithm doc).

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch.
2. Read this package and the strategy card or algorithm doc named in the Files section.
3. Install the code paths named in the Files section at the same relative paths in a desk3-compatible runtime; the sleeve wrapper imports its shared engine by the module path recorded there, so keep the repo directory layout unchanged.
4. Configure the sleeve with the exact parameters in the Configuration section; do not substitute values from a different variant.
5. Provide the data inputs named in the Data inputs section through the runtime view (bars, positions, and quotes where the engine declares them).
6. Call the sleeve module's evaluate(view, ctx) function on the cadence recorded in the Configuration section and route the returned intents through the desk dispatcher; this package does not include a standalone broker connector.
7. Run the Verification checklist before trusting any output.

## Verification

Behavior checklist (no test file for this sleeve was located in Test):
1. A symbol with at least 252 bars closing above its prior 55-day high and above SMA200, with positive ATR14 and dollar volume, produces a ranked entry candidate; ranking follows (close minus prior high) / ATR14 descending.
2. A held position closing at or below its recorded 2 x ATR14 stop is sold in full, and no entry is emitted in that evaluation.
3. A held position closing below the prior 20-day low or below SMA200 is sold in full.
4. A position held 126 completed bars is sold in full.
5. Entry share count never exceeds min(0.10 x equity, 0.01 x 20-day average dollar volume, cash) divided by price, nor the 0.5 percent risk size over 2 x ATR14.
