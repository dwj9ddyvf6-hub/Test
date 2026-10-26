# R19 10-minute EMA cloud reclaim

On an hourly uptrend, buys the first 10-minute bar that reclaims the EMA 5/12 cloud after a shallow dip, targeting the prior day's high.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17 intraday geometry research |
| **Asset** | US equities |
| **Timeframe** | 10m (1h bias) |
| **Universe** | Frozen 42-name list |
| **Style** | Intraday pullback |
| **Status** | 2 waiting |

## Entry

- Hourly bias: EMA34 > EMA50 on each of the last 3 hourly closes.
- A 10-minute bar dips into the EMA 5/12 cloud after a bar fully above it; within 3 bars and no deeper than 0.5 ATR below the cloud, a bar closes back above it with the EMA spread widening.
- Enters 09:50-15:30 ET only if the target (prior session high) is at least 2× the risk.

## Exit

- Stop at the dip's low - 0.1 ATR; target the prior session high; time exit after 100 minutes, by 15:50 ET at the latest.

## Sizing

- min(10% or 20% of $100,000 notional, cash) and a 0.25% or 0.5% risk budget over the stop; 8 slots.

## Data

- IEX 10-minute and hourly regular-session bars; prior daily high.

## Variants

| Book | Risk | Notional |
|---|---|---|
| CLOUD_BASE | 0.25% | 10% |
| CLOUD_AGGRESSIVE | 0.5% | 20% |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch15.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_timing.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)
