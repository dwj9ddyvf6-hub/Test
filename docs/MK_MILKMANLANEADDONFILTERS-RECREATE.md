# mk-milkmanlaneaddonfilters: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Milkman filters on Tensor lanes", type forecast and ML models, family milkman. Algorithm grade PARTIAL in the accounting, gaps: entry/signal rule, exit rule and sizing not recorded in its consulted sources (Test catalog entry/variants only). Those gaps are filled in Test by the strategy card below. Alias `mk_milkmanlaneaddonfilters`. Card Source: the Milkman v2 study's add-on rules, on the research lab's Tensor lanes.
- Strategy card in Test: `strategies/milkman/mk-milkmanlaneaddonfilters.md`. Its Source row carries the family codename token, which is omitted here under the repo PII rule.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start (b24_Test_tree.txt in the run workspace, reused as the batch-start tree) and searched by filename for the canonical id, its aliases and its distinguishing tokens across sleeves/, strategies/, packages/ and docs/; the Silicon, quant-research-backup and Midna trees taken at the same time were searched the same way and contain no file named for this id. The code paths below are the paths named in the strategy card's Code section, verified present in the Test tree, and the named module was read and confirmed to carry this strategy's id / logic.

## What this strategy is

Takes the lab's Tensor lane fires through the Milkman study's add-on rules: four lanes, each with one filter or boost (strategy card).

## Full algorithm

From the strategy card in Test (`strategies/milkman/mk-milkmanlaneaddonfilters.md`), in evaluation order:

1. Lanes: weekly Cyan and Green (a closed weekly bar with the marker, bar >= 60); daily Green (bar >= 250); daily Swing (a green bar within 3 bars of its setup square).
2. Add-on rules: weekly Cyan unless EMA13 crossed above EMA48 in the last 10 days; weekly Green unless the fire day closed exactly 3 lower closes; daily Green unless the Phase Oscillator is >= 61.8; daily Swing at double size after a compression release up in the last 5 days.
3. Stream filter: 20-day dollar volume >= $100,000.
4. Execution: bought at the market in the first 90 minutes of the session after the fire (one session late at most), at the live ask.
5. Exit: held 78 weeks (weekly lanes), 60 sessions (daily Green) or 40 (daily Swing), then sold market-on-close.
6. Sizing: $1,000 a fire ($2,000 for a boosted Swing); a $5,000,000 book.

## Files in this repo

- This package: `docs/MK_MILKMANLANEADDONFILTERS-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Strategy card: `strategies/milkman/mk-milkmanlaneaddonfilters.md`
- Code (already in Test): the Milkman family Tensor-lane module in `sleeves/milkman/` (the module file name carries the family codename token and is omitted here under the repo PII rule; its header describes the Milkman-family rows built on the lab's Tensor lane fires, replayed over Yahoo payloads with the vendored engine, and it was read and confirmed to carry this strategy's tokens), `sleeves/milkman/vendored.py`, `sleeves/milkman/vendor/milkman/dstrats.py`
- Rule lines: `docs/verify/milkman.md`
- Not in Test (card Notes): the Tensor engine these lanes run (desk/vendor/ engine directory) is not published in this repo; the lanes' own logic is in the files above and the engine is an external dependency of the recreation.
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Universe 1,822 US stocks (the store_v1 survivors); asset class US equities; timeframe 1w and 1d; family milkman.
- Book $5,000,000; ticket $1,000 a fire, $2,000 for a boosted Swing.
- Cadence and state beyond the above: not in the record.

## Data inputs

- Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes) (card Data section).

## Install and run

1. Clone the Test repo.
2. Take the Milkman family Tensor-lane module in `sleeves/milkman/` (file name omitted under the PII rule, see Files) with `sleeves/milkman/vendored.py` and `sleeves/milkman/vendor/milkman/dstrats.py` at the paths shown in Files.
3. Provide the Tensor engine dependency named in the card Notes (not published in Test) so weekly/daily Tensor fires can be produced; without it the lane logic cannot fire.
4. Configure the book size, ticket and universe exactly as in Configuration.
5. First evaluation: run one evaluation on a snapshot with no qualifying fire and confirm no entry intent is emitted (fail-closed), then run the Verification checklist.

## Verification

No per-sleeve test file for this id was found in Test; the rule lines are at `docs/verify/milkman.md`. Behaviour checklist from the recorded algorithm:

- Lane membership is exact: weekly Cyan/Green need a closed weekly marker bar >= 60; daily Green needs bar >= 250; daily Swing needs a green bar within 3 bars of its setup square.
- Each add-on rule vetoes or boosts exactly as recorded: EMA13/EMA48 cross in the last 10 days vetoes weekly Cyan; exactly 3 lower closes on the fire day vetoes weekly Green; Phase Oscillator >= 61.8 vetoes daily Green; a compression release up in the last 5 days doubles a daily Swing to $2,000.
- 20-day dollar volume below $100,000 is skipped; entry is market in the first 90 minutes of the session after the fire at the live ask.
- Exits are market-on-close after 78 weeks (weekly), 60 sessions (daily Green) or 40 sessions (daily Swing); no other exit.
