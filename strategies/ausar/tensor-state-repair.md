# Tensor state repair (hourly / weekly)

Buys names whose seven Tensor vote channels have repaired by two or more points over three bars, and sells 20 bars later.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R11 Tensor state research |
| **Asset** | US equities |
| **Timeframe** | 1h · 1w |
| **Universe** | 1,820 hourly / 1,813 weekly names |
| **Style** | Momentum repair |
| **Status** | 2 waiting |

## Entry

- Full 7-vote panel now and 3 bars ago, vote balance up ≥ 2, ≥ 2 channels rising; close ≥ $5, 20-bar dollar volume ≥ $1M, ATR > 0; 20-bar cooldown.
- Ranked by repair + 0.01 × balance + 0.001 × clip(OBV slope / volume); bought at the next open.

## Exit

- Sells at the open 20 native bars after entry.

## Sizing

- floor(min(10% equity, 1% of 20-bar dollar volume, settled cash) / (price × 1.001)); 10 slots.

## Data

- Yahoo 1h / 1wk bars; Tensor v690 vote channels.

## Variants

| Row | Frame |
|---|---|
| ausar_h1state | 1h |
| ausar_wstate | 1w |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch1.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_ts/backend/tensor_strategy.py`, `desk/sleeves/families/tensor_state.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)
