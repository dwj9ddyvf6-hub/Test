# griffith-top-decile-sue - Recreation Package

Grade: PARTIAL (accounting) - code present in Test; see Files and Verification

## Provenance

- Canonical ID: `griffith-top-decile-sue`
- Canonical name: Top-decile SUE drift
- Aliases: griffith_top_decile_sue
- Type: momentum; Family: griffith; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Top-decile SUE drift" (also `docs/ALL-SLEEVES.md`); local census copy at research_notes/sleeve-census-20261029/accounting.json. doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Top-decile SUE drift" (also docs/ALL-SLEEVES.md); Test catalog entry 'griffith-top-decile-sue' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus file reads of strategies/griffith/griffith-top-decile-sue.md and sleeves/griffith/event_research.py); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for this canonical id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found in Test, so nothing was vendored.
- Accounting algorithm record: entry: []; exit: []; filters: []; parameters: {}; gaps: ['entry/signal rule not recorded in any consulted source', 'exit rule not recorded in any consulted source', 'sizing not recorded in any consulted source']. Where the accounting graded PARTIAL, the algorithm below is taken from the code and the strategy card in Test, which are the truth where they go beyond the accounting.

## What this strategy is

Top-decile SUE drift. Universe: SCOPE stocks (ETF basket excluded); Asset: US equities; Timeframe: 1d (20-session hold).

Strategy card in Test (verbatim body):

Buys SCOPE stocks whose standardized earnings surprise ranks in the top tenth of the last 91 days' at the first open after the report and holds them 20 sessions, in equal weight.

| | |
|---|---|
| **Family** | Griffith |
| **Source** | Griffith R4 parallel lab registration PEAD_SUE_20D_1_0_0, on Nasdaq's public earnings calendar |
| **Asset** | US equities |
| **Timeframe** | 1d (20-session hold) |
| **Universe** | SCOPE stocks (ETF basket excluded) |
| **Style** | Earnings drift |
| **Status** | live |

## Entry

- Events: Nasdaq's earnings calendar for the SCOPE names outside the ETF basket (reported EPS, consensus, release time), refreshed at each session's open.
- Trigger: SUE = (actual - consensus) / the sample SD of the name's 8 prior surprises, at or above the 90th percentile of the universe's SUEs public within the trailing 91 days (at least 10).
- Entry: the open of the first session that can trade the report (a pre-market report that day, otherwise the next session); one event per name at a time.
- Book: every active event at 1/N of the book, re-targeted at each session's first pass.

## Exit

- Market-on-close in the last 25 minutes of the 20th session (the entry session counts as 1).

## Sizing

- $100,000 book in equal calendar-time weights.

## Data

- Nasdaq's archived earnings calendar pages and live quotes.

## Code

- **Master desk**: `sleeves/griffith/event_research.py`, `sleeves/griffith/feedlib/griffith_earnings.py`
- **Rule lines**: [docs/verify/griffith.md](../../docs/verify/griffith.md)

## Full algorithm

Evaluation order in sleeves/griffith/event_research.py (class EarningsDrift, SPECS maps the sleeve id to PEAD_SUE_20D_1_0_0; events() / trigger() / entry_session()):
1. Events: Nasdaq's earnings calendar for the SCOPE names outside the ETF basket (reported EPS, consensus, release time), refreshed at each session's open (feedlib griffith_earnings).
2. Trigger: SUE = (actual - consensus) / the sample SD of the name's 8 prior surprises (sue_series requires >= 8 prior point-in-time surprises, sample std of the prior 8), at or above the 90th percentile of the universe's SUEs public within the trailing 91 days (cross_section; at least 10 SUEs).
3. Entry session: the open of the first session that can trade the report (a pre-market report that day, otherwise the next session); one event per name at a time.
4. Book: every active event at 1/N of the $100,000 book, re-targeted at each session's first pass.
Exit: market-on-close in the last 25 minutes of the 20th session (the entry session counts as 1). No stop or early target is recorded for this sleeve.

## Files in this repo

- Strategy card: `strategies/griffith/griffith-top-decile-sue.md` (in Test)
- Sleeve: `sleeves/griffith/event_research.py` (in Test)
- Earnings feed: `sleeves/griffith/feedlib/griffith_earnings.py` (in Test)

## Configuration

- Registration: PEAD_SUE_20D_1_0_0. Book $100,000, equal calendar-time weights (1/N of active events). Hold 20 sessions.
- Own parameters: see the trigger in the Full algorithm; no other per-sleeve parameters are recorded.

## Data inputs

Nasdaq's archived earnings calendar pages (reported EPS, consensus, release time) and live quotes; SCOPE stock universe with the ETF basket excluded.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and confirm the files listed in "Files in this repo" are present at the stated paths.
2. Confirm the configuration in the Configuration section against the code constants and, where one exists, the config/sleeves.json row.
3. Wire the data inputs named in Data inputs so the sleeve receives them at evaluation time in the form the code expects.
4. Register / enable the sleeve in the host desk exactly as its code entry point expects (see the strategy card Code section).
5. Run one evaluation on fixture data and confirm the emitted behaviour matches the Verification checks before enabling live dispatch.

## Verification

No per-sleeve test file for this canonical strategy is present in the repo tree. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- Trigger check: a name with fewer than 8 prior surprises, or a SUE below the 90th percentile of the trailing-91-day cross-section (fewer than 10 SUEs), produces no event.
- Entry-session check: a pre-market report is tradable that session's open; an after-hours report is tradable the next session's open.
- Weight check: with N active events each target is 1/N of the book, re-targeted at the session's first pass.
- Exit check: the position is sold market-on-close in the last 25 minutes of the 20th session counting the entry session as 1.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
