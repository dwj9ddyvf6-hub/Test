# Tensor HTF relay (T1-T7)

Buys fresh daily and weekly Tensor buys (daily greens, inside a weekly bull episode or not, and weekly greens and cyans) and holds each until the first completed daily or weekly sell.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith Tensor HTF research (TENSOR_HTF_RELAY_1_0_0), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1d · 1w |
| **Universe** | Tensor research roster: 1,838 US names |
| **Style** | Tensor signal relay |
| **Status** | live |

## Entry

- Arms: T1 a daily buy-green; T4 one inside an active weekly bull episode (the latest fresh weekly green or cyan with no weekly sell since); T5 a T4 with consensus-buy or lifecycle P active; T6 a daily bounce buy inside a weekly bull episode; T7 the first daily green of each weekly episode; T2 a weekly buy-green; T3 a weekly buy-cyan; each arm is a sub-lot.
- Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it.
- Entry: the next session's open, a market order within that session; skipped once it has passed.

## Exit

- The next session's open after the first completed daily or weekly sell-red / sell-magenta after the entry bar, at the market.

## Sizing

- One slot per event: the $100,000 book / (1,838 names × 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; the desk's own fees.

## Data

- Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/griffith/vendor/griffith/tensor_htf_strategy_spec.json`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)
