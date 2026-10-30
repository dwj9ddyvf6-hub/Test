# qr-alphaqcmiqcmfactorpolicyreconstructi: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "AlphaQCM factor rotation", type forecast and ML models, family quant_research. Algorithm grade PARTIAL in the accounting, gaps: entry/signal rule, exit rule and sizing not recorded in its consulted sources (Test catalog entry/variants only). Those gaps are filled in Test by the strategy card and the code below. Alias `qr_alphaqcmiqcmfactorpolicyreconstructi`; status live in the accounting. Card Source: AlphaQCM (ZhuZhouFan/AlphaQCM), reconstructed in the desk's six-strategy study.
- Strategy card in Test: `strategies/quant_research/qr-alphaqcmiqcmfactorpolicyreconstructi.md`.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start (b24_Test_tree.txt in the run workspace, reused as the batch-start tree) and searched by filename for the canonical id, its aliases and its distinguishing tokens across sleeves/, strategies/, packages/ and docs/; the Silicon, quant-research-backup and Midna trees taken at the same time were searched the same way and contain no file named for this id. The code paths below are the paths named in the strategy card's Code section, verified present in the Test tree, and the named module was read and confirmed to carry this strategy's id / logic.

## What this strategy is

Every 20 sessions buys the top 20% of a frozen 100-stock roster by AlphaQCM's ten-factor pool, equal weight, and holds until the next decision (strategy card).

## Full algorithm

In evaluation order, from the strategy card in Test (`strategies/quant_research/qr-alphaqcmiqcmfactorpolicyreconstructi.md`) and the code header in Test (`sleeves/quant_research/alphaqcm.py`, read for this package; it names this id, the validation-selected frozen pool of ten factor expressions with their pool weights, vendored byte-exact as desk/vendor/quant_research/alphaqcm/frozen-pool.json in the master-desk package in Test, scored on the frozen 100-name roster):

1. Score: the ten frozen formula factors of AlphaQCM's validation-selected pool, each evaluated on split-adjusted daily OHLCV and VWAP, masked to the eligible names, z-scored across them by day and summed with its pool weight.
2. Eligible: 252 complete prior sessions, a 20-session average dollar volume >= $10M and a close >= $5.
3. Decision: every 20th session from 2023-01-03, on that close; traded from the next session's first pass.
4. Pick: the top 20% of the scored names (at least 1), equal weight; with fewer than 10 scored names it holds cash until the next decision.
5. Orders: marketable limits 1% through the quote, each good for 30 minutes; sells first, buys once no sell is outstanding.
6. Exit: names outside the next decision's pick are sold at that rebalance; holdings drift in between.
7. Sizing: $1,000,000 book: each weight x NAV (cash plus holdings at the bid) at the ask, fractional shares, fixed at the decision.

## Files in this repo

- This package: `docs/QR_ALPHAQCMIQCMFACTORPOLICYRECONSTRUCTI-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Strategy card: `strategies/quant_research/qr-alphaqcmiqcmfactorpolicyreconstructi.md`
- Code (already in Test): `sleeves/quant_research/alphaqcm.py`, `sleeves/quant_research/alphagen_np.py`, `sleeves/quant_research/common.py`. Card Notes: its vendored AlphaQCM upstream files (under their own license) are not copied into the card's repo listing.
- Rule lines: `docs/verify/quant_research.md`
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Universe frozen 100-stock roster (the most traded of 2016-2020); asset class US equities; timeframe 1d (every 20 sessions); family quant_research.
- Book $1,000,000; decision every 20th session from 2023-01-03; pick top 20% (at least 1), equal weight; cash if fewer than 10 scored names.
- Cadence and state beyond the above: not in the record.

## Data inputs

- Split-adjusted daily bars (Alpaca; Yahoo without keys) of the 100 names, the last 300 sessions (card Data section).

## Install and run

1. Clone the Test repo.
2. Take the code files named in Files at their Test paths, with their shared `sleeves/quant_research/common.py` dependencies.
3. Configure the book size, roster and cadence exactly as in Configuration; provide the Data inputs feeds.
4. First run: score one close on a small fixture roster and confirm the eligibility, ranking and order rules in the Verification checklist before any live-size run.

## Verification

Behaviour checklist from the recorded algorithm (rule lines at `docs/verify/quant_research.md`):

- Decisions occur only every 20th session from 2023-01-03, on that close, and trade from the next session's first pass; no trades occur between decisions except the rebalance itself.
- Eligibility is exact: 252 complete prior sessions, 20-session average dollar volume >= $10M, close >= $5.
- The pick is the top 20% of scored names (at least 1), equal weight; with fewer than 10 scored names the book holds cash until the next decision.
- Names outside the new pick are sold at the rebalance; sizing is weight x NAV at the ask, fractional shares, fixed at the decision; sells complete before buys.
