# Swing Golden Gate (monthly ATR)

When price opens the monthly Golden Gate (38.2% of the monthly ATR from last month's close), rests a stop entry at 61.8% and targets the full ATR, flat by month end.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), Swing GG; the Milkman v2 study |
| **Asset** | US equities, index ETFs and futures |
| **Timeframe** | 1d (monthly ATR levels) |
| **Universe** | 1,822 US stocks + 14 index ETFs and futures |
| **Style** | ATR levels |
| **Status** | live |

## Entry

- Levels from last month's close (PC) and the monthly ATR(14): gate PC ± 0.382 ATR, entry ± 0.618, target ± 1.0, stop PC.
- The month's first gate touch decides: it arms only with ≥ 4 sessions left in the month, the prior close on the other side of EMA(21) (below it for a long, above for a short) and the liquidity gate.
- Armed: a resting stop entry at the 61.8% level until the month's last session.

## Exit

- Target or stop by touch (on the entry bar the stop counts only on a close through it); otherwise flat at the month's last close.

## Sizing

- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Data

- Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far.

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)
