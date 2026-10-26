# Tensor tracker lanes (1H / 1D / 1W)

Buys the tradeable fires of Galath's canonical Tensor v698 tracker on hourly, daily and weekly bars, and holds each to its calibrated plan.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath research (canonical Tensor v698 tracker), run by Lazarus |
| **Asset** | US equities |
| **Timeframe** | 1h · 1d · 1w |
| **Universe** | The tracker's canonical universe |
| **Style** | Tensor signal |
| **Status** | 5 live |

## Entry

- Signal: a tracker fire marked tradeable on the lane's timeframe, on Yahoo canonical bars, within the last 5 sessions.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: the tracker's calibrated hold (max bars) and stop for that fire.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- 1H: $1,725 a position, 30 slots, $51,750; 1D: $1,725, 5 slots, $8,625; 1W: $1,410, 14 slots, $17,877; dv20 floor $1M, cap 1% of dv20.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- Galath's tracker fire files (latest fires + 5-session log); Yahoo daily bars; desk quotes.

## Variants

| Lane | Entry window | Limit band | Hold counted from |
|---|---|---|---|
| 1h (`lz_1h`) | 30 min | 3% | plan |
| 1d (`lz_1d`) | 65 min | 5% | fill |
| 1w (`lz_1w`) | 65 min | 5% | plan |
| Midna 1D / 1W (`midna_hourly_1d`, `midna_hourly_1w`) | 65 min | 5% | plan; $1,000 positions |

Rows: 5 on the master desk, 4 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/lazarus.py`, `integration/*_adapter.py`
- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
- **Rule lines**: [docs/verify/lazarus.md](../../docs/verify/lazarus.md)

## Notes

- Midna v3 reads fires from its Tensor bundle, keeps the QQQ-down entry gate on most lanes, uses a 15% stop on several, counts holds in sessions and buys at market with capital / slots.
- The 1D and 1W lanes also run as Midna's own lanes on the same tracker fires (`midna_hourly_1d`, `midna_hourly_1w`), with $1,000 positions.
