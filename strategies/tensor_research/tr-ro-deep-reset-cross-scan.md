# Deep Reset cross-scan

Buys a name with a fresh Tensor buy (daily green, weekly green or cyan) that is not extended and reads as a deep reset, and sells at the close of its 15th session.

| | |
|---|---|
| **Family** | Tensor research |
| **Source** | FolioTend's Deep Reset cross-scan, as a forward-test book |
| **Asset** | US equities |
| **Timeframe** | 1d · 1wk |
| **Universe** | 1,838-name genome roster |
| **Style** | Reset after a drawdown |
| **Status** | live |

## Entry

- Groups: a fresh daily buy-green, or a fresh weekly buy-green or buy-cyan, while the daily bar before the latest closes under 8% above its EMA 21.
- Deep Reset score ≥ 60 on the group's last 2 years: 35 × the drawdown from the 60-bar high (full at 35%) + 30 × closeness to the nearest of the 12-bar low, EMA 21 and EMA 50 (zero at 8% away) + 20 when 3-12% under the 20-bar high + 15 when RSI(14) is 45-60.
- Entry at the next session's open; a weekly signal counts from the week's last session.

## Exit

- Exit: the close of the 15th session.

## Sizing

- One slot per event: the $100,000 book / (1,838 × 2 timeframes) = about $27; the engine's own fees.

## Data

- Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`; not in this repo: `desk/vendor/foliotend_research/doorway/prepare_current_doorway_inputs.py`

## Notes

- The Tensor engine and the FolioTend research code these rules run are not published in this repo.
