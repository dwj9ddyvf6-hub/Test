# Small-cap high-beta beaten-down (52 weeks)

Each week, buys the qualifiers that are beaten down, small by dollar volume and 'high beta', and holds them 52 weeks.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | The old Alpaca swing desk's killed research studies, forward-tested on the master desk |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | The weekly M2 qualifier list |
| **Style** | Deep value (research forward test) |
| **Status** | waiting |

## Entry

- BEAT: the weekly close ≤ 80% of the 52-week high, or a 13-week return ≤ -20%.
- SMALL: the bottom third of the week's qualifiers by 52-week mean weekly dollar volume.
- HIBETA: the 52-week weekly beta > 1.2 (≥ 40 weeks).
- All three: bought at the next session's open.
- Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.

## Exit

- Sold market-on-close on the Friday 52 weeks later (the session before, on a holiday).

## Sizing

- $10,000 per name (fractional shares).

## Data

- The desk's weekly M2 qualifier file and merged weekly bars, SPY weekly.

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/smcap.py`, `sleeves/killed/common.py`, `sleeves/killed/feedlib/killed_data.py`, `sleeves/killed/vendor/midna_research/run_smcap_beta_52w.py`

## Notes

- The beta is computed as the study computed it: the slope of SPY's weekly returns on the stock's, so volatile names score low.
