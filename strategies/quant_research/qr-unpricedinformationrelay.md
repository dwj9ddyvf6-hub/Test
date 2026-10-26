# UIR filing relay

A 47.5% SPY / 47.5% QQQ book that adds a sender's fixed receivers for 20 sessions after a CAT, DE or MSFT quarterly filing whose cash-flow surprise a ridge model scores above 30 bp.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | UIR, R8's fixed-relay ABSORPTION policy on R3's SEC filing events (desk research) |
| **Asset** | US equities and ETFs |
| **Timeframe** | 1d (20-session hold) |
| **Universe** | Senders CAT, DE, MSFT; receivers DE, CAT, AAPL, AMZN, GOOGL, NVDA, AVGO, ORCL |
| **Style** | Filing-surprise relay |
| **Status** | live |

## Entry

- Events: each sender's first SEC 10-Q / 10-K accession per fiscal quarter; surprise = (the quarter's CFO - capex less the prior year's same quarter) / max(the mean |CFO - capex| of the last 8 contiguous quarters, $1), with at least 4 contiguous prior quarters; decided at the first close at or after SEC acceptance.
- Receivers: CAT → DE, DE → CAT, MSFT → AAPL, AMZN, GOOGL, NVDA, AVGO, ORCL.
- Features: the sender's and receiver's decision-day and 20-session log returns over SPY, the receiver's 20-session volatility and the reaction gap, the receiver one-hot, plus s, |s|, s × gap, s × absorption and max(s, 0) × max(-sender reaction, 0) (gap and absorption in volatility units, capped ±5).
- Model: ridge (penalty 10) refit for each event's month on matured rows, labelled by the receiver's next-open to open-after-20 return less the 50/50 QQQ / SPY return; labels end 21 sessions before the month, with at least 24 source filings; inputs z-scored and capped ±5.
- Admission: a prediction above 30 bp keeps the name in the basket for 20 sessions.
- Orders: marketable limits 1% through the quote, each good for 30 minutes; sells first, buys once no sell is outstanding.

## Exit

- A name leaves the basket 20 sessions after its event's close.

## Sizing

- $1,000,000 book: SPY and QQQ (95% - the sleeve) / 2 each, the sleeve min(45%, 15% × active names) split equally; re-weighted at each session's first pass at the ask, fractional shares.

## Data

- The recorded R3 event rows, SEC companyfacts and filing acceptances (fetched after each close) and all-adjusted daily bars (Alpaca; Yahoo without keys), the last 120 sessions.

## Code

- **Master desk**: `sleeves/quant_research/uir.py`, `sleeves/quant_research/relay.py`, `sleeves/quant_research/common.py`; not in this repo: `desk/vendor/quant_research/r3/`

## Notes

- Live filings join the training set only while their prices sit inside the 120 daily bars it loads.
