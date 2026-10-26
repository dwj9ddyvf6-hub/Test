# Support scanner (5-minute)

Buys a stock holding its completed 5-minute swing support, not stretched and with momentum intact.

| | |
|---|---|
| **Family** | Sable |
| **Source** | Sable / Autopilot desk, the legacy completed-bar support scanner |
| **Asset** | US equities |
| **Timeframe** | 5m |
| **Universe** | Sable catalog: 488 stocks |
| **Style** | Support bounce |
| **Status** | live |

## Entry

- Deep list: held names, the last scan's buy-side names, SPY / QQQ / IWM, then the best spark screen scores (near the 52-week or day low, down on the day) up to 36 names.
- Each gets a quote from the last 5 sessions' completed regular-hours 5-minute bars: support = the 64-bar low, ATR(14), RSI(14), the 12 / 26 EMA gap, VWAP; with the spark's 52-week range.
- Buy: a SETUP with price ≥ 99.5% of support and ≤ 1.6 ATR above it, RSI 38-68, EMA gap ≥ -0.15, below 88% of the 52-week range; stocks only.
- Hands: the first 6 buy-side rows, SETUPs first by score (improving momentum, a tight range, volume and the lowest 30% of the 52-week range add points).
- Buys each SETUP hand not held, not sold in the last 8 hours, while under 6 positions (working buys count), in the regular session; free slots fill in the catalog's order.
- Orders: marketable limits (1% through the quote), good for an hour; a working buy is cancelled once its name leaves the hands.

## Exit

- Stop at fill - 1.6 × ATR, target at fill + 2.8 × ATR (5-minute ATR(14), at least 1.5% of the fill: -2.4% / +4.2% at that floor), checked every 5 minutes.
- Time stop: after 15 days if the position is not in profit.

## Sizing

- min(0.5% of equity / (1.6 × ATR), 15% of equity, 98% of cash) in whole shares; a $100,000 book.

## Data

- Yahoo spark quotes (5-minute closes, day and 52-week range) and Yahoo 5-minute bars (last 5 sessions).

## Code

- **Master desk**: `sleeves/sable/sable.py`, `sleeves/sable/desk_scanner.py`, `sleeves/sable/runtime.py`
- **Rule lines**: [docs/verify/sable.md](../../docs/verify/sable.md)

## Notes

- No earnings filter: the 5-minute quotes carry no earnings flag.
- Tensor reads are not supplied, so the source's Tensor SELL veto and score badges are off.
- Breakeven at +1R: once the stop is moved to the entry price, it stays there (the owner's decision Q44, 2026-10-26). Before that, the stop floor reset it on every pass, so it never fired.
