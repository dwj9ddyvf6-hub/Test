# QuantJourney Report Analyst

Use this skill to read a QuantJourney backtest report — the metrics, the plots,
and the trade blotter — and judge whether the result is trustworthy.

## Read the headline metrics first

- **CAGR** — annualized return. Context, not verdict.
- **Sharpe / Sortino** — risk-adjusted return; Sortino only penalizes downside.
  A Sharpe > 2 on a simple strategy is a red flag to investigate, not celebrate.
- **Max drawdown / Calmar** — worst peak-to-trough and return-per-unit-drawdown.
  Ask: could you hold through that drawdown?
- **VaR / CVaR** — tail loss at a confidence level (loss-positive convention).

## Read the plots

- **Cumulative returns (± regime overlay)** — the shape. Is the edge steady or
  one lucky period? Is it just long-beta?
- **Drawdown / underwater** — depth and *time to recover*. Long underwater
  periods break real allocators.
- **Monthly returns heatmap** — consistency vs a few dominating months.
- **Rolling Sharpe / volatility / beta** — *when* it worked. A rolling Sharpe
  that collapses in recent years is a warning.
- **Crisis analysis** — per-crisis return, vol, drawdown, beta (GFC, COVID,
  2022). How does it behave when the market breaks?
- **Blotter** — trade PnL distribution (a few big winners vs broad edge),
  holding-period distribution, and transaction-cost analysis (did costs eat it?).

## Read the walk-forward diagnostics

- **OOS equity** vs in-sample — does the edge survive out of sample?
- **Sharpe decay** IS→OOS — a large drop means fit to noise.
- **Overfit ratio / efficiency** traffic lights — heed the red verdicts.
- A single good out-of-sample result is not proof of robustness.

## Red flags to call out

- Edge concentrated in one regime or a handful of trades.
- Sharpe that vanishes once realistic costs are added.
- High turnover with thin per-trade PnL.
- Big in-sample / out-of-sample Sharpe decay.
- Market-neutral book that is actually net long (check exposure).
- Short strategy whose return is mostly the un-modeled borrow carry.

Summarize as: what the strategy is, where the return comes from, the top risk,
and whether the result is trustworthy enough to develop further.
