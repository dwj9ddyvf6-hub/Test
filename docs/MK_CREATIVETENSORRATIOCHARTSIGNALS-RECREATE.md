# mk-creativetensorratiochartsignals: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor ratio-chart signals", type forecast and ML models, family milkman. Algorithm grade PARTIAL in the accounting, gaps: entry/signal rule, exit rule and sizing not recorded in its consulted sources (Test catalog entry/variants only). Those gaps are filled in Test by the strategy card below. Alias `mk_creativetensorratiochartsignals`. Card Source: the research lab TENSOR_CREATIVE ratio-chart study.
- Strategy card in Test: `strategies/milkman/mk-creativetensorratiochartsignals.md`. Its Source row carries the family codename token, which is omitted here under the repo PII rule.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start (b24_Test_tree.txt in the run workspace, reused as the batch-start tree) and searched by filename for the canonical id, its aliases and its distinguishing tokens across sleeves/, strategies/, packages/ and docs/; the Silicon, quant-research-backup and Midna trees taken at the same time were searched the same way and contain no file named for this id. The code paths below are the paths named in the strategy card's Code section, verified present in the Test tree, and the named module was read and confirmed to carry this strategy's id / logic.

## What this strategy is

Runs the weekly Tensor engine on each stock's price relative to SPY and buys the stock on a Cyan or Green ratio fire, holding 252 sessions (strategy card).

## Full algorithm

From the strategy card in Test (`strategies/milkman/mk-creativetensorratiochartsignals.md`), in evaluation order:

1. Ratio bars: the stock's adjusted open, high, low and close over SPY's (high = the largest of the four ratios, low = the smallest), the stock's volume, in Friday weeks.
2. Signal: a closed weekly ratio bar with a buy-cyan or buy-green marker; 20-day dollar volume >= $100,000.
3. Execution: bought at the market in the first 90 minutes of the session after the fire (one session late at most), at the live ask.
4. Exit: 252 sessions after the fire week, sold market-on-close on that session.
5. Sizing: $1,000 a fire; a $3,000,000 book.

## Files in this repo

- This package: `docs/MK_CREATIVETENSORRATIOCHARTSIGNALS-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Strategy card: `strategies/milkman/mk-creativetensorratiochartsignals.md`
- Code (already in Test): the Milkman family Tensor-lane module in `sleeves/milkman/` (the module file name carries the family codename token and is omitted here under the repo PII rule; its header describes the Milkman-family rows built on the lab's Tensor lane fires, replayed over Yahoo payloads with the vendored engine, and it was read and confirmed to carry this strategy's tokens), `sleeves/milkman/vendored.py`, `sleeves/milkman/vendor/milkman/dstrats.py`
- Rule lines: `docs/verify/milkman.md`
- Not in Test (card Notes): the Tensor engine these lanes run (desk/vendor/ engine directory) is not published in this repo; the lanes' own logic is in the files above and the engine is an external dependency of the recreation.
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Universe 1,822 US stocks (the store_v1 survivors); asset class US equities; timeframe 1w; family milkman.
- Book $3,000,000; ticket $1,000 a fire; hold 252 sessions.
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

- Ratio bars are built exactly as recorded (each OHLC element divided by SPY's, high the largest of the four ratios, low the smallest, stock volume, Friday weeks).
- A fire counts only on a closed weekly ratio bar carrying buy-cyan or buy-green with 20-day dollar volume >= $100,000.
- Entry is market in the first 90 minutes of the session after the fire at the live ask, $1,000 a fire.
- The only exit is market-on-close 252 sessions after the fire week.
