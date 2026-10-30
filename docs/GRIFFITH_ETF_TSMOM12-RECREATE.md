# griffith-etf-tsmom12 - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "ETF 12-month time-series momentum", type momentum, family griffith, style time-series momentum, universe "13 ETFs on the tape of a frozen 17-ETF basket", asset class US ETFs, timeframe 1d (monthly), creator "Griffith R4 parallel strategy lab (ETF_TSMOM_12M)", algorithm grade PARTIAL with gaps: entry/signal rule, exit rule and sizing not recorded in any consulted source. Alias griffith_etf_tsmom12, status test_catalog live (entry griffith-etf-tsmom12).
- Test catalog entry: `docs/CATALOG.json` entry 'griffith-etf-tsmom12'.
- Strategy card in Test: `strategies/griffith/griffith-etf-tsmom12.md` ("Each month holds, in equal weight, every ETF of a frozen basket whose 252-session return is positive; cash otherwise." Family Griffith; source Griffith R4 parallel strategy lab (ETF_TSMOM_12M); status live). The card names the code: `sleeves/griffith/griffith_factor.py`, `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py`, `sleeves/griffith/feedlib/griffith.py`, rule lines in `docs/verify/griffith.md`.
- Code search record, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads of the three code files above and the card: all found in Test, listed under Files in this repo); dwj9ddyvf6-hub/Silicon (recursive tree: no griffith sleeve path; only unrelated rea-teardown assets); dwj9ddyvf6-hub/quant-research-backup (recursive tree: no griffith ETF-TSMOM code path); dwj9ddyvf6-hub/Midna (recursive tree: its tsmom scripts and reports are a separate TSMOM study, not this Griffith ETF book). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

A monthly, long-or-cash, equal-weight ETF time-series momentum book. Once a month it looks at each ETF in a frozen 17-name basket (13 of which the tape actually carries), keeps every ETF whose 252-session (12-month) return is positive, weights the survivors equally, and holds cash for the rest. There is no short side and no leverage in the record.

## Full algorithm

From the code in Test (`sleeves/griffith/griffith_factor.py` class R4MonthlyBook with sleeve_id griffith_etf_tsmom12 mapped to version ETF_TSMOM_12M_1_0_0, and the vendored `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py` function evaluate_etf_candidate). The accounting graded this PARTIAL; the rules below are supplied by the card and the code, and the accounting gaps are named at the end.

1. Decision timing: at the first pass of each month, the cutoff is the prior month's last SPY bar (month_end_cutoff in griffith_factor.py). A month is decided only on a tape carrying at least 99% of the names it can carry at the cutoff (coverage, EQ-02; COVERAGE = 0.99). For ETF books the expected names are the frozen basket intersected with the tape symbols, less the NOT_LISTED names no exchange lists. Until coverage is met the month waits undecided and the next pass asks again; a blocker signal intent records the shortfall.
2. Frozen basket (ETF_BASKET in the vendored lab): SPY, QQQ, IWM, DIA, XLF, XLK, XLE, XLI, XLY, XLP, XLV, XLU, XLB, XLRE, TLT, IEF, GLD (17 names). The tape never carries XLY, XLB, XLRE or IEF, so 13 names are tradable: SPY, QQQ, IWM, DIA, XLF, XLK, XLE, XLI, XLP, XLV, XLU, TLT, GLD. Each pick needs a bar on the cutoff day.
3. Per-ETF signal (evaluate_etf_candidate, version ETF_TSMOM_12M_1_0_0): the symbol must be in the frozen basket (else INELIGIBLE); bars are taken at or before the cutoff and the last bar's date must equal the cutoff date (else UNAVAILABLE, cutoff bar required); at least 253 bars are required; the metric is return252 = close[-1] / close[-253] - 1 (the 252-session return); status is SETUP when return252 > 0, otherwise WAIT. The lab spec records: family ETF_TIME_SERIES_MOMENTUM, lookback 252, rule LONG_IF_252_SESSION_RETURN_POSITIVE_ELSE_CASH, rebalance MONTH_END, horizonSessions 21, state IMPLEMENTED_SHADOW.
4. Selection and sizing: monthly_selection collects every basket ETF with status SETUP, sorted by symbol; each pick is held at equal weight 1/N of the book (the card: $100,000 book in equal weights; griffith_factor stores targets {symbol: 1/N}); names not selected go to zero; an empty selection is all cash.
5. Orders: rebalance children are marketable limits (the card: 1% through the quote, 30 minutes), re-sent on each of the month's first 5 sessions (RETRY_SESSIONS = 5 in the code). Named divergence in the code: entries trade the next regular open after the completed decision bar, where the source materializer booked the decision bar's own close; monthly books hold until the next month's rebalance (19-23 sessions) where the materializer's label measured exactly 21. The source materializer charged 10 bps per side (ONE_WAY_BPS = 10.0, adverse_one_way_bps).
6. Exit: a name out of the next month's pick is sold at that rebalance; an empty pick is cash. There is no intra-month stop or target in the record.
7. Fallback-tape rule in the code: a month decided on the keyless Yahoo fallback tape is decided again once, on the source's own IEX tape, when that tape becomes available (fresh order keys on the re-decision).
8. Accounting gaps, per the accounting itself: entry/signal rule, exit rule and sizing were not recorded in any consulted accounting source; steps 1-7 above come from the strategy card and the code in Test, not from the accounting.

## Files in this repo

- This package: `docs/GRIFFITH_ETF_TSMOM12-RECREATE.md`
- Sleeve code (already in Test): `sleeves/griffith/griffith_factor.py` (R4MonthlyBook; MONTHLY map griffith_etf_tsmom12 -> ETF_TSMOM_12M_1_0_0; coverage, month_end_cutoff, monthly_selection).
- Vendored source lab (already in Test): `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py` (ETF_BASKET, SPECS for ETF_TSMOM_12M_1_0_0, evaluate_etf_candidate).
- Tape feed (already in Test): `sleeves/griffith/feedlib/griffith.py`.
- Strategy card: `strategies/griffith/griffith-etf-tsmom12.md`.
- Rule lines: `docs/verify/griffith.md`.
- Accounting and catalog: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`; `docs/CATALOG.json` entry griffith-etf-tsmom12.
- Other copies of the same code in Test (already present, not the primary source): `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/griffith_factor.py`, `packages/claude/master-desk-parity-tools/tools/parity/griffith_factor.py`.

## Configuration

- SleeveConfig in griffith_factor.py R4MonthlyBook: sleeve_id griffith_etf_tsmom12, family griffith_factor, cadence_s 300, universe = the tape (SCOPE) symbols, needs feeds [griffith_iex_1d] and equity quotes, schedule rth, params {version_id: ETF_TSMOM_12M_1_0_0, cost_bps: 10.0, selection: "ETF basket"}, state_schema {month, targets}.
- Book size on the card: $100,000, equal weights.
- Constants in the code: COVERAGE 0.99, RETRY_SESSIONS 5, ONE_WAY_BPS 10.0, HORIZON 20 (the daily-book observation horizon in the same module; the monthly lab spec's horizonSessions is 21).
- Accounting-level configuration beyond the catalog entry: not in the record.

## Data inputs

- Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session (card Data section); the feed falls back to Yahoo daily bars without Alpaca credentials (code divergence note).
- SPY daily bars to derive the month-end cutoff.
- Equity quotes for the marketable-limit rebalance orders.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc, the accounting entry for this strategy in `docs/ALL-SLEEVES.json`, and the card `strategies/griffith/griffith-etf-tsmom12.md`.
3. Confirm `sleeves/griffith/griffith_factor.py`, `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py` and `sleeves/griffith/feedlib/griffith.py` are present at those paths.
4. Wire the griffith_iex_1d feed so each session's snapshot carries daily bars for the tape symbols (including SPY) and equity quotes, in the shapes the Full algorithm describes.
5. Register the sleeve as griffith_etf_tsmom12 with version_id ETF_TSMOM_12M_1_0_0 and run the desk cycle; the sleeve decides at the first pass of each month as described above.
6. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec derived from the Full algorithm (no per-sleeve test file for this exact canonical id is present in this repo):

- Signal: an ETF with 253 bars ending on the cutoff day and close[-1] / close[-253] - 1 exactly 0 is WAIT (not held); any positive value is SETUP; 252 bars is UNAVAILABLE and the name is not held.
- Coverage: a month whose tape carries under 99% of the expected ETF names produces no rebalance and a blocker signal; the next pass re-asks.
- Weights: with 4 SETUP ETFs, each target weight is 0.25 and every other held name's target is 0; with no SETUP ETF, the book is all cash.
- Exit: a name held last month and absent from this month's selection is sold at this rebalance.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
