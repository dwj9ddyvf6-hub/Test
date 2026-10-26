# Tensor weekly cyan confirmation (CY01-CY18)

Buys a fresh weekly Tensor buy-cyan that fits any of 18 frozen context hypotheses (two of them negative controls) and holds it 12 weeks, at most once per hypothesis and name every 84 days.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith Tensor HTF research (TENSOR_WEEKLY_CYAN_CONFIRMATION_1_0_0), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Tensor research roster's operating companies |
| **Style** | Tensor signal + context |
| **Status** | waiting |

## Entry

- Universe: the roster's operating companies (current metadata).
- Hypotheses: CY01-CY18 on the fresh weekly buy-cyan (listed below); each match is a sub-lot.
- Purge: a hypothesis takes a name again only 84 days after its last event there.
- Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it.
- Entry: the next session's open, a market order within that session; skipped once it has passed.

## Exit

- Close of week 12, market-on-close.

## Sizing

- One slot per event: the $100,000 book / (1,838 names × 1 timeframe) = about $54, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side.

## Data

- Completed regular-session weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_htf_weekly_cyan_spec.json`

## Notes

- The two negative controls, CY17 (a damaged trend) and CY18 (extended), are traded like the rest.

**The 18 hypotheses** (each on the fresh weekly buy-cyan; weeks are bars)

| Id | Condition |
|---|---|
| CY01 | above a rising EMA 200, compressed (20/60-week range ratio ≤ 0.75) |
| CY02 | CY01 plus a close at or above the prior 20-week high |
| CY03 | above a rising EMA 200, the first cyan in 26 weeks |
| CY04 | above a rising EMA 200, participation footprint active |
| CY05 | above a rising EMA 200, consensus-buy active |
| CY06 | above a rising EMA 200, fast and slow states bullish |
| CY07 | compressed, a 20-week breakout, the prior 52-week high ≤ 15% above, not extended |
| CY08 | the first cyan in 26 weeks, compressed, a 20-week breakout, not extended |
| CY09 | repaired, the active call bullish after a reversal |
| CY10 | repaired, participation footprint active |
| CY11 | ≥ 30% under the prior 52-week high, repaired |
| CY12 | a bounce buy 1-8 weeks before, repaired |
| CY13 | a sell-red, sell-magenta or consensus-sell 1-8 weeks before, repaired |
| CY14 | the first cyan in 26 weeks, the prior 52-week high ≤ 15% above, not extended |
| CY15 | above a rising EMA 200, within 15% of the prior 52-week high, not extended |
| CY16 | tight (range ratio ≤ 0.45), a bullish candle regime, not extended |
| CY17 | below a falling EMA 200 (a negative control) |
| CY18 | extended (a negative control) |

Repaired: not below a falling EMA 200, above EMA 21, no more than 3% under EMA 50, a positive 20-week return.
Extended: ≥ 15% over EMA 21 or a 20-week return ≥ 50%.
