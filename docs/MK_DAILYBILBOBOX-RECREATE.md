# mk-dailybilbobox: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Daily Bilbo Box", type volatility, family milkman, style "Volatility breakout", universe "1,822 US stocks + 14 index ETFs and futures", asset class US equities, index ETFs and futures, timeframe "1d", creator "Milkman Trades (milkmantrades.com), Daily Bilbo Boxes on Saty's compression; the Milkman v2 study". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `mk-dailybilbobox` (`docs/CATALOG.json`): card `strategies/milkman/mk-dailybilbobox.md`.
- Alias: `mk_dailybilbobox`.

## What this strategy is

Boxes the first 5 days of a daily squeeze, buys a break above the box (shorts a break below) and trails the stop along the 50-day EMA. Note on the card: a related long-only desk sleeve trades this box with a nowcast arm and earnings exits; that sleeve is a different strategy and is not this package.

## Full algorithm

From `strategies/milkman/mk-dailybilbobox.md`, in evaluation order:

1. Squeeze (Saty's compression): the 21-day, 2-sd Bollinger band inside 2 x ATR(14) around EMA(21), not while the gap widens inside 1.854 x ATR.
2. Box: the high and low of a squeeze's first 5 bars (fewer if it ends sooner), locked at the 5th bar or at its end.
3. For 20 bars after the lock: buys when the high reaches the box high with the prior close above EMA(21) (short: the low through the box low, the prior close below EMA21), at max(open, box high); void once the other side is reached first.
4. One trade at a time per symbol and side.
5. Stocks trade only while their 20-day mean dollar volume is >= $5M and the close >= $3.
6. Exit: stop at the box's other side, ratcheted each bar to the prior bar's EMA(50), never back; the entry bar stops only on a close through it; out after 250 bars.
7. Execution / sizing: close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open. $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol. Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Files in this repo

- This doc: `docs/MK_DAILYBILBOBOX-RECREATE.md`
- Strategy card: `strategies/milkman/mk-dailybilbobox.md`
- Code (already in Test): `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- Rule lines: `docs/verify/milkman.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms (apex / bilbo). No distinct code for this strategy was found in Silicon, quant-research-backup or Midna; the code below is already in Test. Midna holds Milkman study / backtest material for the Bilbo family (a daily Bilbo backtest script and study texts), not the desk sleeve code above, which is already in Test; quant-research-backup holds a different intraday options sleeve with a similar name, not this daily sleeve.

## Configuration

- Universe: 1,822 US stocks + 14 index ETFs and futures. Timeframe: 1d. Asset class: US equities, index ETFs and futures.
- Book: $1,000,000; $10,000 a trade, every signal taken. One trade at a time per symbol and side; the sleeve trades the net per symbol.

## Data inputs

- Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, >= 260 since 2016. Live quotes for the session so far.

## Install and run

1. Clone the Test repo.
2. Read `strategies/milkman/mk-dailybilbobox.md` and the matching section of `docs/verify/milkman.md`.
3. Open `sleeves/milkman/daily.py` with `sleeves/milkman/rules.py` and the vendored Milkman modules in Files.
4. Provide the daily bars and live quotes listed above.
5. Run daily: form squeezes and boxes, watch the 20-bar break window, and manage the EMA(50) trailing stop. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- No box unless the squeeze test in step 1 holds; the box is the first 5 squeeze bars and locks at the 5th bar or at the squeeze's end.
- No entry after 20 bars from the lock, after the other side is reached first, or (for stocks) when 20-day mean dollar volume is under $5M or the close is under $3.
- Long entry requires the prior close above EMA(21) and fills at max(open, box high); the short is the mirror.
- The stop starts at the box's other side, ratchets only forward to the prior bar's EMA(50), and every position exits after 250 bars.
