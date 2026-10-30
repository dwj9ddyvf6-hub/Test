# tensor2-washout-reclaim: Recreation package

## Provenance

Filed under a sanitized filename per the owner's ruling of 2026-10-30. The canonical strategy name in the ALL-SLEEVES accounting carries the originating research family name, which this repo's privacy gate does not allow in file paths or new content. The canonical name and this file's mapping are recorded in the owner's private recreation index. 35 mention(s) of that name in source material were replaced with a neutral placeholder or omitted; no rule, parameter, or code content was changed. The count covers the strategy card, the catalog entry and the ALL-SLEEVES accounting entry consulted for this package. Exact repo paths that carry that name are likewise shown below with a neutral placeholder for the name segment; the private recreation index holds the exact paths.

- ALL-SLEEVES accounting: canonical name "Tensor 2 washout / reclaim printer", type forecast and ML models, algorithm grade PARTIAL, with gaps in the accounting only: entry, exit and sizing not recorded in the accounting sources consulted there.
- Existing Test strategy card: strategies/[family]/[canonical id].md (full entry, exit, sizing, data and code text used in substance below).
- Catalog entry in docs/CATALOG.json: status waiting, style Washout reclaim, source "The originating desk Tensor 2 replica (src/lib/tensor/engine.ts); a recorder made a book by the owner D32".
- Code found in Test already: sleeves/[family]/monitor/printer_books.py, sleeves/[family]/monitor/[family]_tensor_mon.py, sleeves/[family]/monitor/reads.py and sleeves/[family]/monitor.py. The printer_books module contains the Tensor2Book for this transition id.
- Code not in this repo: the Tensor 2 replica engine itself, listed in the card as desk/vendor/[family]_mon/src/lib/tensor/engine.ts, and the card note says the replica it runs is not published in this repo. It was not found in the other repos searched below. For that reason this package is graded INCOMPLETE-CODE: the book and monitor code are present, the signal engine code is not.
- Code search record: Searched, in order: Test (fresh recursive tree in this run, 4647 tree lines, plus content reads of the strategy card, docs/CATALOG.json and docs/ALL-SLEEVES.json); Silicon (recursive tree, 24953 lines, no path named for this strategy); quant-research-backup (recursive tree, 47379 lines, no path named for this strategy); Midna (recursive tree, 7855 lines, no code path named for this strategy). Desk source read only: /home/hatch/workspace/muse-desk-v3 (no file named for this strategy). Midna holds only a data file data/tensor/h1/PPC.json, which is not this engine.

## What this strategy is

Tensor 2 washout / reclaim printer. It buys a watch-list name when the Tensor 2 replica prints a green buy on a completed hour after a washout, and sells when an hour closes red under its 21-hour EMA. Asset class US equities and ETFs. Timeframe 1h. Universe: the 13-name default watch list in the Full algorithm section. Status in the card: waiting. It was a recorder until owner ruling D32 (2026-10-26) funded it as a paper book; its first live signal was pending at the card pin.

## Full algorithm

Accounting grade PARTIAL: everything the record holds is written below, from the strategy card, in evaluation order.

1. Read once per completed canonical hour for each of the 13 names: SATL, SKYQ, RDW, INDI, SPY, QQQ, NVDA, MU, AAPL, AMD, TSLA, WULF, POET, once the frame holds 200 bars (the source authority).
2. Washout: within the last 9 hours, a bar low at the 12-hour swing low with RSI(14) at most 42.
3. Green buy, on the hour: no buy signal held and no green buy in the last 12 hours; a washout; the bar closes at or above its open; RSI(14) rising from a 9-hour trough at most 48 and still under 58, with the MACD histogram rising; at most 0.8 ATR(14) above EMA21; the close reclaiming EMA21 or at a reclaim or launch-pad location, never extended (over 1.2 ATR above it).
4. Orders: each decision once, at the book next pass in the session (from 5 minutes after the open): a market buy of one slot while the signal is buy and the name is not held, a market sell once it is no longer buy; a decision unsent by the close of the session after its bar lapses, and a name without a live equity quote is not bought.
5. Exit: out when the signal ends: an hour that closes below EMA21 on a red bar (the magenta sell); sold at the book next pass in the session. No stop of its own.
6. Sizing: an equal slot of the book equity divided by 13 a name; $100,000 book.

## Files in this repo

- This package: docs/TENSOR2_WASHOUT_RECLAIM-RECREATE.md
- Strategy card: strategies/[family]/[canonical id].md
- Code, already in Test, nothing vendored: sleeves/[family]/monitor/printer_books.py, sleeves/[family]/monitor/[family]_tensor_mon.py, sleeves/[family]/monitor/reads.py, sleeves/[family]/monitor.py
- Code not in this repo: the Tensor 2 replica engine (src/lib/tensor/engine.ts in the source desk vendor tree named in Provenance)
- Rule lines: docs/verify/[family].md
- Accounting: docs/ALL-SLEEVES.json and docs/ALL-SLEEVES.md; catalog: docs/CATALOG.json

## Configuration

- Universe: the 13 names in step 1. Asset: US equities and ETFs. Timeframe: 1h.
- Sizing and book: $100,000 book; equal slot equity / 13 per name.
- Authority bars: 200. Producer timing and staleness: see Data inputs.
- No separate roster config row for this strategy: not in the record.

## Data inputs

- Yahoo 60-minute bars (the desk canonical 1H series, a year, regular session) and daily bars (2 years); the producer job runs 2 to 11 minutes after each completed hour, and a read older than 90 minutes is not used.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and keep its layout.
2. Read the strategy card at the path listed above and this package.
3. Confirm the four monitor and printer-book code files listed above are present at their Test paths.
4. Supply the missing Tensor 2 replica engine from the owner private source before claiming a complete recreation: this package does not invent it, and the book code alone does not generate the signal.
5. Wire Yahoo 60-minute bars and daily bars as in Data inputs, plus live equity quotes, and run the producer 2 to 11 minutes after each completed hour.
6. Run the book pass from 5 minutes after the open in session; each decision trades once as in step 4.
7. Run the Verification checks on fixtures before treating a recreation as faithful.

## Verification

Behaviour spec derived from the Full algorithm section. No per-strategy test file for this strategy is present in this repo.

- A frame with fewer than 200 bars produces no read.
- No washout in the last 9 hours, or RSI(14) above 42 at the swing low, produces no green buy.
- A green buy requires every condition in step 3, including the 0.8 ATR upper bound and the never-extended 1.2 ATR rule.
- A held name exits only on an hour closing below EMA21 on a red bar, at the next in-session pass; there is no other stop.
- Sizing is exactly one equal slot, book equity / 13, per name.
- Completeness check: a recreation that cannot point to the replica engine code is INCOMPLETE-CODE, as graded here.
- Read-back check: this doc was written through the PII gate and read back from Test; its sha256 matches the intended bytes, recorded in the batch results file.
