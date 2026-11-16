# QuantJourney Strategy Ideas

Use this skill to turn a strategy idea into a runnable QuantJourney backtest.

## First decision: weights or orders

- **Weights** (`execution_mode="weights"`) — portfolio thinking: factor
  portfolios, rotation, long/cash, long/short, risk overlays, scheduled
  rebalancing. Implement `_compute_signals` and `_compute_weights`.
- **Orders** (`execution_mode="orders"`) — execution thinking: stop-losses,
  limits, brackets, trailing stops, gaps. Implement `_compute_orders`.

Prototype in weight mode; switch to orders only when the *fill* is the point.

## Map the idea to the nearest example

| Idea shape | Start from |
|---|---|
| Trend on a basket | W01 (SMA), W22 (MACD) |
| Mean reversion | W03 / W21 (Bollinger), O02 |
| Momentum rotation | W04, W18 |
| Long/short factor | W15 (momentum), W16 (reversal) |
| Pairs / market-neutral | W13 (ratio), W14 (hedge ratio) |
| Risk-scaled exposure | W17/W18 (vol target), W19/W20 (risk parity) |
| Realistic stops/brackets | O06, O09, O12, O14 |
| Intraday | W07–W09, O15–O16 |
| Validate / tune | WF01–WF05 |

Copy the closest file in `strategies/`, change the rule, keep the structure.

## The weight-mode pattern

```python
class MyStrategy(Backtester):
    def _compute_signals(self) -> pd.DataFrame:      # dates x instruments panel
        feat = self.instruments_data.get_feature("SMA_50_close")
        return (feat > self.instruments_data.get_feature("SMA_200_close")).astype(float)

    def _compute_weights(self) -> pd.DataFrame:
        active = self.signals == 1.0
        return active.div(active.sum(axis=1), axis=0).fillna(0.0).clip(upper=0.25)
```

## Rules

- Data arrives as a **panel** (dates × instruments) — ranking across the universe
  on each date is one line of pandas (`.nlargest`, `.rank(axis=1)`).
- Signal on day *t* trades on day *t+1* — the engine applies `shift(1)`; never
  hand-build look-ahead.
- Features come from `get_feature(...)`: prices (`adj_close`, `high`), computed
  metrics (`returns`), or `indicators_config` names (`SMA_50_close`,
  `RSI_14_close`). Multi-output indicators (MACD, Bollinger) are computed inline
  from `adj_close`.
- Long/short weights are allowed (sum ≈ 0 for market-neutral); short
  borrow/financing is not modeled — say so in the docstring.
- Keep the universe small enough to read the report; use widely available
  symbols.
