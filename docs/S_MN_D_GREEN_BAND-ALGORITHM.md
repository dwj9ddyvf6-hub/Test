Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_mn_d_green_band: Algorithm

## What it trades
A Midna fire-consumer sleeve. The file adapters3/s_mn_d_green_band.py is a
thin wrapper: evaluate() delegates to desk3/lazarus_midna.py
evaluate(SLEEVE_ID, view, ctx). Position management is in that
engine; signal generation stays upstream in the fire producer.
Fires fail closed when absent or stale.

## Spec (from SPECS in desk3/lazarus_midna.py)
family="green", timeframe 1D, hold_sessions=21, stop=None, gate="band", budget=1000.0.
- Budget $1,000, maximum 1 open position in the engine.
- Fire shape consumed: sleeve_id, symbol, family, timeframe, date
  and price. A fire older than 10 days, or dated after the session,
  is skipped. Family and timeframe must match the spec.

## Entry rules
- Exits are evaluated first; if any exit is emitted, or a position
  is already held, no entry is emitted.
- Price used: the fresh last bar close when the ENH19 reprice
  switch is on (default) and a fresh close exists; otherwise the
  fire price. A price at or below zero is skipped.
- ENH20 cross-stale gate (on by default): refuse a symbol whose
  last bar lags the latest bar date across the snapshot bars by
  more than 4 days.
- Gate "band": the entry price must lie between $10.00 and $20.00 inclusive.
- Quantity is whole shares: int(1000.0 // price). Market, day,
  buy_to_open entry intent.

## Exit rules
- Time exit at 21 sessions. No stop (stop=None).
- Config row: cadence_s 300, session rth, capital_usd 1000, inputs tensor, bars, positions.
- A stop exit applies only where the spec sets a stop; see the
  spec line above. Where stop is None, there is no price stop.

## Sizing, session and cadence
- $1,000 budget, 1 slot. Config row for this sleeve is listed
  under Data inputs below.

## Data inputs
Declared INPUTS in the engine: tensor, bars, positions. Producers
named in the engine: tensor_bundle (86400s freshness), bars
(900s), broker_readback (900s).
