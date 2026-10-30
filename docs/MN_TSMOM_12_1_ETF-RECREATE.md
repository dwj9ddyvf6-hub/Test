# mn-tsmom-12-1-etf - Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "TSMOM 12-1 ETF book", type momentum, family midna, style Time-series momentum, algorithm grade PARTIAL (entry/exit/sizing gaps in the accounting), universe 30 diversified ETFs (equity, sector, bond, commodity, currency), asset US ETFs, timeframe 1d (every 21 sessions), creator Midna's TSMOM forms study (scripts/tsmom-forms.ts), its ETF 12-1 book, ported line for line; alias mon_midna_tsmom_forms (test_catalog, status waiting).
- Existing Test strategy card: `strategies/midna/mn-tsmom-12-1-etf.md` (full text used below).
- Code found in Test already (vendored from the Midna repo): `sleeves/midna/vendor/midna_mon/scripts/tsmom-forms.ts` and `sleeves/midna/vendor/midna_mon/src/lib/research/tsmom.ts`; the same files exist in dwj9ddyvf6-hub/Midna at `scripts/tsmom-forms.ts` and `src/lib/research/tsmom.ts` (read in this run; sizes 21,764 and 14,506 bytes in the Midna tree, matching the Test vendor copies' tree sizes). Master-desk book code named in the card: `sleeves/midna/monitor/midna_books.py`, `sleeves/midna/monitor/midna_mon.py`, the monitor module under `sleeves/` whose directory name carries a gate-blocked token (not reproduced here).
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken in this run, 4,609 paths, plus content reads of the files named below); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 paths; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 paths; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 paths; no path named for this id except where stated for mn-tsmom-12-1-etf). Desk source read only: /home/hatch/workspace/muse-desk-v3/desk3/ where stated.

## What this strategy is

TSMOM 12-1 ETF book: every 21 sessions it holds, in equal weights, each of 30 diversified ETFs whose 12-1 month return is positive; cash otherwise. A recorder until the owner's ruling D32 (2026-10-26) funded it as a paper book; its first live signal was pending in the card's record.

## Full algorithm

From the strategy card and the TypeScript source (sign12 in src/lib/research/tsmom.ts; the etf-12-1-flat book in scripts/tsmom-forms.ts), in evaluation order:

1. Sign 12-1: adjusted close 21 sessions back over the adjusted close 252 sessions before it, minus one, > 0. The panel is aligned to SPY's sessions and a name needs 260 valid sessions.
2. Rebalance: every 21 sessions from the book's first session, in the last 40 to 15 minutes of the session: equal weights over the names with a positive sign, as market-on-close orders.
3. Exit: a held name whose sign is no longer positive goes to cash at that rebalance (market-on-close); weights drift between rebalances; no stop.
4. Sizing: 1 / N of the book per long name (N = number of positive-sign names at the rebalance); $100,000 book.
5. Study scope note from the card: the recorder read seven momentum forms on this panel; the study trades only its primary 12-1 form on it, so the row is converted as that book (the long/short etf-12-1-ls form in the study is not this book).

## Files in this repo

- This package: `docs/MN_TSMOM_12_1_ETF-RECREATE.md`
- Code (already in Test; nothing vendored in this run): `sleeves/midna/vendor/midna_mon/scripts/tsmom-forms.ts`, `sleeves/midna/vendor/midna_mon/src/lib/research/tsmom.ts`, `sleeves/midna/monitor/midna_books.py`, `sleeves/midna/monitor/midna_mon.py`
- Original source repo: dwj9ddyvf6-hub/Midna `scripts/tsmom-forms.ts`, `src/lib/research/tsmom.ts`, and its test `tests/tsmom-forms.test.ts`
- Strategy card: `strategies/midna/mn-tsmom-12-1-etf.md`; rule lines: `docs/verify/midna.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

Book $100,000; rebalance every 21 sessions; lookback 252 sessions with 21-session skip; minimum 260 valid sessions; universe 30 diversified ETFs; equal weights 1/N over positive-sign names; market-on-close orders in the last 40 to 15 minutes of the rebalance session; no stop.

## Data inputs

Yahoo daily bars (600 sessions) of the 30 ETFs on rebalance days, adjusted closes (the close when the provider gives no adjusted close), aligned to SPY's sessions.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and keep its layout.
2. Read `strategies/midna/mn-tsmom-12-1-etf.md` and this package.
3. Confirm the vendored TypeScript files and the monitor book code at their Test paths.
4. Wire Yahoo daily bars for the 30 ETFs (600 sessions) on rebalance days.
5. Run the book on its 21-session rebalance cadence; the entry point in the study source is scripts/tsmom-forms.ts (npx tsx scripts/tsmom-forms.ts in the Midna repo layout).
6. Run the Verification checks before treating a recreation as faithful.

## Verification

- sign12 for a name with adjusted close[-21] / adjusted close[-252] - 1 <= 0 is false and the name is cash at the rebalance; > 0 it is held at weight 1/N.
- A name with fewer than 260 valid sessions is not eligible.
- Between rebalances weights drift and no exit fires; at a rebalance a name losing its positive sign goes to cash in full.
- The Midna repo test file tests/tsmom-forms.test.ts covers the study's pure functions.
- Read-back check: this doc was written through the PII gate and read back from Test; its sha256 matches the intended bytes.
