# Weekly Cyan tier A

Buys weekly Tensor Cyan fires that rate tier A, split by market-cap band, and holds 52 weeks.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | Galath research (tracker sc_tag / ue_tag tiers), run by Lazarus |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Tracker universe by PIT SEC band |
| **Style** | Tensor signal |
| **Status** | 1 live · 2 waiting |

## Entry

- Signal: a tracker 1W Cyan fire whose tier is A: small band (core lane 1wa), micro band, or mid/large band (unified tier).
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, time exit 52 weeks.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000 a position: 1wa 17 slots / $17,250 (cap 5% dv20); micro 1 slot; mid/large 7 slots.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- Tracker ledger tags; PIT SEC shares for the band.

## Variants

| Lane | Band |
|---|---|
| `lz_1wa` | small (core) |
| `lz_1wc_micro` | micro |
| `lz_1wc_ml` | mid/large |

Rows: 3 on the master desk, 3 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/lazarus.py`, `integration/*_adapter.py`
- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`

## Notes

- Midna v3 reads fires from its Tensor bundle, keeps the QQQ-down entry gate on most lanes, uses a 15% stop on several, counts holds in sessions and buys at market with capital / slots.
