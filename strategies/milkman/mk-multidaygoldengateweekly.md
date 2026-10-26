# Multi-day Golden Gate (weekly ATR)

Enters when price opens the weekly Golden Gate (38.2% of the weekly ATR from last week's close) with the Phase Oscillator stretched the same way, targets 61.8%, flat by week end.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), Multi-day GG; the Milkman v2 study |
| **Asset** | US equities, index ETFs and futures |
| **Timeframe** | 1d (weekly ATR levels) |
| **Universe** | 1,822 US stocks + 14 index ETFs and futures |
| **Style** | ATR levels |
| **Status** | live |

## Entry

- Levels from last week's close (PC) and the weekly ATR(14): entry at the gate, PC ± 0.382 ATR; target ± 0.618; stop PC.
- The week's first gate touch decides: it trades only with the prior bar's Phase Oscillator above 61.8 (long) or below -61.8 (short) and the liquidity gate.
- Phase Oscillator = EMA(3) of (close - EMA21) / (3 × ATR14) × 100.

## Exit

- Target or stop by touch (on the entry bar the stop counts only on a close through it); otherwise flat at the week's last close.

## Sizing

- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Data

- Index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures): Yahoo daily bars, full history. Stocks: the desk's split-adjusted daily bars, ≥ 260 since 2016. Live quotes for the session so far.

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)
