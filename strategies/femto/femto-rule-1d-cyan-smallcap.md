# Daily Cyan small-cap rule

Buys daily Tensor Cyan fires on $5-10 small caps that pass a frozen two-feature rule, and holds 21 sessions.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk's Daily Cyan GBM and GBM-rule research on its Tensor engine replica, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 1,838-name genome |
| **Style** | Tensor signal + frozen rule |
| **Status** | waiting |

## Entry

- A daily cyan fire with the scorer's pxn = 2 and DI between -10.59 and 12.56; close $5-10, 20-day dollar volume ≥ $1M, EDGAR log market cap ≤ 9.38.
- Candidates come from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; fires on each name's last bar). It ranks after the close; buys go market-on-close the next session through the fill law.

## Exit

- Hold 21 sessions; no stop.
- Sold once the hold minus one bar has closed after entry; backstop = hold × 1.45 + 3 days.

## Sizing

- Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions.
- Cost modeled at 10 bps a side.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- The nightly DCG scoring file, split-adjusted daily bars (200), desk quotes.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/rule_1d_cyan_smallcap.py`, `desk/sleeves/femto/dcg_core.py`
- **Midna v3**: `sleeves/rule_1d_cyan_smallcap.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): a 25% disaster stop.
