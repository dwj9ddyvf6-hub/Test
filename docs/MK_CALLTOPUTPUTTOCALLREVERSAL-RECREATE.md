# mk-calltoputputtocallreversal: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "Call-to-put reversal (SPY)", type mean reversion, family milkman, style evidence "Intraday reversal", universe SPY, asset US ETF, timeframe 1m, creator "Milkman Trades (milkmantrades.com), Call to Put reversal; the Milkman v2 study". Test catalog entry `mk-calltoputputtocallreversal`, status waiting (1). Algorithm grade PARTIAL with recorded gaps "entry/signal rule not recorded", "exit rule not recorded", "sizing not recorded".
- Test strategy card: `strategies/milkman/mk-calltoputputtocallreversal.md`. The card does record entry, exit and sizing (quoted below), and the running code in this repo (the `C2P` cell in `sleeves/milkman/intraday.py`, detector `detect21`). The accounting gaps are gaps of the accounting pass, not of this repo's record.

## What this strategy is

An intraday SPY reversal: before noon, after SPY tags one ATR trigger level and closes back through the prior close, it trades the run to the opposite trigger, targeting the 38.2% level.

## Full algorithm

From the strategy card, in evaluation order:

1. ATR levels: the prior regular session's close plus/minus x times its daily ATR(14); 0.236 is the trigger, 0.382 the Golden Gate, then 0.5, 0.618, 0.786, 1.0.
2. Entry, before 12:00 ET: the high reaches +0.236, then a close below the prior close, then the low reaches -0.236: short at min(open, trigger). The mirror (low reaches -0.236 first, a close above the prior close, then the high reaches +0.236) buys.
3. Exit: target at the opposite 0.382 level; stop on a 10-minute close back beyond the prior close; otherwise out at the close.
4. Execution and sizing (card): each minute the sleeve re-reads the session's completed 1-minute bars; a new trade enters at the market at the next pass (not if seen more than 2 bars late, or opened and closed inside one bar); open trades are closed by a market-on-close order 12 minutes before the close. $10,000 a trade on a $1,000,000 book, every trade taken; lanes and overlapping trades net on SPY.

## Files in this repo

- This package: `docs/MK_CALLTOPUTPUTTOCALLREVERSAL-RECREATE.md`
- Strategy card: `strategies/milkman/mk-calltoputputtocallreversal.md`
- Running code (already in Test; nothing vendored for this package): `sleeves/milkman/intraday.py` (cell `C2P`, mapped to `mk_calltoputputtocallreversal` with both sides at target=0.382; detector `detect21`), `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- Rule lines referenced by the card: `docs/verify/milkman.md`

## Configuration

- Universe: SPY only. Timeframe 1m. Book $1,000,000, $10,000 per trade.
- Levels: prior close plus/minus ATR(14) multiples 0.236 (trigger), 0.382 (target), 0.5, 0.618, 0.786, 1.0. Entry window: before 12:00 ET. Forced close: market-on-close 12 minutes before the close.
- Status in the Test catalog: waiting.

## Data inputs

Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only (card).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. The strategy runs inside the milkman intraday sleeve: cell `C2P` in `sleeves/milkman/intraday.py` with the vendored library `sleeves/milkman/vendor/milkman/mlib.py`.
3. Feed the SPY bars described in Data inputs; run the per-minute passes during the session.
4. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- The level set is computed from the prior regular session's close and its daily ATR(14) at the recorded multiples; no level uses the current session's ATR.
- The full three-step sequence (trigger tag, close back through the prior close, opposite trigger tag) before 12:00 ET produces exactly one trade at min(open, trigger) for the short form (mirrored for the long form); an incomplete or post-noon sequence produces none.
- The trade exits at the opposite 0.382 target, on a 10-minute close back beyond the prior close, or by the market-on-close order 12 minutes before the close, whichever comes first.
- A signal seen more than 2 bars late, or opened and closed inside one bar, is not taken.
