# Moonshot weekly lane

Buys cheap, deeply drawn-down weekly Cyan or Green fires and holds 52 weeks.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath research (MOONSHOT_FROZEN_SPEC v1.0), run by Lazarus |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Tracker universe |
| **Style** | Value recovery |
| **Status** | live |

## Entry

- Signal: a tracker 1W Cyan or Green fire with close ≤ $14.94, 60-week depth ≥ 70, dv20 ≥ $1M; tier A first on ties.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, time exit 52 weeks.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position, 2 slots, $2,581.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- Tracker ledger fires and ue_tag values.

## Code

- **Midna v3**: `desk3/lazarus.py`, `integration/*_adapter.py`
- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`

## Notes

- Midna v3 reads fires from its Tensor bundle, keeps the QQQ-down entry gate on most lanes, uses a 15% stop on several, counts holds in sessions and buys at market with capital / slots.
