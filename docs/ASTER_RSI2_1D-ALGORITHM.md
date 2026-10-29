Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_rsi2_1d: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_rsi2_1d.py is the per-sleeve
core: evaluate() delegates to the shared engine
desk3/aster_batch1.py evaluate(SLEEVE_ID, view, ctx), with
INPUTS = inputs_for(SLEEVE_ID) and PRODUCERS taken from that
engine. It trades long stock positions under the RSI2 dip rebound 1d (TRADER_RSI2) rules
below. Signal generation and position management are in that
engine; this sleeve implements no math of its own. The sleeve
runs on the shared engine desk3/aster_batch1.py.

## Spec (from SPECS in desk3/aster_batch1.py)
kind="rsi2", cadence_s=300, session="rth".
- Universe (UNIVERSE15): SPY, QQQ, IWM, DIA, XLK, XLF, XLE,
  XLV, XLI, XLP, XLU, XLB, XLY, SMH, SOXX (daily bars).
- Inputs for this kind: bars, positions.
- Frozen source rule: trader_rsi2_public_v1 (backend/trader_signals.py,
  indicator math ported function-for-function: Wilder RSI via
  RMA seed, EMA seed = first-period mean, BB population stdev,
  LazyBear momentum = linreg endpoint of delta).

## Entry rules
- Exits are evaluated first; if any exit is emitted, no entry
  is evaluated in the same pass.
- RSI2 pullback signal on completed daily bars (at least 252
  bars required): Wilder RSI(2) (RMA-seeded, ported
  function-for-function from the frozen rule
  trader_rsi2_public_v1) <= 5.0, close > SMA200 and
  close < SMA5.
- Candidates are ranked by (RSI2 ascending, -(SMA5 - close)/ATR14
  ascending, symbol ascending); entries fill free slots up to
  10 positions.
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
- Signal exit: close > SMA5 ("close_above_sma5").
- Time exit: held >= 10 completed holding bars.
- RSI2 has NO initial stop (stop_distance is None).

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
