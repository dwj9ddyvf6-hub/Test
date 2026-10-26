# O'Neil follow-through-day race

After a 10% correction, a follow-through day (day 4+ of a rally, up 1.25% on rising volume) starts a race: the long row targets the same distance up, the short row the correction low.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | William O'Neil's follow-through day, as coded by the Milkman v2 study |
| **Asset** | US index ETFs and futures |
| **Timeframe** | 1d |
| **Universe** | 14 index ETFs and futures |
| **Style** | Market-timing breakout |
| **Status** | 2 waiting |

## Entry

- Correction: a close 10% under the highest close of the last 63; the lowest low since is the correction low.
- Rally: the first up close is day 1; a low under day 1's low restarts the count; from day 4, a close up ≥ 1.25% on higher volume than the day before is the follow-through day; enters at its close.
- A close back within 0.1% of the 63-day high resets it.

## Exit

- Long: target close + (close - correction low), stop the correction low. Short: target the correction low, stop close + the same distance. From the next bar, stop first; else out at the close after 120 sessions.

## Sizing

- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.
- Futures lanes trade on a simulated venue quoted from Yahoo, or are only recorded where that venue has no quote.

## Data

- Yahoo daily bars of the index set (SPY, QQQ, IWM, DIA, XLK, XLF, XLE, SMH, TLT, GLD; ES, NQ, RTY, YM futures), full history; live quotes for the session so far.

## Variants

| Row | Side | Target | Stop |
|---|---|---|---|
| `mk_oneilfollowthroughdayrace` | long | close + distance | correction low |
| `mk_oneilfollowthroughdayrace_short` | short | correction low | close + distance |

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
- **Rule lines**: [docs/verify/milkman.md](../../docs/verify/milkman.md)
