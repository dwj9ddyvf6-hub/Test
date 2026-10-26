# Hourly Tensor playbook

Buys first-of-setup hourly Tensor consensus-buy fires of the swing basket under the frozen playbook 1.0.0, with a no-stop variant.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | US equities |
| **Timeframe** | 1h |
| **Universe** | Midna's swing basket |
| **Style** | Tensor signal |
| **Status** | 2 live |

## Entry

- Fire: a gap20, first-of-setup 1H consensus buy; skipped when its unit matches a killed rule, it is not tradeable, or dv20 < $1M.
- Window: the next bar's open + 30 min (1D / 1W: 09:30 + 65 min); price within 3% (1H) or 5% of the fire close.

## Exit

- 1h-basket plan: no stop, time exit 60 bars; otherwise the calibrated stop and max bars.

## Sizing

- $100,000 account, 20 slots of min($5,000, 1% of dv20); lane caps 1h 5 / 1d 5 / 1w 10.

## Data

- The hourly watch's inbox (tensor-watch port).

## Variants

| Row | Plan |
|---|---|
| `midna_hourly_playbook` | playbook 1.0.0 |
| `midna_nostop` (Lazarus lane) | no stop, 60 hour bars, $1,000 × 2 |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `sleeves/lazarus/s_mn_hourly.py`, `sleeves/lazarus/s_mn_nostop.py`. They call `laz_sleeves._common`, which is not in this repo
- **Master desk**: `sleeves/midna/hourly.py`, `sleeves/midna/lanes.py`
