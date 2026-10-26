# Weekly swing high-beta WaveTrend rule

Buys weekly Tensor swing fires on high-beta names with a strong WaveTrend and rising ribbons, and holds 126 sessions.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk's Daily Cyan GBM and GBM-rule research on its Tensor engine replica, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | 1,838-name genome |
| **Style** | Tensor signal + frozen rule |
| **Status** | waiting |

## Entry

- A weekly swing fire with beta to SPY ≥ 1.355, WaveTrend wt1 ≥ 25.93 and ribbons ≥ 0.0095; close ≥ $5, 20-day dollar volume ≥ $1M.
- Candidates come from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; fires on each name's last bar). It ranks after the close; buys go market-on-close the next session through the fill law.

## Exit

- Hold 126 sessions; no stop.
- Sold once the hold minus one bar has closed after entry; backstop = hold × 1.45 + 3 days.

## Sizing

- Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions.
- Cost modeled at 10 bps a side.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- The nightly DCG scoring file, split-adjusted daily bars (200), desk quotes.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/rule_1w_swing_beta_wt.py`, `desk/sleeves/femto/dcg_core.py`
- **Midna v3**: `sleeves/rule_1w_swing_beta_wt.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): each position is sized by its fire's beta.
