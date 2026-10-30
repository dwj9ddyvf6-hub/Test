# griffith-xs-momentum - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Cross-sectional momentum (12-1 / 6-1)", type momentum, family griffith, style evidence "Cross-sectional momentum", universe "SCOPE universe: 550 US names", asset class US equities, timeframe 1d (monthly), creator "Griffith R4 parallel strategy lab (XSMOM_12_1 / XSMOM_6_1)", algorithm grade PARTIAL with gaps: entry/signal rule, exit rule and sizing "not recorded in any consulted source"; variant axes record the two rows: 12-1 (griffith_xs_mom_12_1, lookback 252 sessions skipping the last 21) and 6-1 (griffith_xs_mom_6_1, lookback 126 sessions skipping the last 21); merge tier A groups the two rows under this one catalog entry. Those gaps are closed below by the strategy card and the code in this repo.
- Strategy card in Test: `strategies/griffith/griffith-xs-momentum.md` (status: 2 live), which names the code: `sleeves/griffith/griffith_factor.py`, `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py` and `sleeves/griffith/feedlib/griffith.py`, with rule lines in `docs/verify/griffith.md`.
- Code search record, in order: dwj9ddyvf6-hub/Test (fresh recursive tree plus the content reads named under Files in this repo); dwj9ddyvf6-hub/Silicon (fresh recursive tree, grepped for the canonical id, its aliases and its family tokens: no matching path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree, same grep: no matching path); dwj9ddyvf6-hub/Midna (fresh recursive tree, same grep: no matching path, except where a note below says otherwise). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

The Griffith R4 monthly cross-sectional momentum book, in two rows that are one strategy with two lookbacks: each month it holds the top decile of the more liquid half of the 550-name SCOPE universe, ranked by 12-1 momentum (row griffith_xs_mom_12_1) or 6-1 momentum (row griffith_xs_mom_6_1), in equal weight. Frozen version ids XSMOM_12_1_MONTHLY_1_0_0 and XSMOM_6_1_MONTHLY_1_0_0.

## Full algorithm

Evaluation order, from the card, `sleeves/griffith/griffith_factor.py` (R4MonthlyBook, MONTHLY map) and the vendored lab (`evaluate_cross_section` / `_feature`):

1. Decision timing and coverage: exactly as for the other R4 monthly books: first pass of each month, cutoff = the prior month's last SPY bar, and the month is decided only on a tape carrying 99% of the expected names (EQ-02, COVERAGE = 0.99).
2. Feature (per name, bars at or before the cutoff only): score = close[-1-skip] / close[-1-lookback] - 1, with skip = 21 and lookback = 252 (12-1) or 126 (6-1); a name needs at least lookback+1 bars, a bar on the cutoff day, and 60 sessions of positive volume, otherwise UNAVAILABLE.
3. Liquidity: keep the top half by 60-day median dollar volume (at or above the cross-sectional median).
4. Selection: rank by score descending, ties by symbol; top decile, count = max(1, ceil(count/10)). Fewer than 10 featured names makes the whole cross-section UNAVAILABLE (INCOMPLETE_CROSS_SECTION).
5. Orders: each pick at 1/N of the $100,000 book, the rest to zero, marketable limits (1% through the quote, 30 minutes), re-sent on each of the month's first 5 sessions; modeled cost 10 bps per side.
6. Exit: a name out of the next month's pick is sold at that rebalance; an empty pick is cash.
7. Named divergences (griffith_factor.py docstring): entries trade the next regular open after the completed decision bar; the desk book holds until the next rebalance where the lab label measured 21 sessions; Yahoo fallback tape without Alpaca credentials.

## Files in this repo

- This package: `docs/GRIFFITH_XS_MOMENTUM-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-xs-momentum.md`
- Desk book (already in Test): `sleeves/griffith/griffith_factor.py` (MONTHLY map: griffith_xs_mom_12_1 and griffith_xs_mom_6_1)
- Vendored frozen lab (already in Test): `sleeves/griffith/vendor/griffith/r4_parallel_strategy_lab.py`
- Tape feedlib: `sleeves/griffith/feedlib/griffith.py`
- Rule lines: `docs/verify/griffith.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`; Test catalog entry `griffith-xs-momentum` in `docs/CATALOG.json`

## Configuration

- Book: $100,000, equal weights.
- SleeveConfig in griffith_factor.py: family griffith_factor, cadence_s 300, schedule rth, universe = the SCOPE tape symbols, params {version_id, cost_bps: 10.0, selection: "top decile, top half by liquidity"}, state_schema {month, targets}.
- Frozen lab specs: XSMOM_12_1 (lookback 252, skip 21) and XSMOM_6_1 (lookback 126, skip 21); both rebalance MONTH_END, liquidity TOP_HALF_MEDIAN_DOLLAR_VOLUME_60D, selection TOP_DECILE_EQUAL_WEIGHT, horizonSessions 21, state IMPLEMENTED_SHADOW.

## Data inputs

- Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars as fallback.
- SPY bars for the month-end cutoff; equity quotes for the marketable-limit orders.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc and the ALL-SLEEVES accounting entry for this strategy.
3. Confirm the MONTHLY map in `sleeves/griffith/griffith_factor.py` still binds both rows to their version ids, and the vendored lab and feedlib are present.
4. Wire the daily-bar tape and quotes; run the desk cycle so each row's book evaluates at the first pass of each month.
3. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec from the Full algorithm (no dedicated per-strategy test file for this id was found in Test):

- Score check: a name whose close 21 sessions before the cutoff equals its close 252 (12-1 row) sessions before it scores exactly 0.
- A cross-section with fewer than 10 featured names returns UNAVAILABLE and no orders.
- The 12-1 and 6-1 rows are evaluated independently; the same name may be held by both.
- A held name absent from its row's next selection is taken to zero at that rebalance.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
