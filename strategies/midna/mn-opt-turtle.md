# Listed Turtle ATM call

Expresses Turtle breakouts as one at-the-money call about 30 days out.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | Equity options |
| **Timeframe** | 1d |
| **Universe** | Midna's listed surface set |
| **Style** | Breakout (options) |
| **Status** | waiting |

## Entry

- On a 20- or 55-day breakout: the expiry nearest 30 days (14-60) and the strike nearest spot; ask ≥ $0.20, spread ≤ 50% of mid; at most 4 open.

## Exit

- Closed when the stock trades at or under last - 2 × ATR20, on the 10-day low exit, or at expiry.

## Sizing

- qty = floor(min(cash, 1% of equity) / (ask × 100)).

## Data

- Cboe delayed option chains; board signals.

## Code

- **Midna v3**: `sleeves/s_mn_opt_turtle.py`. Its `laz8_opt` helper is not in this repo
- **Master desk** (not in this repo): `desk/sleeves/midna/options.py`
- **Rule lines**: [docs/verify/midna.md](../../docs/verify/midna.md)

## Notes

- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
