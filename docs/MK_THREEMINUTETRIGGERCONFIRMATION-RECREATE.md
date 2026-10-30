# mk-threeminutetriggerconfirmation: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Three-minute trigger confirmation (SPY)", type breakout, family milkman, universe SPY, asset US ETF, timeframe 3m, creator "Milkman Trades, 3-Minute Close; the Milkman v2 study". Algorithm grade PARTIAL with entry, exit and sizing not in the accounting's consulted sources; the rules below are from the Test card and running Test code (`sleeves/milkman/intraday.py` CT3 row: mk_threeminutetriggerconfirmation, both sides, target=0.382; the code branch is annotated 3-minute trigger confirmation).
- Test catalog entry `mk-threeminutetriggerconfirmation`: card `strategies/milkman/mk-threeminutetriggerconfirmation.md`, code as below, status waiting.
- Code search record: Searched for code: Test tree at batch start (sleeves/, strategies/, packages/, desk3/, engines/) - found as listed below; Silicon tree (research/, desk trees) and quant-research-backup tree and Midna tree - no additional code file for this canonical id was found in those trees (tree grep for the id, alias and card slug).

## What this strategy is

When SPY opens inside its +/-23.6% triggers, trades the first 3-minute close beyond a trigger toward 38.2% (card summary).

## Full algorithm

Evaluation order, from the card and the CT3 branch in `sleeves/milkman/intraday.py`:

1. Levels: the prior regular session's close plus/minus x times its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate target, then 0.5, 0.618, 0.786, 1.0.
2. Setup: the open is between the two +/-0.236 triggers.
3. Entry: the first 3-minute close beyond one trigger, at that close (each side once per day).
4. Exit: target at +/-0.382; stop on a 3-minute close back beyond the trigger; otherwise out at the close.
5. Common Milkman execution (card, all three SPY intraday strategies): each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close; $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Files in this repo

- This package: `docs/MK_THREEMINUTETRIGGERCONFIRMATION-RECREATE.md`
- Strategy card: `strategies/milkman/mk-threeminutetriggerconfirmation.md`
- Running code (already in Test; nothing vendored): `sleeves/milkman/intraday.py` (per-day setup engine), `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`.

## Configuration

- Universe: SPY only. Timeframe: 3-minute closes built from 1-minute bars. Size: $10,000 per trade on a $1,000,000 book. Each side at most once per day (card).

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

- An open outside the +/-0.236 triggers produces no CT3 entry that day.
- The first 3-minute close beyond a trigger produces exactly one entry on that side at that close; a second break on the same side produces none.
- A 3-minute close back beyond the trigger exits; reaching +/-0.382 exits at target; otherwise the position is closed at the close.
