# apex-benchmarks - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `apex-benchmarks`
- Canonical name: APEX QQQ benchmark
- Aliases: apex_benchmarks
- Type: other; Family: apex; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "APEX QQQ benchmark" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "APEX QQQ benchmark" (also docs/ALL-SLEEVES.md); Test catalog entry 'apex-benchmarks' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start, 4,430 entries; plus file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,441 entries; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no matching sleeve path). Code was found already in Test for every strategy in this batch; nothing was vendored.
- Accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Where the accounting graded PARTIAL, those gaps are gaps of the accounting's consulted sources only; the Test strategy card and code cited below are the fuller record used here, and any remaining gap is marked 'not in the record' in place.

## What this strategy is

APEX QQQ benchmark. Universe in accounting: QQQ. Asset class in accounting: US ETFs. Timeframe in accounting: 1d. Creator in accounting: APEX research desk (Cursor2), APEX-NDX v1.0 benchmark.

## Full algorithm

From the card (`strategies/apex/apex-benchmarks.md`) and the rule lines in `docs/verify/apex.md`, in evaluation order:

1. Entry: Nasdaq-100 exposure 1x every session. (Rule lines: `sleeves/apex/vendor/apex/strategies.py:57-58`; `sleeves/apex/vendor/apex/engine.py:98-102`; `sleeves/apex/feedlib/apex_rules.py:148-149,212-214`.)
2. Exit: None: always fully invested. (Rule lines: `sleeves/apex/vendor/apex/engine.py:98-102`.)
3. Sizing: Market-on-close in the next session (orders from the open to 20 minutes before the close): the whole book in QQQ. Shares = floor(weight x book equity / the last close), frozen per decision; a $100,000 book; debits pay 7.75% a year.
4. Recorded baselines (card Notes; rule lines `sleeves/apex/feedlib/apex_rules.py:26,212-214`; `sleeves/apex/vendor/apex/strategies.py:57-65`): each decision also records QQQ, 2x and 3x daily reset, SMA200 at 1x and 3x, the trend score at 1x and 3x, and 30% volatility targeting up to 3x.

## Files in this repo

- This recreation doc: `docs/APEX_BENCHMARKS-RECREATE.md`
- Strategy card: `strategies/apex/apex-benchmarks.md`
- Running code (already in Test): `sleeves/apex/apex.py` (row `apex_benchmarks`, TITLES 'QQQ benchmark (core variants recorded)'; the eight baselines' positions recorded with every decision per the module header), `sleeves/apex/feedlib/apex.py`, `sleeves/apex/feedlib/apex_rules.py`, `sleeves/apex/feedlib/apex_book.py`
- Vendored source (already in Test): `sleeves/apex/vendor/apex/strategies.py`, `sleeves/apex/vendor/apex/engine.py`, `sleeves/apex/vendor/apex/sim.py`, `sleeves/apex/vendor/apex/series.py`, `sleeves/femto/vendor/aurelia/features.py`
- Rule lines: `docs/verify/apex.md` (APEX QQQ benchmark section). Tests in Test: `tests/test_apex.py` re-hashes every vendored excerpt block.
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

- Universe: QQQ. Timeframe: 1d. Book: $100,000.
- Cadence / schedule: per `sleeves/apex/apex.py`: CADENCE 1800 s, SCHEDULE "rth&close-400:close-20" (the next session, from the open until 20 minutes before the close); decisions computed by the apex_decisions job after each close (weekday 16:20-23:59 ET, 1800 s).

## Data inputs

Yahoo full daily histories: ^NDX and QQQ (the Nasdaq-100 total return), ^IRX (T-bills); recomputed after each close. (Per the card.)

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc, the strategy card / family card named in Files, and `docs/ALL-SLEEVES.json` for the accounting record.
3. Use the code files listed in Files as the runnable logic, preserving their exact delegation and parameter values.
4. Supply the data inputs named above in the shape the code expects.
5. Run on the cadence and in the window stated in Configuration / Full algorithm; exits / rebalances are evaluated in the order the algorithm states.
6. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- Tests in Test: `tests/test_apex.py` (vendored excerpt re-hash).
- Every session the target is QQQ at 1x the whole book; shares = floor(weight x book equity / last close), frozen per decision.
- No exit, stop, or reduction is ever emitted while the benchmark runs.
- Each decision records the eight baselines named in the Full algorithm.
