# mk-connorsdouble7: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "Connors Double 7", type mean reversion, family milkman, style evidence "Mean reversion", universe "1,822 US stocks + 14 index ETFs and futures", asset "US equities, index ETFs and futures", timeframe 1d, creator "Larry Connors' Double 7, as coded by the Milkman v2 study". Test catalog entry `mk-connorsdouble7`, status live (1). Algorithm grade PARTIAL with recorded gaps "entry/signal rule not recorded", "exit rule not recorded", "sizing not recorded".
- Test strategy card: `strategies/milkman/mk-connorsdouble7.md`. The card does record entry, exit and sizing (quoted below), and the running code in this repo (rule class `D7` in `sleeves/milkman/rules.py`). The accounting gaps are gaps of the accounting pass, not of this repo's record.

## What this strategy is

Connors' Double 7 as a daily sleeve: buy a 7-day closing low above the 200-day average (short a 7-day closing high below it) and exit at the opposite 7-day closing extreme.

## Full algorithm

From the strategy card, in evaluation order:

1. Entry, long: the close is above its 200-day SMA and is the lowest of the last 7 closes; enter at the close. Entry, short: the close is below the SMA200 and is the highest of the last 7 closes; enter at the close.
2. One trade at a time per symbol and side.
3. Liquidity filter for stocks: a stock trades only while its 20-day mean dollar volume is at least $5M and the close is at least $3.
4. Exit: at the first close that is the highest of the last 7 (for a short: the lowest), or after 60 sessions, at the close.
5. Sizing and execution conventions (card):
- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of a completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Files in this repo

- This package: `docs/MK_CONNORSDOUBLE7-RECREATE.md`
- Strategy card: `strategies/milkman/mk-connorsdouble7.md`
- Running code (already in Test; nothing vendored for this package): `sleeves/milkman/rules.py` (rule class `D7`, non-overlapping), `sleeves/milkman/daily.py`, `sleeves/milkman/vendored.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`
- Rule lines referenced by the card: `docs/verify/milkman.md`

## Configuration

- Universe: 1,822 US stocks + 14 index ETFs and futures. Timeframe 1d. Book $1,000,000, $10,000 per trade, every signal taken.
- Trend filter SMA 200; extreme window 7 closes; maximum hold 60 sessions; one trade per symbol per side.
- Session/cadence and state files: not in the record beyond the daily cadence and the card's execution conventions.

## Data inputs

Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, at least 260 since 2016. Live quotes for the session so far (card).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. The strategy runs inside the milkman daily sleeve package: the rule class named in Files, in `sleeves/milkman/rules.py`, driven by `sleeves/milkman/daily.py` with the vendored library under `sleeves/milkman/vendor/milkman/`.
3. Configure the cell for this strategy with the rule named in Files and the parameters in Configuration (the code defaults).
4. Feed the daily bars described in Data inputs and run the daily driver; it emits enter/exit events at the close per the algorithm above.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A close that is the lowest of the last 7 closes but at or below the SMA200 produces no long entry; the same close above the SMA200 enters long at the close.
- A held long exits at the first close that is the highest of the last 7 closes, or at the close 60 sessions after entry if no such close occurs.
- The short side mirrors both rules below the SMA200.
- No second entry in the same symbol and side occurs while a trade is open; a stock under the $5M / $3 liquidity gate produces no entry.
