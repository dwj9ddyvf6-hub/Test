# R19 causal overnight hold

When the 13:00-15:00 ET move ranks in the top fifth of its history, buys near the close and sells at the next open.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R18 overnight research |
| **Asset** | US equities |
| **Timeframe** | 30m |
| **Universe** | Frozen 42-name list |
| **Style** | Overnight |
| **Status** | 2 live |

## Entry

- The 13:00-15:00 ET return (closes of the 12:30 and 14:30 half-hour bars) ≥ the 80th percentile of the last 252 full sessions (at least 126).
- Buys 15:30-15:35 ET on full-length sessions.

## Exit

- Sells at the next session's open.

## Sizing

- min(10% of $100,000, cash), whole shares; 8 slots.

## Data

- IEX 30-minute regular-session bars.

## Variants

| Book | Cost per side |
|---|---|
| OVERNIGHT_5BP | 5 bps |
| OVERNIGHT_25BP | 25 bps |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch15.py`, `desk3/aster_batch16.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_timing.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)
