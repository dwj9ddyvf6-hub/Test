# Tensor weekly green / cyan deep confirmation (WG / WC)

Buys a fresh weekly Tensor buy-green or buy-cyan meeting any of 24 frozen two-condition candidates and holds it 12 weeks, at most once per candidate and name every 84 days.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith Tensor HTF research (TENSOR_WEEKLY_GREEN_CYAN_DEEP_CONFIRMATION_1_0_0), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Tensor research roster's operating companies |
| **Style** | Tensor signal + context |
| **Status** | waiting |

## Entry

- Universe: the roster's operating companies (current metadata).
- Candidates: WG01-WG10 on a fresh weekly buy-green and WC01-WC14 on a fresh weekly buy-cyan, each passing all its conditions (listed below); each match is a sub-lot.
- Purge: a candidate takes a name again only 84 days after its last event there.
- Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it.
- Entry: the next session's open, a market order within that session; skipped once it has passed.

## Exit

- Close of week 12, market-on-close.

## Sizing

- One slot per event: the $100,000 book / (1,838 names × 1 timeframe) = about $54, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side.

## Data

- Completed regular-session weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_spec.json`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)

**The 24 candidates** (each on the fresh weekly marker named; weeks are bars)

| Id | Marker | Conditions |
|---|---|---|
| WG01 | buy-green | ATR ≥ 12% of price · close at or above the upper Bollinger band |
| WG02 | buy-green | ATR ≥ 12% · the Tensor cycle over 10 bars old |
| WG03 | buy-green | ADX 20-35 · ≥ 15% over EMA 21 |
| WG04 | buy-green | SPY above a rising EMA 200 · up-week volume ≥ 60% of 13 weeks' |
| WG05 | buy-green | SPY above a rising EMA 200 · 4-week volume ≥ 1.35 × the 20-week |
| WG06 | buy-green | ATR ≥ 12% · 20/60-week range ratio ≤ 0.45 |
| WG07 | buy-green | a close at or above the prior 13-week high · a bullish candle regime |
| WG08 | buy-green | range ratio ≤ 0.45 · relative volume ≥ 1.2 |
| WG09 | buy-green | 26-week beta ≥ 1.5 · a close at or above the prior 26-week high |
| WG10 | buy-green | 13- and 26-week returns above SPY's |
| WC01 | buy-cyan | ≥ 15% over EMA 21 · SPY above a rising EMA 200 |
| WC02 | buy-cyan | the Tensor cycle BULL_WEAK · 4-week volume ≥ 1.35 × the 20-week |
| WC03 | buy-cyan | Bollinger bandwidth ≥ 0.50 · SPY above a rising EMA 200 |
| WC04 | buy-cyan | ATR ≥ 12% · SPY above a rising EMA 200 |
| WC05 | buy-cyan | the cycle's momentum diverging · SPY above a rising EMA 200 |
| WC06 | buy-cyan | 26-week beta ≥ 1.5 · the cycle BULL_WEAK |
| WC07 | buy-cyan | SPY above a rising EMA 200 · 4-week volume ≥ 1.35 × the 20-week |
| WC08 | buy-cyan | ATR ≥ 12% · fast and slow states bullish |
| WC09 | buy-cyan | 26-week return above SPY's · SPY above a rising EMA 200 |
| WC10 | buy-cyan | range ratio 0.45-0.75 · SPY above a rising EMA 200 |
| WC11 | buy-cyan | ATR ≥ 12% · a close at or above the prior 13-week high |
| WC12 | buy-cyan | Bollinger bandwidth ≥ 0.50 · the cycle's momentum diverging |
| WC13 | buy-cyan | a bounce buy 1-8 weeks before |
| WC14 | buy-cyan | the cycle BULL_WEAK · a buy-green 1-8 weeks before |
