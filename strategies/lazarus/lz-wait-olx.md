# OLX R1/R2 books

Buys fires of 29 frozen OLX clean-support rules scored by the live lab, and holds each for its horizon.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath Research Lab frozen spec, wired on the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Lab panel names |
| **Style** | Rule set |
| **Status** | live |

## Entry

- Signal: a lab fire of one of the frozen OLX R1/R2 rule ids.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, exit after the rule's H sessions (H + 1 from the fill).
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position; K = 20.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- The lab's OLX job outputs.

## Code

- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
- **Rule lines**: [docs/verify/lazarus.md](../../docs/verify/lazarus.md)
