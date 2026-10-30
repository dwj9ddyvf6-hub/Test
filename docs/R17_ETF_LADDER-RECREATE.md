# r17-etf-ladder: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "R17 ETF ladder rules", type market timing and rotation, family ausar, style "Momentum rotation", universe "QQQ, SPY, SMH and the 11 sector SPDRs", asset class US ETFs, timeframe "1d, monthly", creator "Ausar R17 ETF research". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `r17-etf-ladder` (`docs/CATALOG.json`): card `strategies/ausar/r17-etf-ladder.md`, status live x 6, rows r17_accel3, r17_escape1, r17_leader3, r17_relative3, r17_repair3, r17_voladj3.
- Variants (accounting): the six rules LEADER3, RELATIVE3, VOLADJ3, ACCEL3, REPAIR3 (3 slots each) and ESCAPE1 (1 slot).
- Code provenance recorded in the code itself (`sleeves/ausar/r17_etf.py` header): the vendored ladder logic originates in dwj9ddyvf6-hub/quant-research-backup at commit d170596b, path `research-archives/2026-10-09-third-pass-edge-r17/inventions/run_ladder.py` (blob 0392bb5d) with its EXPERIMENT_PROTOCOL.json (blob e0c26c42), both vendored in Test under `sleeves/ausar/vendor/quant_r17/`.
- Search record: a fresh recursive tree of dwj9ddyvf6-hub/Test was taken at batch start and searched by filename for the canonical id, its alias and its distinguishing tokens, across sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, laz_sleeves/, config/ and docs/; the Silicon, quant-research-backup and Midna trees in this run's workspace were searched the same way. The code is already in Test; no other distinct code for this strategy was found in Silicon or Midna.

## What this strategy is

Six monthly ETF selection rules (relative strength, acceleration, repair, volatility-adjusted) that put unused slots in QQQ. One canonical package covers all six rules, which share one engine, one universe and one sizing law and differ only in their selection rule and slot count.

## Full algorithm

From `strategies/ausar/r17-etf-ladder.md` and the wrapper header in `sleeves/ausar/r17_etf.py`, in evaluation order:

1. Decision: month-end, on the completed month-end close. Signals: 126- and 21-day log returns, 63-day volatility, 200-day MA, 20-day drawdown. A decision needs 252 QQQ sessions through the signal close. Closes are all-adjusted (total-return) daily closes on QQQ's session axis, NaN where a fund has no bar.
2. Selection rules:
   - LEADER3: top 3 by 126-day return.
   - RELATIVE3: top 3 beating QQQ.
   - VOLADJ3: relative strength / volatility.
   - ACCEL3: (21-day - 126-day/6) / volatility, above the 200-day MA.
   - REPAIR3: beating QQQ, 2-10% off the 20-day high, up 3 days, above the 200-day MA.
   - ESCAPE1: best positive 126-day return above the 200-day MA (1 slot).
3. Unfilled slots go to QQQ (ESCAPE1 stays in cash).
4. Execution (wrapper book law for the protocol's primary cell): pending weights x gross become desired units at the next open, from that open's marks and the pretrade NAV; desired units persist until the next decision. Each open: sells first. Each fund is capped at 0.1% of its prior-session raw dollar volume, the cap shared by sells then buys; buys are scaled to settled cash / (1 + cost). Sale proceeds settle T+1 and cannot be spent before then. Units are fractional. Each side costs 15 bps.
5. Exit: held to the next month-end decision; sells first at the open. No stop is recorded.
6. Sizing: equal weights x gross 0.98; cash account; $100,000 book (the primary cell recorded in the wrapper header).

## Files in this repo

- This package: `docs/R17_ETF_LADDER-RECREATE.md`
- Strategy card: `strategies/ausar/r17-etf-ladder.md`
- Code (already in Test): `sleeves/ausar/r17_etf.py`, `sleeves/ausar/vendor/quant_r17/run_ladder.py`, `sleeves/ausar/vendor/quant_r17/EXPERIMENT_PROTOCOL.json`; parity tool `packages/claude/master-desk-parity-tools/tools/parity/r17_etf.py`
- Rule lines: `docs/verify/ausar.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Original GitHub home of the vendored ladder logic: dwj9ddyvf6-hub/quant-research-backup, `research-archives/2026-10-09-third-pass-edge-r17/inventions/run_ladder.py` at commit d170596b (as recorded in the Test code header; already vendored in Test, so nothing was vendored by this package).

## Configuration

- Universe: QQQ, SPY, SMH and the 11 sector SPDRs. Timeframe: 1d, monthly decisions.
- Six sleeves, one per rule: r17_leader3, r17_relative3, r17_voladj3, r17_accel3, r17_repair3 (3 slots each), r17_escape1 (1 slot).
- Book: $100,000 cash account, gross 0.98, 15 bps per side, per-fund cap 0.1% of prior-day dollar volume.

## Data inputs

- Total-return (all-adjusted) daily closes and raw dollar volume for the universe, on QQQ's session axis; 252 QQQ sessions required through the signal close.

## Install and run

1. Clone the Test repo.
2. Read `strategies/ausar/r17-etf-ladder.md`, the matching section of `docs/verify/ausar.md`, and the header of `sleeves/ausar/r17_etf.py`.
3. Use the code files listed in Files as the runnable logic: `sleeves/ausar/r17_etf.py` loads the vendored `weights(rule, closes, i)` from `sleeves/ausar/vendor/quant_r17/run_ladder.py`.
4. Provide the data inputs listed above.
5. Run monthly: decide after each month-end close, execute at the next open sells-first, and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test; a parity tool exists at `packages/claude/master-desk-parity-tools/tools/parity/r17_etf.py`. Behaviour checklist from the algorithm above:

- Each rule selects exactly as defined in step 2, with 3 slots for LEADER3 / RELATIVE3 / VOLADJ3 / ACCEL3 / REPAIR3 and 1 for ESCAPE1.
- Unfilled slots go to QQQ, except ESCAPE1 which stays in cash.
- Weights are equal x gross 0.98, no fund exceeds 0.1% of its prior-day dollar volume, and each side is charged 15 bps.
- Positions are held to the next month-end decision and sells execute before buys at that open.
