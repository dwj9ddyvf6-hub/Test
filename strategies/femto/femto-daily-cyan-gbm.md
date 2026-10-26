# Daily Cyan GBM

Buys fresh daily Tensor Cyan fires that a frozen gradient-boosted model scores in its top tier, and holds 21 sessions.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk's Daily Cyan GBM and GBM-rule research on its Tensor engine replica, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 1,838-name genome |
| **Style** | Tensor signal + frozen rule |
| **Status** | 1 live · 1 waiting |

## Entry

- A daily cyan fire with the frozen GBM score ≥ 0.00208; close ≥ $5 and 20-day dollar volume ≥ $1M; best score first. Midna's lab account uses the training 90th-percentile cut.
- Candidates come from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; fires on each name's last bar). It ranks after the close; buys go market-on-close the next session through the fill law.

## Exit

- Hold 21 sessions; a 25% disaster stop (Femto).
- Sold once the hold minus one bar has closed after entry; backstop = hold × 1.45 + 3 days.

## Sizing

- Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions.
- Cost modeled at 10 bps a side.
- Each sleeve trades its own $100,000 book unless its spec row names another.
- Midna's lab account: floor(($20,000 / 6) / (price × (1 + cost))); up to 6 hits; entry from 10:00 ET the next session.

## Data

- The nightly DCG scoring file, split-adjusted daily bars (200), desk quotes.

## Variants

| Variant | Rows | Score cut | Size |
|---|---|---|---|
| Femto-lean | `femto_daily_cyan_gbm`; Midna v3 `daily_cyan_gbm` | 0.00208 | fill law |
| Midna's forward lab | `midna_d_cyan_gbm` | training 90th percentile | $20,000 account / 6 |

Rows: 2 on the master desk, 1 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/daily_cyan_gbm.py`, `desk/sleeves/femto/dcg_core.py`
- **Master desk (Midna's lab account)**: `sleeves/midna/forward.py`, `sleeves/midna/forward_scan.py`
- **Midna v3**: `sleeves/daily_cyan_gbm.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): the cut is the session's own 90th percentile of scores.
