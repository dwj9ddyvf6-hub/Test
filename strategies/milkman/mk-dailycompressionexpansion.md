# Daily compression expansion

Enters at the next open when a daily squeeze of at least N bars releases in the direction of the EMA21/48 trend, and exits a set number of sessions later.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | The Milkman v2 study, on Saty's compression |
| **Asset** | US equities, index ETFs and futures |
| **Timeframe** | 1d |
| **Universe** | 1,822 US stocks + 14 index ETFs and futures |
| **Style** | Volatility breakout |
| **Status** | live |

## Entry

- Squeeze (Saty's compression): the 21-day, 2-sd Bollinger band inside 2 × ATR(14) around EMA(21), not while the gap widens inside 1.854 × ATR.
- Signal: the first bar out of a squeeze of ≥ N bars, with EMA(21) above EMA(48) for a long (below for a short); ≥ 60 bars.
- Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3.
- Enters at the next open.

## Exit

- At the close H sessions after the signal bar.

## Sizing

- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Data

- Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far.

## Variants

| Lane | Squeeze ≥ N bars | H |
|---|---|---|
| Stocks, long | 10 | 5 |
| Stocks, short | 5 | 20 |
| Index set, long | 10 | 5 |
| Index set, short | 3 | 10 |

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
