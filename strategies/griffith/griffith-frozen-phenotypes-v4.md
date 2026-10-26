# Tensor frozen phenotypes v4

Buys the four enabled frozen Tensor phenotypes (a daily green base expansion and three weekly consensus-buy patterns) at the next open, in thirds closing after 4, 13 and 26 bars.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith Tensor research (tensor-frozen-phenotype-specifications/4.0.0), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1d · 1w |
| **Universe** | Tensor research roster: 1,838 US names |
| **Style** | Tensor phenotype |
| **Status** | live |

## Entry

- Phenotypes, on the market-scan context (the last 420 daily or 260 weekly bars), only on bars after the registry's late-August 2026 freeze: a daily buy-green passing the base-expansion test (above a rising EMA 200, a range ratio ≤ 0.75, a 20-bar breakout, under 15% over EMA 21, constructive participation); a weekly buy-green early markup out of a recovery; a weekly buy-cyan accumulation out of a recovery; a weekly buy-cyan early markup; the weekly three each READY with bullish-aligned energy, deep normal participation and a consensus-buy enrichment.
- Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it.
- Entry: the next session's open, a market order within that session; skipped once it has passed.

## Exit

- Three equal sub-lots at the close of bars 4, 13 and 26, market-on-close.

## Sizing

- One slot per event: the $100,000 book / (1,838 names × 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 15 bp a side.

## Data

- Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_phenotype_registry.json`
