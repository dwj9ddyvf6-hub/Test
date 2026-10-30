# next-support-plan recreation package

## Provenance

- Sanitized id: next-support-plan. Canonical id: recorded in the owner's private recreation index (see the disclosure below).
- Accounting: docs/ALL-SLEEVES.json and docs/ALL-SLEEVES.md in this repo, strategy entry "Next-support plan". Algorithm grade in the accounting: PARTIAL, with entry, exit and sizing listed as gaps in the accounting entry. The Test catalog card for this strategy, which the accounting itself cites as its source (Test catalog entry and variants), does record those rules in full, and the Full algorithm below is taken from that card.
- Catalog status in the card: live.
- Code search, in order: Test (found, see Files in this repo), Silicon (no path matching komar, next-support or scanner-book fragments), quant-research-backup (no matching filename; it does hold the older originating desk tree, which is not the code home cited by the card), Midna (no matching filename; same older desk tree copy).
- Filed under a sanitized filename per the owner's ruling of 2026-10-30. The canonical strategy name in the ALL-SLEEVES accounting carries the originating research family name, which this repo's privacy gate does not allow in file paths or new content. The canonical name and this file's mapping are recorded in the owner's private recreation index. 17 mention(s) of that name in source material were replaced with a neutral placeholder or omitted; no rule, parameter, or code content was changed. The count is the mentions in the ALL-SLEEVES accounting entry plus the Test catalog card for this strategy.

## What this strategy is

Next-support plan. Type: mean reversion. Style: support pullback. Asset class: US equities. Timeframe: 1d, with 1-minute passes. Universe: the 30-name folio list recorded on the card. Creator as recorded: the originating research desk, admit-ticker v1.1. In one line from the card: each morning it plans a buy at the next support under the last close for 30 names, and buys when the price trades within 3% of it.

## Full algorithm

Evaluation order, with the strategy's own parameter values:

1. Plan, built once a session from the last completed bar (admit-ticker v1.1). Buy price: the highest support at most 1.5% above the last close, where a support is a 38.2 to 78.6% retrace of the 60-day swing, the 21-day EMA, or the 12-day low, when that support is under 99.8% of the close; otherwise 1.5% under the close.
2. Plan stop and target: stop 0.6% under the 12-day low, kept 2.5 to 3.5% under the buy price. Target 5R, at least +6% and at most +18%, moved to the 21-day or 50-day EMA when one sits in that band.
3. Buy window and book caps: buys run 09:35 to 15:45 ET on weekdays, only for a name that is not held, not traded that day, with under 6 swings, under 10 open names, under 16 new buys a day, and under 2 names of one story (semis, software, EV, space, and the other story groups as recorded on the card). Caps count this sleeve's own book only.
4. Live trigger: at the live price, buy only within 3% of the plan buy price, above its stop and under its target, with the MACD histogram above its level 3 sessions back (or a coil). Best tier and best R first, at most 6 buys a pass, marketable order.
5. Exit: the plan stop and target ride as an engine-held bracket.
6. Trims: 20% when price is rejected at the first Fib above the buy (38.2, 50 or 61.8% of the 90-day range) with the gain under 35%; half after +50% within 8 days, or at a weekly RSI at or above 68 with a daily bearish divergence after +80%.
7. Add: one add when price is back within 2% of the 50-day or 200-day EMA after 5 of the prior 16 closes were below it.
8. A position worth under $75 is sold.
9. Sizing: 1.5% of equity at risk to the stop (2% of price without a stop), capped at 8% of equity, whole shares.
10. Notes carried on the card: the swing manager's other sells (a broken-then-rejected level, a Wave-B rejection) are re-judged without daily bars, so only a print through the stop confirms them. At the catalog pin the +50%-in-a-week trim is not recorded as a trim, so it repeats each pass while that holds, down to one share; a master-desk commit dated 2026-10-26 (hash 6d6ae54e) makes every trim fire once per position.

## Files in this repo

- This doc: docs/NEXT_SUPPORT_PLAN-RECREATE.md.
- Accounting entry: docs/ALL-SLEEVES.json and docs/ALL-SLEEVES.md (entry under the canonical name, which is withheld here per the disclosure).
- Catalog entry: docs/CATALOG.json (entry under the canonical id, withheld here) and the catalog card in the strategies directory under the canonical id (its path carries the blocked token, so it is not written here; it is recorded in the private recreation index).
- Code, already in Test, no vendoring needed: in the master-desk sleeve directory for this family (the directory segment and the main sleeve module basename both carry the blocked token, so neither is written here), the main sleeve module plus levels.py (14,273 bytes in the tree), paper.py (27,072 bytes) and wire.py (17,561 bytes). The card also points to a rule-lines verify doc under docs/verify/ whose filename carries the blocked token.
- Vendored in this package: none. The code was already present in Test, so nothing was copied into engines/universe/next-support-plan/.

## Configuration

- No separate configuration file is recorded for this strategy. Configuration is the plan parameters in the Full algorithm (support band, stop placement band, 5R target band, book caps, buy window) plus the catalog status, live.
- Anything else about configuration: not in the record.

## Data inputs

- Split-adjusted daily bars, 300 sessions, with today's bar taken from the live quote.
- Live quotes, on 1-minute passes inside the buy window.

## Install and run

1. Clone this repository (Test) and check out the main branch, keeping the directory layout unchanged.
2. Read this doc, the accounting entry in docs/ALL-SLEEVES.json, and the catalog card for this strategy (path in the private recreation index).
3. Locate the code named in Files in this repo: the main sleeve module, levels.py, paper.py and wire.py in the same sleeve directory.
4. Wire split-adjusted daily bars (300 sessions) and live quotes so each morning pass can build the plan from the last completed bar and each 1-minute pass can test the live trigger.
5. Build the plan once per session, then run buy passes only 09:35 to 15:45 ET on weekdays under the book caps, with the engine-held bracket, trims and add exactly as the Full algorithm states.
6. Verify against the Verification section before treating a recreation as faithful.

## Verification

Behaviour spec (no per-strategy test file for this exact id is recorded in this repo; this spec is the testable form of the rules above):

- A plan whose highest qualifying support is at or above 99.8% of the close falls back to a buy price 1.5% under the close.
- Every plan stop sits 0.6% under the 12-day low and between 2.5% and 3.5% under the buy price; every target is 5R clamped to +6% to +18%, or the 21-day or 50-day EMA when one sits in that band.
- No buy fires outside 09:35 to 15:45 ET on a weekday, for a held name, for a name traded that day, or beyond any book cap (6 swings, 10 open names, 16 new buys a day, 2 of one story, 6 buys a pass).
- No buy fires more than 3% from the plan buy price, at or under its stop, at or over its target, or without the MACD histogram condition or a coil.
- Position size targets 1.5% of equity at risk to the stop and never exceeds 8% of equity, in whole shares.
- A position worth under $75 is sold; the 20% Fib-rejection trim requires a gain under 35%.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
