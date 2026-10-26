# Lab rule books (1D / 1W)

Buys fires of the lab's frozen clean-support rules and holds each for its rule's horizon.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath research lab (frozen rules), run by Lazarus |
| **Asset** | US equities |
| **Timeframe** | 1d · 1w |
| **Universe** | Lab panel names |
| **Style** | Rule set |
| **Status** | 2 live |

## Entry

- Signal: a lab fire that matches a frozen rule; the rule's horizon H (default 21 daily or 126 weekly).
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, time exit H + 1 sessions from the fill.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position: 1D 73 slots / $73,616; 1W 1 slot.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- The lab's book outputs and frozen rule ids.

## Variants

| Lane | Frame |
|---|---|
| `lz_rules_1d` | daily |
| `lz_rules_1w` | weekly |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/lazarus.py`, `integration/*_adapter.py`
- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`

## Notes

- Midna v3 reads fires from its Tensor bundle, keeps the QQQ-down entry gate on most lanes, uses a 15% stop on several, counts holds in sessions and buys at market with capital / slots.
