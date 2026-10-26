# Hourly Cyan range-expansion rule

Buys hourly Tensor Cyan fires on a wide-range bar with a strong WaveTrend gap while semis are up, and holds 7 hourly bars.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk's Daily Cyan GBM and GBM-rule research on its Tensor engine replica, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | 1h |
| **Universe** | 41-name old-desk basket |
| **Style** | Tensor signal + frozen rule |
| **Status** | waiting |

## Entry

- An hourly cyan fire on the latest closed regular-hours bar with range/ATR ≥ 2.05, WaveTrend gap ≥ 6.88 and SMH up; close ≥ $5; 20-day dollar volume ≥ $1M; 100+ hourly bars.
- Scans hourly at :26 and buys at the next :04 pass, 10:00-15:59 ET, through the fill law.

## Exit

- Sold 7 hourly bars after entry; backstop 2 days; no stop.

## Sizing

- Fill law: budget = 30% of the book less held and working notional, split over the staged buys; whole shares at a fresh mid plus cost, at least 1; at most 10 positions.
- Cost modeled at 10 bps a side.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- The hourly DCG fire file, regular-hours hourly bars (1,000), daily bars for dollar volume.

## Code

- **Master desk**: `sleeves/femto/sleeve_core.py`; not in this repo: `desk/sleeves/femto/rule_1h_cyan_raw.py`
- **Midna v3**: `sleeves/rule_1h_cyan_raw.py`
- **Rule lines**: [docs/verify/femto.md](../../docs/verify/femto.md)

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): a stop at the signal bar's low.
