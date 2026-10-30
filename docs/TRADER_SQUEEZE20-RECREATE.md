# TRADER_SQUEEZE20 - Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "TRADER_SQUEEZE20", type volatility, algorithm grade PARTIAL with gaps: ["entry/signal rule not recorded in any consulted source", "exit rule not recorded in any consulted source", "sizing not recorded in any consulted source"], and UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description". The accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources". Alias status: ausar_deployed, "mode=original_independent_local_paper running=False". Classification evidence on the accounting entry: "Classification 2026-10-30: volatility (name_only evidence): Name only: SQUEEZE20 names the Bollinger and Keltner squeeze, and the Test catalog public-squeeze20 entry records style Volatility breakout from the LazyBear and TTM squeeze; no algorithm text is recorded for this id itself"
- The rule this deployed id names is the frozen public rule `trader_squeeze20_public_v1`, whose full record is already in Test: the sibling recreation package `docs/AUSAR_G_TRADER_SQUEEZE20_PUBLIC_V1-RECREATE.md` documents it from the strategy card `strategies/ausar/public-squeeze20.md` and the code, and `desk3/aster_batch1.py` ports it as sleeve `aster_squeeze_1d`. Every parameter below is taken from those in-repo records, read for this package.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads of `desk3/aster_batch1.py` and the AUSAR_G package above; no file is named for the uppercase deployed id itself, the code lives under the rule id and the aster sleeve id); dwj9ddyvf6-hub/Silicon (recursive tree; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree; no path named for this id).

## What this strategy is

A Bollinger/Keltner volatility-squeeze breakout (LazyBear / TTM squeeze family): buy when the bands expand out of a squeeze with rising positive momentum and a 20-day breakout, on a universe of liquid ETFs. The accounting records no strategy description for this deployed id itself: "No strategy description recorded in consulted sources."

## Full algorithm

Evaluation order (from `desk3/aster_batch1.py` `_squeeze_series`, `_trader_features` and `_eval_trader`, kind squeeze, confirmed against the card and sibling package):

1. Squeeze definition (period 20): Bollinger Bands BB(20, 2, population stdev) around the 20-period SMA; Keltner Channel KC(20, 1.5 x ATR) around EMA(20) with Wilder/RMA ATR; a bar is in squeeze when the BB lower band is above the KC lower band and the BB upper band is below the KC upper band. Momentum is the LazyBear momentum: the linear-regression endpoint of the last 20 values of delta, where delta = close - ((20-bar high/low midpoint + SMA20) / 2).
2. Entry (all must hold on a completed daily bar): the prior bar was in squeeze and the current bar is not; momentum > 0 and momentum > the prior bar's momentum; close > the prior 20-day high (the maximum high of the 20 bars before the current bar). Features require at least 252 daily bars, and the desk port drops bars dated the current session from the feature set (completed-bar rule).
3. Exit (first that fires): close < EMA20 (the Keltner centre); momentum <= 0; the initial 2 x ATR(14) stop is touched (the bar's low against the stop price recorded at entry, entry close minus 2 x ATR(14)); or 20 completed holding bars.
4. Sizing (code): cap = min(0.10 x equity, 0.01 x DV20, cash); shares = floor(cap / close), further capped at floor(0.005 x equity / stop_distance) with stop_distance = 2 x ATR(14); at most 10 positions held; candidates ranked by -momentum / ATR, then symbol.
5. Universe (code UNIVERSE15): SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX. Cadence 300 seconds, regular trading hours (code spec).
6. Accounting gaps for this deployed id (entry/exit/sizing "not recorded in any consulted source" in the accounting itself) are filled above only from the in-repo code and card records named in Provenance; anything beyond them is not in the record.

## Files in this repo

- This package: `docs/TRADER_SQUEEZE20-RECREATE.md`
- Code (already in Test; nothing vendored): `desk3/aster_batch1.py` (sleeve `aster_squeeze_1d`, `_squeeze_series`, `_trader_features`, `_eval_trader`); strategy card `strategies/ausar/public-squeeze20.md`; adapter stub `adapters3/aster_squeeze_1d.py`; family algorithm doc `docs/ASTER_SQUEEZE_1D-ALGORITHM.md`; hosted rule code under `packages/ausar/aster-execution-r15/desk/` (backend/trader_signals.py, strategies/trader_catalogue/rules-v1.json, rule id `trader_squeeze20_public_v1`).
- Sibling package: `docs/AUSAR_G_TRADER_SQUEEZE20_PUBLIC_V1-RECREATE.md`.
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id.

## Configuration

- Universe: the 15 ETFs in step 5. Timeframe: 1d. Asset class: US ETFs. Cadence: 300 seconds in regular trading hours (code spec).
- Sizing and slot limit: algorithm step 4. State: per-symbol entry bar count and stop price, kept by the engine's state store.
- Deployed status for this id (accounting): mode=original_independent_local_paper, running=False.
- Any further configuration for the deployed form: not in the record.

## Data inputs

- Posted Ausar runtime inputs (accounting note); the card records Yahoo daily bars, and the in-repo port consumes completed daily bars from the desk snapshot.

## Install and run

1. Clone this repository (Test) and check out the main branch.
2. Read `strategies/ausar/public-squeeze20.md` and the sibling package `docs/AUSAR_G_TRADER_SQUEEZE20_PUBLIC_V1-RECREATE.md`.
3. Open `desk3/aster_batch1.py` and locate the `aster_squeeze_1d` spec and the squeeze branch of `_trader_features` / `_eval_trader`.
4. Provide completed daily bars (at least 252 per symbol), equity, cash and positions in the snapshot shape that module documents.
5. Run every 300 seconds in regular trading hours; verify against the Verification section before treating any recreation as faithful.

## Verification

- No dedicated test file for this sleeve was found in Test (the sibling package records the same finding).
- Behaviour checklist: no entry unless the prior bar was in squeeze, the current bar is not, momentum is positive and rising, and the close exceeds the prior 20-day high; shares never exceed floor(min(0.10 x equity, 0.01 x DV20, cash) / close) nor floor(0.005 x equity / (2 x ATR(14))), and holdings never exceed 10 positions; the recorded stop at entry equals entry close minus 2 x ATR(14), and a bar whose low touches it exits; a position exits on close below EMA(20), on momentum <= 0, on the stop, or after 20 completed holding bars, whichever comes first; no entry or exit is decided on a bar dated the current, still-forming session.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.

