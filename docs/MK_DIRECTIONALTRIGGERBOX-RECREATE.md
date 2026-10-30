# mk-directionaltriggerbox: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Directional trigger box (SPY)", type breakout, family milkman, universe SPY, asset US ETF, timeframe 10m, creator "Milkman Trades, Trigger Box directional; the Milkman v2 study". Algorithm grade PARTIAL with entry, exit and sizing not in the accounting's consulted sources; the rules below are from the Test card and running Test code (`sleeves/milkman/intraday.py` TBOX row: mk_directionaltriggerbox, both sides, target=0.382).
- Test catalog entry `mk-directionaltriggerbox`: card `strategies/milkman/mk-directionaltriggerbox.md`, code as below, status waiting.
- Code search record: Searched for code: Test tree at batch start (sleeves/, strategies/, packages/, desk3/, engines/) - found as listed below; Silicon tree (research/, desk trees) and quant-research-backup tree and Midna tree - no additional code file for this canonical id was found in those trees (tree grep for the id, alias and card slug).

## What this strategy is

When SPY opens between the prior close and a trigger and holds that box for the first hour, trades the first 10-minute close through the trigger toward 38.2% (card summary).

## Full algorithm

Evaluation order, from the card and the trigger-box branch in `sleeves/milkman/intraday.py`:

1. Levels: the prior regular session's close plus/minus x times its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate target, then 0.5, 0.618, 0.786, 1.0.
2. Setup: the open is between the prior close and the +/-0.236 trigger on one side; every 10-minute close of the first hour stays inside that box.
3. Entry: the first 10-minute close beyond the trigger, at that close, in the direction of the break.
4. Exit: target at +/-0.382; stop on a 10-minute close back beyond the trigger; otherwise out at the close.
5. Common Milkman execution (card, all three SPY intraday strategies): each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close; $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Files in this repo

- This package: `docs/MK_DIRECTIONALTRIGGERBOX-RECREATE.md`
- Strategy card: `strategies/milkman/mk-directionaltriggerbox.md`
- Running code (already in Test; nothing vendored): `sleeves/milkman/intraday.py` (per-day setup engine), `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`.

## Configuration

- Universe: SPY only. Timeframe: 10-minute closes built from 1-minute bars. Size: $10,000 per trade on a $1,000,000 book.

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

- If any 10-minute close in the first hour leaves the box, no trigger-box entry occurs that day on that side.
- The first 10-minute close beyond the trigger after a held box produces exactly one entry at that close.
- A 10-minute close back beyond the trigger exits at the stop rule; reaching +/-0.382 exits at target; otherwise the position is closed at the close via the 12-minutes-before-close market-on-close order.
