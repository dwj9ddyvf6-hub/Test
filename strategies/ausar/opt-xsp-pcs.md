# XSP weekly put credit spread

Each Monday, sells an XSP put spread an ATR below the prior close when the options market prices a low chance of a drop.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Milkman Trades' ATR premium spec; Ausar R17/R18 options research; the old swing desk via Femto-lean |
| **Asset** | Index options |
| **Timeframe** | 1w |
| **Universe** | XSP (mini-SPX) |
| **Style** | Options income |
| **Status** | 5 waiting |

## Entry

- First session of the week, 10:00-10:05 ET.
- Regime: the current-week digital put price (from two adjacent puts) must be below the 75th percentile of the last 52 weeks; the calm books also need it below the median.
- Short strike near prior close - ATR14(weekly) × 1.0 (calm regime) or × 1.236; the long strike 5 points lower (calm) or at 1.618 / 1.786 ATR (graded).

## Exit

- Held to the weekly PM expiry and cash-settled.
- Femto variant: no regime filter; short = prior weekly close - 1 × weekly ATR(14), long 5 points lower, this week's last expiry, credit > 0; held to settlement; a loss of 90% of the wing pauses entries 4 weeks.

## Sizing

- Contracts = min(NAV × 3% (A) or 1% (B) / max loss, cash / width, displayed sizes).
- Femto variant: 1 lot, only with book equity ≥ $37,000.

## Data

- XSP weekly index bars, OPRA XSP put chain and quotes.
- Femto variant: S&P 500 daily sessions / 10 (Yahoo), the desk's 0-7 DTE XSP put chain.

## Variants

| Variant | Rows | Regime filter | Wing | Size |
|---|---|---|---|---|
| Ausar calm A / B | `ausar_opt_xsp_calm_a`, `_calm_b`; Midna v3 `aster_xsp_pcs_calm_a`, `_calm_b` | digital put below median and 75th pct | 5 points | 3% / 1% of NAV at risk |
| Ausar graded A / B | `ausar_opt_xsp_graded_a`, `_graded_b`; Midna v3 `aster_xsp_pcs_graded_a`, `_graded_b` | digital put below 75th pct | 1.618 / 1.786 ATR | 3% / 1% of NAV at risk |
| Milkman spec (Femto-lean) | `femto_spx_premium`; Midna v3 `spx_premium` | none | 5 points | 1 lot; 4-week pause after a full loss |

Rows: 5 on the master desk, 5 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_b4.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_options.py`
- **Master desk (Femto-lean)** (not in this repo): `desk/sleeves/femto/spx_premium.py`
- **Midna v3 (Femto-lean)**: `sleeves/spx_premium.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)

## Notes

- Midna v3's `spx_premium` adds an Edge-IMPROVE change (2026-10-24, on by default): no entry when the credit is below a third of the spread's width.
