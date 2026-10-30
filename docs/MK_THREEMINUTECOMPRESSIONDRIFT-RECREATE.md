# mk-threeminutecompressiondrift: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Three-minute compression drift (SPY)", type volatility, family milkman. Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and the code in this repo (see Files).
- Test catalog entry `mk-threeminutecompressiondrift` (`docs/CATALOG.json`): card `strategies/milkman/mk-threeminutecompressiondrift.md`.
- Alias: `mk_threeminutecompressiondrift`.

## What this strategy is

After a 3-minute squeeze of 8 or more candles that drifts one way, enters on the first candle out of it that closes past the squeeze's late midpoint, with a 1-ATR stop. Both sides use the ATR gate 0.045% of price (code cell atrgate=0.00045).

## Full algorithm

From `strategies/milkman/mk-threeminutecompressiondrift.md` and the code in Files, in evaluation order:

1. Episodes: a squeeze of >= 8 three-minute candles within one session; one-candle breaks are allowed (a single non-compression candle inside the run does not end the episode, per the code's flicker rule in `detect_cdc` in `sleeves/milkman/intraday.py`, setup CDC).
2. Drift: up drift = the later candles' high >= the first 5 candles' high + 0.5 x ATR(3-minute, at the episode's last candle) AND their low >= the first 5's low - 0.25 x ATR; down drift is the mirror. If both or neither hold, there is no trade.
3. Trigger: the first candle out of the squeeze that closes beyond the midpoint of the last 5 squeeze candles in the drift's direction (close above the midpoint for up, below for down).
4. ATR gate: entry only when the 3-minute ATR at the trigger candle is >= 0.045% of the entry price (code: atrgate=0.00045, both sides).
5. Entry: at the next 1-minute bar's open after the trigger candle.
6. Exit: stop 1 x the 3-minute ATR from entry, by touch; otherwise out at the close.
7. Execution / sizing: each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Files in this repo

- This doc: `docs/MK_THREEMINUTECOMPRESSIONDRIFT-RECREATE.md`
- Strategy card: `strategies/milkman/mk-threeminutecompressiondrift.md`
- Code (already in Test): `sleeves/milkman/intraday.py` (setup CDC and `detect_cdc`), `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- Rule lines: `docs/verify/milkman.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, tests/) was searched for the canonical id and alias; Silicon tree, quant-research-backup tree and Midna tree were also searched for the canonical id, its alias and family terms (milkman / compression). No code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: SPY only. Timeframe: 3m candles built from 1-minute bars. Asset class: US ETF.
- Book: $1,000,000; $10,000 a trade, every trade taken; trades net on SPY.
- ATR gate 0.00045 and the >= 8-candle episode rule are in algorithm steps 1 and 4. Status on the card: waiting.

## Data inputs

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Install and run

1. Clone the Test repo.
2. Read `strategies/milkman/mk-threeminutecompressiondrift.md` and the matching section of `docs/verify/milkman.md`.
3. Open the code files listed in Files and locate this strategy's setup row and rule implementation.
4. Provide the data inputs listed above.
5. Run on the cadence in Configuration and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- No episode with fewer than 8 squeeze candles, and an episode never crosses a session boundary.
- No trade when the drift test holds in both directions or in neither.
- The trigger candle must close beyond the last-5-candles midpoint in the drift direction, and the ATR gate (0.045% of price) must pass.
- The stop is exactly 1 x the 3-minute ATR from entry and an untouched position is flat at the close.
