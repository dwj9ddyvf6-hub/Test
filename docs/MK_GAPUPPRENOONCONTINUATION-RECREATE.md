# mk-gapupprenooncontinuation - Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Gap-up pre-noon continuation (SPY)", type momentum, family milkman, style evidence "Intraday momentum", universe SPY, asset class US ETF, timeframe 1m, creator "The Milkman v2 study", algorithm grade PARTIAL with gaps: entry/signal rule, exit rule and sizing "not recorded in any consulted source"; algorithm sources: Test catalog entry/variants. Those gaps are closed below by the strategy card and the code in this repo.
- Strategy card in Test: `strategies/milkman/mk-gapupprenooncontinuation.md` (status waiting), naming the code `sleeves/milkman/intraday.py`, `sleeves/milkman/vendor/milkman/mlib.py` and `sleeves/milkman/vendored.py`, with rule lines in `docs/verify/milkman.md`. In intraday.py the setup is registered as GUPN: ("mk_gapupprenooncontinuation", [(1, "X=1.0")]) (long only, cell parameter X=1.0).
- Code search record, in order: dwj9ddyvf6-hub/Test (fresh recursive tree plus the content reads named under Files in this repo); dwj9ddyvf6-hub/Silicon (fresh recursive tree, grepped for the canonical id, its aliases and its family tokens: no matching path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree, same grep: no matching path); dwj9ddyvf6-hub/Midna (fresh recursive tree, same grep: no matching path, except where a note below says otherwise). Because the executable code is already in Test, no vendoring was performed.

## What this strategy is

An intraday SPY momentum trade: when SPY opens above the prior close and trades 1% above that prior close before noon ET, buy the next 1-minute bar's open and hold to the close. No stop and no target.

## Full algorithm

From the card and `sleeves/milkman/intraday.py` gupn_trade(P, d, X) with X = 1.0, in code order:

1. Day data: P.day(d) gives the session's bar range, its open and the prior day's close (pdc). If the open or the prior close is not finite, or the open is at or below the prior close, no trade.
2. Level: lv = pdc x (1 + X/100) = pdc x 1.01.
3. Trigger window: bars from the session open up to noon (the _noon boundary, capped at the session end). The first bar whose high is at or above lv is the trigger.
4. Entry: j = the bar after the trigger bar; the entry price is that bar's open. If j is past the session end on a non-live day, no trade. The recorded trade is long (side 1), decide bar j-1.
5. Exit: out at the close: run_exit over the session with the exit at the last session bar (LIVE_LAST on a live day), i.e. a market-on-close exit 12 minutes before the close in the desk form (card Sizing section). No stop or target (both recorded as NaN in the trade record).
6. Desk-form sizing and cadence (card): $10,000 a trade on a $1,000,000 book, every trade taken; the sleeve re-reads the session's completed 1-minute bars each minute; a new trade enters at the market at the next pass, not if seen more than 2 bars late, and not if it opened and closed inside one bar; lanes and overlapping trades net on SPY.

## Files in this repo

- This package: `docs/MK_GAPUPPRENOONCONTINUATION-RECREATE.md`
- Strategy card: `strategies/milkman/mk-gapupprenooncontinuation.md`
- Code (already in Test): `sleeves/milkman/intraday.py` (GUPN registration and gupn_trade; lane_trades GUPN branch)
- Vendored library: `sleeves/milkman/vendor/milkman/mlib.py`; loader `sleeves/milkman/vendored.py`
- Rule lines: `docs/verify/milkman.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`; Test catalog entry `mk-gapupprenooncontinuation` in `docs/CATALOG.json`

## Configuration

- Cell: GUPN, side +1 (long only), parameter X=1.0 (the percent above the prior close).
- Desk form: $10,000 per trade on a $1,000,000 book (card); timeframe 1m; universe SPY; status waiting in the catalog.
- No other parameter is recorded for this strategy; anything further is not in the record.

## Data inputs

- Yahoo SPY 1-minute bars with the extended session (7 days), clock hours (59 days) and daily bars; full sessions only (card Data section).
- The prior session's close and the session open, derived from those bars in code.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc and the ALL-SLEEVES accounting entry for this strategy.
3. Confirm `sleeves/milkman/intraday.py` still registers GUPN to this id with cell "X=1.0" and that gupn_trade matches the Full algorithm.
4. Wire the SPY 1-minute panel (P) in the shape intraday.py expects and evaluate lane_trades("GUPN", P, day_index, "X=1.0", 1) per session.
3. Verify against the Verification section before treating any recreation as faithful.

## Verification

Behaviour spec from the code (no dedicated test file for this exact id was found in Test):

- A session that opens at or below the prior close produces no trade, however high it later trades.
- A session that opens above the prior close but never reaches prior close x 1.01 before noon produces no trade; a touch at or after noon does not count.
- On a qualifying touch, the entry is the next bar's open and the exit is the session close; no stop or target fires in between.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
