# Fast Numbers earnings surprise

On each earnings release's first session, long the stocks whose standardized EPS surprise ranks in the top 10% of all earlier releases and short the bottom 10%, open to close.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | Fast Numbers / Slow Words, principal numeric ledger, reconstructed in the desk's six-strategy study |
| **Asset** | US equities (long and short) |
| **Timeframe** | 1d (open to close) |
| **Universe** | US stocks with reported and consensus EPS |
| **Style** | Earnings surprise, intraday hold |
| **Status** | live |

## Entry

- Events: the vendored Yahoo EPS history, then Nasdaq's earnings calendar (reported and consensus EPS; pre-market releases count from 08:00 ET, after-hours from 16:30 ET, untimed from 23:59, so the next session).
- Surprise: SUE = (actual - consensus EPS) / the sample SD of the issuer's previous 8 forecast errors (at least 4).
- Rank: each month's SUEs against every SUE since 2022-01-01 released before that month (at least 30; ties at the midpoint).
- Session: the first regular open at least a minute after the release.
- Weight: (2 / N) × 2 × (p - 0.5) when |p - 0.5| ≥ 0.4, else 0, with N the session's whole scored cohort.
- Orders: from 09:31 ET, market orders, longs at the ask and shorts (whole shares) at the bid; a name still unquoted at 09:45 is skipped.

## Exit

- Market-on-close orders from 15:45 ET; a position the close missed is closed at the next pass.

## Sizing

- $1,000,000 book: NAV × weight / price shares; the weight of an unpriced name stays in cash.

## Data

- The vendored Yahoo EPS history, Nasdaq earnings calendar pages (re-read each session) and live quotes.

## Code

- **Master desk**: `sleeves/quant_research/fastnumbers.py`; not in this repo: `desk/vendor/quant_research/fastnumbers/`, `desk/feedlib/griffith_earnings.py`
