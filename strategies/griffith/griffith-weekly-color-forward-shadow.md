# Tensor weekly color forward shadow (FG / FC)

Buys a fresh weekly Tensor buy-green or buy-cyan meeting any of 9 frozen two-condition candidates and holds it 12 weeks.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith Tensor HTF research (TENSOR_WEEKLY_COLOR_FORWARD_SHADOW_1_0_0), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1w |
| **Universe** | Tensor research roster's operating companies |
| **Style** | Tensor signal + context |
| **Status** | waiting |

## Entry

- Universe: the roster's operating companies (current metadata).
- Candidates: FG01-FG03 on a fresh weekly buy-green and FC01-FC06 on a fresh weekly buy-cyan, each passing both its conditions (listed below); each match is a sub-lot; no purge.
- Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it.
- Entry: the next session's open, a market order within that session; skipped once it has passed.

## Exit

- Close of week 12, market-on-close.

## Sizing

- One slot per event: the $100,000 book / (1,838 names × 1 timeframe) = about $54, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side.

## Data

- Completed regular-session weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_forward_spec.json`

**The 9 candidates** (each on the fresh weekly marker named; weeks are bars)

| Id | Marker | Conditions |
|---|---|---|
| FG01 | buy-green | SPY above a rising EMA 200 · 4-week volume ≥ 1.35 × the 20-week |
| FG02 | buy-green | SPY above a rising EMA 200 · up-week volume ≥ 60% of 13 weeks' |
| FG03 | buy-green | 13- and 26-week returns above SPY's |
| FC01 | buy-cyan | a 13-week return of 25-60% · ≥ 20 points over SPY's |
| FC02 | buy-cyan | the Tensor cycle over 10 bars old · ADX 20-35 |
| FC03 | buy-cyan | the cycle BULL_WEAK · up-week volume ≥ 60% of 13 weeks' |
| FC04 | buy-cyan | a buy-green 1-8 weeks before · the cycle over 10 bars old |
| FC05 | buy-cyan | the 4-week range under half the 13-week · a 13-week return ≥ 20 points over SPY's |
| FC06 | buy-cyan | participation footprint active · a 13-week return of 25-60% |
