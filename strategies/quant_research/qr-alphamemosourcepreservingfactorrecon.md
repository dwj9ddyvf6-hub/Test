# AlphaMemo factor book

Holds the 50 best-scored stocks of a frozen 640-name roster under AlphaMemo's frozen factor model, replacing at most 5 a session.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | AlphaMemo (jarrettyu/AlphaMemo), reconstructed in the desk's six-strategy study |
| **Asset** | US equities |
| **Timeframe** | 1d |
| **Universe** | Frozen 640-name roster |
| **Style** | Factor model · TopkDropout |
| **Status** | live |

## Entry

- Score: after each close, AlphaMemo's frozen residual pool (15 formulas) beside four base features (intraday return, 20-day relative volume, range, 1-day return), each z-scored across the eligible names, through its saved LightGBM model.
- Eligible: an equity candidate with 252 complete prior sessions, a 20-session average dollar volume ≥ $10M and a close ≥ $5.
- Book: holds the 50 best-scored names; each session, buys the best new names in place of those sold.
- Each close's scores trade from the first pass of the next session.
- Orders: marketable limits 1% through the quote, each good for 30 minutes; sells first, buys once no sell is outstanding.

## Exit

- Sale: a held name among the 5 lowest of the held and best new names (an unscored one ranks last) is sold once held a session; each sale ≤ 1% of its 20-session dollar volume.

## Sizing

- $1,000,000 book: buys share 95% of the cash left after sales (sales net of 5 bp) equally across the planned buys; every trade ≤ 1% of the name's 20-session dollar volume and buys scaled to the cash; fractional shares at the ask.

## Data

- Split-adjusted daily bars (Alpaca; Yahoo without keys) of the 640 names (the last 320 sessions), scored after each close from 16:50 ET.

## Code

- **Master desk**: `sleeves/quant_research/factor_books.py`, `sleeves/quant_research/dropout_book.py`, `sleeves/quant_research/sixai.py`, `sleeves/quant_research/scores.py`, `sleeves/quant_research/lgbm_text.py`, `sleeves/quant_research/common.py`

## Notes

- Its vendored AlphaMemo files (upstream code under its own license) are not copied here.
