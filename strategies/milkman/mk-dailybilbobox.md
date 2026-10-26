# Daily Bilbo Box

Boxes the first 5 days of a daily squeeze, buys a break above the box (shorts a break below) and trails the stop along the 50-day EMA.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), Daily Bilbo Boxes on Saty's compression; the Milkman v2 study |
| **Asset** | US equities, index ETFs and futures |
| **Timeframe** | 1d |
| **Universe** | 1,822 US stocks + 14 index ETFs and futures |
| **Style** | Volatility breakout |
| **Status** | live |

## Entry

- Squeeze (Saty's compression): the 21-day, 2-sd Bollinger band inside 2 × ATR(14) around EMA(21), not while the gap widens inside 1.854 × ATR.
- Box: the high and low of a squeeze's first 5 bars (fewer if it ends sooner), locked at the 5th bar or at its end.
- For 20 bars after the lock: buys when the high reaches the box high with the prior close above EMA(21) (short: the low through the box low, the prior close below EMA21), at max(open, box high); void once the other side is reached first.
- One trade at a time per symbol and side.
- Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3.

## Exit

- Stop at the box's other side, ratcheted each bar to the prior bar's EMA(50), never back; the entry bar stops only on a close through it; out after 250 bars.

## Sizing

- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Data

- Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far.

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)

## Notes

- Femto-lean's [Phase compression breakout](../femto/femto-phase-daily.md) trades this box long only, with a nowcast arm and earnings exits.
