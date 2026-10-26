# Weekly green recovery

Buys a stock on a weekly Tensor buy-green with a bullish consensus that is up over the last 13 weeks, and sells at the close of week 20.

| | |
|---|---|
| **Family** | Tensor research |
| **Source** | FolioTend / Griffith Tensor research (archived desk research), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1wk |
| **Universe** | 1,838-name genome roster |
| **Style** | Early markup |
| **Status** | waiting |

## Entry

- A completed weekly bar with a Tensor 5-of-7 bullish consensus (≥ 5 bullish votes, ≥ 4 more than bearish), bullish votes ≥ bearish + 2, dollar volume ≥ $10M and relative volume 0.8-2.
- A buy-green marker with the close at or above its level 13 weeks back.
- Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
- Entry: the next week's first open, a market order within that session; skipped once it has passed.

## Exit

- Exit: the close of week 20 (market-on-close when it ends a session).

## Sizing

- One equal slot per event: the $100,000 book / (1,838 names × 1 timeframe) = about $54; skipped when the book lacks the cash; a modeled cost of 25.5 bp a side.

## Data

- Completed regular-session weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`; not in this repo: `desk/vendor/foliotend_research/v619/app/lib/foliotend-research-sidecar.ts`

## Notes

- The Tensor engine and the FolioTend research code these rules run are not published in this repo.
