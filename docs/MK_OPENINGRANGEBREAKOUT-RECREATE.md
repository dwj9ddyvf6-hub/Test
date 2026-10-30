# mk-openingrangebreakout: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Opening range breakout (SPY)", type breakout, family milkman, universe SPY, asset US ETF, timeframe "1m (5-minute closes)", creator "The Milkman v2 study". Algorithm grade PARTIAL; the accounting records the variant axes (Long lane: 5-minute range, filter 10-minute EMA8 > EMA21 and close above VWAP; Short lane: 10-minute range, no filter) and gaps entry, exit and sizing in its consulted sources; the full rules below are from the Test card and running Test code (`sleeves/milkman/intraday.py` ORB row: mk_openingrangebreakout, long or=5;filter=ribbon_vwap;stop=mid, short or=10;filter=none;stop=mid).
- Test catalog entry `mk-openingrangebreakout`: card `strategies/milkman/mk-openingrangebreakout.md`, variants as above, status waiting.
- Code search record: Searched for code: Test tree at batch start (sleeves/, strategies/, packages/, desk3/, engines/) - found as listed below; Silicon tree (research/, desk trees) and quant-research-backup tree and Midna tree - no additional code file for this canonical id was found in those trees (tree grep for the id, alias and card slug).

## What this strategy is

Trades the first 5-minute close outside SPY's opening range, with the stop at the range's midpoint, flat by the close (card summary).

## Full algorithm

Evaluation order, from the card and the ORB branch in `sleeves/milkman/intraday.py`:

1. Range: the first 5 minutes' high and low (long lane) or the first 10 minutes' high and low (short lane).
2. Entry: the first 5-minute close beyond the range sets the side and enters at that close. The long lane additionally requires the last 10-minute EMA(8) above EMA(21) and the close above the session VWAP; the short lane has no filter.
3. Exit: stop at the range's midpoint, by touch; otherwise out at the close.
4. Common Milkman execution (card, all three SPY intraday strategies): each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close; $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Files in this repo

- This package: `docs/MK_OPENINGRANGEBREAKOUT-RECREATE.md`
- Strategy card: `strategies/milkman/mk-openingrangebreakout.md`
- Running code (already in Test; nothing vendored): `sleeves/milkman/intraday.py` (per-day setup engine), `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`.

## Configuration

- Universe: SPY only. Timeframe: 5-minute closes from 1-minute bars. Lanes: long (5-minute range, EMA/VWAP filter) and short (10-minute range, no filter). Size: $10,000 per trade on a $1,000,000 book.

## Data inputs

Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only (card).

## Install and run

1. Clone this repository (Test).
2. Import the Milkman intraday sleeves from `sleeves/milkman/intraday.py` and register the sleeve id for this strategy with the desk runtime.
3. Configure SPY 1-minute bars with the extended session, clock hours and daily bars as in the Data inputs.
4. Run the per-minute pass during the regular session.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist:

- A first 5-minute close above the 5-minute range with the 10-minute EMA8 at or below EMA21, or the close at or below VWAP, produces no long entry.
- A first 5-minute close beyond the applicable range (with the long filter passed) produces exactly one entry at that close.
- A touch of the range midpoint after entry exits the position; otherwise it is closed at the close.
