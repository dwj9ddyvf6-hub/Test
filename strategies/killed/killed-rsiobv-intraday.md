# RSI × OBV intraday (5-minute)

Buys a strong bullish RSI divergence on 5-minute bars of 8 names and holds it 2, 4 or 8 hours.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | The old Alpaca swing desk's killed RSI × OBV 5-minute bucket (an @PredictionAlgos method), forward-tested |
| **Asset** | US equities |
| **Timeframe** | 5m |
| **Universe** | MU, ARM, SNDK, WDC, CLS, ANF, CVNA, FFIV |
| **Style** | Divergence (research forward test) |
| **Status** | live |

## Entry

- Divergence: two price pivots 5-60 bars apart that RSI (8 / 13 / 21) disagrees with (bullish regular: a lower low on a higher RSI low; bearish regular the mirror); STRONG at an RSI under 32 (over 68), SUPERSTRONG under 27 (over 73).
- Bullish regular RSI divergences, STRONG or SUPERSTRONG, on the last 600 5-minute bars; one per name per 24 h; bought at the next regular-session pass.
- Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.

## Exit

- Three tranches sell after 24, 48 and 96 bars past the signal bar.

## Sizing

- $100,000 / 24 per tranche (fractional shares).

## Data

- 5-minute bars (600).

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/intraday.py`, `sleeves/killed/common.py`, `sleeves/femto/vendor/old_desk_research/rsiobv.py`
- **Rule lines**: [docs/verify/killed.md](../../docs/verify/killed.md)
