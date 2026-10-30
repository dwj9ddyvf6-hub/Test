# killed-intraday-momentum-gao - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Intraday momentum (Gao et al.)", type momentum, family killed, style intraday momentum, universe SPY, QQQ, asset class US ETFs, timeframe 5m, creator "Gao, Han, Li and Zhou (2018) market intraday momentum; a killed study of the old Alpaca swing desk", algorithm grade PARTIAL with gaps: entry/signal rule, exit rule and sizing not recorded in any consulted source. Alias killed_intraday_momentum_gao, status test_catalog live.
- Test catalog entry: `docs/CATALOG.json` entry 'killed-intraday-momentum-gao'.
- Strategy card in Test: `strategies/killed/killed-intraday-momentum-gao.md` ("At 15:30 ET goes long or short SPY and QQQ in the direction of the first half hour's return, and exits at the close." Status live; notes: the master desk trades the short side; the old desk's long-only rail is dropped.) The card names the code: `sleeves/killed/killed_studies.py`, `sleeves/killed/intraday.py`, `sleeves/killed/common.py`, rule lines in `docs/verify/killed.md`.
- Sleeve registry in Test: `sleeves/killed/killed_studies.py` lists killed_intraday_momentum_gao as "SPY/QQQ sign(first-30-min) from 15:30 to the close (intraday.py)" among the killed studies forward-tested exactly as the killed formulation specified.
- Code search record, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads of `sleeves/killed/intraday.py`, `sleeves/killed/killed_studies.py`, `sleeves/killed/common.py` and the card: all found in Test, listed under Files in this repo; the vendored study source is also in Test at `sleeves/killed/vendor/midna_research/intraday_momentum_2026_10_02.py`); dwj9ddyvf6-hub/Silicon (recursive tree: no killed-studies sleeve path); dwj9ddyvf6-hub/quant-research-backup (recursive tree: no matching Gao sleeve code path); dwj9ddyvf6-hub/Midna (recursive tree: the original study files are the pinned source of the Test port, named by hash in the code SOURCE record; no separate executable sleeve for this id). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

The Gao, Han, Li and Zhou (2018) intraday-momentum study, forward-tested as a sleeve after the original study was killed: on each full trading day, measure SPY's and QQQ's first-half-hour return, then at 15:30 ET take a position in each symbol in the sign of that return (long if positive, short if negative), and exit at the 16:00 close the same day. It holds nothing overnight.

## Full algorithm

From the code in Test (`sleeves/killed/intraday.py` class IntradayMomentumGao, SLEEVE_ID killed_intraday_momentum_gao; tranche ledger in `sleeves/killed/common.py`). The accounting graded this PARTIAL; the rules below are supplied by the card and the code, and the accounting gaps are named at the end.

1. Day gate: plan runs once per day (state day marker). A non-trading day produces nothing. A half-day (session close before 16:00) produces no trade, only a signal intent with reason naming the half-day and "no last-30 window".
2. Clock gate: no decision before 15:30 ET (view.now at or after session close minus 30 minutes) and not after the sleeve's before_cutoff check.
3. First-half-hour return (r_first): build the day's 5-minute bar map by bar-start time. FIRST_HM = 09:30, 09:35, 09:40, 09:45, 09:50, 09:55. r_first = close of the 09:55 bar / open of the 09:30 bar - 1, only when all six first-window bars exist and their total volume is non-zero; otherwise the symbol is not eligible (a skip signal intent is recorded).
4. Entry: for each eligible symbol in universe (SPY, QQQ), in that order: if r_first > 0 take a long tranche, if r_first < 0 take a short tranche; r_first exactly 0 is not eligible and produces no trade. The tranche is added to the tranche book as open on the decision day with exit at that day's close ("open" leg on day d, "close" leg on day d), with the reason recording r_first.
5. Sizing: PARAMS notional = CAPITAL / 2 per symbol, with CAPITAL = 100,000 in common.py, i.e. $50,000 per symbol, fractional shares on both sides (the card's sizing line). WHOLE_SHORT = False in the class.
6. Exit: out market-on-close the same day (exit 16:00, the close of the 15:55 bar in the study formulation).
7. Named divergences recorded in the code (DIVERGENCES): entry is the first pass at or after 15:30:00 (marketable) instead of the 15:30 bar's open print; exit is the market-on-close order instead of the 15:55 bar's close; the last-window completeness and zero-volume exclusions cannot be known at 15:30, so the trade is taken and the exclusion is the post-hoc reader's; 5-minute bars are the hub's equity source (Alpaca SIP when keyed, else Yahoo consolidated 5m bars). Removed gate: the old desk's long-only rail (PARAMS removed_gates) - the short side trades.
8. Source pinning in the code: SOURCE names the vendored study intraday_momentum_2026-10-02.py with its preregistration and results documents (intraday_momentum_prereg_2026-10-02.md, Test 2, the tradable version) by blob hash; SPY is the primary and QQQ the secondary symbol in the class docstring.
9. Schedule and cadence in the code: SCHEDULE "close-31:close-9", CADENCE 60 seconds, NEEDS bars {source equity, interval 5m, n 120} and equity quotes for SPY and QQQ.
10. Accounting gaps, per the accounting itself: entry/signal rule, exit rule and sizing were not recorded in any consulted accounting source; steps 1-9 above come from the strategy card and the code in Test, not from the accounting.

## Files in this repo

- This package: `docs/KILLED_INTRADAY_MOMENTUM_GAO-RECREATE.md`
- Sleeve code (already in Test): `sleeves/killed/intraday.py` (IntradayMomentumGao, r_first, FIRST_HM / LAST_HM).
- Registry and common ledger (already in Test): `sleeves/killed/killed_studies.py` (sleeves() includes intraday.IntradayMomentumGao()), `sleeves/killed/common.py` (CAPITAL = 100,000, TrancheBook, LONG_ONLY_RAIL record).
- Vendored study source (already in Test): `sleeves/killed/vendor/midna_research/intraday_momentum_2026_10_02.py`.
- Strategy card: `strategies/killed/killed-intraday-momentum-gao.md`.
- Rule lines: `docs/verify/killed.md`.
- Accounting and catalog: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`; `docs/CATALOG.json` entry killed-intraday-momentum-gao.
- Other copies in Test (already present, not the primary source): `packages/claude/master-desk-sleeve-port-library/desk/sleeves/killed/intraday.py`, `packages/claude/master-desk-parity-tools/tools/parity/killed_gao.py`.

## Configuration

- Class values in intraday.py: SLEEVE_ID killed_intraday_momentum_gao, UNIVERSE (SPY, QQQ), SCHEDULE close-31:close-9, CADENCE 60, WHOLE_SHORT False, PARAMS {first_window: "09:30-10:00", entry: "15:30", exit: "16:00 (market-on-close)", notional: 50,000 per symbol, removed_gates: [the long-only rail]}.
- Common capital in common.py: CAPITAL = 100,000.
- Accounting-level configuration beyond the catalog entry: not in the record.

## Data inputs

- 5-minute equity bars, 120 bars, for SPY and QQQ (the day's first-window bars 09:30-09:55 with volume, and the session calendar for trading-day and half-day checks).
- Equity quotes for SPY and QQQ (NEEDS in the class).
- The trading calendar (is_trading_day, close_minutes) and the sleeve's per-day state marker.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc, the accounting entry in `docs/ALL-SLEEVES.json`, and the card `strategies/killed/killed-intraday-momentum-gao.md`.
3. Confirm `sleeves/killed/intraday.py`, `sleeves/killed/common.py` and `sleeves/killed/killed_studies.py` are present at those paths.
4. Wire the equity feed so each pass carries 5-minute bars (120) and quotes for SPY and QQQ, plus the trading calendar, in the shapes the Full algorithm describes.
5. Register the sleeve through killed_studies.sleeves() (or instantiate IntradayMomentumGao directly) and run the desk cycle on its 60-second cadence within the close-31:close-9 schedule.
6. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec derived from the Full algorithm (no per-sleeve test file for this exact canonical id is present in this repo):

- A day missing any of the six 09:30-09:55 bars for a symbol, or with zero total first-window volume, produces a skip signal for that symbol and no tranche.
- r_first exactly 0 produces no trade; r_first positive at 15:30 produces a long tranche of $50,000 notional in that symbol, negative a short tranche of $50,000.
- A half-day produces no tranche in either symbol, only the half-day signal intent.
- Every tranche opened is exited market-on-close the same day; nothing is held overnight, and a second plan call the same day produces nothing (day marker).
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
