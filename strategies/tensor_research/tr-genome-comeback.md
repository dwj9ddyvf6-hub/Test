# Comeback genome

Buys a stock when the Tensor research sidecar marks a Comeback (a repair back over EMA 21) on a completed buy bar, hourly, daily or weekly, and sells at the close of bar 20.

| | |
|---|---|
| **Family** | Tensor research |
| **Source** | FolioTend / Griffith Tensor research (archived desk research), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1h · 1d · 1wk |
| **Universe** | 1,838-name genome roster |
| **Style** | Repair |
| **Status** | live |

## Entry

- Comeback tests: close ≥ EMA 21; the Tensor medium RSI up ≥ 5 points from 11 bars earlier; the MACD histogram above its value 4 bars earlier; bearish votes plus markers fewer than 11 bars earlier; close at or above the 52-bar low.
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
- **Rule lines**: [docs/verify/tensor_research.md](../../docs/verify/tensor_research.md)

## Notes

- The Tensor engine and the FolioTend research code these rules run are not published in this repo.
