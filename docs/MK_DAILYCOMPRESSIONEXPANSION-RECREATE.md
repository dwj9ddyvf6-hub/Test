# mk-dailycompressionexpansion: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Daily compression expansion", type volatility, family milkman. Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and the code in this repo (see Files).
- Test catalog entry `mk-dailycompressionexpansion` (`docs/CATALOG.json`): card `strategies/milkman/mk-dailycompressionexpansion.md`.
- Alias: `mk_dailycompressionexpansion`.

## What this strategy is

Enters at the next open when a daily squeeze of at least N bars releases in the direction of the EMA21/48 trend, and exits a set number of sessions later. Variants: Stocks long N=10 H=5; stocks short N=5 H=20; index set long N=10 H=5; index set short N=3 H=10.

## Full algorithm

From `strategies/milkman/mk-dailycompressionexpansion.md` and the code in Files, in evaluation order:

1. Squeeze (Saty's compression): the 21-day, 2-sd Bollinger band inside 2 x ATR(14) around EMA(21), not while the gap widens inside 1.854 x ATR.
2. Signal (code class CEX in `sleeves/milkman/rules.py`, setup row CEX in `sleeves/milkman/daily.py`): the first bar out of a squeeze whose run length at the prior bar is at least N, with at least 60 bars of history, EMA(21) above EMA(48) for a long (below for a short), and the liquidity filter passing.
3. Lane parameters (minbars N, hold H): stocks long N=10, H=5; stocks short N=5, H=20; index set long N=10, H=5; index set short N=3, H=10. In the code these are the CEX cells: (index, long) minbars=10;H=5, (univ, long) minbars=10;H=5, (index, short) minbars=3;H=10, (univ, short) minbars=5;H=20.
4. Stocks trade only while their 20-day mean dollar volume is >= $5M and the close >= $3.
5. Entry: at the next open after the signal bar (the code queues the signal as next_open and enters at the following bar's open).
6. Exit: at the close H sessions after the signal bar (code: exit when t == signal index + H, at that bar's close). No stop is recorded for this strategy.
7. Execution / sizing: close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Files in this repo

- This doc: `docs/MK_DAILYCOMPRESSIONEXPANSION-RECREATE.md`
- Strategy card: `strategies/milkman/mk-dailycompressionexpansion.md`
- Code (already in Test): `sleeves/milkman/daily.py` (setup CEX), `sleeves/milkman/rules.py` (class CEX), `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- Rule lines: `docs/verify/milkman.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, tests/) was searched for the canonical id and alias; Silicon tree, quant-research-backup tree and Midna tree were also searched for the canonical id, its alias and family terms (milkman / compression). No code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test.

## Configuration

- Universe: 1,822 US stocks + 14 index ETFs and futures. Timeframe: 1d. Asset class: US equities, index ETFs and futures.
- Book: $1,000,000; $10,000 a trade, every signal taken; lanes net per symbol.
- Lane parameters are in algorithm step 3.

## Data inputs

- Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, >= 260 since 2016. Live quotes for the session so far.

## Install and run

1. Clone the Test repo.
2. Read `strategies/milkman/mk-dailycompressionexpansion.md` and the matching section of `docs/verify/milkman.md`.
3. Open the code files listed in Files and locate this strategy's setup row and rule implementation.
4. Provide the data inputs listed above.
5. Run on the cadence in Configuration and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- No signal unless the prior bar ends a squeeze run of at least the lane's N bars, at least 60 bars of history exist, and EMA(21) is on the lane's side of EMA(48).
- A stock signal is suppressed when 20-day mean dollar volume is under $5M or the close is under $3.
- Entry is at the open of the bar after the signal bar, never on the signal bar itself.
- Exit is at the close exactly H sessions after the signal bar, with H from the lane table, and no other exit fires.
