# qr-timecutflowtransport: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json, also docs/ALL-SLEEVES.md): canonical name "TCFT index-flow swap", type other, family quant_research. Algorithm grade PARTIAL, unresolved false. Accounting sources: Test catalog entry/variants. Recorded accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source.
- Accounting home record: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "TCFT index-flow swap" (also docs/ALL-SLEEVES.md); Test catalog entry 'qr-timecutflowtransport' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus the file reads named in this package); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries).
- Code home: dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/tcft.py + sleeves/quant_research/r10.py.

## What this strategy is

TCFT index-flow swap Type: other; family: quant_research. Universe: QQQ and registered index-event stocks. Asset class: US equities and QQQ. Timeframe: 1d (to the event's endpoint). Creator / source: TCFT, from the desk's ten-strategy repair review (R10) playbook. Style evidence in the accounting: Index-event flow (registered inputs) | Classification 2026-10-30: other (code evidence): Master desk sleeves/quant_research/tcft.py read: it transports a funded QQQ position into index event stocks only when a time cut flow gap envelope and net advantage bounds pass and exits at the index event endpoint, an index event flow mechanism none of the 12 types names

## Full algorithm

Code truth: sleeves/quant_research/tcft.py carries SID qr_timecutflowtransport, class TCFT(Sleeve) with cadence_s=300, universe (QQQ,) and capital 1,000,000.0; sleeves() returns the TCFT sleeve. With no events registered it holds QQQ (card). Vendor inputs under desk/vendor/quant_research/r10/tcft/ are named on the card as not in this repo. Accounting grade PARTIAL; the full rule is on the card and in the code in this repo.

Strategy card record, in full:

A 99% QQQ book that swaps up to 20% into stocks facing a registered index-rebalance flow gap; with no events registered it holds QQQ.

| | |
|---|---|
| **Family** | Quant research |
| **Source** | TCFT, from the desk's ten-strategy repair review (R10) playbook |
| **Asset** | US equities and QQQ |
| **Timeframe** | 1d (to the event's endpoint) |
| **Universe** | QQQ and registered index-event stocks |
| **Style** | Index-event flow (registered inputs) |
| **Status** | blocked |

## Entry

- Core: QQQ 99%, bought once at the live quotes.
- Inputs: a hand-kept registry file of index events (the original target row, owner-lot scenarios, price, 60-session dollar ADV, the endpoint session, bounds and support counts).
- Admission at 18:30 ET of session D: a valid original index target; positive lower bounds on the timed debt and the time-cut gap; price × the gap's lower bound / ADV ≥ 0.1 with its width ≤ half its upper bound; at least 300 event clusters, 60 securities, 30 calibration clusters and 5 years; a funded net lower bound ≥ 20 bp and a positive paired base increment.
- Breakers: no new admissions after a 10% drawdown or a 2% drop against QQQ.
- Execution: on D+1 09:45-10:00 ET sell QQQ worth min(4% of NAV, 0.25% of the 60-session dollar ADV, the 20% budget left); on D+2 09:45-10:00 buy the stock with a limit 3 bp over the ask, good for 15 minutes.

## Exit

- First of: 15:50 ET of the endpoint session, the bid 5% under the entry, or a registered correction or vanished gap; sold at the market, and the QQQ restored at the next 09:45 window.

## Sizing

- $1,000,000 book; each stock leg is the QQQ notional it displaced, in fractional shares.

## Data

- The registry file and live quotes.

## Code

- **Master desk**: `sleeves/quant_research/tcft.py`, `sleeves/quant_research/r10.py`; not in this repo: `desk/vendor/quant_research/r10/tcft/`
- **Rule lines**: [docs/verify/quant_research.md](../../docs/verify/quant_research.md)

## Files in this repo

- This package: docs/QR_TIMECUTFLOWTRANSPORT-RECREATE.md
- Accounting: docs/ALL-SLEEVES.json, docs/ALL-SLEEVES.md
- Code home (see Provenance): dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/tcft.py + sleeves/quant_research/r10.py
- Strategy card and code evidence were read from Test at the paths named in the Provenance / code home lines and in the card's own Code section.

## Configuration

Universe QQQ and registered index-event stocks; timeframe 1d to the event's endpoint; $1,000,000 book, QQQ 99% core, swap budget up to 20%; status blocked in the Test catalog. Registry file is hand-kept (see Data inputs); its exact path and contents are not in the record beyond the card's description.

## Data inputs

The hand-kept registry file of index events (the original target row, owner-lot scenarios, price, 60-session dollar ADV, the endpoint session, bounds and support counts) and live quotes (card).

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path (all are already in Test for a built package; for an INCOMPLETE-CODE package there is no code to place).
3. Wire the producers so the inputs named under Data inputs arrive in the shapes the Full algorithm describes, with the configuration under Configuration.
4. Run the sleeve's entry point named in the code (its sleeves() factory or evaluate(view, ctx) wrapper) on a fixture snapshot that satisfies the entry conditions and confirm the expected intent before any live use.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

- With no events registered the book holds QQQ only (99%).
- Admission only at 18:30 ET of session D and only when every card bound passes, including price x gap lower bound / ADV >= 0.1, width at most half the upper bound, at least 300 event clusters / 60 securities / 30 calibration clusters / 5 years, funded net lower bound >= 20 bp and a positive paired base increment.
- No new admissions after a 10% drawdown or a 2% drop against QQQ.
- Execution timing is D+1 09:45-10:00 ET (sell QQQ worth min(4% of NAV, 0.25% of 60-session dollar ADV, the 20% budget left)) and D+2 09:45-10:00 (buy the stock, limit 3 bp over the ask, good for 15 minutes); exit is the first of 15:50 ET of the endpoint session, bid 5% under entry, or a registered correction / vanished gap, with QQQ restored at the next 09:45 window.
