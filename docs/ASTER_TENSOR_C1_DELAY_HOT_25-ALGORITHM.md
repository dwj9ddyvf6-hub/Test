Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_tensor_c1_delay_hot_25: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_tensor_c1_delay_hot_25.py is the per-sleeve
core: evaluate() delegates to the shared engine
desk3/aster_batch13.py evaluate(SLEEVE_ID, view, ctx), with
INPUTS = INPUTS_TENSOR and PRODUCERS taken from that engine.
It consumes canonical Tensor v698 products at the sleeve layer
via the Tensor bundle fire channel (the Tensor ENGINE is
untouched) and trades long stock positions under the rules
below. Signal generation is the Tensor bundle's; this sleeve
implements the fire gating, sizing and exit rules in that
engine and no signal math of its own. The sleeve runs on the
shared engine desk3/aster_batch13.py.

## Spec (from SPECS in desk3/aster_batch13.py)
kind="tensor", family="C1", capital_mode="delay",
volatility="hot".
- Constants: TICKET = $400 (the $4,000 source book ticket
  scaled to the $10k slice), SLOTS = 25 distinct symbols,
  HOLD_SESSIONS = 260.
- Inputs (INPUTS_TENSOR): tensor, bars, positions.

## Entry rules
- Exits are evaluated first; if any exit is emitted, no entry
  is evaluated in the same pass.
- One entry per evaluation pass, into a symbol not already
  held, while fewer than 25 distinct symbols are held.
- C1 entry: a Tensor bundle fire whose signal names a
  buy-cyan event, fire price <= 5, ret60 >= 31, vol20 >= 0.07
  and average dollar volume >= $2,000,000.
- Volatility split (source-exact per r19_tensor.passes,
  HARDEN batch-1 fidelity cure): this sleeve takes only
  fires with atr_ratio > 1; a fire with no atr_ratio is
  skipped.
- Capital mode delay: the fire date must be at least 1 day before the current session (one extra session wait) before an entry can act on it.
- Enhancement (ENH batch 12, stale-fire pricing, on by
  default): when a current bar is available, the C1 price
  cap is revalidated against the latest close (a current
  close > 5 refuses the entry) and sizing uses the latest
  close; the fire-price decision is kept as the paired
  shadow control record.
- Sizing: qty = floor($400 / entry price); qty < 1 emits
  nothing.

## Exit rules
- 52nd-calendar-week deadline, modelled as 260 sessions
  held: the full position is sold ("week52_deadline").
- No price stop and no profit cap in this policy (TSV).

## Sizing, session and cadence
- $400 fixed ticket, at most 25 distinct symbols. No cadence
  or session row is defined for the tensor rows in
  desk3/aster_batch13.py itself.

## Data inputs
Declared inputs (INPUTS_TENSOR): tensor, bars, positions.
Producers named in the engine: bars (900s freshness),
tensor_bundle (86400s, outputs tensor), broker_readback
(900s, positions). With no tensor key in the snapshot the
registry marks the sleeve UNFED, never fake-fed.
