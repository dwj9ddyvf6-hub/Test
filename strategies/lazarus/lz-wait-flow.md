# FLOW short volume / FTD / dark pool

Buys small-cap daily Green fires priced $5-20 with heavy short-sale volume, and holds 60 sessions.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath Research Lab frozen spec, wired on the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Tracker universe, small band |
| **Style** | Flow |
| **Status** | blocked |

## Entry

- Signal: a tracker 1D Green fire, dv20 ≥ $100k, PIT band small, $5 ≤ close < $20, and the 5-file mean of FINRA short volume / total volume ≥ 0.447678 (files ≤ 7 days old).
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, exit at the close of D + 60.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position; K = 10.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- Tracker ledger; FINRA Reg SHO daily short-volume files.

## Code

- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
