# Daily Green turn-of-month rule

Buys daily Tensor Green fires with strong 12-1 momentum and calm dispersion on a turn-of-month day, and holds 63 sessions.

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

- A daily green fire with 12-1 momentum ≥ 0.65, dispersion 0.0208-0.0286 and a turn-of-month day (the last trading day or the first 3 of the month, NYSE calendar); close ≥ $5, 20-day dollar volume ≥ $1M.
- Candidates come from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; fires on each name's last bar). It ranks after the close; buys go market-on-close the next session through the fill law.

## Exit

- Hold 63 sessions; no stop.
- Sold once the hold minus one bar has closed after entry; backstop = hold × 1.45 + 3 days.

## Sizing

- Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions.
- Cost modeled at 10 bps a side.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- The nightly DCG scoring file, split-adjusted daily bars (200), desk quotes.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/rule_1d_green_tom.py`, `desk/sleeves/femto/dcg_core.py`
- **Midna v3**: `sleeves/rule_1d_green_tom.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): the first-3-days branch needs the market's day list.
