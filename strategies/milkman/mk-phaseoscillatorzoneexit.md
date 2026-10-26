# Phase Oscillator zone exit

Buys when the Phase Oscillator climbs back out of an oversold zone (shorts when it falls out of an overbought one) and holds a set number of sessions.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | The Milkman v2 study's doctrine signal, on Saty's Phase Oscillator |
| **Asset** | US equities, index ETFs and futures |
| **Timeframe** | 1d |
| **Universe** | 1,822 US stocks + 14 index ETFs and futures |
| **Style** | Oscillator reversal |
| **Status** | live |

## Entry

- Phase Oscillator = EMA(3) of (close - EMA21) / (3 × ATR14) × 100.
- Accumulation: crosses up through -61.8 (short: down through +61.8); extreme: through -100 (+100); at the close; ≥ 30 bars.
- Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3.

## Exit

- At the close after the hold.

## Sizing

- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Data

- Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far.

## Variants

| Lane | Zone | Hold |
|---|---|---|
| Stocks, long | accumulation (-61.8) | 20 sessions |
| Stocks, short | extreme (+100) | 20 sessions |
| Index set, long | extreme (-100) | 20 sessions |
| Index set, short | accumulation (+61.8) | 10 sessions |

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
