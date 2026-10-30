# qr-unpricedinformationrelay: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json, also docs/ALL-SLEEVES.md): canonical name "UIR filing relay", type other, family quant_research. Algorithm grade PARTIAL, unresolved false. Accounting sources: Test catalog entry/variants. Recorded accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source.
- Accounting home record: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "UIR filing relay" (also docs/ALL-SLEEVES.md); Test catalog entry 'qr-unpricedinformationrelay' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus the file reads named in this package); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries).
- Code home: dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/uir.py + sleeves/quant_research/relay.py + sleeves/quant_research/common.py.

## What this strategy is

UIR filing relay Type: other; family: quant_research. Universe: Senders CAT, DE, MSFT; receivers DE, CAT, AAPL, AMZN, GOOGL, NVDA, AVGO, ORCL. Asset class: US equities and ETFs. Timeframe: 1d (20-session hold). Creator / source: UIR, R8's fixed-relay ABSORPTION policy on R3's SEC filing events (desk research). Style evidence in the accounting: Filing-surprise relay | Classification 2026-10-30: other (config evidence): Accounting and Test catalog record only Filing-surprise relay on SEC filing events with a fixed relay and ABSORPTION policy named, no entry, exit or sizing rule readable in any consulted source

## Full algorithm

Code truth (sleeves/quant_research/uir.py): class UIR(RelayBook) with SID qr_unpricedinformationrelay, FAMILY_ROWS UIR_receivers, POLICY ABSORPTION__H20__L10, HORIZON=20, THRESHOLD=0.003 (30 bp), RIDGE=10.0, RELAY map CAT to (DE,), DE to (CAT,), MSFT to (AAPL, AMZN, GOOGL, NVDA, AVGO, ORCL). Its features are absorption_features: the sender/receiver x_price block plus [s, |s|, s*gap, s*absorption, max(s,0) x max(-sender reaction, 0)] where gap and absorption are in volatility units. The shared RelayBook in relay.py supplies the event, refit, admission and basket machinery also used by the CRG package.

Strategy card record, in full:

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
- **Rule lines**: [docs/verify/quant_research.md](../../docs/verify/quant_research.md)

## Notes

- Live filings join the training set only while their prices sit inside the 120 daily bars it loads.

## Files in this repo

- This package: docs/QR_UNPRICEDINFORMATIONRELAY-RECREATE.md
- Accounting: docs/ALL-SLEEVES.json, docs/ALL-SLEEVES.md
- Code home (see Provenance): dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/uir.py + sleeves/quant_research/relay.py + sleeves/quant_research/common.py
- Strategy card and code evidence were read from Test at the paths named in the Provenance / code home lines and in the card's own Code section.

## Configuration

Senders CAT, DE, MSFT; receivers DE, CAT, AAPL, AMZN, GOOGL, NVDA, AVGO, ORCL; timeframe 1d, 20-session hold; $1,000,000 book per the card (SPY and QQQ (95% minus the sleeve)/2 each, the sleeve min(45%, 15% x active names) split equally). Code constants: HORIZON 20, THRESHOLD 0.003, RIDGE 10.0, POLICY ABSORPTION__H20__L10. Accounting grade PARTIAL with gaps entry/exit/sizing not recorded in its consulted sources; filled here from the card and code in this repo.

## Data inputs

The recorded R3 event rows, SEC companyfacts and filing acceptances (fetched after each close) and all-adjusted daily bars (Alpaca; Yahoo without keys), the last 120 sessions (card).

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path (all are already in Test for a built package; for an INCOMPLETE-CODE package there is no code to place).
3. Wire the producers so the inputs named under Data inputs arrive in the shapes the Full algorithm describes, with the configuration under Configuration.
4. Run the sleeve's entry point named in the code (its sleeves() factory or evaluate(view, ctx) wrapper) on a fixture snapshot that satisfies the entry conditions and confirm the expected intent before any live use.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

- Only the fixed relay map trades: CAT to DE, DE to CAT, MSFT to AAPL/AMZN/GOOGL/NVDA/AVGO/ORCL; no other receiver is admitted.
- A receiver prediction at or below 30 bp admits nothing; above 30 bp the receiver stays in the basket exactly 20 sessions.
- The ridge penalty is 10 (not the CRG package's 1), refit per event month on matured rows (labels ending 21 sessions before the month, at least 24 source filings), inputs z-scored and capped at plus/minus 5.
- Orders are marketable limits 1% through the quote, good for 30 minutes, sells before buys; sizing follows the card's core/sleeve split.
