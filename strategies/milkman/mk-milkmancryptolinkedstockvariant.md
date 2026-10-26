# Milkman daily rules on crypto-linked stocks

Runs nine of the study's daily rules, long and short, on 134 crypto-linked US stocks.

| | |
|---|---|
| **Family** | Milkman |
| **Source** | The Milkman v2 study's crypto variant, on Galath research's crypto-linked stock list |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 134 crypto-linked US stocks |
| **Style** | Rule basket |
| **Status** | live |

## Entry

- Rules: Connors Double 7 (7, SMA200), Legend's Buy Day overnight (3), Daily Bilbo Box (5, EMA50 trail), Swing and Multi-day Golden Gates, EMA21 deviation (2 ATR, 10 sessions), Phase Oscillator accumulation (20 sessions), Pivot Ribbon 13/48, compression expansion (10 bars, 5 sessions); each long and short.
- Names: the crypto-linked stock list's symbols among the 1,822 stocks (134).
- Stocks trade only while their 20-day mean dollar volume is ≥ $5M and the close ≥ $3.

## Exit

- Each rule exits by its own rule: a 7-day closing extreme, the next open, the EMA50 trail, a gate target, stop or period end, an EMA21 touch, a fixed hold, the opposite cross.

## Sizing

- Close rules are decided 15 to 11 minutes before the close on the bar so far and sent market-on-close; level touches trade at the market when seen; signals of the completed bar trade at the next open.
- $10,000 a trade on a $1,000,000 book, every signal taken; each lane keeps its own trades and the sleeve trades the net per symbol.

## Data

- The desk's split-adjusted daily bars (≥ 260 since 2016) and live quotes.

## Code

- **Master desk**: `sleeves/milkman/daily.py`, `sleeves/milkman/rules.py`, `sleeves/milkman/vendor/milkman/dstrats.py`, `sleeves/milkman/vendor/milkman/dlib.py`, `sleeves/milkman/vendor/milkman/mlib.py`, `sleeves/milkman/vendored.py`
