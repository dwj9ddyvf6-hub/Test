# scanner-book-swing recreation package

## Provenance

- Sanitized id: scanner-book-swing. Canonical id: recorded in the owner's private recreation index (see the disclosure below).
- Accounting: docs/ALL-SLEEVES.json and docs/ALL-SLEEVES.md in this repo, strategy entry "Scanner book swing". Algorithm grade in the accounting: PARTIAL, with entry, exit and sizing listed as gaps in the accounting entry, and type recorded as other because the accounting read only the style text. The Test catalog card for this strategy, which the accounting itself cites as its source (Test catalog entry and variants), does record those rules in full, and the Full algorithm below is taken from that card.
- Catalog status in the card: waiting.
- Code search, in order: Test (found, see Files in this repo), Silicon (no path matching komar, next-support or scanner-book fragments), quant-research-backup (no matching filename; it does hold the older originating desk tree, which is not the code home cited by the card), Midna (no matching filename; same older desk tree copy).
- Filed under a sanitized filename per the owner's ruling of 2026-10-30. The canonical strategy name in the ALL-SLEEVES accounting carries the originating research family name, which this repo's privacy gate does not allow in file paths or new content. The canonical name and this file's mapping are recorded in the owner's private recreation index. 20 mention(s) of that name in source material were replaced with a neutral placeholder or omitted; no rule, parameter, or code content was changed. The count is the mentions in the ALL-SLEEVES accounting entry plus the Test catalog card for this strategy.

## What this strategy is

Scanner book swing. Type in the accounting: other. Style: structural swing. Asset class: US equities. Timeframe: 1d, with a 5-minute session tape. Universe: the 411-stock universe described in the card as Signal Prism US 413 without its two crypto pairs. Creator as recorded: the originating research desk, the scanner book (desk-scan plus buy-desk). In one line from the card: it buys the Signal Prism scan's best S and A-grade events at support in a turning sector, on the next-support plan (see docs/NEXT_SUPPORT_PLAN-RECREATE.md for that plan's own package).

## Full algorithm

Evaluation order, with the strategy's own parameter values:

1. Scan, once a session, on the last completed session: the nine Signal Prism engines (Vector, Meridian, Cascade, Threshold, Fissure, Dread, Reverb, Zenith, Strata), with SPY as the benchmark.
2. Candidate: an S or A-grade event, or a first-defense event, that is not contradicted and is developing or expired; the selection read must say BUY (a coil, a washout, or a held level with two confirmations), and the name needs a washout, a coil, a bottom-screen buy, or an RSI or MACD curl.
3. Sector gate: the name's sector ETF must be turning against SPY. Waterfall, trend and trough sectors, and names without a sector ETF, are skipped; cyclicals wait in a risk-off tape.
4. Book build: the Prism candidates first (S tier and curl first), then the bottom screen's buys, up to 20 names, each put on the next-support plan. A name is dropped when RSI is at or above 50 off support.
5. Book maintenance: the book is rebuilt every 10 minutes. Outside 11:25 to 11:55 and 14:10 to 14:50 ET, each name is re-read on the 5-minute session tape: dropped when 3% through the buy price, at its stop, or within 1% of its target, and the plan is rebased to the last print.
6. Buys: 09:35 to 15:45 ET on weekdays, only for a name that is not held, not traded that day, with under 6 swings, under 10 open names, under 16 new buys a day, and under 2 names of one story. At the live price, buy only within 3% of the plan buy price, above its stop and under its target, with the MACD histogram above its level 3 sessions back (or a coil). Best tier and best R first, at most 6 buys a pass, marketable order. Caps count this sleeve's own book only.
7. Exit: the plan stop and target ride as an engine-held bracket, on the terms in the next-support plan.
8. Trims: 20% when price is rejected at the first Fib above the buy (38.2, 50 or 61.8% of the 90-day range) with the gain under 35%; half after +50% within 8 days, or at a weekly RSI at or above 68 with a daily bearish divergence after +80%.
9. Add: one add when price is back within 2% of the 50-day or 200-day EMA after 5 of the prior 16 closes were below it.
10. A position worth under $75 is sold.
11. Sizing: 1.5% of equity at risk to the stop (2% of price without a stop), capped at 8% of equity, whole shares.
12. Notes carried on the card: the swing manager's other sells (a broken-then-rejected level, a Wave-B rejection) are re-judged without daily bars, so only a print through the stop confirms them. At the catalog pin the +50%-in-a-week trim is not recorded as a trim, so it repeats each pass while that holds, down to one share; a master-desk commit dated 2026-10-26 (hash 6d6ae54e) makes every trim fire once per position.

## Files in this repo

- This doc: docs/SCANNER_BOOK_SWING-RECREATE.md.
- Accounting entry: docs/ALL-SLEEVES.json and docs/ALL-SLEEVES.md (entry under the canonical name, which is withheld here per the disclosure).
- Catalog entry: docs/CATALOG.json (entry under the canonical id, withheld here) and the catalog card in the strategies directory under the canonical id (its path carries the blocked token, so it is not written here; it is recorded in the private recreation index).
- Code, already in Test, no vendoring needed: in the master-desk sleeve directory for this family (the directory segment and the main sleeve module basename both carry the blocked token, so neither is written here), the main sleeve module plus book.py (100,103 bytes in the tree), prism.py (70,535 bytes), levels.py (14,273 bytes), paper.py (27,072 bytes) and wire.py (17,561 bytes). The card also points to a rule-lines verify doc under docs/verify/ whose filename carries the blocked token.
- Vendored in this package: none. The code was already present in Test, so nothing was copied into engines/universe/scanner-book-swing/.
- Companion package: docs/NEXT_SUPPORT_PLAN-RECREATE.md, for the plan this book trades on.

## Configuration

- No separate configuration file is recorded for this strategy. Configuration is the scan, sector, book and plan parameters in the Full algorithm (engine list, grade and event filters, book cap of 20, 10-minute rebuild, re-read blackout windows, buy window and book caps) plus the catalog status, waiting.
- Anything else about configuration: not in the record.

## Data inputs

- Split-adjusted daily bars, 502 sessions.
- Extended-hours 5-minute bars with the forming bar, for the session tape re-reads.
- Live quotes.
- Sector ETF prices relative to SPY, and SPY as the scan benchmark.

## Install and run

1. Clone this repository (Test) and check out the main branch, keeping the directory layout unchanged.
2. Read this doc, the accounting entry in docs/ALL-SLEEVES.json, the catalog card for this strategy (path in the private recreation index), and docs/NEXT_SUPPORT_PLAN-RECREATE.md.
3. Locate the code named in Files in this repo: the main sleeve module, book.py, prism.py, levels.py, paper.py and wire.py in the same sleeve directory.
4. Wire split-adjusted daily bars (502 sessions), extended-hours 5-minute bars with the forming bar, live quotes, and sector ETF and SPY prices in the shapes the code expects.
5. Run the scan once per session on the last completed session, build the book up to 20 names on the next-support plan, rebuild it every 10 minutes, re-read names on the 5-minute tape outside the two blackout windows, and run buy passes only 09:35 to 15:45 ET on weekdays under the book caps.
6. Verify against the Verification section before treating a recreation as faithful.

## Verification

Behaviour spec (no per-strategy test file for this exact id is recorded in this repo; this spec is the testable form of the rules above):

- A candidate that is contradicted, is neither S or A-grade nor first-defense, lacks a BUY selection read, or lacks a washout, coil, bottom-screen buy or RSI or MACD curl does not enter the book.
- A name in a waterfall, trend or trough sector, a name without a sector ETF, and a cyclical in a risk-off tape are skipped.
- The book never holds more than 20 names; Prism candidates rank ahead of bottom-screen buys, S tier and curl first; a name at RSI at or above 50 off support is dropped.
- On a 5-minute re-read outside the blackout windows, a name 3% through its buy price, at its stop, or within 1% of its target is dropped and its plan rebased to the last print; inside 11:25 to 11:55 or 14:10 to 14:50 ET no such re-read drop fires.
- No buy fires outside the buy window, beyond any book cap, more than 3% from the plan buy price, at or under its stop, at or over its target, or without the MACD histogram condition or a coil.
- Position size targets 1.5% of equity at risk to the stop and never exceeds 8% of equity, in whole shares; a position worth under $75 is sold.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
