# R19 weekly Tensor beta M2 52-week cohort

Each week, buys the least-liquid third of high-beta stocks that print a qualifying Tensor buy signal after a drawdown, and holds 52 weeks.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17/R18 Tensor research on the v625 engine |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Frozen 1,838-name research cohort |
| **Style** | High-beta recovery |
| **Status** | blocked |

## Entry

- M2 label: weekly dollar volume ≥ $10M, relative volume 0.8-2, bullish votes ≥ bearish + 2, consensus buy; then a buy-green (13-week return ≥ 0) or buy-cyan print.
- Beaten down (close ≤ 80% of the 52-week high, or 13-week return ≤ -20%) and 52-week beta to SPY > 1.2.
- Takes only the bottom third of that week's qualifiers by 52-week dollar volume.

## Exit

- Sells at the close of the 52nd calendar week. No stop.

## Sizing

- Ticket = $100,000 / 25 slots, whole shares.

## Data

- 200+ weekly bars per name, SPY weekly bars, the v625 Tensor engine.

## Code

- **Midna v3**: `desk3/aster_batch13.py`. Reads the M2-qualified fires from its Tensor bundle
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_tensor.py`
