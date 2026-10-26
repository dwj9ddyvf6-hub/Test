# Six short candidates

Six fade tests on 41 names: shorts strong late-day runs, extended closes, strong-close streaks and gaps at the high, and buys bearish RSI divergences on 30-minute bars.

| | |
|---|---|
| **Family** | Killed studies |
| **Source** | The old Alpaca swing desk's killed research studies, forward-tested on the master desk |
| **Asset** | US equities |
| **Timeframe** | 30m · 1d |
| **Universe** | 41-name old-desk basket |
| **Style** | Fade / short (research forward test) |
| **Status** | live |

## Entry

- C1: the return since 14:00 (live price over the 13:30 bar's close) in the name's top fifth of the last 252 days (≥ 63 days): short market-on-close; cover at the next close (a) or the next open (b).
- C2: the return since 15:00 in its top fifth: short market-on-close, cover at the next close.
- C3: the close in the top 5% of its 20-day range and above the 20-day mean + 1.5 ATR(14): short market-on-close; cover at the close 3 sessions later (a), or at the first touch of the 20-day mean (b).
- C4: two closes in a row in the top 20% of their day's range: short at the next open, cover at the close of the session after.
- C5: a gap up ≥ 2% opening within 2% of the 252-day high: short at the open; cover at the end of the first 30 minutes, or earlier at the prior close (a).
- C6: bearish regular RSI divergences, STRONG or SUPERSTRONG, on 30-minute bars, one per name per day: buy at the next pass, sell after 4, 8 or 16 bars.
- Orders: an open leg trades at the session's first pass (marketable); a close leg is market-on-close, sent 30-11 minutes before the close.

## Exit

- Each arm's exit above; touch exits trade at the market when the live price reaches the level.

## Sizing

- $1,000 per tranche (fractional shares long; shorts in whole shares, at least 1).

## Data

- Regular-session 30-minute bars (3,400), split-adjusted daily bars (260), live quotes.

## Code

- **Master desk**: `sleeves/killed/killed_studies.py`, `sleeves/killed/intraday.py`, `sleeves/killed/common.py`, `sleeves/femto/vendor/old_desk_research/rsiobv.py`

## Notes

- The master desk trades the short side; the old desk's long-only rail is dropped.
