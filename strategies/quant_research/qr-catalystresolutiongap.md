# CRG own-stock filing surprise

A 47.5% SPY / 47.5% QQQ book that adds CAT, DE or MSFT itself for 20 sessions after its quarterly filing, when a ridge model reading the cash-flow surprise against the issuer's surprise history scores above 30 bp.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | CRG, R8's surprise-history policy on R3's SEC filing events (desk research) |
| **Asset** | US equities and ETFs |
| **Timeframe** | 1d (20-session hold) |
| **Universe** | CAT, DE, MSFT |
| **Style** | Filing-surprise drift |
| **Status** | live |

## Entry

- Events: each issuer's first SEC 10-Q / 10-K accession per fiscal quarter; surprise = (the quarter's CFO - capex less the prior year's same quarter) / max(the mean |CFO - capex| of the last 8 contiguous quarters, $1), with at least 4 contiguous prior quarters; decided at the first close at or after SEC acceptance.
- Features: the issuer's decision-day and 20-session log returns over SPY, its 20-session volatility, the issuer one-hot, plus the surprise s, the issuer's previous surprise p, s × p and the mean of its last four.
- Model: ridge (penalty 1) refit for each event's month on matured rows, labelled by its own next-open to open-after-20 return less the 50/50 QQQ / SPY return; labels end 21 sessions before the month, with at least 24 source filings; inputs z-scored and capped ±5.
- Admission: a prediction above 30 bp keeps the name in the basket for 20 sessions.
- Orders: marketable limits 1% through the quote, each good for 30 minutes; sells first, buys once no sell is outstanding.

## Exit

- A name leaves the basket 20 sessions after its event's close.

## Sizing

- $1,000,000 book: SPY and QQQ (95% - the sleeve) / 2 each, the sleeve min(45%, 15% × active names) split equally; re-weighted at each session's first pass at the ask, fractional shares.

## Data

- The recorded R3 event rows, SEC companyfacts and filing acceptances (fetched after each close) and all-adjusted daily bars (Alpaca; Yahoo without keys), the last 120 sessions.

## Code

- **Master desk**: `sleeves/quant_research/crg.py`, `sleeves/quant_research/relay.py`, `sleeves/quant_research/common.py`; not in this repo: `desk/vendor/quant_research/r3/`
- **Rule lines**: [docs/verify/quant_research.md](../../docs/verify/quant_research.md)

## Notes

- Live filings join the training set only while their prices sit inside the 120 daily bars it loads.
