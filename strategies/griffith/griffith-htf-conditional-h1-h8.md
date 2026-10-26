# Tensor HTF conditional holdout (H1-H8)

Buys fresh daily or weekly Tensor signals that match one of eight frozen conditional labels and holds them 20 sessions or 12 weeks.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith Tensor HTF research (TENSOR_HTF_CONDITIONAL_HOLDOUT_1_0_0), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1d · 1w |
| **Universe** | Tensor research roster's operating companies |
| **Style** | Tensor signal + context |
| **Status** | live |

## Entry

- Universe: the roster's operating companies (current metadata).
- Labels: H1 a weekly buy-cyan with an annualized 20-bar volatility ≥ 60% and a 20-bar median dollar volume of $20-100M; H2 a weekly buy-cyan above a rising EMA 200; H3 a weekly buy-cyan with the fast and slow states bullish; H4 a daily buy-green above a rising EMA 200 with a 20/60-bar range ratio ≤ 0.75 and a 20-bar breakout; H5 a daily bounce buy above a rising EMA 200; H6 a daily buy-green with a participation footprint active; H7 a fresh daily participation footprint; H8 a weekly bounce buy while consensus-sell is active.
- Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it.
- Entry: the next session's open, a market order within that session; skipped once it has passed.

## Exit

- Close of bar 20 (daily) or week 12 (weekly), market-on-close.

## Sizing

- One slot per event: the $100,000 book / (1,838 names × 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side.

## Data

- Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_htf_holdout_spec.json`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)

## Notes

- On the desk's 10-year weekly tape the 20-bar volatility is annualized with √252 (the feature code treats any tape over 300 bars as daily), so H1's 60% line sits near 27% on a weekly √52 basis.
