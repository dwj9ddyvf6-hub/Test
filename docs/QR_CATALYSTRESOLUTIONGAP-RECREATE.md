# qr-catalystresolutiongap: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json, also docs/ALL-SLEEVES.md): canonical name "CRG own-stock filing surprise", type forecast and ML models, family quant_research. Algorithm grade PARTIAL, unresolved false. Accounting sources: Test catalog entry/variants. Recorded accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source.
- Accounting home record: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "CRG own-stock filing surprise" (also docs/ALL-SLEEVES.md); Test catalog entry 'qr-catalystresolutiongap' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus the file reads named in this package); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries).
- Code home: dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/crg.py + sleeves/quant_research/relay.py + sleeves/quant_research/common.py.

## What this strategy is

CRG own-stock filing surprise Type: forecast and ML models; family: quant_research. Universe: CAT, DE, MSFT. Asset class: US equities and ETFs. Timeframe: 1d (20-session hold). Creator / source: CRG, R8's surprise-history policy on R3's SEC filing events (desk research). Style evidence in the accounting: Filing-surprise drift | Classification 2026-10-30: forecast and ML models (code evidence): Master desk sleeves/quant_research/crg.py read: a monthly ridge model on price and filing surprise features must predict over 30 bp over a 20 session horizon

## Full algorithm

Code truth (sleeves/quant_research/crg.py): class CRG(RelayBook) with SID qr_catalystresolutiongap, FAMILY_ROWS CRG_own_stock, POLICY SURPRISE_HISTORY__H20__L1, HORIZON=20, THRESHOLD=0.003 (30 bp), RIDGE=1.0. Its features(row, prior) are surprise_history(row, prior): the row's x_price (15-coordinate price features including the issuer one-hot) plus [s, p, s*p, m], where s is the current seasonal CFO-minus-capex surprise, p is the issuer's previous surprise (0 without one) and m is the mean of its last four (0 without any).

Strategy card record, in full:

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

## Files in this repo

- This package: docs/QR_CATALYSTRESOLUTIONGAP-RECREATE.md
- Accounting: docs/ALL-SLEEVES.json, docs/ALL-SLEEVES.md
- Code home (see Provenance): dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/crg.py + sleeves/quant_research/relay.py + sleeves/quant_research/common.py
- Strategy card and code evidence were read from Test at the paths named in the Provenance / code home lines and in the card's own Code section.

## Configuration

Universe CAT, DE, MSFT plus the SPY/QQQ core book; timeframe 1d, 20-session hold; $1,000,000 book per the card (SPY and QQQ (95% minus the sleeve)/2 each, the sleeve min(45%, 15% x active names) split equally). Code constants: HORIZON 20, THRESHOLD 0.003, RIDGE 1.0. Accounting grade PARTIAL with gaps entry/exit/sizing not recorded in its consulted sources; those gaps are filled here from the card and code in this repo, and nothing beyond them is claimed.

## Data inputs

The recorded R3 event rows, SEC companyfacts and filing acceptances (fetched after each close) and all-adjusted daily bars (Alpaca; Yahoo without keys), the last 120 sessions (card). Code docstring: live events from SEC companyfacts / acceptance times (job qr_relay) and the desk's all-adjusted daily bars; live events use the true UTC EDGAR acceptance, and a filing accepted after 16:00 ET decides at the next close.

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path (all are already in Test for a built package; for an INCOMPLETE-CODE package there is no code to place).
3. Wire the producers so the inputs named under Data inputs arrive in the shapes the Full algorithm describes, with the configuration under Configuration.
4. Run the sleeve's entry point named in the code (its sleeves() factory or evaluate(view, ctx) wrapper) on a fixture snapshot that satisfies the entry conditions and confirm the expected intent before any live use.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

- A prediction at or below 30 bp (0.003) admits nothing; above 30 bp the issuer stays in the basket exactly 20 sessions and then leaves.
- The surprise uses at least 4 contiguous prior quarters and the stated CFO-minus-capex seasonal formula; a filing accepted after 16:00 ET decides at the next close, not that close.
- The ridge is refit per event month on matured rows only (labels ending 21 sessions before the month, at least 24 source filings), inputs z-scored and capped at plus/minus 5, penalty 1.0.
- Orders are marketable limits 1% through the quote, good for 30 minutes, sells before buys; sizing follows the card's SPY/QQQ core and min(45%, 15% x active names) sleeve split.
