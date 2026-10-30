Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_trader_donchian55: Algorithm

## What it trades
A thin wrapper sleeve. The file
adapters3/aster_trader_donchian55.py is the per-sleeve
core: evaluate() delegates to the shared engine
desk3/aster_batch16.py evaluate(), kind="donchian". It is
a Donchian 55/20 trend-following sleeve over a fixed
15-ETF universe: buy a close above the prior 55-day high
while above the 200-day SMA, exit on a close below the
prior 20-day low or below the 200-day SMA, an initial
2xATR14 stop, or 126 holding bars. Sizing is on the
$10,000 slice (SLICE = 10000.0). Paper only. The sleeve
runs on the shared engine desk3/aster_batch16.py.

## Spec and constants (desk3/aster_batch16.py)
kind="donchian", inputs=("bars", "positions"),
cadence_s=86400, session="rth", slice capital $10,000.
Universe: SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI,
XLP, XLU, XLB, XLY, SMH, SOXX. Minimum bars 252; entry
channel 55, exit channel 20, SMA 200; maximum hold 126
bars; slots 10; notional fraction 0.10 of equity;
dollar-volume fraction 0.01 of the 20-day average dollar
volume; risk fraction 0.005 of equity; stop = 2.0 x
ATR14 (Wilder RMA).

## Entry rules
- Exits are evaluated first; if any exit is emitted the
  evaluation returns with no entry.
- A candidate needs at least 252 daily bars, a positive
  ATR14 and a positive 20-day average dollar volume.
- Entry condition: last close above the prior 55-day
  high (the maximum high of the 55 bars before the last
  bar) and last close above the 200-day SMA.
- Candidates are ranked by (close - prior55_high) / ATR14
  descending, symbol ascending on ties.
- Sizing: cap = min(equity x 0.10, dollar_volume20 x
  0.01, available cash); shares = int(cap // price),
  then capped by the risk size int((equity x 0.005) //
  (2.0 x ATR14)); fewer than 1 share emits nothing.
- The entry intent is market, day, buy_to_open, with
  stop_price = round(price - 2.0 x ATR14, 4) recorded on
  the intent.

## Exit rules
- Initial stop: a held position whose last close is at
  or below its recorded stop_price (the entry 2xATR14
  stop, read from the position or its meta) is sold in
  full.
- Timeout: a position held at least 126 completed
  holding bars is sold in full, reason
  126_completed_holding_bars.
- Signal exits (with at least 252 bars): a last close
  below the prior 20-day low and/or below the 200-day
  SMA sells the position in full, with the triggered
  conditions named in the reason.
- Exits are market, day, sell_to_close intents, in full.

## Data inputs
Declared inputs: bars, positions. Producers named in
desk3/aster_batch16.py: bars (900s freshness),
broker_readback (900s, positions).
