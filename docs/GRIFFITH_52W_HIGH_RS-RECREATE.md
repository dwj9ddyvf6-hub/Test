# griffith-52w-high-rs - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "52-week-high strength", type momentum, family griffith, style evidence "52-week-high momentum", universe "SCOPE universe: 550 US names", asset class US equities, timeframe 1d (monthly), creator "Griffith R4 parallel strategy lab (HIGH52_MONTHLY)", algorithm grade PARTIAL with gaps: entry/signal rule, exit rule and sizing "not recorded in any consulted source"; algorithm sources: Test catalog entry/variants. Those gaps are closed below by the strategy card and the code in this repo, which the accounting did not consult.
- Strategy card in Test: `strategies/griffith/griffith-52w-high-rs.md` (status live), which names the code: `sleeves/griffith/griffith_factor.py`, `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py` and `sleeves/griffith/feedlib/griffith.py`, with rule lines in `docs/verify/griffith.md`.
- Code search record, in order: dwj9ddyvf6-hub/Test (fresh recursive tree plus the content reads named under Files in this repo); dwj9ddyvf6-hub/Silicon (fresh recursive tree, grepped for the canonical id, its aliases and its family tokens: no matching path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree, same grep: no matching path); dwj9ddyvf6-hub/Midna (fresh recursive tree, same grep: no matching path, except where a note below says otherwise). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

The Griffith R4 monthly 52-week-high book: each month it holds the top decile of the more liquid half of the 550-name SCOPE universe, ranked by closeness of the latest close to the highest high of the last 252 sessions, in equal weight. Alias row: griffith_52w_high_rs; frozen version id HIGH52_MONTHLY_1_0_0.

## Full algorithm

Evaluation order, from the card, `sleeves/griffith/griffith_factor.py` (R4MonthlyBook, MONTHLY map griffith_52w_high_rs -> HIGH52_MONTHLY_1_0_0) and the vendored lab (`evaluate_cross_section` / `_feature`):

1. Decision timing: at the first pass of each month, on the prior month's last SPY bar as cutoff; the month is decided only when the tape carries 99% of the names a tape can carry at the cutoff (coverage rule EQ-02 in griffith_factor.py, COVERAGE = 0.99, expected names = the SCOPE tape symbols less the recorded NOT_LISTED set); until then it waits and asks again at the next pass.
2. Feature (per name, bars at or before the cutoff only): score = cutoff close / max(high of the last 252 sessions); a name needs at least 252 bars, a bar on the cutoff day, and 60 sessions of positive volume (the last 60 bars all with volume > 0), otherwise it is UNAVAILABLE and excluded.
3. Liquidity: median 60-day dollar volume (close x volume) per featured name; keep the top half at or above the cross-sectional median.
4. Selection: rank the liquid half by score descending, ties by symbol; take the top decile, count = max(1, ceil(count/10)).
5. Orders: each pick at 1/N of the $100,000 book, every other held name to zero, as marketable limits (1% through the quote, 30 minutes), re-sent on each of the month's first 5 sessions (RETRY_SESSIONS = 5). A modeled cost of 10 bps per side applies (ONE_WAY_BPS = 10.0).
6. Exit: a name out of the next month's pick is sold at that rebalance; an empty pick is cash. The lab's own horizon label is 21 sessions; the desk book holds until the next month's rebalance (19-23 sessions), a divergence recorded in the griffith_factor.py module docstring.
7. Named divergences recorded in that docstring: entries trade the next regular open after the completed decision bar (the study booked the decision bar's own close); the tape falls back to Yahoo daily bars without Alpaca credentials.

## Files in this repo

- This package: `docs/GRIFFITH_52W_HIGH_RS-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-52w-high-rs.md`
- Desk book (already in Test): `sleeves/griffith/griffith_factor.py` (R4MonthlyBook; MONTHLY map entry griffith_52w_high_rs)
- Vendored frozen lab (already in Test): `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py` (SPECS HIGH52_MONTHLY_1_0_0; evaluate_cross_section; _feature)
- Tape feedlib: `sleeves/griffith/feedlib/griffith.py`
- Rule lines: `docs/verify/griffith.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`; Test catalog entry `griffith-52w-high-rs` in `docs/CATALOG.json`

## Configuration

- Book: $100,000, equal weights (card Sizing section).
- SleeveConfig in griffith_factor.py: family griffith_factor, cadence_s 300, schedule rth, universe = the SCOPE tape symbols, params {version_id: HIGH52_MONTHLY_1_0_0, cost_bps: 10.0, selection: "top decile, top half by liquidity"}, state_schema {month, targets}.
- Frozen lab spec: lookback 252, rebalance MONTH_END, liquidity TOP_HALF_MEDIAN_DOLLAR_VOLUME_60D, selection TOP_DECILE_EQUAL_WEIGHT, horizonSessions 21, state IMPLEMENTED_SHADOW; lab authority string OFFLINE_SHADOW_NO_PROMOTION_NO_RISK_NO_BROKER (the desk book is the forward-test form of the shadow rule).

## Data inputs

- Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys as the fallback tape (card Data section).
- SPY bars, for the month-end cutoff.
- Equity quotes for the marketable-limit orders.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc and the ALL-SLEEVES accounting entry for this strategy.
3. Confirm `sleeves/griffith/griffith_factor.py`, the vendored lab and the feedlib are present at the listed paths and the MONTHLY map still binds griffith_52w_high_rs to HIGH52_MONTHLY_1_0_0.
4. Wire the daily-bar tape (Alpaca IEX, or the Yahoo fallback) and equity quotes; run the desk cycle so the book's signal(view) evaluates at the first pass of each month.
3. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec from the Full algorithm (no dedicated per-strategy test file for this id was found in Test):

- A name with fewer than 252 bars, no cutoff-day bar, or any non-positive volume in its last 60 bars contributes no feature and cannot be selected.
- A month whose tape coverage is below 99% of the expected names produces no decision that pass.
- Selection check: with 100 featured liquid names, exactly 10 are selected, the highest scores first, ties broken by symbol.
- A held name absent from the next month's selection is taken to zero at that rebalance; an empty selection leaves the book in cash.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
