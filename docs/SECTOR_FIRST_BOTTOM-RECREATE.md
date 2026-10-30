# sector-first-bottom: Recreation package

## Provenance

Filed under a sanitized filename per the owner's ruling of 2026-10-30. The canonical strategy name in the ALL-SLEEVES accounting carries the originating research family name, which this repo's privacy gate does not allow in file paths or new content. The canonical name and this file's mapping are recorded in the owner's private recreation index. 32 mention(s) of that name in source material were replaced with a neutral placeholder or omitted; no rule, parameter, or code content was changed. The count covers the strategy card, the catalog entry and the ALL-SLEEVES accounting entry consulted for this package. Exact repo paths that carry that name are likewise shown below with a neutral placeholder for the name segment; the private recreation index holds the exact paths.

- ALL-SLEEVES accounting: canonical name "Sector-first bottom", type other, algorithm grade PARTIAL, with gaps in the accounting only: entry, exit and sizing not recorded in the accounting sources consulted there. Classification evidence in the accounting: only style Bottom recovery was recorded there, with no rule in any consulted accounting source.
- Existing Test strategy card: strategies/[family]/[canonical id].md (full entry, exit, sizing, data and code text used in substance below; the card supplies the rules the accounting omitted).
- Catalog entry in docs/CATALOG.json: status waiting, style Bottom recovery, source "originating research family / GrokBot desk, bottom screen v1.0".
- Code found in Test already: the master desk module named for the family, plus book.py, levels.py, paper.py and wire.py, all under sleeves/[family]/ in this repo. The main module contains the bottom lane: a scan lane for this strategy at its sleeves() registration, the bottom screen distillation and the sector tape read cited in the card notes.
- Code search record: Searched, in order: Test (fresh recursive tree in this run, 4647 tree lines, plus content reads of the strategy card, docs/CATALOG.json and docs/ALL-SLEEVES.json); Silicon (recursive tree, 24953 lines, no path named for this strategy); quant-research-backup (recursive tree, 47379 lines, no path named for this strategy); Midna (recursive tree, 7855 lines, no code path named for this strategy). Desk source read only: /home/hatch/workspace/muse-desk-v3 (no file named for this strategy).

## What this strategy is

Sector-first bottom. It buys a cheap, liquid stock basing under its long averages when its sector has turned against SPY, on the next-support plan. Asset class US equities. Timeframe 1d with a 5m session tape. Universe: the 411-stock universe described in the card (Signal Prism US 413 without its two crypto pairs). Status in the card: waiting.

## Full algorithm

Accounting grade PARTIAL: everything the record holds is written below, from the strategy card, in evaluation order. No entry, exit or sizing rule is in the accounting itself; the card is the source for the rules below.

1. Bottom screen on the scan daily bars: single names only (no index products), price at least $8, 20-day dollar volume at least $15M, no more than a 70% collapse over 60 days (the card wording: no > 70% 60-day collapse).
2. Points. Quality: above 45% of the 200-day, no > 45% 60-day drop, at least $25M volume. Cheap: 18 to 55% off the 52-week high, 3 to 28% under the 200-day. Sector: lagging SPY over 126 days, leading over 20 days, its ETF turning. Structure: a contracting base, a spring. A selling climax. Impulse: on the 21-day under the 50-day, the 21-day rising.
3. Buy threshold: at least 8 points with at least 2 turn points (structure, climax, impulse), cheap at least 1 and quality at least 2. Under 9 points it waits while SPY is under its 200-day with a new 20-day low, or the tape is risk-off.
4. Sector filter: waterfall, trend and trough sectors and names without a sector ETF are skipped; cyclicals wait in a risk-off tape.
5. Book: up to 20 names by R, on the next-support plan; dropped when RSI is at least 50 off support; the same 10-minute rebuild and session-tape re-read as the Scanner book swing.
6. Admission window and caps: buys 09:35 to 15:45 ET on weekdays; not held, not traded that day, under 6 swings, 10 open names, 16 new buys a day and 2 of one story (semis, software, EV, space and the other story groups named in the source).
7. Live price admission: only within 3% of the plan buy, above its stop and under its target, with the MACD histogram above its level 3 sessions back (or a coil); best tier and R first, at most 6 buys a pass; marketable order.
8. Exit, bracket: the plan stop and target ride as an engine-held bracket.
9. Exit, trims: 20% when price is rejected at the first Fib above the buy (38.2 / 50 / 61.8% of the 90-day range) with the gain under 35%; half after +50% within 8 days, or at a weekly RSI at least 68 with a daily bearish divergence after +80%.
10. Exit, add and dust: one add when price is back within 2% of the 50-day or 200-day EMA after 5 of the prior 16 closes below it. A position worth under $75 is sold.
11. Notes from the card: the swing manager other sells (a broken-then-rejected level, a Wave-B rejection) are re-judged without daily bars, so only a print through the stop confirms them. At the catalog pin the +50%-in-a-week trim is not recorded as a trim, so it repeats each pass while that holds, down to one share; master-desk commit 6d6ae54e (2026-10-26) makes every trim fire once per position. Caps count this sleeve own book only.

## Files in this repo

- This package: docs/SECTOR_FIRST_BOTTOM-RECREATE.md
- Strategy card: strategies/[family]/[canonical id].md
- Code, already in Test, nothing vendored: sleeves/[family]/[family].py, sleeves/[family]/book.py, sleeves/[family]/levels.py, sleeves/[family]/paper.py, sleeves/[family]/wire.py
- Rule lines: docs/verify/[family].md
- Accounting: docs/ALL-SLEEVES.json and docs/ALL-SLEEVES.md; catalog: docs/CATALOG.json

## Configuration

- Universe: 411 stocks as above. Asset: US equities. Timeframe: 1d, 5m session tape.
- Sizing: 1.5% of equity at risk to the stop (2% of price without one), capped at 8% of equity; whole shares.
- Book caps: up to 20 names by R in the plan book; admission caps in step 6 above (10 open names, 16 new buys a day, 2 of one story, at most 6 buys a pass).
- No separate roster config row for this strategy: not in the record.

## Data inputs

- Split-adjusted daily bars (502 sessions) of the universe, SPY and 18 sector and regime ETFs; extended-hours 5-minute bars; live quotes.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and keep its layout.
2. Read the strategy card at the path listed above and this package.
3. Confirm the five code files listed above are present at their Test paths under sleeves/[family]/.
4. Wire split-adjusted daily bars (502 sessions) for the universe, SPY and the 18 sector and regime ETFs, extended-hours 5-minute bars, and live quotes.
5. Run the desk scan and book pass on weekdays in the 09:35 to 15:45 ET window; the bottom lane distils buys through the admission rules above and the engine-held bracket manages exits.
6. Run the Verification checks on fixtures before treating a recreation as faithful.

## Verification

Behaviour spec derived from the Full algorithm section. No per-strategy test file for this strategy is present in this repo.

- A name under $8, with 20-day dollar volume under $15M, or with a > 70% 60-day collapse produces no buy.
- A candidate scoring under 8 points, or with fewer than 2 turn points, or cheap under 1, or quality under 2, produces no buy.
- A name in a waterfall, trend or trough sector, or without a sector ETF, is skipped; a cyclical in a risk-off tape waits.
- A qualifying buy is sized at 1.5% of equity at risk to the stop, capped at 8% of equity, whole shares, and respects the caps in step 6.
- Trims, the single add, the under $75 sale and the bracket stop and target behave exactly as in steps 8 to 10.
- Read-back check: this doc was written through the PII gate and read back from Test; its sha256 matches the intended bytes, recorded in the batch results file.
