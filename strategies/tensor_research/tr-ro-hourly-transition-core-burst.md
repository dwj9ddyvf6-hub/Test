# Hourly Core / Burst transition

Buys a confirmed hourly Tensor Swing on a daily buy-cyan name when its hourly volatility and EMA distance read Core or Burst, with the Swing's own target and invalidation.

| | |
|---|---|
| **Family** | Tensor research |
| **Source** | FolioTend's hourly transition genome proposal (Core / Burst), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1h |
| **Universe** | 1,838-name genome roster |
| **Style** | Swing confirmation |
| **Status** | waiting |

## Entry

- A confirmed v615 hourly Swing, the name's latest daily bar carrying a buy-cyan, and no sell-red or sell-magenta on the confirmation bar.
- Core: hourly ATR 1-2% of price with the nearest of EMA 21 / 50 / 200 0.5-1.0 ATR away; Burst: hourly ATR 2-4% with a daily supply or range breakout; both tags split the slot.
- Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
- Entry: the next hour's open, a market order within that hour; skipped once it has passed.

## Exit

- The Swing's frozen target (the nearest supply above, else close + 2 ATR) and invalidation (the nearest demand below, else the bar's low), on the bid; a later hourly sell-red or sell-magenta exits after its bar; else the close of hour 20.

## Sizing

- One equal slot per event: the $100,000 book / (1,838 names × 1 timeframe) = about $54; skipped when the book lacks the cash; a modeled cost of 25.5 bp a side.

## Data

- Completed regular-session hourly bars (1 year) and daily bars (2 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`; not in this repo: `desk/vendor/foliotend_research/v615/lib/tensor-swing-signals.mjs`, `desk/vendor/foliotend_research/v615/lib/tensor-enrichment-signals.mjs`
- **Rule lines**: [docs/verify/tensor_research.md](../../docs/verify/tensor_research.md)

## Notes

- The Tensor engine and the FolioTend research code these rules run are not published in this repo.
