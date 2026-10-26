# Tensor phenotype experiment (HIGH_BREAK_4)

Sends each frozen-phenotype prediction through the Griffith desk's bracket path: a buy up to 0.1 ATR over the event high, a stop 2 ATR under its close and a target 10% (daily) or 25% (weekly) higher.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith Tensor experimental paper lane (TENSOR_EXPERIMENTAL_1_1_0) |
| **Asset** | US equities |
| **Timeframe** | 1d · 1w |
| **Universe** | Tensor research roster: 1,838 US names |
| **Style** | Tensor phenotype, bracketed |
| **Status** | live |

## Entry

- Predictions: the frozen v4 phenotype events, at most 25 a cycle, oldest first, each once.
- Plan: trigger = the event bar's high, ceiling = trigger + 0.10 ATR(14), stop = its close - 2 ATR(14), target = the ceiling × 1.10 (daily) or × 1.25 (weekly).
- Order: the planner hands the ceiling (rounded to 8 places) to the overlay as the ask, so the trigger always reads as crossed: when that rounding went up the prediction gets no plan; otherwise a GTC buy limit at the ceiling, armed 7 days (daily) or 28 (weekly), which fills at once while the market is under it.
- Delivery, every regular-session pass (15 minutes): a plan is dropped when the name is held or the ask is at or under its stop and waits while an entry works on the name; otherwise it goes in as a GTC order carrying its stop-loss and take-profit.

## Exit

- Bracket: the plan's stop and target.

## Sizing

- Risk 1% of equity / risk per share, within the strategy's 3% risk cap less its open and armed risk; per order ≤ 35% of equity and ≤ 98% of buying power; a held name is not added to; $100,000 book.

## Data

- Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/griffith.py`, `sleeves/griffith/vendor/griffith/strategy_execution.py`; not in this repo: `desk/vendor/griffith/config.json`

## Notes

- The HIGH_BREAK_4 rule's wait for a break of the event high is lost in this path.
- The decision's horizon (26 / 130 sessions) is recorded, not enforced: only the bracket exits.
