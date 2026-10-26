# Daily green base expansion

Buys a stock on a daily Tensor buy-green that breaks out of a quiet base above a rising 200-day average, and sells at the close of day 20.

| | |
|---|---|
| **Family** | Tensor research |
| **Source** | FolioTend / Griffith Tensor research (archived desk research), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | 1,838-name genome roster |
| **Style** | Base breakout |
| **Status** | live |

## Entry

- A completed daily bar with a buy-green marker; close above EMA 200, which is above its level 20 bars back; 20-bar mean range ≤ 0.75 × the 40 bars before; close above the prior 20 highs; < 15% above EMA 21; up-volume ≥ 50% of the last 13 bars' (or a high-participation footprint).
- Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
- Entry: the next session's open, a market order within that session; skipped once it has passed.

## Exit

- Exit: the close of day 20 (market-on-close when it ends a session).

## Sizing

- One equal slot per event: the $100,000 book / (1,838 names × 1 timeframe) = about $54; skipped when the book lacks the cash; a modeled cost of 25.5 bp a side.

## Data

- Completed regular-session daily bars (2 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`; not in this repo: `desk/vendor/foliotend_research/v619/app/lib/foliotend-research-sidecar.ts`
- **Rule lines**: [docs/verify/tensor_research.md](../../docs/verify/tensor_research.md)

## Notes

- The Tensor engine and the FolioTend research code these rules run are not published in this repo.
