# XSP weekly put credit spread

Each Monday, sells an XSP put spread an ATR below the prior close when the options market prices a low chance of a drop.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17/R18 options research |
| **Asset** | Index options |
| **Timeframe** | 1w |
| **Universe** | XSP (mini-SPX) |
| **Style** | Options income |
| **Status** | 4 waiting |

## Entry

- First session of the week, 10:00-10:05 ET.
- Regime: the current-week digital put price (from two adjacent puts) must be below the 75th percentile of the last 52 weeks; the calm books also need it below the median.
- Short strike near prior close - ATR14(weekly) × 1.0 (calm regime) or × 1.236; the long strike 5 points lower (calm) or at 1.618 / 1.786 ATR (graded).

## Exit

- Held to the weekly PM expiry and cash-settled.

## Sizing

- Contracts = min(NAV × 3% (A) or 1% (B) / max loss, cash / width, displayed sizes).

## Data

- XSP weekly index bars, OPRA XSP put chain and quotes.

## Variants

| Parameter | Values |
|---|---|
| Structure | calm (5-point wing) · graded (ATR wing) |
| Risk | A 3% · B 1% |

Rows: 4 on the master desk, 4 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_b4.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_options.py`
