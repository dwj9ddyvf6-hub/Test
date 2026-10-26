# Pivot Ribbon 13/48 cross

Buys when EMA13 crosses above EMA48 (shorts the cross below) and exits on the opposite cross, at most 120 sessions.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | The Milkman v2 study, on Saty's Pivot Ribbon (its 13/48 conviction arrow) |
| **Asset** | US equities, index ETFs and futures |
| **Timeframe** | 1d |
| **Universe** | 1,822 US stocks + 14 index ETFs and futures |
| **Style** | Trend following |
| **Status** | live |

## Entry

- Long when EMA(13) crosses above EMA(48) (short: below), at the close; ≥ 60 bars.
- Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3.

## Exit

- At the opposite cross or after 120 sessions, at the close.

## Sizing

- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Data

- Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far.

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)
