# Leaders Rest

Buys a market leader resting off its high (a 3-12% pullback or a tight base) with RSI 48-68, on a GTC limit at the prior close bracketed at -1.6 / +2.8 ATR.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith / Ledge desk, Leaders Rest LR_1_1_0_CORRECTED |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | SCOPE universe: 550 US names (SPY, QQQ, IWM and the sector ETFs excluded) |
| **Style** | Pullback in a leader |
| **Status** | live |

## Entry

- Decision: once a trading day before the open (else at the session's first pass), on the last completed bars, through the source's orchestrator over the universe.
- Leader: ≥ 253 sessions; price ≥ $10 or 20-day dollar volume ≥ $20M; within 25% of the 52-week high; EMA 50 rising over 10 sessions; 12-1 momentum above SPY's; price above EMA 50 (or above EMA 21 with EMA 50 rising); SPY not below a falling EMA 50, and SPY's 12-1 momentum not under -4% while SPY is under its EMA 200 or its EMA 50 is falling.
- SETUP: resting (3-12% under the 20-day high, or the last 15 days' range ≤ 60% of the prior 20 days' with 2-18% off the 52-week high) and RSI(14) 48-68.
- Order: a GTC buy limit at the decision close, armed 5 days.
- Delivery, every regular-session pass (15 minutes): a plan is dropped when the name is held or the ask is at or under its stop and waits while an entry works on the name; otherwise it goes in as a GTC order carrying its stop-loss and take-profit.

## Exit

- Bracket: stop at the limit - 1.6 ATR, target at the limit + 2.8 ATR (ATR(14), at least 1.5% of price).

## Sizing

- Risk 0.5% of equity / risk per share, within the strategy's 3% risk cap less its open and armed risk; per order ≤ 35% of equity and ≤ 98% of buying power; a held name is not added to; $100,000 book.

## Data

- Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys.

## Code

- **Master desk**: `sleeves/griffith/griffith.py`, `sleeves/griffith/vendor/griffith/strategy_system.py`, `sleeves/griffith/vendor/griffith/strategy_orchestrator.py`, `sleeves/griffith/vendor/griffith/strategy_execution.py`, `sleeves/griffith/feedlib/griffith.py`; not in this repo: `desk/vendor/griffith/config.json`

## Notes

- Only the bracket exits: the source's lifecycle exits (thesis break, a 15-session time exit, breakeven, trailing) are not carried.
