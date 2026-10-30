# washout-ppc-coil: Recreation package

## Provenance

Filed under a sanitized filename per the owner's ruling of 2026-10-30. The canonical strategy name in the ALL-SLEEVES accounting carries the originating research family name, which this repo's privacy gate does not allow in file paths or new content. The canonical name and this file's mapping are recorded in the owner's private recreation index. 29 mention(s) of that name in source material were replaced with a neutral placeholder or omitted; no rule, parameter, or code content was changed. The count covers the strategy card, the catalog entry and the ALL-SLEEVES accounting entry consulted for this package. Exact repo paths that carry that name are likewise shown below with a neutral placeholder for the name segment; the private recreation index holds the exact paths.

- ALL-SLEEVES accounting: canonical name "Washout and PPC coil", type mean reversion, algorithm grade PARTIAL, with gaps in the accounting only: entry, exit and sizing not recorded in the accounting sources consulted there.
- Existing Test strategy card: strategies/[family]/[canonical id].md (full entry, exit, sizing, data and code text used in substance below; the card supplies the rules the accounting omitted).
- Catalog entry in docs/CATALOG.json: status live, style Washout pullback, source "originating research family / GrokBot desk, washout v1.2 and the PPC coil".
- Code found in Test already: the master desk module named for the family, plus levels.py, paper.py and wire.py, all under sleeves/[family]/ in this repo. The main module contains the WashoutCoil lane for this strategy, calling the washout buy logic and the admission planner.
- Code search record: Searched, in order: Test (fresh recursive tree in this run, 4647 tree lines, plus content reads of the strategy card, docs/CATALOG.json and docs/ALL-SLEEVES.json); Silicon (recursive tree, 24953 lines, no path named for this strategy); quant-research-backup (recursive tree, 47379 lines, no path named for this strategy); Midna (recursive tree, 7855 lines, no code path named for this strategy). Desk source read only: /home/hatch/workspace/muse-desk-v3 (no file named for this strategy).

## What this strategy is

Washout and PPC coil. It buys a stock washed out under its 50-day average on a Fib, its 12-day shelf or the 21-day EMA, or coiled tight just under the 50-day, on the next-support plan. Asset class US equities. Timeframe 1d, with 1-minute passes. Universe: the 411-stock universe described in the card (Signal Prism US 413 without its two crypto pairs). Status in the card: live.

## Full algorithm

Accounting grade PARTIAL: everything the record holds is written below, from the strategy card, in evaluation order.

1. Washout setup: under the 50-day EMA, RSI(14) under 50, the MACD histogram below zero (or rising and under 0.15), at least 8% under the 60-day high, at most 6% over the 12-day low unless on the 21-day, on a 50 / 61.8 / 78.6% retrace (within 2.5%), the 12-day shelf (at most 4% over it) or the 21-day EMA (within 2%), relative volume under 2.2.
2. PPC coil setup, tier S, ranked first: 0 to 3% under the 50-day EMA, within 2% of the 21-day, RSI 40 to 52, the histogram rising below zero, a 60-day range at most 25%, relative volume at most 1.1, within 2.5% of the 50 or 61.8% retrace, and a 78.6% shakeout that held in the last 6 sessions.
3. Levels: the next-support plan (the Next-support plan card).
4. Admission window and caps: buys 09:35 to 15:45 ET on weekdays; not held, not traded that day, under 6 swings, 10 open names, 16 new buys a day and 2 of one story (semis, software, EV, space and the other story groups named in the source).
5. Live price admission: only within 3% of the plan buy, above its stop and under its target, with the MACD histogram above its level 3 sessions back (or a coil); best tier and R first, at most 6 buys a pass; marketable order.
6. Exit, bracket: the plan stop and target ride as an engine-held bracket.
7. Exit, trims: 20% when price is rejected at the first Fib above the buy (38.2 / 50 / 61.8% of the 90-day range) with the gain under 35%; half after +50% within 8 days, or at a weekly RSI at least 68 with a daily bearish divergence after +80%.
8. Exit, add and dust: one add when price is back within 2% of the 50-day or 200-day EMA after 5 of the prior 16 closes below it. A position worth under $75 is sold.
9. Notes from the card: the swing manager other sells (a broken-then-rejected level, a Wave-B rejection) are re-judged without daily bars, so only a print through the stop confirms them. At the catalog pin the +50%-in-a-week trim is not recorded as a trim, so it repeats each pass while that holds, down to one share; master-desk commit 6d6ae54e (2026-10-26) makes every trim fire once per position. Caps count this sleeve own book only.

## Files in this repo

- This package: docs/WASHOUT_PPC_COIL-RECREATE.md
- Strategy card: strategies/[family]/[canonical id].md
- Code, already in Test, nothing vendored: sleeves/[family]/[family].py, sleeves/[family]/levels.py, sleeves/[family]/paper.py, sleeves/[family]/wire.py
- Rule lines: docs/verify/[family].md
- Accounting: docs/ALL-SLEEVES.json and docs/ALL-SLEEVES.md; catalog: docs/CATALOG.json

## Configuration

- Universe: 411 stocks as above. Asset: US equities. Timeframe: 1d, 1-minute passes.
- Sizing: 1.5% of equity at risk to the stop (2% of price without one), capped at 8% of equity; whole shares.
- Tier: the PPC coil is tier S and ranked first; the washout setup is the other setup in step 1.
- No separate roster config row for this strategy: not in the record.

## Data inputs

- Split-adjusted daily bars (300 sessions) with today bar from the live quote; live quotes.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and keep its layout.
2. Read the strategy card at the path listed above and this package.
3. Confirm the four code files listed above are present at their Test paths under sleeves/[family]/.
4. Wire split-adjusted daily bars (300 sessions), today bar from the live quote, and live quotes.
5. Run the desk pass on weekdays in the 09:35 to 15:45 ET window with 1-minute passes; the WashoutCoil lane evaluates steps 1 and 2, ranks the coil first, and admits through the next-support plan.
6. Run the Verification checks on fixtures before treating a recreation as faithful.

## Verification

Behaviour spec derived from the Full algorithm section. No per-strategy test file for this strategy is present in this repo.

- A name at or above the 50-day EMA, with RSI(14) at least 50, or failing every location in step 1 (retrace, shelf and 21-day), produces no washout buy.
- A coil candidate failing any bound in step 2 is not tier S and is not ranked first as a coil.
- Admission respects the window, caps and live price rules in steps 4 and 5, including at most 6 buys a pass.
- A qualifying buy is sized at 1.5% of equity at risk to the stop, capped at 8% of equity, whole shares.
- Trims, the single add, the under $75 sale and the bracket stop and target behave exactly as in steps 6 to 8.
- Read-back check: this doc was written through the PII gate and read back from Test; its sha256 matches the intended bytes, recorded in the batch results file.
