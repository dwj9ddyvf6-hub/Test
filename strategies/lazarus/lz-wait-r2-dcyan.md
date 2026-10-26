# R2 Daily Cyan extended

Buys the lab's 1D Cyan covered rule-search book picks on the tracker universe and holds 21 sessions.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath Research Lab frozen spec, wired on the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Tracker universe |
| **Style** | Tensor signal + rules |
| **Status** | live |

## Entry

- Signal: a 1D-cyan-covered rule-search fire from the live lab.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, 21 sessions from the fill.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position; K = min(20, ⌈20 × 21 / 126⌉) = 4.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- The lab's book outputs.

## Code

- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
