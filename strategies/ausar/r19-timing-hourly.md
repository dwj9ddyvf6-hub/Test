# R19 hourly confirmed swing

Buys a confirmed hourly Tensor swing signal with a defined stop and target.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17 hourly geometry research on the v625 engine |
| **Asset** | US equities |
| **Timeframe** | 1h |
| **Universe** | Frozen 42-name list |
| **Style** | Swing |
| **Status** | 2 live · 2 waiting |

## Entry

- v625 engine swing: confirmed, score ≥ 8, no bearish conflict, stop < close < target.
- A TRANSITION phenotype is skipped when the bar's body > 0.5 ATR or its range > 1.5 ATR.
- delay1 waits one bar and drops the signal if that bar touches the stop or target.

## Exit

- Stop (floor1 widens it to at least 1 ATR below entry), the engine's target, or 20 hourly bars.

## Sizing

- min(10% of $100,000, cash) and a 0.25% risk budget over the stop; 8 slots.

## Data

- IEX hourly bars (60+), the v625 Tensor engine.

## Variants

| Book | Stop floor | Delay |
|---|---|---|
| HOUR_FLOOR0_DELAY0 | engine stop | 0 |
| HOUR_FLOOR0_DELAY1 | engine stop | 1 bar |
| HOUR_FLOOR1_DELAY0 | ≥ 1 ATR | 0 |
| HOUR_FLOOR1_DELAY1 | ≥ 1 ATR | 1 bar |

Rows: 4 on the master desk, 4 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch15.py`. Waits on a `timing_signals` producer v3 does not yet have
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_timing.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)
