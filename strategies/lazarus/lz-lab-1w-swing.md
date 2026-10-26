# Lab 1W Swing covered

Buys the live lab's weekly Swing rule-search picks and holds 126 sessions.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath research lab (lab_live), run by Lazarus |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Lab panel names |
| **Style** | Model |
| **Status** | waiting |

## Entry

- Signal: a 1W-swing-covered lab fire from the rule search.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, time exit 126 sessions from the fill.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000, 1 slot.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- The lab's book outputs.

## Code

- **Midna v3**: `desk3/lazarus.py`, `integration/*_adapter.py`
- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`

## Notes

- Midna v3 reads fires from its Tensor bundle, keeps the QQQ-down entry gate on most lanes, uses a 15% stop on several, counts holds in sessions and buys at market with capital / slots.
