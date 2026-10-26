# Leader genome

Buys a stock when the Tensor research sidecar marks a Leader (extended, strong, active) on a completed buy bar, hourly, daily or weekly, and sells at the close of bar 20.

| | |
|---|---|
| **Family** | Tensor research |
| **Source** | FolioTend / Griffith Tensor research (archived desk research), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1h · 1d · 1wk |
| **Universe** | 1,838-name genome roster |
| **Style** | Momentum |
| **Status** | live |

## Entry

- Leader tests: close ≥ 8% above EMA 21; the Tensor medium RSI ≥ 60; the event bar's relative volume ≥ 1.2; 20-bar path efficiency ≥ 0.30; ≥ 4 bullish votes.
- Shown only on a bar with a Tensor buy marker or a phenotype; at least 3 of the 5 tests pass, read on the bar before the event.
- Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
- Entry: the next bar's open, a market order within that hour (hourly) or session (daily, weekly); skipped once it has passed.

## Exit

- Exit: the close of bar 20 (market-on-close when it ends a session).

## Sizing

- One equal slot per event: the $100,000 book / (1,838 names × 3 timeframes) = about $18; skipped when the book lacks the cash; a modeled cost of 25.5 bp a side.

## Data

- Completed regular-session hourly bars (1 year), daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`; not in this repo: `desk/vendor/foliotend_research/v619/app/lib/foliotend-research-sidecar.ts`

## Notes

- Femto-lean's [Leader-1d event](../femto/femto-leader-d.md) runs the same five tests daily, gated by a UT Bot cyan or EMA-cross green bar instead of a Tensor buy marker.
- The Tensor engine and the FolioTend research code these rules run are not published in this repo.
