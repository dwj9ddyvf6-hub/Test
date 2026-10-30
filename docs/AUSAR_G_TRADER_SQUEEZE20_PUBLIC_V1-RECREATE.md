# ausar_g_trader_squeeze20_public_v1: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Volatility-squeeze breakout · 1d", type volatility, family public_recipe. Algorithm grade PARTIAL, gap: sizing not recorded in the accounting's consulted sources. That gap is filled here from the code in this repo (see Files), whose header records the sizing it ported. Algorithm sources per accounting: ausar_map params/variant and md2 catalog entry/exit/strategy text (for `ausar_pb2`); md2 catalog entry/exit/strategy text (for `ausar_g_trader_squeeze20_public_v1`).
- Test strategy card: `strategies/ausar/public-squeeze20.md` ("Public BB/KC squeeze (daily)"), source: trader.dev public strategy; LazyBear squeeze momentum; StockCharts TTM squeeze.
- Alias record: `ausar_g_trader_squeeze20_public_v1` is the runtime-id form of the frozen rule trader_squeeze20_public_v1; its accounting status history is 'installed' in the md2 catalog. It is the same canonical strategy entry as `ausar_pb2` in the accounting (both map to the single 'Volatility-squeeze breakout · 1d' strategy).
- Accounting data note: data: posted Ausar runtime inputs.

## What this strategy is

Buys when Bollinger Bands expand out of the Keltner Channel with rising positive momentum and a 20-day breakout, on a universe of liquid ETFs. It is the frozen public rule trader_squeeze20_public_v1, implemented in this repo as the sleeve `aster_squeeze_1d` in `desk3/aster_batch1.py`.

## Full algorithm

In evaluation order, from the card, the accounting and the code:

1. Squeeze definition in the code (`desk3/aster_batch1.py`, `_squeeze_series`, period 20): Bollinger Bands BB(20, 2, population stdev) around the 20-period SMA; Keltner Channel KC(20, 1.5 x ATR) around EMA(20) with Wilder/RMA ATR; a bar is in squeeze when the BB lower band is above the KC lower band and the BB upper band is below the KC upper band. Momentum is the LazyBear momentum: the linear-regression endpoint of the last 20 values of delta, where delta = close - ( (20-bar high/low midpoint + SMA20) / 2 ).
2. Entry (all must hold on a completed daily bar): the prior bar was in squeeze and the current bar is not; momentum > 0 and momentum > the prior bar's momentum; close > the prior 20-day high (the maximum high of the 20 bars before the current bar).
3. Exit (first that fires): close < EMA20 (the Keltner centre, EMA(20) of closes); momentum <= 0; the initial 2 x ATR(14) stop is touched (the code checks the bar's low against the stop price recorded at entry, entry close minus 2 x ATR(14)); or 20 completed holding bars.
4. Sizing (from the code header and entry logic in `desk3/aster_batch1.py`): cap = min(0.10 x equity, 0.01 x DV20, cash); shares = floor(cap / close), further capped at floor(0.005 x equity / stop_distance) with stop_distance = 2 x ATR(14) (the 0.5% risk cap the card records); at most 10 positions held; candidates ranked by -momentum / ATR.
5. Cadence and bars: the sleeve spec is cadence 300 seconds, regular trading hours; features require at least 252 daily bars, and the code's completed-bar rule drops bars dated the current session from the feature set, so entries and exits are decided on completed daily bars only.

## Files in this repo

- This doc: `docs/AUSAR_G_TRADER_SQUEEZE20_PUBLIC_V1-RECREATE.md`
- Strategy card: `strategies/ausar/public-squeeze20.md`
- Code (already in Test): `desk3/aster_batch1.py` (sleeve `aster_squeeze_1d`, kind squeeze; `_squeeze_series`, `_trader_features`, `_eval_trader`)
- Adapter stub in Test: `adapters3/aster_squeeze_1d.py`; family algorithm doc: `docs/ASTER_SQUEEZE_1D-ALGORITHM.md`
- Rule lines: `docs/verify/ausar.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, desk3/, tests/) was searched for the canonical id, its alias and the rule name trader_squeeze20_public_v1; Silicon tree, quant-research-backup tree and Midna tree were also searched for the canonical id and squeeze20 terms: no file for this strategy was found in those repos. The code below is already in Test. The strategy card also names a master-desk file `desk/vendor/ausar/trader_signals.py` which is marked '(not in this repo)' on the card itself; the in-repo port is `desk3/aster_batch1.py`.

## Configuration

- Universe: the 15 liquid ETFs in the code's UNIVERSE15: SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX (the card records "15 liquid ETFs (as RSI2)").
- Timeframe: 1d. Asset class: US ETFs. Cadence: 300 seconds in regular trading hours (code spec).
- Sizing and slot limit: algorithm step 4. State: per-symbol entry bar count and stop price, kept by the engine's state store.

## Data inputs

- Posted Ausar runtime inputs (accounting filter note for this alias: 'data: posted Ausar runtime inputs'); the card records Yahoo daily bars, and the in-repo port consumes completed daily bars from the desk snapshot.

## Install and run

1. Clone the Test repo.
2. Read `strategies/ausar/public-squeeze20.md` and the squeeze section of `docs/verify/ausar.md`.
3. Open `desk3/aster_batch1.py` and locate the `aster_squeeze_1d` spec and the squeeze branch of `_trader_features` / `_eval_trader`.
4. Provide completed daily bars (at least 252 per symbol), equity, cash and positions in the snapshot shape that module documents.
5. Run every 300 seconds in regular trading hours; verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist from the algorithm above:

- No entry unless the prior bar was in squeeze, the current bar is not, momentum is positive and rising, and the close exceeds the prior 20-day high.
- Shares never exceed floor(min(0.10 x equity, 0.01 x DV20, cash) / close) nor floor(0.005 x equity / (2 x ATR(14))), and holdings never exceed 10 positions.
- The recorded stop at entry equals entry close minus 2 x ATR(14), and a bar whose low touches it exits.
- A position exits on close below EMA(20), on momentum <= 0, on the stop, or after 20 completed holding bars, whichever comes first.
- No entry or exit is decided on a bar dated the current, still-forming session.
