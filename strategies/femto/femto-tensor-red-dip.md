# Tensor red-dip buys on fear days

On a fear day (QQQ down 1.5%+ intraday), buys the flagship's fresh Tensor signals (confidence 7+) on names that are red too, and sells at +3%, -8% or after 3 days.

| | |
|---|---|
| **Family** | Femto-lean |
| **Source** | The old Alpaca swing desk, via Femto-lean |
| **Asset** | US equities |
| **Timeframe** | Intraday · 1h signals |
| **Universe** | 41-name old-desk basket |
| **Style** | Tensor signal + fear dip |
| **Status** | live |

## Entry

- Fear day: QQQ's live price ≤ -1.5% vs the prior close (unknown fails closed).
- Candidates: today's fresh flagship signals with confidence ≥ 7, one per name; bought while the name is red on the day; at most 5.

## Exit

- +3% target, -8% stop (engine-held from the fill), or the 3rd trading day.

## Sizing

- 0.25% of the book on the 8% stop, at least 1 share.
- Each sleeve trades its own $100,000 book unless its spec row names another.

## Data

- The Tensor swing flagship's fresh signals, live quotes, prior closes.

## Code

- **Master desk** (not in this repo): `desk/sleeves/femto/tensor_red_dip.py`, `desk/sleeves/femto/tensor_swing.py`
- **Midna v3**: `sleeves/tensor_red_dip.py`

## Notes

- Midna v3 adds an Edge-IMPROVE change (2026-10-24, on by default): the name itself must be down 1.5% or more, not just red.
