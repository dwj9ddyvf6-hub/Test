# qr-fastnumbersslowwordseventreconstruct: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json, also docs/ALL-SLEEVES.md): canonical name "Fast Numbers earnings surprise", type momentum, family quant_research. Algorithm grade PARTIAL, unresolved false. Accounting sources: Test catalog entry/variants. Recorded accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source.
- Accounting home record: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Fast Numbers earnings surprise" (also docs/ALL-SLEEVES.md); Test catalog entry 'qr-fastnumbersslowwordseventreconstruct' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus the file reads named in this package); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries).
- Code home: dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/fastnumbers.py + sleeves/quant_research/vendor/quant_research/fastnumbers/prepare_events.py + sleeves/quant_research/vendor/quant_research/fastnumbers/run_reconstruction.py + sleeves/griffith/feedlib/griffith_earnings.py.

## What this strategy is

Fast Numbers earnings surprise Type: momentum; family: quant_research. Universe: US stocks with reported and consensus EPS. Asset class: US equities (long and short). Timeframe: 1d (open to close). Creator / source: Fast Numbers / Slow Words, principal numeric ledger, reconstructed in the desk's six-strategy study. Style evidence in the accounting: Earnings surprise, intraday hold | Classification 2026-10-30: momentum (code evidence): Master desk sleeves/quant_research/fastnumbers.py read: canonical SUE tails are held long the top tail and short the bottom tail from open to close of the first tradable session after the release

## Full algorithm

Code truth (sleeves/quant_research/fastnumbers.py docstring, executed not restated): variant numeric_sue_canonical_raw_error. Each session D at the first pass from 09:31 ET: events are the vendored Yahoo EPS history (79,924 releases, 2016-01 to 2025-11), then Nasdaq's earnings calendar after its last day, every release with both reported and consensus EPS. SUE = prepare_events.historical_sue: forecast error over the sample SD of the issuer's previous eight errors (at least four). p = run_reconstruction.cdf_scores(SUE, expanding, from 2022-01-01, at least 30): every release of a month ranked against all earlier months' SUEs (midpoint ties), frozen for the month. Session = the first regular-session open at or after availability plus 1 minute. N = D's whole cohort with finite SUE and p (before any price filter). Weight = (2/N) x 2 x (p - 0.5) where |p - 0.5| >= 0.4, else 0. Orders: NAV x weight / price shares, long the top tail and short the bottom tail at the market; every position closes market-on-close (submitted from 15:45 ET); a position the close did not take is closed at the next pass. Shorts are whole shares. Named divergences in the code: live-event availability from Nasdaq tags (pre-market 08:00 ET, after-hours 16:30 ET, untimed end of day); execution at desk quotes from 09:31 ET (a name still unquoted at 09:45 stays unexecuted); NAV is the sleeve's equity at the decision pass.

Strategy card record, in full:

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

- **Master desk**: `sleeves/quant_research/fastnumbers.py`, `sleeves/griffith/feedlib/griffith_earnings.py`; not in this repo: `desk/vendor/quant_research/fastnumbers/`
- **Rule lines**: [docs/verify/quant_research.md](../../docs/verify/quant_research.md)

## Files in this repo

- This package: docs/QR_FASTNUMBERSSLOWWORDSEVENTRECONSTRUCT-RECREATE.md
- Accounting: docs/ALL-SLEEVES.json, docs/ALL-SLEEVES.md
- Code home (see Provenance): dwj9ddyvf6-hub/Test (code already in Test): sleeves/quant_research/fastnumbers.py + sleeves/quant_research/vendor/quant_research/fastnumbers/prepare_events.py + sleeves/quant_research/vendor/quant_research/fastnumbers/run_reconstruction.py + sleeves/griffith/feedlib/griffith_earnings.py
- Strategy card and code evidence were read from Test at the paths named in the Provenance / code home lines and in the card's own Code section.

## Configuration

Universe US stocks with reported and consensus EPS; timeframe 1d open to close; $1,000,000 book per the card, NAV x weight sizing. Accounting grade PARTIAL with gaps entry/exit/sizing not recorded in its consulted sources; filled here from the card and code in this repo.

## Data inputs

The vendored Yahoo EPS history, Nasdaq earnings calendar pages (re-read each session) and live quotes (card).

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path (all are already in Test for a built package; for an INCOMPLETE-CODE package there is no code to place).
3. Wire the producers so the inputs named under Data inputs arrive in the shapes the Full algorithm describes, with the configuration under Configuration.
4. Run the sleeve's entry point named in the code (its sleeves() factory or evaluate(view, ctx) wrapper) on a fixture snapshot that satisfies the entry conditions and confirm the expected intent before any live use.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

- SUE with fewer than 4 prior forecast errors, or a month CDF built on fewer than 30 earlier SUEs, produces no score.
- Weight is zero unless |p - 0.5| >= 0.4; the top tail is long and the bottom tail short, sized NAV x weight / price with N the whole scored cohort (unpriced names keep their weight in cash).
- Entry is at the first session open at least a minute after the release, from 09:31 ET at the market; a name unquoted at 09:45 is skipped; shorts are whole shares.
- Every position is submitted market-on-close from 15:45 ET, and a missed close is closed at the next pass.
