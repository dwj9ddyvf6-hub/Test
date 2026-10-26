# R19 weekly Tensor G4 green ownership

Buys cheap, deeply drawn-down stocks on a weekly Tensor buy-green print and holds each for 52 weeks.

| | |
|---|---|
| **Family** | Ausar |
| **Source** | Ausar R17/R18 Tensor research on the archived Galath v615 engine |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Frozen 1,838-name research cohort |
| **Style** | Value recovery |
| **Status** | 12 waiting |

## Entry

- Weekly buy-green primary marker, close ≤ $10, 60-week drawdown depth ≥ 70%, 60-session return ≥ 0, weekly volatility ≥ 0.09, 20-day dollar volume ≥ $2M.
- cool / hot cuts: ATR20/ATR60 ≤ 1 or > 1; all takes both.
- Buys at the open after the signal week (one session later in delay and reserve modes); red_timeout waits up to 5 sessions for a QQQ red day with the stock ≤ 1.02 × signal close.
- Needs ≥ 99% census and feature coverage; ranks by 20-day dollar volume; one position per issuer.

## Exit

- Sells 5 minutes before the close of the last session of the 52nd calendar week. No stop, no target.

## Sizing

- Ticket = $100,000 / slots (25 or 10 slots), whole shares, fees 30 / 15 / 10 bps by price.
- reserve mode parks idle cash in QQQ weekly and sells it to fund tickets.

## Data

- Raw SIP daily bars built into weekly bars, the archived Galath v615 Tensor engine (Node).

## Variants

| Parameter | Values |
|---|---|
| Volatility cut | all · cool · hot |
| Capital mode | cash · delay · reserve · red_timeout |
| Slots | 25 · 10 |

Rows: 12 on the master desk, 12 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/aster_batch14.py`, `desk3/aster_batch15.py`
- **Master desk** (not in this repo): `desk/vendor/ausar_r19/r19_tensor.py`, `desk/sleeves/families/r19_tensor.py`
- **Rule lines**: [docs/verify/ausar.md](../../docs/verify/ausar.md)

## Notes

- Midna v3 reads Tensor v698 fires from its Tensor bundle, sizes $400 or $1,000 tickets on a $10,000 slice, and models the 52-week exit as 260 sessions held.
