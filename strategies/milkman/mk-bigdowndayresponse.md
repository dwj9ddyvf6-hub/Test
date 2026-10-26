# Big down-day response

After an index instrument closes down 2% or more, buys (the short row: shorts) at the close and exits 10 sessions later.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), SPX -2% days; the Milkman v2 study |
| **Asset** | US index ETFs and futures |
| **Timeframe** | 1d |
| **Universe** | 14 index ETFs and futures |
| **Style** | Event reversal |
| **Status** | 2 live |

## Entry

- A close ≤ 2% below the prior close; enters at the close.

## Exit

- At the close 10 sessions later.

## Sizing

- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Data

- Yahoo daily bars of the index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures), full history; live quotes for the session so far.

## Variants

| Row | Side |
|---|---|
| `mk_bigdowndayresponse` | long |
| `mk_bigdowndayresponse_short` | short |

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
