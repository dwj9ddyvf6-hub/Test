# FinRL-X adaptive rotation

Each week splits a regime-set budget over the two strongest of three asset groups (growth tech, real assets, defensive), three names each, with a five-fund fallback.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | FinRL-X adaptive rotation (AI4Finance Foundation, FinRL-Trading), reconstructed in the desk's six-strategy study |
| **Asset** | US equities and ETFs |
| **Timeframe** | 1w |
| **Universe** | 21 stocks and ETFs in three groups, plus SPY and QQQ |
| **Style** | Regime-gated group rotation |
| **Status** | live |

## Entry

- Decision: once a week on the completed Friday close, the released FinRL-X engine and its v1.2.1 config (SPY standing in for the S&P 500, with Yahoo's VIX), traded from the next session.
- Budget: a point each for SPY under its 26-week average, a 13-week drawdown ≥ 10% and a VIX robust z-score (3 years) ≥ 3; 0 points invests 100%, 1 point 85%, 2-3 points 70%; 70% too when SPY or QQQ fell ≥ 3% over 3 sessions, or when the VIX z-score is ≥ 3 and its change's ≥ 3.5.
- Groups: growth tech (AAPL, MSFT, NVDA, META, AMZN, GOOGL, TSLA), real assets (XOM, CVX, COP, FCX, BHP, GLD, SLV) and defensive (TLT, IEF, XLU, XLV, IAU, SHY, UUP), ranked by 12-week information ratio against QQQ; the best two that beat QQQ over those 12 weeks are active.
- Names: in each active group, the 3 with the highest robust z-score of their latest weekly return over the group's (against the last 12 weeks); the budget splits equally over the groups, then over their names.
- Exception: a picked name with a z-score ≥ 3.5 and a positive 12-week return above 1.5 × QQQ's gets 1.5 × its weight; the total is capped at 100%.
- Fallback: with no active group, SPY, QQQ, IAU, XLU and XLV share the budget equally.
- Orders: marketable limits 1% through the quote, each good for 30 minutes; sells first, buys once no sell is outstanding.

## Exit

- Names outside the new week's allocation are sold at that rebalance; holdings drift between Fridays.

## Sizing

- $1,000,000 book: each weight × NAV at the ask, fractional shares; the unallocated budget stays in cash.

## Data

- Split-adjusted daily bars (Alpaca; Yahoo without keys) of the 23 tradables from 2016, and Yahoo's daily VIX.

## Code

- **Master desk**: `sleeves/quant_research/finrlx.py`, `sleeves/quant_research/common.py`; not in this repo: `desk/vendor/quant_research/finrlx/`

## Notes

- The config's daily stops (-5%, -10% trailing) never act: the engine is given no positions.
- Only each Friday's own readings count: the 10-day fast risk-off hold and the 4-week persistence exception never act.
- The config's two-names-per-group cap is not read; the engine takes the top 3 of each group.
- The released FinRL-X code it runs keeps its upstream license and is not copied here.
