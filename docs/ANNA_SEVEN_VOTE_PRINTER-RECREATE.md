# anna-seven-vote-printer - Recreation Package

## Provenance

- Sanitized filing: Filed under a sanitized filename per the owner's ruling of 2026-10-30. The canonical strategy name in the ALL-SLEEVES accounting carries the originating research family name, which this repo's privacy gate does not allow in file paths or new content. The canonical name and this file's mapping are recorded in the owner's private recreation index. 8 mention(s) of that name in source material were replaced with a neutral placeholder or omitted; no rule, parameter, or code content was changed.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Anna seven-vote printer", type forecast and ML models, style evidence "Tensor signal", algorithm grade PARTIAL in the accounting alone (entry, exit and sizing listed as not recorded there), unresolved false. The fuller record below comes from the code and the strategy card in this repo, which the accounting entry points to.
- Accounting fields: universe "13-name dashboard watchlist (SATL, SKYQ, RDW, INDI, SPY, QQQ, NVDA, MU, AAPL, AMD, TSLA, WULF, POET)", asset class US equities, timeframe 1d, creator recorded as the originating desk's Tensor dashboard Anna printer (anna-replica, before Tensor 2.0). Test catalog status for the canonical entry: live (1 entry). Variant: base form only; the single alias is the underscored form of the canonical id (not reproduced: it carries the blocked name).
- Strategy card in this repo: the card for this canonical id under `strategies/` in the family folder (path not reproduced: it carries the blocked name). It gives the entry, exit, sizing and data lines summarized and then verified against code below.
- Code search record, in order: dwj9ddyvf6-hub/Test (fresh recursive tree plus content reads of every file named below; all code for this strategy is present, including the original TypeScript replica library copies under the packages listed in Files in this repo); dwj9ddyvf6-hub/Silicon (fresh recursive tree; no path named for this strategy); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree; one copy of the original anna-replica library under a femto-lean vendor path, the same source the Test port was made from; nothing needed vendoring because the port and the library copies are already in Test); dwj9ddyvf6-hub/Midna (fresh recursive tree; two copies of the original anna-replica library in a research engine tree; same conclusion). Desk source read only at muse-desk-v3 for cross checking.
- Code grade: complete. The executable Python port, its indicator library, its watchlist source file, and its execution sleeve are all in Test.

## What this strategy is

A daily printer that holds each of 13 dashboard watchlist names while the seven vote Anna printer reads buy, and sells when it turns sell or the 200 day EMA is lost. It is the historical printer from the Tensor dashboard, the last version before Tensor 2.0 retired it, kept as a live paper sleeve.

## Full algorithm

Evaluation order, from the code in this repo: the replica in `sleeves/[family]/anna.py` (build_anna_replica, default variant), and the execution sleeve AnnaPrinter in the family module in `sleeves/[family]/` (the main family module; its filename carries the blocked name and is not reproduced).

1. Universe and bars: the dashboard default watchlist, read in code from the vendored desk-store source file: SATL, SKYQ, RDW, INDI, SPY, QQQ, NVDA, MU, AAPL, AMD, TSLA, WULF, POET (13 names). Bars are split adjusted daily bars, 500 sessions requested. A name needs 200 bars before a marker counts (AUTHORITY_BARS 200 in the replica module; the replica itself returns nothing under 35 bars).
2. Indicators per name: EMA 8, 13, 21, 34, 48 and 200; Bollinger and Keltner bands from the squeeze block; ATR 14 (Wilder); RSI 14; MACD; relative volume over 20; session VWAP; the Strat bar classification. Squeeze epoch table (default variant): E0 (from the start), E1 (2026-04-11), E2 (2026-04-16), E3 (2026-04-27) and E4 (2026-05-22) read squeeze length 14 and momentum length 9; E4b (2026-06-17) and E5 (2026-07-26) read squeeze length 20 and momentum length 10. The strategy card records the same fact as: squeeze length 20, momentum 10 (14 and 9 before 2026-06-17).
3. Seven votes on each completed daily bar: (a) Stochastic RSI K over D (RSI 14, stochastic 14, K smoothing 3, D smoothing 3; if K equals D the vote follows the 1 bar slope of K); (b) Aroon up over down, length 14; (c) plus DI over minus DI, length 14 Wilder; (d) OBV 5 bar slope positive; (e) squeeze momentum (linear regression endpoint over the epoch momentum length; bullish if its 1 bar slope is positive, else if the value is at least 0); (f) EMA 8 over EMA 21; (g) WaveTrend 1 over 2 (channel 10, average 21, smoothing 4). An unreadable vote is unavailable.
4. Buy gate: all seven votes available, at least 5 bullish, and bullish minus bearish at least 4.
5. Markers: a UT Bot flip up (ATR length 10, sensitivity 1) through the gate is CYAN_BUY. An EMA 8 over 21 cross up within 6 bars of a UT Bot up flip, through the gate, is GREEN_BUY. A UT Bot flip down is RED_SELL. An EMA 8 over 21 cross down within 6 bars of a UT Bot down flip is MAGENTA_SELL. On a same bar clash in this default variant the sell marker wins.
6. Location printer (classify_location in the same module, options deepRel 0.65, minBull 5, invertLaunchpadSell true, warnUpgrade false, padSequence true, supportBounce true, reclaimAllowRed true, warnConfirm true, holdCyan false, holdLook 22, holdRel 0.94, holdLast true, holdLastBars 2): locations are above, below, reclaim, launchpad (deep pad at rel at most 0.65, or washout with drawdown at least 0.18, days above at most 2 and pos20 at most 0.65), failed euphoria (pos20 at least 0.88, bbPct at least 1.2, stochastic K at least 88, not above), extended (days above at least 8, pos20 at least 0.88, bbPct at least 0.85, stochastic K at least 85), and fight (within 0.6 times ATR 14 of EMA 200). Re prints: a sell print on a deep pad with at least 5 bullish votes inverts to a buy; a reclaim with bbPct 0.35 to 0.92 is an extra buy; a pad sequence buy needs at least 6 bullish votes, rising squeeze momentum, bbPct 0.20 to 1.05 and close at or over the open, with no buy print in the prior 8 bars; a support bounce buy needs at least 5 bullish votes, rel 0.82 to 1.04, bbPct 0.20 to 1.05, close at or over the open, pos20 0.35 to 0.85 and the low within 1.5 times ATR 14 of the 10 bar low; a warn confirm buy follows a GOLD_WARNING with at least 5 bullish votes and rel 0.88 to 1.05. A failed euphoria or an extended failure is an extra sell.
7. Sell suppression (the strategy card's hold rule): a sell marker within 2 bars of a buy flip is ignored while price is at least 94 percent of the 200 day EMA (rel at least 0.94), unless the bar is a failed euphoria or an extended failure. In code this is apply_printer with the hold options in step 6.
8. Signal persistence: buy on CYAN or GREEN, sell on RED or MAGENTA, otherwise the previous signal carries, except that while the previous signal is buy, a close crossing below EMA 200 (previous close at or over EMA 200) turns the signal to sell.
9. Execution (AnnaPrinter): cadence 60 seconds, schedule regular trading hours plus after_close+20 to after_close+240. After the session close, for each watchlist name whose last daily bar is that session and which has at least 200 bars, the sleeve computes the replica and records a todo for the next trading day: buy for a name with signal buy and not held, sell for a name with signal sell and held. Each session is printed once.
10. Orders: at the next session's first regular hours pass, each todo row is sent once: a buy is an enter intent for a notional of one slot (book equity divided by 13) with the live quote as price hint, and only if that quote is over 0; a sell is an exit intent for the held name. No stop or target of its own is attached; the exit is step 8's signal change.

## Files in this repo

- This package: `docs/ANNA_SEVEN_VOTE_PRINTER-RECREATE.md`
- Replica code (already in Test; nothing vendored): `sleeves/[family]/anna.py` (build_anna_replica, the votes, the gate, the markers, classify_location; [family] denotes the family directory whose name carries the blocked name and is not reproduced) and `sleeves/[family]/tensor.py` (the shared indicator library it imports).
- Execution code (already in Test): the main family module in `sleeves/[family]/` (its filename carries the blocked name; it is the 70,995 byte module whose AnnaPrinter class carries the sleeve id for this strategy), and the vendored watchlist source `sleeves/[family]/vendor/[family]/desk-store.ts` (the inner vendor folder name also carries the blocked name; the file itself is desk-store.ts, which holds DEFAULT_WATCH).
- Original library copies (already in Test): the anna-replica library under `packages/ausar/aster-desk-r13-baseline/` and `packages/ausar/aster-execution-r15/` in their tensor engine lib folders, and the port library copy under `packages/claude/master-desk-sleeve-port-library/` in its family sleeves folder (file anna.py there).
- Parity tools (already in Test): `packages/claude/master-desk-parity-tools/tools/parity/` holds the family parity set named in the code headers (the anna parity file is named for the family there and is not reproduced).
- Strategy card (already in Test): the card for this canonical id in `strategies/[family]/` (path not reproduced: it carries the blocked name).
- Accounting: `docs/ALL-SLEEVES.json` and `docs/ALL-SLEEVES.md`, entry "Anna seven-vote printer".

## Configuration

- Sleeve config in code (AnnaPrinter): cadence 60 seconds; schedule "rth,after_close+20:after_close+240"; needs: split adjusted equity daily bars, 500 sessions, and live equity quotes; title "Historical seven-vote Anna printer" (the full title in code carries the blocked name before "seven-vote").
- Source pin in code: the replica source is pinned to commit 7683c7dd of the originating desk repo, file src/lib/tensor/anna-replica.ts, with its printer, epochs and indicator files at the pins recorded in the anna.py header. The repo name itself carries the blocked name and is not reproduced.
- Replica constants: AUTHORITY_BARS 200, minimum replica bars 35, location options and epoch table as in steps 2 and 6 of the Full algorithm.
- Sizing: an equal slot, book equity divided by 13 per name. No other sizing configuration is in the record.

## Data inputs

- Split adjusted daily bars, 500 sessions, for the 13 watchlist names.
- Live equity quotes at the execution pass, for the buy price hint and the quote over 0 check.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo layout unchanged.
2. Read this package and the accounting entry in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/[family]/anna.py` and confirm the votes, the gate, the markers, the epoch table and classify_location match steps 2 to 8.
4. Open the main family module in `sleeves/[family]/`, find AnnaPrinter, and confirm its universe (DEFAULT_WATCH from desk-store.ts), its 200 bar authority check, its after close todo, and its slot sizing match steps 1, 9 and 10.
5. Run the sleeve on a completed session, then at the next session's first pass, and verify against the Verification section before treating any recreation as faithful.

## Verification

- Behavior spec, from the recorded algorithm: no decision for a name under 200 bars; a buy only when the gate in step 4 holds and the print is CYAN or GREEN (including a location re print in step 6); a sell on RED or MAGENTA or the EMA 200 cross in step 8, subject to the suppression in step 7; a same bar clash resolves to sell in this variant; sizing is always equity divided by 13; a todo row is sent at most once, at the next session's first pass.
- Parity: the anna.py header names its Node parity tool in this repo's master desk parity package; the port was proved against the TypeScript source under Node 22 per that header.
- Read back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read back bytes.
