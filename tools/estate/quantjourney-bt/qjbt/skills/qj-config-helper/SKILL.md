# QuantJourney Config Helper

Use this skill to configure a QuantJourney `Backtester` — choose the right
parameters, rebalance policy, risk overlay, granularity, and report settings.

## Core parameters

```python
strategy = MyStrategy(
    strategy_name="...",                 # names the report folder
    instruments=["AAPL", "MSFT", ...],   # or a market-neutral pair, or a wide universe
    backtest_period={"start": "2015-01-01", "end": "2025-01-01"},
    source="yfinance",                   # intraday requires yfinance
    granularity="1d",                    # 1d | 1m | 5m | 15m | 30m | 1h
    execution_mode="weights",            # weights | orders
    initial_capital=100_000,
    max_position_size=0.25,              # per-name cap; use 1.0 for long/short legs
    indicators_config=[...],             # declares SMA/EMA/RSI features
    benchmark_symbol="^GSPC",
    reporting_frequency="daily",         # daily | weekly | monthly | quarterly
    theme_plots="quantjourney",          # or bloomberg, dark, academic, minimal
    show_text_reports=True, save_portfolio_plots=True,
)
```

## Rebalance policy (weight mode)

Compose triggers with `RebalancePolicy(...)`:

- `frequency` — `"D"`, `"W"` (+`weekday`), `"BME"`, `"BQE"`, `"BYE"`, or `None`.
- `drift_threshold` (+`drift_type`) — rebalance only when a weight drifts past X.
- `tracking_error_threshold` (+`tracking_error_window`) — rebalance vs benchmark TE.
- `rebalance_on_signal_change` (+`signal_change_threshold`) — trade only on flips.
- `max_drawdown_trigger` (+`max_drawdown_action`, `circuit_breaker_cooldown_days`)
  — circuit breaker.
- `max_annual_turnover` — turnover budget (cost gate).
- `partial_rebalance` — trade only the drifted names.

## Risk overlays (weight mode)

Attach via `risk_model=`; applied between weights and rebalance:

- `VolTargetModel(target_vol=0.10, lookback=63, max_leverage=1.5)`
- `RiskParityModel(lookback=63)` — equal risk contribution
- `InverseVolModel(lookback=63)`
- `PositionLimitModel(max_weight=0.25)`
- `RiskModelChain([...])` — apply several in order

## Order mode

Set `execution_mode="orders"`, add `slippage_model=` and `commission_scheme=`,
and implement `_compute_orders`. Rebalance timing is expressed in your order
logic, not `RebalancePolicy`.

## Rules

- Intraday (`1m`–`1h`) requires `source="yfinance"` and is limited by provider
  history (1m ≈ 7 days, 5m/15m/30m ≈ 60 days).
- Don't set `reporting_frequency` finer than the data (no monthly-data → daily
  report).
- For long/short strategies set `max_position_size` high enough (e.g. `1.0`) so
  the legs are not clipped.
- Match the universe size to the strategy: pairs = 2, cross-sectional = wide
  (20–30), asset-allocation = a handful of asset-class ETFs.
