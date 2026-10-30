Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_mn_w_green_smh: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/s_mn_w_green_smh.py is the
per-sleeve core: evaluate() delegates to the shared engine
desk3/lazarus_midna.py evaluate(SLEEVE_ID, view, ctx), with
INPUTS and PRODUCERS taken from that engine. It is a long-only
equity Midna fire-consumer sleeve: signal generation stays
upstream in the fire producer and fires are consumed via the
desk Tensor bundle producer channel using the validated fire
schema. Fail-closed if fires are absent or stale. The sleeve
runs on the shared engine desk3/lazarus_midna.py.

## Spec (from SPECS in desk3/lazarus_midna.py)
family="green", tf="1W", hold_sessions=126, stop=None,
gate="smh_calm", budget=1000.0.
- Inputs: tensor, bars, positions. Budget is $1,000 and the
  engine holds at most 1 open position.
- Fire shape consumed: sleeve_id, symbol, family, timeframe,
  date and price.

## Entry rules
- Exits are evaluated first; if any exit intent is emitted, or
  any (non-zero-qty) position is already held, no entry is
  emitted (max 1 slot).
- Fires are read from view["midna_fires"], view["fires"],
  extra["midna_fires"]/["fires"], or the tensor / tensor_bundle
  value (a list, a dict with a fires/midna_fires list, or a
  sleeves dict of fire lists).
- A fire is skipped if its sleeve_id differs, its family/kind/
  signal does not contain the spec family, its timeframe/tf
  does not match the spec timeframe (1W accepts 1W/W/WEEKLY/
  WEEK), it has no symbol, or its date/fire_date/ts is after
  the session or more than 10 days before it.
- Cross-stale gate (ENH20-MN-XSTALE-20261024, switch default
  ON; OFF via extra["s_mn_w_green_smh_enh20"]["xstale_gate"]=False):
  refuse a symbol whose last bar lags the latest bar date
  across the snapshot bars by more than 4 days.
- Price: the fresh last bar close when the ENH19 reprice
  switch is on (default) and a fresh close exists; otherwise
  the fire price. A price at or below zero is skipped.
- Gate "smh_calm": an extra smh_calm value, when carried,
  must be truthy; otherwise SMH calm is derived from bars:
  at least 21 SMH bars are required and the absolute
  return from the 21st-from-last close to the last close
  must be at most 0.05; fewer bars fails closed.
- Sizing: qty = int(1000.0 // price); qty < 1 emits nothing.
  Orders are market, day, buy_to_open.

## Exit rules
- No price stop (stop=None).
- Time: a position held for at least 126 sessions is sold
  in full.
- Exits are market, day, sell_to_close, in full. Age is
  read from sessions_held / age_sessions / held_sessions /
  bars_held, or age_weeks / held_weeks x 5, or counted from
  entry_date/opened_at against the symbol bars.

## Data inputs
Declared inputs: tensor, bars, positions. Producers named in
the engine: tensor_bundle (86400s freshness, outputs tensor),
bars (900s), broker_readback (900s, positions).
