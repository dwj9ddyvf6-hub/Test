# mk-pivotribbon1348cross: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Pivot Ribbon 13/48 cross", type trend following, family milkman, Test catalog entry `mk-pivotribbon1348cross`. Algorithm grade in the accounting: PARTIAL, with recorded gaps "entry/signal rule not recorded", "exit rule not recorded", "sizing not recorded". The accounting's cited source is the Test catalog entry itself.
- Test strategy card: `strategies/milkman/mk-pivotribbon1348cross.md`. The card does record entry, exit and sizing (quoted in the algorithm section below), and the running code in this repo (class `RIB` in `sleeves/milkman/rules.py`) confirms the card. The accounting gaps are therefore gaps of the accounting pass, not of this repo's record; both facts are stated here rather than merged silently.
- Creator per the card: "The Milkman v2 study, on Saty's Pivot Ribbon (its 13/48 conviction arrow)".

## What this strategy is

A daily trend-following cross system built on Saty's Pivot Ribbon 13/48 conviction arrow: it goes long when EMA(13) crosses above EMA(48), short when EMA(13) crosses below EMA(48), and exits on the opposite cross or after at most 120 sessions. Status in the Test catalog: live.

## Full algorithm

Evaluation order, from the strategy card (`strategies/milkman/mk-pivotribbon1348cross.md`) and confirmed against class `RIB` in `sleeves/milkman/rules.py`:

1. Indicators: EMA(13) and EMA(48) of the daily close (columns `e13` / `e48` in the engine). A name needs at least 60 bars before any entry (card: "at least 60 bars"; code: entries only when `t >= 60`).
2. Liquidity filter for stocks: a stock trades only while its 20-day mean dollar volume is at least $5M and the close is at least $3 (the `liq` column gate in the code).
3. Entry (at the close): long when EMA(13) crosses above EMA(48) on this bar (`e13 > e48` now and not on the prior bar); short when EMA(13) crosses below EMA(48).
4. Exit (at the close): exit on the opposite cross, or when the holding reaches the cap of 120 sessions (`cap`, default 120 in the code), whichever comes first.
5. Execution conventions (card): close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of a completed bar trade at the next open.
6. Sizing (card): $10,000 per trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

Recorded variants: the accounting records only the base form (variant zero, alias `mk_pivotribbon1348cross`); no distinct variant is recorded.

## Files in this repo

- This package: `docs/MK_PIVOTRIBBON1348CROSS-RECREATE.md`
- Strategy card: `strategies/milkman/mk-pivotribbon1348cross.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/milkman/rules.py` (rule class `RIB`, section "9. Pivot Ribbon")
  - `sleeves/milkman/daily.py` (daily driver)
  - `sleeves/milkman/vendored.py`
  - `sleeves/milkman/vendor/milkman/dstrats.py`
  - `sleeves/milkman/vendor/milkman/dlib.py`
  - `sleeves/milkman/vendor/milkman/mlib.py`
- Rule lines referenced by the card: `docs/verify/milkman.md`

## Configuration

- Universe: 1,822 US stocks + 14 index ETFs and futures (card and accounting agree).
- Asset class: US equities, index ETFs and futures. Timeframe: 1d.
- Book: $1,000,000 with $10,000 per trade (card sizing section).
- Session/cadence and state files: not in the record beyond the daily cadence implied by the 1d timeframe and the card's execution conventions.

## Data inputs

Per the card: index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures) from Yahoo daily bars, full history; stocks from the desk's split-adjusted daily bars, at least 260 bars since 2016; live quotes for the session so far.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. The strategy runs inside the milkman daily sleeve package: rule class `RIB` in `sleeves/milkman/rules.py`, driven by `sleeves/milkman/daily.py` with the vendored library under `sleeves/milkman/vendor/milkman/`.
3. Configure the cell for this strategy with the Pivot Ribbon rule (`RIB`), exit mode opposite-cross, and the session cap 120 (the code defaults: `cap` 120, entries from bar 60, liquidity gate on).
4. Feed the daily bars described in Data inputs and run the daily driver; it emits enter/exit events at the close per the algorithm above.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A synthetic series where EMA(13) crosses above EMA(48) at bar t (t at least 60, liquidity gate passing) produces exactly one long entry at bar t's close, and none before bar 60.
- The position exits at the close of the first opposite cross, or at entry bar + 120 sessions if no opposite cross occurs.
- A mirrored falling series produces the short entry on the downward cross and the symmetric exit.
- A stock whose 20-day mean dollar volume is under $5M, or whose close is under $3, produces no entry.
