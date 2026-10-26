# Weekly Cyan momentum ADX rule

Buys weekly Tensor Cyan fires on thinner names with a 44%+ 126-day run and ADX ≥ 26, and holds 126 sessions.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk's Daily Cyan GBM and GBM-rule research on its Tensor engine replica, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | 1,838-name genome |
| **Style** | Tensor signal + frozen rule |
| **Status** | 1 live · 1 waiting |

## Entry

- A weekly cyan fire with log10 dollar volume ≤ 7.35, 126-day return ≥ 44.5% and ADX ≥ 25.8; close ≥ $5, 20-day dollar volume ≥ $1M.
- Candidates come from the nightly DCG scoring file (the Tensor engine replica and frozen scorers over the genome; fires on each name's last bar). It ranks after the close; buys go market-on-close the next session through the fill law.

## Exit

- Hold 126 sessions; no stop.
- Sold once the hold minus one bar has closed after entry; backstop = hold × 1.45 + 3 days.

## Sizing

- Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions.
- Cost modeled at 10 bps a side.
- Each sleeve trades its own $100,000 book unless its spec row names another.
- Midna's lab account: floor(($20,000 / 6) / (price × (1 + cost))); up to 6 hits; entry from 10:00 ET the next session.

## Data

- The nightly DCG scoring file, split-adjusted daily bars (200), desk quotes.

## Variants

| Variant | Rows | Thresholds | Size |
|---|---|---|---|
| Femto-lean | `femto_rule_1w_cyan_mom_adx`; Midna v3 `rule_1w_cyan_mom_adx` | 7.3503 / 0.4446 / 25.795 | fill law |
| Midna's forward lab (w-cyan-adx) | `midna_w_cyan_high_adx` | 7.35 / 0.445 / 25.8 | $20,000 account / 6 |

Rows: 2 on the master desk, 1 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/rule_1w_cyan_mom_adx.py`, `desk/sleeves/femto/dcg_core.py`
- **Master desk (Midna's lab account)**: `sleeves/midna/forward.py`, `sleeves/midna/forward_scan.py`
- **Midna v3**: `sleeves/rule_1w_cyan_mom_adx.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): a held name is sold once its 126-session return turns negative.
