# mk-creativetensorbreadthtiming: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor breadth timing (IWM)", type forecast and ML models, family milkman. Algorithm grade PARTIAL in the accounting, gaps: entry/signal rule, exit rule and sizing not recorded in its consulted sources (Test catalog entry/variants only). Those gaps are filled in Test by the strategy card below. Alias `mk_creativetensorbreadthtiming`. Card Source: the research lab TENSOR_CREATIVE breadth study, on the lab's Tensor engine.
- Strategy card in Test: `strategies/milkman/mk-creativetensorbreadthtiming.md`. Its Source row carries the family codename token, which is omitted here under the repo PII rule.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start (b24_Test_tree.txt in the run workspace, reused as the batch-start tree) and searched by filename for the canonical id, its aliases and its distinguishing tokens across sleeves/, strategies/, packages/ and docs/; the Silicon, quant-research-backup and Midna trees taken at the same time were searched the same way and contain no file named for this id. The code paths below are the paths named in the strategy card's Code section, verified present in the Test tree, and the named module was read and confirmed to carry this strategy's id / logic.

## What this strategy is

Holds IWM when few stocks show strong weekly Tensor votes (breadth at or below its train-period median), else cash (strategy card).

## Full algorithm

From the strategy card in Test (`strategies/milkman/mk-creativetensorbreadthtiming.md`), in evaluation order:

1. Breadth: the share of the 1,822 names whose closed weekly Tensor bar has >= 5 bullish votes (weeks with >= 500 names).
2. In when the latest week's breadth is at or below the median of the weeks to 2023-09-29 (at least 20 of them).
3. Decided once the week's scan is in; trades the next session at the market.
4. Exit: to cash when breadth is above the median.
5. Sizing: the whole $100,000 book in IWM, or none.

## Files in this repo

- This package: `docs/MK_CREATIVETENSORBREADTHTIMING-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Strategy card: `strategies/milkman/mk-creativetensorbreadthtiming.md`
- Code (already in Test): the Milkman family Tensor-lane module in `sleeves/milkman/` (the module file name carries the family codename token and is omitted here under the repo PII rule; its header describes the Milkman-family rows built on the lab's Tensor lane fires, replayed over Yahoo payloads with the vendored engine, and it was read and confirmed to carry this strategy's tokens), `sleeves/milkman/vendored.py`, `sleeves/milkman/vendor/milkman/dstrats.py`
- Rule lines: `docs/verify/milkman.md`
- Not in Test (card Notes): the Tensor engine these lanes run (desk/vendor/ engine directory) is not published in this repo; the lanes' own logic is in the files above and the engine is an external dependency of the recreation.
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Universe IWM; asset class US ETF; timeframe 1w; family milkman.
- Book $100,000, all-in IWM or cash; breadth median computed over the weeks to 2023-09-29 (at least 20 weeks).
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

- Breadth counts only weeks with >= 500 names and names whose closed weekly bar has >= 5 bullish votes.
- The book is fully in IWM when the latest breadth is at or below the train-period median (weeks to 2023-09-29, at least 20), and fully in cash when it is above; there is no partial position.
- The decision is made once the week's scan is in and trades at the market in the next session.
