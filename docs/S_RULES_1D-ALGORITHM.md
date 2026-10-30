Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_rules_1d: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/s_rules_1d.py is the
per-sleeve core: evaluate() delegates to the shared engine
desk3/lazarus.py evaluate(SLEEVE_ID, view, ctx), with the
spec in that engine's SPECS dict. It is a Lazarus
fire-consumer sleeve for the frozen lab rules (43 frozen
rules, CSV ON, live, per the wrapper docstring): entries
come only from ingested Tensor fires in the snapshot;
position management is engine code. Fail-closed: no fresh
matching fire means no entry. The sleeve runs on the shared
engine desk3/lazarus.py.

## Spec (from SPECS in desk3/lazarus.py)
slots=44, capital=44000.0, cadence_s=300, session="rth",
max_age_min=60*48 (48 hours), stop_pct=None,
horizon_sessions=22, horizon_from_fire=True,
horizon_plus_one=True.
Catalog note in the wrapper: Lab rule 1D, 43 frozen rules
(CSV ON, Live). Per-slot capital = $1,000.
- Declared INPUTS in the engine: lazarus_fires, bars,
  positions. Per-slot capital = capital / slots.

## Entry rules
- Exits are evaluated first; if any exit is emitted the
  evaluation returns with no entry.
- No entry when the number of held positions reaches slots.
- Fires are read from view["lazarus_fires"], else view
  extra["lazarus_fires"], else view["tensor_fires"], else
  view extra["fires"]. A fire is skipped if its sleeve_id
  (when carried) differs, it has no symbol or its symbol is
  held, its side (when carried) is not buy/long, it has no
  parseable fired_at/ts, or its age is under 0 or over
  max_age_min.
- Family/tier/cap filters are enforced only when the spec
  names them and the fire carries the field; this spec
  names none of family, signal_tier or cap_tier.
- No QQQ-down gate in this spec (qqq_down is not set).
- Freshest-first for the rules lanes
  (ENH25-RULES-FRESH-20261024, switch default ON; OFF
  restores producer list order): candidate fires are
  ordered by fired_at, freshest first.
- Price: the fire price (falling back to the last bar
  close). Fresh-price reprice (ENH-LAZ-REPRICE-20261024,
  switch default ON): when a fresh last bar close exists
  and differs, sizing, stop and price_hint use the fresh
  close, with the fire-price decision kept as a paired
  shadow record on the entry intent.
- Bound guard (ENH19-LAZ-BOUND-20261024, switch default
  ON): an entry is refused when the execution (fresh)
  price is at or above the fire's target_price, or breaks
  a spec max_price bound (this spec sets no max_price).
- Sizing: qty = int(per_slot // price); qty < 1 emits
  nothing. Entries are market, day, buy intents with
  reason s_rules_1d_tensor_fire and price_hint = the execution
  price; the position's horizon and target_price (from the
  fire) are recorded in the engine state file.

## Exit rules
- No price stop (stop_pct is None).
- Target: a held position whose current price reaches the
  target_price recorded from its entry fire is sold in
  full, reason s_rules_1d_target.
- Time: a position held at least its horizon in sessions
  is sold in full, reason s_rules_1d_time_exit_<horizon>s.
  The horizon is the entry fire's horizon_sessions + 1
  when the fire carries one (horizon_from_fire and
  horizon_plus_one), else the spec horizon of 22 sessions.
  Held sessions are counted on snapshot session dates
  (SPY bar dates as fallback), else business days.
- Exits are market, day, sell intents, in full. If any
  exit is emitted, no entry is evaluated that pass.


## Data inputs
Declared inputs: lazarus_fires, bars, positions. Fires are
the ingested Tensor fires in the cycle snapshot (the desk
Tensor bundle producer substitutes for the unreachable
tracker fire file, per the engine docstring).
