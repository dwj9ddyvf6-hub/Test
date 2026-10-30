# mk-bigdowndayresponse: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "Big down-day response", type mean reversion, family milkman, style evidence "Event reversal", universe "14 index ETFs and futures", asset "US index ETFs and futures", timeframe 1d, creator "Milkman Trades (milkmantrades.com), SPX -2% days; the Milkman v2 study". Test catalog entry `mk-bigdowndayresponse`, status live (2 rows). Algorithm grade PARTIAL with recorded gaps "entry/signal rule not recorded", "exit rule not recorded", "sizing not recorded". Merge evidence (Tier A): the Test catalog entry groups the rows `mk_bigdowndayresponse` (long) and `mk_bigdowndayresponse_short` (short); the accounting records the long row's variant as not recorded in any source and the short row's variant as "short".
- Test strategy card: `strategies/milkman/mk-bigdowndayresponse.md`. The card does record entry, exit and sizing (quoted below), and the running code in this repo (rule class `BIG` in `sleeves/milkman/rules.py`). The accounting gaps are gaps of the accounting pass, not of this repo's record.

## What this strategy is

An event-reversal sleeve: after an index instrument closes down 2% or more, it buys (the short row: shorts) at the close and exits 10 sessions later.

## Full algorithm

From the strategy card, in evaluation order:

1. Entry: a close at most 2% below the prior close (a close 2% or more down); enter at the close. The long row buys; the short row (`mk_bigdowndayresponse_short`) shorts the same event.
2. Exit: at the close 10 sessions later. No stop or target is recorded.
3. Sizing and execution conventions (card):
- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of a completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Files in this repo

- This package: `docs/MK_BIGDOWNDAYRESPONSE-RECREATE.md`
- Strategy card: `strategies/milkman/mk-bigdowndayresponse.md`
- Running code (already in Test; nothing vendored for this package): `sleeves/milkman/rules.py` (rule class `BIG`), `sleeves/milkman/daily.py`, `sleeves/milkman/vendored.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`
- Rule lines referenced by the card: `docs/verify/milkman.md`

## Configuration

- Universe: 14 index ETFs and futures (the index set in Data inputs). Timeframe 1d. Book $1,000,000, $10,000 per trade, every signal taken.
- Hold: 10 sessions. Variants: long row `mk_bigdowndayresponse`, short row `mk_bigdowndayresponse_short`.
- Session/cadence and state files: not in the record beyond the daily cadence and the card's execution conventions.

## Data inputs

Yahoo daily bars of the index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures), full history; live quotes for the session so far (card).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. The strategy runs inside the milkman daily sleeve package: the rule class named in Files, in `sleeves/milkman/rules.py`, driven by `sleeves/milkman/daily.py` with the vendored library under `sleeves/milkman/vendor/milkman/`.
3. Configure the cell for this strategy with the rule named in Files and the parameters in Configuration (the code defaults).
4. Feed the daily bars described in Data inputs and run the daily driver; it emits enter/exit events at the close per the algorithm above.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A close exactly 2% below the prior close triggers an entry at that close; a close 1.9% down does not.
- The position exits at the close of the 10th session after entry, with no earlier stop or target exit.
- The short row mirrors the long row on the same event.
- Each signal takes $10,000 on the $1,000,000 book, netted per symbol across lanes.
