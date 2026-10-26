# Anna seven-vote printer

Holds each of 13 names while Galath's seven-vote Anna printer reads buy, and sells when it turns sell or the 200-day EMA is lost.

| | |
|---|---|
| **Family** | Galath / GrokBot |
| **Source** | Galath's Tensor dashboard: the Anna printer (anna-replica, before Tensor 2.0) |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 13-name dashboard watchlist (SATL, SKYQ, RDW, INDI, SPY, QQQ, NVDA, MU, AAPL, AMD, TSLA, WULF, POET) |
| **Style** | Tensor signal |
| **Status** | live |

## Entry

- Seven daily votes: StochRSI K vs D, Aroon up vs down, +DI vs -DI, the 5-bar OBV slope, squeeze momentum, the 8- vs 21-day EMA, WaveTrend; the gate needs all 7, ≥ 5 bullish and bulls - bears ≥ 4.
- CYAN buy: the UT Bot (ATR 10) flips up with the gate. GREEN buy: the 8-day EMA crosses over the 21-day within 6 bars of a UT Bot up flip, with the gate.
- Buys at the next session's first pass while the signal is buy; names need 200 bars.

## Exit

- RED sell: the UT Bot flips down. MAGENTA: the 8-day EMA crosses under the 21-day within 6 bars of a UT Bot down flip. A sell wins a same-bar clash.
- A buy signal also ends when the close falls below the 200-day EMA.
- A sell within 2 bars of a buy flip is ignored while price is ≥ 94% of the 200-day EMA, unless the bar is a failed euphoria or an extended failure.
- Sold at the next session's first pass.

## Sizing

- An equal slot: equity / 13 per name.

## Data

- Split-adjusted daily bars (500 sessions), live quotes.

## Code

- **Master desk**: `sleeves/galath/galath.py`, `sleeves/galath/anna.py`
- **Rule lines**: [docs/verify/galath.md](../../docs/verify/galath.md)

## Notes

- Squeeze length 20, momentum 10 (14 / 9 before 2026-06-17).
