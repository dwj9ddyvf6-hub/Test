# Tensor rejection memory (MID21)

Buys a frozen 21-stock basket's names when a Tensor buy trigger lands as price finally accepts above a level it failed at twice, and sells at the open 20 sessions later.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | Tensor rejection memory v1 (MID21), desk quant research on the Tensor engine |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Frozen 21-stock basket |
| **Style** | Resistance acceptance + Tensor trigger |
| **Status** | waiting |

## Entry

- Basket: ABG, ABM, ACAD, ARCB, ARE, ASAN, AYI, AZZ, BILL, CLOV, DXPE, FG, FIBK, FRT, FUL, GRBK, HLI, MBIN, RDW, UPST, VCTR.
- Levels: the Tensor engine's EMA 48, EMA 200 and long ribbon (the highest of ribbons 4-7).
- Memory: an episode opens when a close is ≥ 0.25 ATR under a level; a failed attempt is a close ≥ 0.1 ATR under it on a bar whose high (or the prior close) reached 0.1 ATR over, at least 3 bars apart; acceptance is two closes running ≥ 0.1 ATR over; an episode lasts at most 60 bars.
- Trigger: acceptance after ≥ 2 failed attempts in an episode 5-60 bars old, on a final bar carrying a Tensor buy (a green or cyan marker, or a confirmed swing), after 200 bars of history.
- Scan: nightly after 20:15 ET on each name's full daily history from 2015 through the Tensor engine v698; entries need a complete basket scan and no overdue time exit.
- Order: before the open, in symbol order, whole shares at a limit of 1.03 × the session's unadjusted close (rounded down to the tick), good for the first 10 minutes.

## Exit

- Sold at the market at the open of the 20th session after entry; no stop.

## Sizing

- $100,000 book: min(12.5% of equity, cash) / (limit × 1.001) shares; at most 8 positions.

## Data

- All-adjusted daily bars (Alpaca; Yahoo without keys) from 2015, and split-adjusted bars for the session's unadjusted close.

## Code

- **Master desk**: `sleeves/tensor_research/tensor_research.py`; not in this repo: `desk/vendor/foliotend_research/rejection_memory/strategy.py`, `desk/vendor/foliotend_research/rejection_memory/acceptance_features.py`

## Notes

- The FolioTend research code it runs is not published in this repo.
