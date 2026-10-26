# Weekday open-to-close (Monday)

Buys (the short row: shorts) each index instrument at Monday's open and exits at Monday's close.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | Milkman Trades (milkmantrades.com), ES Monday; the Milkman v2 study |
| **Asset** | US index ETFs and futures |
| **Timeframe** | 1d |
| **Universe** | 14 index ETFs and futures |
| **Style** | Calendar |
| **Status** | 2 waiting |

## Entry

- Every Monday: enters at the open of each of the 14 index instruments.

## Exit

- Out at that session's close, market-on-close.

## Sizing

- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Data

- Yahoo daily bars of the index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures), full history; live quotes for the session so far.

## Variants

| Row | Side |
|---|---|
| `mk_weekdayopentocloseproxy` | long |
| `mk_weekdayopentocloseproxy_short` | short |

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)
