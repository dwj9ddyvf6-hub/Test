# Q14 under-$5 weekly book

Buys tier-A weekly Cyan or Green fires closing at or under $5, capped at $5.00, and holds 78 weeks.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath Research Lab frozen spec, wired on the master desk |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Tracker universe |
| **Style** | Value |
| **Status** | waiting |

## Entry

- Signal: a tracker 1W Cyan or Green fire with tier A and close ≤ $5.00; the entry limit is capped at $5.00.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, exit at the close of the 78th weekly bar.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position; K = min(20, ⌈20 × 390 / 126⌉) = 20 slots.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- Tracker ledger (1W fires, ue_tag tiers).

## Code

- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
