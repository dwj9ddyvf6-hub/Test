# Swing Transition (1H)

On eight named stocks, buys a confirmed hourly Tensor Swing that repairs a slowing decline off a twice-tested floor, and sells at the close of hour 20.

| | |
|---|---|
| **Family** | Tensor research |
| **Source** | FolioTend v698 Swing Transition (the frozen ST classifier), as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1h |
| **Universe** | AG, CMG, CRDO, FLY, LTBR, UAMY, VRT, XPEV |
| **Style** | Swing confirmation |
| **Status** | waiting |

## Entry

- A confirmed v698 hourly Swing (black square, then green arrow) on one of the eight names.
- Transition, all five: a bearish candle regime; the ribbon's decline slowing (the mean slope of the 5 bars before the last 5 negative, the last 5's mean above it); the 24-bar low tapped at least twice within 0.5 ATR, taps 3+ bars apart, the last within 12 bars, and held; a close crossing above EMA 21 on this bar or one of the 3 before, with the close ≥ EMA 8; the broad ribbon bearish or mixed.
- Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
- Entry: the next hour's open, a market order within that hour; skipped once it has passed.

## Exit

- Exit: the close of hour 20 (market-on-close when it ends a session).

## Sizing

- One slot per event: the $100,000 book / 8 = $12,500; a modeled cost of 25.5 bp a side.

## Data

- Completed regular-session hourly bars (1 year) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`; not in this repo: `desk/vendor/old_desk_research/tensor_exact/lib/tensor-swing-transition.mjs`

## Notes

- The Tensor engine and the FolioTend research code these rules run are not published in this repo.
