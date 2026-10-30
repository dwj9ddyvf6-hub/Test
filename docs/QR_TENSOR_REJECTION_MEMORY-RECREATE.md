# qr-tensor-rejection-memory: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor rejection memory (MID21)", type forecast and ML models, family quant_research. Algorithm grade PARTIAL in the accounting, gaps: entry/signal rule, exit rule and sizing not recorded in its consulted sources (Test catalog entry/variants only). Those gaps are filled in Test by the strategy card below. Alias `qr_tensor_rejection_memory`; status waiting in the accounting (status_counts waiting: 1). Card Source: Tensor rejection memory v1 (MID21), desk quant research on the Tensor engine.
- Strategy card in Test: `strategies/quant_research/qr-tensor-rejection-memory.md`.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start (b24_Test_tree.txt in the run workspace, reused as the batch-start tree) and searched by filename for the canonical id, its aliases and its distinguishing tokens across sleeves/, strategies/, packages/ and docs/; the Silicon, quant-research-backup and Midna trees taken at the same time were searched the same way and contain no file named for this id. The code paths below are the paths named in the strategy card's Code section, verified present in the Test tree, and the named module was read and confirmed to carry this strategy's id / logic.

## What this strategy is

Buys a frozen 21-stock basket's names when a Tensor buy trigger lands as price finally accepts above a level it failed at twice, and sells at the open 20 sessions later (strategy card).

## Full algorithm

From the strategy card in Test (`strategies/quant_research/qr-tensor-rejection-memory.md`), in evaluation order:

1. Basket: ABG, ABM, ACAD, ARCB, ARE, ASAN, AYI, AZZ, BILL, CLOV, DXPE, FG, FIBK, FRT, FUL, GRBK, HLI, MBIN, RDW, UPST, VCTR.
2. Levels: the Tensor engine's EMA 48, EMA 200 and long ribbon (the highest of ribbons 4-7).
3. Memory: an episode opens when a close is >= 0.25 ATR under a level; a failed attempt is a close >= 0.1 ATR under it on a bar whose high (or the prior close) reached 0.1 ATR over, at least 3 bars apart; acceptance is two closes running >= 0.1 ATR over; an episode lasts at most 60 bars.
4. Trigger: acceptance after >= 2 failed attempts in an episode 5-60 bars old, on a final bar carrying a Tensor buy (a green or cyan marker, or a confirmed swing), after 200 bars of history.
5. Scan: nightly after 20:15 ET on each name's full daily history from 2015 through the Tensor engine v698; entries need a complete basket scan and no overdue time exit.
6. Order: before the open, in symbol order, whole shares at a limit of 1.03 x the session's unadjusted close (rounded down to the tick), good for the first 10 minutes.
7. Exit: sold at the market at the open of the 20th session after entry; no stop.
8. Sizing: $100,000 book: min(12.5% of equity, cash) / (limit x 1.001) shares; at most 8 positions.

## Files in this repo

- This package: `docs/QR_TENSOR_REJECTION_MEMORY-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Strategy card: `strategies/quant_research/qr-tensor-rejection-memory.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py` (the Tensor research family module in Test; it was read and confirmed to carry the rejection-memory logic and the MID21 marker). Card Code section also names two FolioTend research modules that are not in this repo (desk/vendor/foliotend_research/rejection_memory/ strategy and acceptance_features modules), and its Notes state the FolioTend research code it runs is not published in this repo; those dependencies are recorded here as not in Test.
- Rule lines: `docs/verify/quant_research.md`
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Universe frozen 21-stock basket (tickers in the Full algorithm); asset class US equities; timeframe 1d; family quant_research.
- Book $100,000; per-position min(12.5% of equity, cash) / (limit x 1.001) shares; at most 8 positions; hold 20 sessions; nightly scan after 20:15 ET.
- Cadence and state beyond the above: not in the record.

## Data inputs

- All-adjusted daily bars (Alpaca; Yahoo without keys) from 2015, and split-adjusted bars for the session's unadjusted close (card Data section).

## Install and run

1. Clone the Test repo.
2. Take the code files named in Files at their Test paths, with their shared `sleeves/quant_research/common.py` dependencies.
3. Configure the book size, roster and cadence exactly as in Configuration; provide the Data inputs feeds.
4. First run: score one close on a small fixture roster and confirm the eligibility, ranking and order rules in the Verification checklist before any live-size run.

## Verification

Behaviour checklist from the recorded algorithm (rule lines at `docs/verify/quant_research.md`):

- Episodes, failed attempts and acceptance follow the exact ATR thresholds in the Full algorithm (0.25 ATR open, 0.1 ATR failed-attempt and acceptance bands, attempts at least 3 bars apart, episode at most 60 bars, trigger episode age 5-60 bars).
- A trigger requires acceptance after at least 2 failed attempts, a Tensor buy on the final bar, and at least 200 bars of history; entries require a complete basket scan and no overdue time exit.
- Orders go before the open in symbol order, whole shares, limit 1.03 x the session's unadjusted close rounded down to the tick, good for the first 10 minutes; sizing is min(12.5% of equity, cash) / (limit x 1.001), at most 8 positions.
- The only exit is market at the open of the 20th session after entry; there is no stop.
