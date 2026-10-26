# Intraweek early entry

Buys a provisional weekly Cyan or Green marker on Monday to Thursday, before the week closes, and holds 52 weeks from the fire week.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath Research Lab frozen spec, wired on the master desk |
| **Asset** | US equities |
| **Timeframe** | 1w (daily entry) |
| **Universe** | Tracker universe |
| **Style** | Tensor signal |
| **Status** | live |

## Entry

- Signal: a provisional 1W marker on the developing week (day 1-4), one fire per symbol-week.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, exit at the close of the fire Friday + 52 weeks.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position; K = 20.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- Tracker Yahoo weeks plus the partial week from closed daily bars.

## Code

- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
- **Rule lines**: [docs/verify/lazarus.md](../../docs/verify/lazarus.md)
