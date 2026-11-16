# QuantJourney Strategy Reviewer

Use this skill to review a QuantJourney strategy for correctness before trusting
its results. Check each item.

## Timing / look-ahead

- Signals must use data available at decision time. The engine lags weights by
  one bar (`shift(1)`); do not also peek forward inside `_compute_signals`
  (e.g. `.shift(-1)`, centered rolling windows, using `iloc[i+1]`).
- Rolling indicators must not include the current bar's future. Warm-up bars
  should be NaN/0, not filled with later data.

## Data handling

- Missing bars stay unavailable, not 0% returns. Don't `fillna(0)` on a returns
  series you then treat as real observations.
- `_compute_weights` returning NaN → the name should drop out, not distort the
  normalization.

## Weights and exposure

- Long/cash: weights in [0, cap], sum ≤ 1. Confirm `max_position_size` matches
  the intended cap.
- Long/short: check gross (Σ|w|) and net (Σw). Market-neutral should be net ≈ 0;
  a stray leg breaks neutrality.
- Renormalization should not silently move positions you meant to freeze.

## Costs and realism

- A strategy that only works at zero cost does not work. Confirm slippage and
  commissions are set for anything turnover-heavy (intraday, reversal, daily
  rebalancing).
- Short strategies: borrow/financing is not modeled — is the edge just the
  omitted carry? Flag it.

## Mode fit

- If the edge depends on stop-losses, brackets, or limit fills, it belongs in
  order mode, not weight mode.
- Order mode: check gap handling expectations (a gap through a stop fills at the
  open, not the stop price) and that per-order commission minimums aren't assumed
  per fill.

## Output

Report findings as: severity, where (method/line), what's wrong, and the fix.
Separate real correctness bugs from style. Verify claims against the code, not
assumptions.
