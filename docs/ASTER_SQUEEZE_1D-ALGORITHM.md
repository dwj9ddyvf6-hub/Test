Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_squeeze_1d: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_squeeze_1d.py is the per-sleeve
core: evaluate() delegates to the shared engine
desk3/aster_batch1.py evaluate(SLEEVE_ID, view, ctx), with
INPUTS = inputs_for(SLEEVE_ID) and PRODUCERS taken from that
engine. It trades long stock positions under the Volatility-squeeze breakout 1d (TRADER_SQUEEZE20) rules
below. Signal generation and position management are in that
engine; this sleeve implements no math of its own. The sleeve
runs on the shared engine desk3/aster_batch1.py.

## Spec (from SPECS in desk3/aster_batch1.py)
kind="squeeze", cadence_s=300, session="rth".
- Universe (UNIVERSE15): SPY, QQQ, IWM, DIA, XLK, XLF, XLE,
  XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX (daily bars).
- Inputs for this kind: bars, positions.
- Frozen source rule: trader_squeeze20_public_v1 (backend/trader_signals.py,
  indicator math ported function-for-function: Wilder RSI via
  RMA seed, EMA seed = first-period mean, BB population stdev,
  LazyBear momentum = linreg endpoint of delta).

## Entry rules
- Exits are evaluated first; if any exit is emitted, no entry
  is evaluated in the same pass.
- Volatility-squeeze breakout on completed daily bars (at
  least 252 bars required), frozen rule
  trader_squeeze20_public_v1: Bollinger Bands (20, 2.0,
  population stdev) inside Keltner Channels (EMA20 center,
  1.5 x ATR20 RMA) on the prior bar (squeeze on), released on
  the current bar (squeeze off), LazyBear momentum (linreg
  endpoint of delta over 20 bars, delta = close - average of
  the 20-bar high/low midpoint and SMA20) > 0 and rising, and
  close > the prior 20-bar high.
- Candidates are ranked by (-momentum/ATR14, symbol ascending);
  entries fill free slots up to 10 positions.
- Sizing (per backend/trader_runtime.py as ported): cap =
  min(0.10 x equity, 0.01 x DV20, cash), where DV20 is the
  20-session mean dollar volume; shares = floor(cap / close).
  Risk sleeves with a stop_distance also cap shares at
  floor(0.005 x equity / stop_distance). Shares < 1 emits
  nothing; cash is decremented per filled candidate.
- Enhancement (ENH-B11-TRADER-COMPLETEDBAR-20261024, on by
  default for this sleeve): features are computed on COMPLETED
  daily bars only (bars dated the current ET session are
  dropped); the forming-bar decision is recorded as the paired
  shadow control.

## Exit rules
- Signal exits: close < EMA20 ("close_below_ema20") or
  momentum <= 0 ("momentum_nonpositive").
- Initial stop: entry close - 2 x ATR14; an exit fires when a
  later bar's low <= stop ("observed_quote_initial_2atr_stop").
- Time exit: held >= 20 completed holding bars.

## Sizing, session and cadence
- Cadence 300 seconds, session rth. At most 10 positions.
  Position sizing as above against the desk account equity and
  cash passed in the view/ctx (no fixed per-sleeve slice in
  this engine).

## Data inputs
Declared inputs: bars, positions. Producers named in the
engine: bars, broker_readback (positions). Features require
>= 252 daily bars per symbol and positive ATR14 and DV20,
otherwise the symbol is skipped.
