# Shen first-touch fade (SPY 0DTE)

Buys same-day SPY puts when price first touches a marked level with RSI(14) over 70, calls when under 30, with a +20% / -15% bracket, flat by 11:15.

| | |
|---|---|
| **Family** | Muse |
| **Source** | Shen Lao (@shentrades), his 10-step SPY 0DTE playbook |
| **Asset** | SPY options (0DTE) |
| **Timeframe** | 1m |
| **Universe** | SPY |
| **Style** | Level fade |
| **Status** | waiting |

## Entry

- Levels, fixed at 09:29:30: the prior session's high and low, today's premarket high and low, and the three whole dollars nearest the last premarket close; levels within $0.10 merge.
- Bias from that reference: above the prior high only puts, below the prior low only calls, otherwise both.
- First touch only: the first completed 1-minute bar reaching a level's ±$0.10 zone burns it; RSI(14) on that bar's close above 70 buys puts, below 30 calls, otherwise nothing.
- Contract: today's SPY expiry, strike nearest the touch bar's close, its quote two-sided, spread ≤ 5% of mid, ≤ 60 s old.
- Order: a limit at the mid, at the ask from 60 seconds, cancelled at 180 seconds or once price leaves the zone or RSI leaves its extreme; entries 09:30-11:10, one position at a time.

## Exit

- Take profit: a resting limit at 1.20 × the premium paid; stop: the first pass with the option's mid at or under 0.85 ×, sold at the mid.
- Flat at 11:15: a mid limit, then the bid, then market at 11:17.
- New entries end for the day once realized P&L reaches -1.80% or +2.40% of the slice.

## Sizing

- 4% of the $10,000 slice in premium, whole contracts, at least 1.
- The master desk sends no entry costing more than the slice's free cash.

## Data

- SPY 1-minute bars (2,400: the prior session, the premarket and today), today's SPY option chain with quotes, the sleeve's own fills.

## Code

- **Master desk**: `sleeves/muse/muse.py`; not in this repo: `desk/sleeves/muse/sleeves/shen_fade.py`. The same strategy file as `sleeves/femto/shen_fade.py`
- **Midna's Femto-lean book**: `sleeves/femto/shen_fade.py`

## Notes

- The ladder's middle step, mid plus half the spread, is the ask.
- On the master desk a re-priced entry for the same contract and size counts as the working order, so the first limit at the mid works until the 180-second cancel.
- Half days closing by 11:15 are skipped.
