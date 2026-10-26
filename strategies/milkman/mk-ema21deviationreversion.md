# EMA21 deviation reversion

Fades a close stretched k ATRs from its 21-day EMA and covers when price touches the EMA again, or after a set number of sessions.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), daily 21 EMA reversion draft; the Milkman v2 study |
| **Asset** | US equities, index ETFs and futures |
| **Timeframe** | 1d |
| **Universe** | 1,822 US stocks + 14 index ETFs and futures |
| **Style** | Mean reversion |
| **Status** | live |

## Entry

- Deviation = (close - EMA21) / ATR(14); long when it first reaches -k or below (short: +k or above), at the close; ≥ 30 bars.
- One trade at a time per symbol and lane.
- Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3.

## Exit

- At a touch of the prior bar's EMA21 (or the open beyond it), else at the close after the hold.

## Sizing

- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Data

- Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far.

## Variants

| Lane | k (ATRs) | Max hold |
|---|---|---|
| Stocks, long | 2.0 | 10 sessions |
| Stocks, short | 4.0 | 20 sessions |
| Index set, long | 3.5 | 28 sessions |
| Index set, short | 4.0 | 10 sessions |

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
