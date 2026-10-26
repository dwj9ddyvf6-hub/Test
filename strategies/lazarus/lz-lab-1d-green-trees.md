# Lab 1D Green trees

Buys the live lab's 1D Green boosted-trees picks and holds 21 sessions.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath research lab (lab_live), run by Lazarus |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Lab panel names |
| **Style** | Model |
| **Status** | live |

## Entry

- Signal: a 1D-green-full lab book fire picked by the boosted trees.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, time exit 21 sessions from the fill.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position, 8 slots, $8,320.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- The lab's book outputs.

## Code

- **Midna v3**: `desk3/lazarus.py`, `integration/*_adapter.py`
- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
- **Rule lines**: [docs/verify/lazarus.md](../../docs/verify/lazarus.md)

## Notes

- Midna v3 reads fires from its Tensor bundle, keeps the QQQ-down entry gate on most lanes, uses a 15% stop on several, counts holds in sessions and buys at market with capital / slots.
