# R19 weekly Tensor C1 cyan ownership

Buys low-priced stocks with strong 60-session momentum on a weekly Tensor buy-cyan print and holds each for 52 weeks.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17/R18 Tensor research on the archived Galath v615 engine |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Frozen 1,838-name research cohort |
| **Style** | Momentum |
| **Status** | 9 waiting |

## Entry

- Weekly buy-cyan primary marker, close ≤ $5, 60-session return ≥ 31%, weekly volatility ≥ 0.07, 20-day dollar volume ≥ $2M.
- cool / hot cuts: ATR20/ATR60 ≤ 1 or > 1; all takes both.
- Buys at the open after the signal week, one session later in delay and reserve modes.

## Exit

- Sells 5 minutes before the close of the 52nd calendar week. No stop, no target.

## Sizing

- Ticket = $100,000 / 25 slots, whole shares; reserve mode funds tickets from a QQQ reserve.

## Data

- Raw SIP daily and weekly bars; archived Galath v615 Tensor engine.

## Variants

| Parameter | Values |
|---|---|
| Volatility cut | all · cool · hot |
| Capital mode | cash · delay · reserve |

Rows: 9 on the master desk, 9 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch13.py`, `desk3/aster_batch14.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_tensor.py`

## Notes

- Midna v3 reads Tensor v698 fires and sizes $400 tickets on a $10,000 slice.
