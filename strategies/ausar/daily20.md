# Daily20 tree-model forecasts

Every 20 sessions per name, two frozen gradient-boosted models forecast 20-day excess return over QQQ; buys the top picks for 20 sessions.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R11/R12 Tensor daily research |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Fixed 1,815-name enrollment |
| **Style** | Model forecast |
| **Status** | 2 blocked |

## Entry

- Eligible on its 20-bar phase: close ≥ $5, 20-day dollar volume ≥ $1M, ATR > 0, 234+ bars.
- Selected when the model's forecast ≥ its frozen threshold; ranked by forecast; next open within 300 s; 10 slots.

## Exit

- Sells at the open 20 sessions after entry.

## Sizing

- floor(min(10% equity, 1% of 20-day dollar volume, cash) / (price × 1.001)).

## Data

- Yahoo daily bars; Tensor v690 engine features (Node).

## Variants

| Row | Model |
|---|---|
| ausar_daily20_price_volume | D20_PV (price-volume features) |
| ausar_daily20_tensor | D20_TENSOR (Tensor features) |

Rows: 2 on the master desk, 2 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch16.py`. Its model assets are not in this repo
- **Master desk** (not in this repo): `desk/vendor/ausar_tensor/tensor_daily_models.py`, `desk/sleeves/families/ausar_daily20.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)
