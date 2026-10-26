# BOLT event tilt (SPY / QQQ)

A 50/50 SPY / QQQ book that records index-option bounds around FOMC and CPI releases; it tilts 25/75 either way only once 144 of its own events have matured and a ridge forecast clears its cost and confidence tests.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | BOLT, from the desk's ten-strategy repair review (R10) playbook |
| **Asset** | US ETFs (SPY, QQQ) |
| **Timeframe** | Event windows (about 10 sessions) |
| **Universe** | SPY, QQQ; SPX and NDX options as information |
| **Style** | Options-implied event tilt |
| **Status** | blocked |

## Entry

- Book: 50% SPY, 50% QQQ, bought at the first pass and left to drift; long only, no leverage.
- Events: FOMC statements (14:00 ET) and CPI releases (the BLS schedule); one is skipped when another FOMC, CPI or jobs release falls between 15:45 of its observation session and 09:35 of its exit session.
- Information: at 15:45 ET on the 5th session before the event and the session before that, for SPX (SPXW) and NDX (NDXP), the last expiry before and the first after the event (each within 4 sessions); two-sided calls with spreads ≤ 20% within ±10% of each expiry's put-call-parity forward (at least 9 strikes) bound the net up-crossing payoff (from at or below the forward to θ above it, less the reverse) for θ = 0.5%, 1% and 2%; the bounds, their widths and their changes make 36 features.
- Model: ridge (penalty 100) on the QQQ - SPY return over the event's entry and exit clocks, fitted on matured events; it needs 80 training, 40 calibration and 24 development events, every cost scenario (15, 30, 45 bp a side) leaving 0.25 × (|forecast| - 2 × cost) above 0.5%, and for a positive forecast its 95% lower bound above zero.
- Tilt: a positive forecast holds 25% SPY / 75% QQQ, a negative one 75% / 25%, from 09:35 of the session after the observation; one event at a time; off after a 25% drawdown.
- Orders: marketable limits 1% through the quote, each good for 30 minutes; sells first, buys once no sell is outstanding.

## Exit

- Back to 50/50 at 09:35 ET of the 5th session after the event.

## Sizing

- $1,000,000 book: weight × NAV at the ask, fractional shares, re-sized only when the weights change.

## Data

- SPX and NDX option chains (0-12 days) on the snapshot passes, the BLS CPI and jobs schedules (fetched each weekday morning), the desk's FOMC list and SPY / QQQ quotes.

## Code

- **Master desk**: `sleeves/quant_research/bolt.py`, `sleeves/quant_research/common.py`; not in this repo: `desk/vendor/quant_research/r10/bolt/`

## Notes

- Every event is recorded with its features and QQQ - SPY outcome, tilted or not: this is its training set.
