# Location-first repair

Buys a washed-out stock still under its 50-day average when it sits on a support shelf with MACD lifting and RSI 28-52.

| | |
|---|---|
| **Family** | Sable |
| **Source** | Sable / Autopilot desk, Location-first Repair v2.1.0 |
| **Asset** | US equities |
| **Timeframe** | 1d (5-minute passes) |
| **Universe** | Sable catalog: 488 stocks (68 ETFs as context) |
| **Style** | Support pullback |
| **Status** | live |

## Entry

- Funnel: every stock's 6 months of daily closes; the 48 best under-50-day reads and the 48 best leaders-rest reads (plus SPY, QQQ) are re-read on 400 days of daily OHLC with today's forming bar and the live price.
- Out: price above the 50-day EMA, RSI(14) > 52, the 50-day EMA down > 1.5% over 10 sessions, under $3 with < $2M 20-day dollar volume, or earnings from 12 h before to 48 h ahead.
- Shelf: the 21-day EMA within 2%, the 12-day low within 4%, or a 50 / 61.8 / 78.6% retrace of the 60-day swing within 2.5%; the best by weight, confluence and distance; price ≤ 3% above it.
- Repair: RSI 28-52; the ATR-scaled MACD(12, 26, 9) histogram up in 2 of the last 3 sessions with a net lift; ≥ 8% under the 20-day high; today's low above the prior 11 sessions' low × 1.001; ≥ 20 bars with a real range.
- Grade: S_COIL (on the 21-day, RSI 40-52, MACD up all 3 steps from below zero) at score ≥ 80, or A_WASHOUT at ≥ 68, is a SETUP; the 6 best-scoring SETUP stocks are the hands.
- Buys each SETUP hand not held, not sold in the last 8 hours, while under 6 positions (working buys count), in the regular session; free slots fill in the catalog's order.
- Orders: marketable limits (1% through the quote), good for an hour; a working buy is cancelled once its name leaves the hands.

## Exit

- Stop at fill - 1.6 × ATR, target at fill + 2.8 × ATR (daily ATR(14), at least 1.5% of the fill; both widen if ATR grows), checked on the quote every 5 minutes.
- Time stop: after 15 days if the position is not in profit.

## Sizing

- min(0.5% of equity / (1.6 × ATR), 15% of equity, 98% of cash) in whole shares; a $100,000 book.

## Data

- Yahoo spark daily closes (6 months); split-adjusted daily bars with today's forming bar; live quotes; the Nasdaq earnings calendar.

## Code

- **Master desk**: `sleeves/sable/sable.py`, `sleeves/sable/location_first.py`, `sleeves/sable/runtime.py`
- **Rule lines**: [docs/verify/sable.md](../../docs/verify/sable.md)

## Notes

- ETFs are read as context and never bought.
- Not carried over: the desk pause and 2% daily-loss park, the Edge overlay and the Tensor SELL veto.
- The source's breakeven move at +1R is reset by the stop floor on every pass, so it never fires.
