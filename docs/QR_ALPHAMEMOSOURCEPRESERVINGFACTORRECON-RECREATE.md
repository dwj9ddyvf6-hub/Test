# qr-alphamemosourcepreservingfactorrecon: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "AlphaMemo factor book", type forecast and ML models, family quant_research. Algorithm grade PARTIAL in the accounting, gaps: entry/signal rule, exit rule and sizing not recorded in its consulted sources (Test catalog entry/variants only). Those gaps are filled in Test by the strategy card and the code below. Alias `qr_alphamemosourcepreservingfactorrecon`; status live in the accounting (status_counts live: 1). Card Source: AlphaMemo (jarrettyu/AlphaMemo), reconstructed in the desk's six-strategy study.
- Strategy card in Test: `strategies/quant_research/qr-alphamemosourcepreservingfactorrecon.md`.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start (b24_Test_tree.txt in the run workspace, reused as the batch-start tree) and searched by filename for the canonical id, its aliases and its distinguishing tokens across sleeves/, strategies/, packages/ and docs/; the Silicon, quant-research-backup and Midna trees taken at the same time were searched the same way and contain no file named for this id. The code paths below are the paths named in the strategy card's Code section, verified present in the Test tree, and the named module was read and confirmed to carry this strategy's id / logic.

## What this strategy is

Holds the 50 best-scored stocks of a frozen 640-name roster under AlphaMemo's frozen factor model, replacing at most 5 a session (strategy card).

## Full algorithm

In evaluation order, from the strategy card in Test and the code header in Test (`sleeves/quant_research/factor_books.py`, read for this package):

1. Score: after each close, the strategy's frozen factor pool (see the per-strategy score line in Configuration), each feature z-scored or rank-normalized across the eligible names as recorded for that model, through its saved LightGBM model. Scores are produced by `sleeves/quant_research/scores.py` (job qr_scores after each close) from the frozen pools and models vendored in Test.
2. Eligible: an equity candidate with 252 complete prior sessions, a 20-session average dollar volume >= $10M and a close >= $5.
3. Book: holds the 50 best-scored names; each session, buys the best new names in place of those sold (TopkDropout, top 50, drop 5, minimum hold 1 session, per the code header).
4. Each close's scores trade from the first pass of the next session.
5. Orders: marketable limits 1% through the quote, each good for 30 minutes; sells first, buys once no sell is outstanding.
6. Exit / sale: a held name among the 5 lowest of the held and best new names (an unscored one ranks last) is sold once held a session; each sale <= 1% of its 20-session dollar volume.

Per-strategy score and sizing (card): score = AlphaMemo's frozen residual pool (15 formulas) beside four base features (intraday return, 20-day relative volume, range, 1-day return), each z-scored across the eligible names, through its saved LightGBM model. Sizing: $1,000,000 book: buys share 95% of the cash left after sales (sales net of 5 bp) equally across the planned buys; every trade <= 1% of the name's 20-session dollar volume and buys scaled to the cash; fractional shares at the ask.

## Files in this repo

- This package: `docs/QR_ALPHAMEMOSOURCEPRESERVINGFACTORRECON-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Strategy card: `strategies/quant_research/qr-alphamemosourcepreservingfactorrecon.md`
- Code (already in Test): `sleeves/quant_research/factor_books.py` (its header names this id and the AlphaMemo model, TopkDropout top 50 / drop 5 / minimum hold 1 / risk degree 0.95), `sleeves/quant_research/dropout_book.py`, `sleeves/quant_research/sixai.py`, `sleeves/quant_research/scores.py`, `sleeves/quant_research/lgbm_text.py`, `sleeves/quant_research/common.py`. Card Notes: its vendored AlphaMemo upstream files (under their own license) are not copied into the card's repo listing; the desk's frozen pools and models are the ones the scores module in Test carries.
- Rule lines: `docs/verify/quant_research.md`
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Universe frozen 640-name roster; asset class US equities; timeframe 1d; family quant_research.
- Book $1,000,000; top 50; drop at most 5 a session; minimum hold 1 session; risk degree 0.95 (code header); sales net of 5 bp.
- Scoring runs after each close from 16:50 ET (card Data section).
- Cadence and state beyond the above: not in the record.

## Data inputs

- Split-adjusted daily bars (Alpaca; Yahoo without keys) of the 640 names (the last 320 sessions), scored after each close from 16:50 ET (card Data section).

## Install and run

1. Clone the Test repo.
2. Take the code files named in Files at their Test paths, with their shared `sleeves/quant_research/common.py` dependencies.
3. Configure the book size, roster and cadence exactly as in Configuration; provide the Data inputs feeds.
4. First run: score one close on a small fixture roster and confirm the eligibility, ranking and order rules in the Verification checklist before any live-size run.

## Verification

Behaviour checklist from the recorded algorithm (rule lines at `docs/verify/quant_research.md`):

- Eligibility is exact: 252 complete prior sessions, 20-session average dollar volume >= $10M, close >= $5; ineligible names are never scored into the book.
- The book holds the 50 best-scored names; at most 5 replacements a session; a name is sold only after at least 1 session held and only when it ranks among the 5 lowest of held plus best new names (unscored ranks last).
- Every trade is <= 1% of the name's 20-session dollar volume; sells complete before buys start; orders are marketable limits 1% through the quote, good for 30 minutes.
- Buy sizing matches the per-strategy sizing line in Configuration exactly, at the ask, with fractional shares.
