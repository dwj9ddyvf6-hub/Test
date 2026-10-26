# RSI × OBV daily studies

Trades every arm of three RSI / OBV divergence studies on 19 names' daily bars, each held 5, 10 or 20 sessions.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | The old Alpaca swing desk's killed RSI × OBV studies (the scanner reconstructs an @PredictionAlgos video), forward-tested |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 19 names (MU, WDC, ANF, CLS, FFIV, AAOI, AXTI, SOXL, AEHR, FCEL, TTMI, SIMO, VICR, AG, SILJ, SPY, QQQ, NVDA, AAPL) |
| **Style** | Divergence (research forward test) |
| **Status** | live |

## Entry

- Divergence: two price pivots 5-60 bars apart that RSI (8 / 13 / 21) disagrees with (bullish regular: a lower low on a higher RSI low; bearish regular the mirror); STRONG at an RSI under 32 (over 68), SUPERSTRONG under 27 (over 73).
- Study A: four buckets per direction (all RSI, RSI and OBV agreeing over the same swings, strong regular RSI, RSI and OBV both in the top / bottom tenth of their 144-bar range), one signal per 20 bars; entry the next open, holds 5 / 10 / 20 sessions.
- Study B: regular RSI divergences confirmed by a trendline break (a close, a wick, or two closes) within 5 bars; entry the next open, holds 5 / 10 / 20.
- Study C: a strict 20-day closing high, alone or with RSI (8, 13 or 21) ≤ 30; long, out at the close 21 sessions after the signal.
- Bullish arms buy, bearish arms sell short.
- Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.

## Exit

- Each tranche sells or covers market-on-close at its hold.

## Sizing

- $100,000 / 150 per tranche (fractional shares long; shorts in whole shares, at least 1).

## Data

- Closed daily bars (520).

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/daily.py`, `sleeves/killed/common.py`, `sleeves/femto/vendor/old_desk_research/rsiobv.py`
- **Rule lines**: [docs/verify/killed.md](../../docs/verify/killed.md)

## Notes

- The master desk trades the short side; the old desk's long-only rail is dropped.
