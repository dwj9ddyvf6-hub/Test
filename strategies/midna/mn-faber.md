# Faber ETF trend

Holds each of five asset-class ETFs while it closes above its 10-month average.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | US ETFs |
| **Timeframe** | 1d (monthly average) |
| **Universe** | SPY, EFA, BND, VNQ, GSG |
| **Style** | Trend filter |
| **Status** | live |

## Entry

- Buys a fund whose last close is above the mean of the ten month-end closes before the current month.
- Acts on the session after the signal session, from 10:00 ET.

## Exit

- Sells a held fund that is no longer above its average.

## Sizing

- dollars = min(cash, equity / 5); whole shares at the ask.

## Data

- Yahoo daily closes, two years.

## Code

- **Midna v3**: `sleeves/s_mn_faber.py`
- **Master desk** (not in this repo): `desk/sleeves/midna/quantpedia.py`

## Notes

- Midna v3's `s_mn_faber` reads a different set (SPY, EFA, EEM, VNQ, AGG) with a 210-session average.
- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
