# ChartsLector market-fear rebound (QQQ)

Buys QQQ when ChartsLector's VIX Mood Ring composite drops to 35 or lower, and sells 5 sessions later.

| | |
|---|---|
| **Family** | Lazarus |
| **Source** | ChartsLector (his VIX Mood Ring), via Lazarus |
| **Asset** | US ETF |
| **Timeframe** | 1d |
| **Universe** | QQQ |
| **Style** | Fear rebound |
| **Status** | waiting |

## Entry

- Composite = 0.35 VIX score + 0.25 term (VIX / VIX3M) + 0.25 SKEW + 0.15 VVIX, each scored 0-100; fire at ≤ 35 at the close, then a 5-session cooldown.
- Buys from the open of the bar after the fire, inside the lane's entry window, with a DAY limit at the live price + 1%, capped at the fire close + the lane's band; one position per symbol.

## Exit

- Plan: no stop, time exit 5 sessions.
- Time exit at the first pass from 20 minutes before the planned exit bar; a plan stop below 99% sells on the live price; exits are DAY limits at the live price - 1%.

## Sizing

- $1,000, 1 slot.
- Fixed dollars per position, capped by a share of 20-day dollar volume, whole shares, inside the lane's budget and slot count; names under the lane's dollar-volume floor are skipped.

## Data

- Cboe VIX, VIX3M, VVIX and SKEW daily files; QQQ daily bars.

## Code

- **Midna v3**: `desk3/lazarus.py`, `integration/*_adapter.py`
- **Master desk**: `sleeves/lazarus/lazarus.py`, `sleeves/lazarus/vendor/lazarus/`
- **Midna v3 (lane file)**: `sleeves/lazarus/s_cl_vmr_qqq.py`

## Notes

- Midna v3 reads fires from its Tensor bundle, keeps the QQQ-down entry gate on most lanes, uses a 15% stop on several, counts holds in sessions and buys at market with capital / slots.
- Midna v3's `s_cl_vmr_qqq` uses VIX ≤ 35 alone, not the composite.
