# Parallax

Scores four entry engines (drift, dislocation, compression, reclaim) against the sector's state and the market regime and buys an opportunity of 48 or more with engine-specific brackets; a paper lane also arms strong WAITs as stop-limits above the market.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith / Ledge desk, Parallax PX_1_3_0_EXACT (conditional lane PX_1_3_0_CHALLENGER) |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | SCOPE universe: 550 US names |
| **Style** | Multi-engine swing |
| **Status** | live |

## Entry

- Decision: once a trading day before the open (else at the session's first pass), on the last completed bars, through the source's orchestrator over the universe.
- Field: each sector ETF against SPY (10-, 20- and 126-day relative strength, its 126-day percentile among the sectors, the EMA 50 slope) reads WATERFALL, TURN, TROUGH or TREND; names outside the sector map read TURN; a WATERFALL or unreadable field gives no decision.
- Regime: across the universe, the median day, the share up over 20 days, the median ATR% and the spread of 20-day returns give PANIC, REFLEXIVE_REBOUND, HIGH_VOLATILITY_DELEVERAGING, ORDERLY_RISK_ON, NARROW_RISK_ON or RANGE_BOUND; the medians of 5-, 20- and 60-day returns are the benchmark.
- Engines, 0-100 on returns over that benchmark: DRIFT (20- and 60-day residuals, 20-day path efficiency, above EMA 50, not stretched), DISLOCATION (a 5-day shock against ATR, close location, RSI < 45, MACD turning up), COMPRESSION (a low 20-day range percentile near the 20-day high), RECLAIM (yesterday under the 20-day low, today back above it in the top 45% of the range); TREND allows drift or compression, TURN dislocation, reclaim or compression, TROUGH dislocation or reclaim; the field's own engine gets +6.
- BUY: opportunity = the engine score less penalties (ATR over 4%, thin or heavy volume, a large shock, a stretch over EMA 20) ≥ 48; relative volume ≥ 2.8 is AVOID; a PANIC or HIGH_VOLATILITY_DELEVERAGING regime or a TROUGH field is WAIT.
- Orders: DRIFT, RECLAIM, DISLOCATION a GTC limit at the decision close, armed 2 days; COMPRESSION a stop-limit at the 20-day high + 0.05 ATR (limit + 0.20 ATR), armed 7 days.
- Conditional paper lane: the 8 best WAITs a run of the challenger version with an allowed engine and score ≥ 70 arm stop-limits above the close (the trigger 0.20-0.35 ATR over it by engine, or the 20-day high + 0.05 ATR for compression; the limit at least 0.10 ATR higher), armed 3 days (compression 5).
- Delivery, every regular-session pass (15 minutes): a plan is dropped when the name is held or the ask is at or under its stop and waits while an entry works on the name; otherwise it goes in as a GTC order carrying its stop-loss and take-profit.

## Exit

- Brackets: DRIFT -1.5 / +2.5 ATR, RECLAIM -1.25 / +2.25 ATR, DISLOCATION -1.5 / +2.25 ATR; COMPRESSION a stop 0.25 ATR under the compression low and a target 2.5 × the risk; the conditional lane keeps those stops with a target 2.5 × the risk.

## Sizing

- Risk 0.35% (the conditional lane 0.5%) of equity / risk per share, within the strategy's 3% risk cap less its open and armed risk; per order ≤ 35% of equity and ≤ 98% of buying power; a held name is not added to; $100,000 book.

## Data

- Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys.

## Code

- **Master desk**: `sleeves/griffith/griffith.py`, `sleeves/griffith/vendor/griffith/strategy_system.py`, `sleeves/griffith/vendor/griffith/strategy_orchestrator.py`, `sleeves/griffith/vendor/griffith/strategy_execution.py`, `sleeves/griffith/feedlib/griffith.py`; not in this repo: `desk/vendor/griffith/config.json`

## Notes

- The 28 universe names mapped to XLB, XLC or XLY (among them AMZN, TSLA, META and GOOGL) get no Parallax decision: those ETFs are not on the tape.
- Only the bracket exits: the source's lifecycle exits (thesis break, a 15-session time exit, breakeven, trailing) are not carried.
