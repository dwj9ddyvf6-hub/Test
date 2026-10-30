# mk-tenminutecompressionrelease: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Ten-minute compression release (SPY)", type volatility, family milkman. Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and the code in this repo (see Files).
- Test catalog entry `mk-tenminutecompressionrelease` (`docs/CATALOG.json`): card `strategies/milkman/mk-tenminutecompressionrelease.md`.
- Alias: `mk_tenminutecompressionrelease`.

## What this strategy is

When a 10-minute squeeze releases, enters the next minute in the EMA21/48 direction with the stop at the squeeze's far side, flat by the close. Lanes: long squeeze >= 3 candles, short squeeze >= 18 candles.

## Full algorithm

From `strategies/milkman/mk-tenminutecompressionrelease.md` and the code in Files, in evaluation order:

1. Saty's compression on 10-minute candles (the compression flag from `sleeves/milkman/vendor/milkman/mlib.py`, applied to 10-minute bars in `sleeves/milkman/intraday.py`, setup COMP10).
2. Signal: the first 10-minute candle out of a squeeze (compression flag goes from on to off) whose preceding squeeze run is at least N candles: N=3 for the long lane, N=18 for the short lane (code cells: long minbars=3;exit=eod, short minbars=18;exit=eod).
3. Direction: long when EMA(21) is above EMA(48) on the 10-minute candles, short when below. The stop is the squeeze run's low for a long (its high for a short), taken over the squeeze candles before the release candle.
4. Entry: at the next 1-minute bar's open after the release candle.
5. Exit: the stop, by touch; otherwise out at the close (exit=eod).
6. Execution / sizing: each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Files in this repo

- This doc: `docs/MK_TENMINUTECOMPRESSIONRELEASE-RECREATE.md`
- Strategy card: `strategies/milkman/mk-tenminutecompressionrelease.md`
- Code (already in Test): `sleeves/milkman/intraday.py` (setup COMP10 and its detection loop), `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- Rule lines: `docs/verify/milkman.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, tests/) was searched for the canonical id and alias; Silicon tree, quant-research-backup tree and Midna tree were also searched for the canonical id, its alias and family terms (milkman / compression). No code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: SPY only. Timeframe: 10m candles built from 1-minute bars. Asset class: US ETF.
- Book: $1,000,000; $10,000 a trade, every trade taken; trades net on SPY.
- Lane parameters are in algorithm step 2. Status on the card: waiting.

## Data inputs

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only.

## Install and run

1. Clone the Test repo.
2. Read `strategies/milkman/mk-tenminutecompressionrelease.md` and the matching section of `docs/verify/milkman.md`.
3. Open the code files listed in Files and locate this strategy's setup row and rule implementation.
4. Provide the data inputs listed above.
5. Run on the cadence in Configuration and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- No entry unless the release candle follows a squeeze run of at least 3 candles (long) or 18 candles (short).
- Direction always follows EMA(21) versus EMA(48) on the 10-minute candles at the release.
- The stop equals the squeeze run's low (long) or high (short) and an untouched position is flat at the close.
- A signal seen more than 2 bars late does not enter.
