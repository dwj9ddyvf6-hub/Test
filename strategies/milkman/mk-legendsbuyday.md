# Legend's Buy Day

After a run of down days, buys the close and sells the next open (overnight leg), or buys the next open and sells its close (day leg).

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), Legend's Buy Day; the Milkman v2 study |
| **Asset** | US equities, index ETFs and futures |
| **Timeframe** | 1d |
| **Universe** | 1,822 US stocks + 14 index ETFs and futures · SPY |
| **Style** | Short-term mean reversion |
| **Status** | 1 live · 1 waiting |

## Entry

- Overnight leg: after exactly 3 lower closes in a row, buys at the close (short lane: after exactly 3 higher closes, shorts).
- Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3.
- Day leg (SPY, long only): after exactly 4 sessions that each made a lower low than the one before (the one before them did not), buys the next open if it is under the prior close + 0.15 × ATR (the mean of the last 20 daily ranges) and above the stop.

## Exit

- Overnight leg: sold at the next open.
- Day leg: stop one cent under the prior day's low; otherwise sold at that session's close.

## Sizing

- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Data

- Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far.

## Variants

| Row | Leg | Setup | Trade | Universe | Sides |
|---|---|---|---|---|---|
| `mk_legendsbuydaydailyproxy` | overnight | exactly 3 lower closes | close to next open | 1,822 stocks + 14 index instruments | long and short |
| `mk_legendsbuydaydayleg` | day | exactly 4 lower lows; open under prior close + 0.15 ATR | open to close, stop under the prior low | SPY | long |

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`

## Notes

- The day leg reads SPY's regular-session bars in place of ES's full sessions (his ATR and stop use full-session ranges).
