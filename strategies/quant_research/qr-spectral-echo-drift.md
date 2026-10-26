# Spectral Echo Drift

Intraday longs in 20 Nasdaq leaders when returns lead top-of-book pressure with high spectral coherence, held up to 30 minutes.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | Spectral Echo Drift, a desk research package (core model) |
| **Asset** | US equities |
| **Timeframe** | 1m (from IEX quotes) |
| **Universe** | 20 Nasdaq leaders |
| **Style** | Order-book spectral |
| **Status** | blocked |

## Entry

- Tape: IEX top-of-book updates for AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, AVGO, AMD, NFLX, PLTR, MU, COST, INTC, QCOM, AMAT, ADBE, CSCO, PEP and LRCX, folded into minutes: the mid's open, high, low and close and the mean touch imbalance of every 12th update.
- Features: 1- and 3-minute mid returns over contiguous minutes, ATR(20) of the mid, the Katz fractal dimension of the last 32 closes, the latest confirmed fractal low; over the last 128 contiguous minutes, the coherence of imbalance and returns at the three strongest 2-20-minute peaks, the band's spectral entropy, and the lag (0-5 minutes) by which returns best lead imbalance changes.
- Signal: coherence > 0.82, a lag of 2-5 minutes with correlation ≥ 0.10, entropy falling two minutes running, imbalance > 0 and a positive 3-minute return, known before 15:50 ET; per minute the most coherent name.
- Gate: one position at a time; none after the day's loss reaches 1.2% of its starting NAV, or for a signal seen more than 3 minutes late.
- Order: an IOC limit at the ask of the first update at least 250 ms after the minute, refused when that update is more than 1 second late.

## Exit

- First of: the bid at or below the stop, coherence < 0.65, 30 minutes after the signal, 15:55 ET; sold at the market.

## Sizing

- $100,000 book: stop = max(the fractal low - 0.1 ATR, mid - (1 + 0.75 × (D - 1)) ATR) with D the fractal dimension; shares = min(0.4% of NAV / (ask - stop), 10% of NAV / ask, 5% of the displayed ask size).

## Data

- Alpaca's IEX quote stream for the 20 names (the session's tape plus the previous session's).

## Code

- **Master desk**: `sleeves/quant_research/sed.py`, `sleeves/quant_research/vendor/quant_research/sed/engine.py`, `sleeves/quant_research/common.py`
- **Rule lines**: [docs/verify/quant_research.md](../../docs/verify/quant_research.md)

## Notes

- This is the source's market-only core model; the social-attention gate is not computed.
