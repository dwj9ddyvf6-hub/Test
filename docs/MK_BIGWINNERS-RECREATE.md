# mk-bigwinners: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Big Winners weekly Tensor sleeve", type forecast and ML models, family milkman. Algorithm grade PARTIAL in the accounting, gaps: entry/signal rule, exit rule and sizing not recorded in its consulted sources (Test catalog entry/variants only). Those gaps are filled in Test by the strategy card below, named here; nothing is filled from outside Test. Variants in the accounting: rows `mk_bigwinnersmanysmallpositionssleeve` (pace: every eligible fire) and `mk_bigwinnerspacedtokenbucketvariant` (pace: token bucket, at most 3 saved); merge tier A (the Test catalog entry groups both rows). Card Source: the research lab bigwinners study (W52S-CAL).
- Strategy card in Test: `strategies/milkman/mk-bigwinners.md`. Its Source row carries the family codename token, which is omitted here under the repo PII rule.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start (b24_Test_tree.txt in the run workspace, reused as the batch-start tree) and searched by filename for the canonical id, its aliases and its distinguishing tokens across sleeves/, strategies/, packages/ and docs/; the Silicon, quant-research-backup and Midna trees taken at the same time were searched the same way and contain no file named for this id. The code paths below are the paths named in the strategy card's Code section, verified present in the Test tree, and the named module was read and confirmed to carry this strategy's id / logic.

## What this strategy is

Buys $1,000 of every liquid, calibrated weekly Tensor Cyan / Green fire, one per name, holds 52 weeks, inside a $50,000 budget (strategy card).

## Full algorithm

From the strategy card in Test (`strategies/milkman/mk-bigwinners.md`), in evaluation order:

1. Weekly fire: a closed weekly Tensor bar with a buy-cyan or buy-green marker (bar >= 60).
2. Stream filters: 20-day dollar volume >= $1M; not avoided (avoid set: price >= $100; Cyan within 5% of the 52-week high; XLF, XLB, XLRE; Cyan in XLU; Green within 13 weeks of the name's last fire); calibrated (Cyan: <= $14.94 or a 60-week depth >= 70.35%; Green: <= $13.15 with a 20-week standard deviation of weekly returns >= 0.08896).
3. Order: the desk score (5.5, plus up to 1 for the calibration boosts when dollar volume >= $2M), then dollar volume; one position per name.
4. Budget: open cost basis <= $50,000 less realised losses.
5. Execution: bought at the market in the first 90 minutes of the session after the fire (one session late at most), at the live ask.
6. Exit: at the close of the 52nd week after the fire week, market-on-close.
7. Sizing: whole shares = floor($1,000 / the live ask); a $100,000 book. Paced row: a weekly token bucket (starts at 1, refills $50,000 / (52 x $1,000) a week, holds at most 3), one token an entry. Variants: base row takes every eligible fire; paced row uses the token bucket.

## Files in this repo

- This package: `docs/MK_BIGWINNERS-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Strategy card: `strategies/milkman/mk-bigwinners.md`
- Code (already in Test): the Milkman family Tensor-lane module in `sleeves/milkman/` (the module file name carries the family codename token and is omitted here under the repo PII rule; its header describes the Milkman-family rows built on the lab's Tensor lane fires, replayed over Yahoo payloads with the vendored engine, and it was read and confirmed to carry this strategy's tokens), `sleeves/milkman/vendored.py`, `sleeves/milkman/vendor/milkman/dstrats.py`
- Rule lines: `docs/verify/milkman.md`
- Not in Test (card Notes): the Tensor engine these lanes run (desk/vendor/ engine directory) is not published in this repo; the lanes' own logic is in the files above and the engine is an external dependency of the recreation.
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Universe 1,822 US stocks (the store_v1 survivors); asset class US equities; timeframe 1w; family milkman.
- Book $100,000; ticket $1,000; open cost basis budget <= $50,000 less realised losses; token bucket starts at 1, refills $50,000 / (52 x $1,000) per week, holds at most 3 (paced variant).
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

- A fire counts only on a closed weekly bar (index >= 60) carrying buy-cyan or buy-green, with 20-day dollar volume >= $1M, outside the avoid set, and passing the Cyan/Green calibration tests exactly as recorded.
- Candidates are ordered by desk score (5.5 plus up to 1 of calibration boost at dollar volume >= $2M), then dollar volume; one position per name; open cost basis never exceeds $50,000 less realised losses.
- Entry is market, in the first 90 minutes of the session after the fire, at the live ask; whole shares = floor($1,000 / ask).
- The paced variant spends one token per entry from a bucket starting at 1, refilling $50,000/(52 x $1,000) weekly, capped at 3.
- The only exit is market-on-close at the close of the 52nd week after the fire week.
