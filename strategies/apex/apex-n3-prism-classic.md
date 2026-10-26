# APEX N3 / N4: PRISM multi-asset trend

Trend × volatility targets on a basket of assets, scaled together to 35% portfolio volatility: N3 Classic (Nasdaq-100, Treasuries, gold, oil, dollar) and N4 Paradigm (Nasdaq-100, semiconductors, gold, Bitcoin).

| | |
|---|---|
| **Family** | APEX |
| **Source** | APEX research desk (Cursor2), inventions N3 and N4 |
| **Asset** | US ETFs and Bitcoin |
| **Timeframe** | 1d |
| **Universe** | QQQ, TQQQ, IEF, GLD, USO, UUP, SMH, BTC/USD, BIL |
| **Style** | Multi-asset trend × volatility |
| **Status** | 2 live |

## Entry

- Per asset: unit = trend score × min(cap, 20% / HAR volatility), once it has 380 days of history.
- The units are averaged over the assets available, then × min(3, 35% / the forecast volatility of that average); caps Nasdaq 4, Treasuries 5, gold 3, oil 2, dollar 4, semiconductors 3, Bitcoin 1; gross ≤ 6.
- Each asset's held weight moves only on a change of 0.20 or more, a session after the decision.
- Assets: N3 the Nasdaq-100, 7-10-year Treasuries (IEF), gold (GLD), oil (USO), the dollar (UUP); N4 the Nasdaq-100, semiconductors (SOX, held as SMH), gold (GLD), Bitcoin.

## Exit

- No stop: weights follow the targets; a trend score of 0 takes an asset to 0.

## Sizing

- Nasdaq exposure as QQQ / TQQQ; every other asset one for one in its ETF; idle capital in BIL; anything above the book's capital runs a margin debit.
- N4's Bitcoin trades on Alpaca crypto in the last 10 minutes of the equity session.
- Shares = floor(weight × book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.

## Data

- Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills), IEF, GLD, USO, UUP and ^TNX (N3); ^SOX, SMH, GLD and BTC-USD (N4); recomputed after each close.
- N3's Treasuries: IEF's total return; before IEF, a duration model on the 10-year yield (^TNX).
- N4's semiconductors: ^SOX + 1% a year until SMH's history starts, then SMH's total return.

## Variants

| Book | Assets | Row |
|---|---|---|
| N3 PRISM Classic | Nasdaq-100, Treasuries, gold, oil, dollar | `apex_n3_prism_classic` |
| N4 PRISM Paradigm | Nasdaq-100, semiconductors, gold, Bitcoin | `apex_n4_prism_paradigm` |

## Code

- **Master desk**: `sleeves/apex/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex.py`, `sleeves/apex/vendor/apex/inventions.py`, `sleeves/femto/vendor/aurelia/features.py`
