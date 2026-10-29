Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_tensor_h1_recovery: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_tensor_h1_recovery.py is the per-sleeve
core: evaluate() delegates to the shared engine
desk3/aster_batch1.py evaluate(SLEEVE_ID, view, ctx), with
INPUTS = inputs_for(SLEEVE_ID) and PRODUCERS taken from that
engine. It is a long-only equity sleeve implementing the Tensor
StateRepairPolicy (source backend/tensor_strategy.py, R11) on the
1h frame (1Hour bars), consuming canonical Tensor products at
the sleeve layer via view["tensor"] (the Tensor ENGINE itself is
untouched; no tensor key in the snapshot means the sleeve is
UNFED, never fake-fed). The sleeve runs on the shared engine
desk3/aster_batch1.py.

## Spec (from SPECS in desk3/aster_batch1.py)
kind="tensor", frame="1h", tf="1Hour", cadence_s=3600,
session="rth".
- Inputs (INPUTS_BY_KIND["tensor"]): tensor, bars, positions.
- Vote channels (7): stoch, aroon, di, obv, squeeze, pivot, wave.
  A panel row's balance is bullish votes minus bearish votes (or
  the row's own balance field); excluded symbols: SPY, QQQ, B,
  GOLD. At most 10 positions are held (free = 10 - held).

## Entry rules (StateRepairPolicy, source-exact)
- Exits are evaluated first; if any exit intent is emitted, the
  call returns exits only.
- A symbol needs at least a 4-bar panel on the sleeve's frame.
  Repair test on the last 4 bars: balance[-1] - balance[0] >= 2;
  at least 2 of the 7 vote channels strictly increase across at
  least one adjacent transition in the panel; total_votes == 7
  at both panel ends; the latest row's native status, when
  present, must be "ready".
- Price/volume gates on the latest panel row: close >= 5,
  dollar_volume20 >= 1,000,000, atr14 > 0.
- Warmup: the current bar index + 1 must be >= 234 (minimum
  source bars). Cooldown: 20 native bars after an entry (the
  sleeve's state file records next_eligible_bar_index =
  entry bar index + 20; a view-supplied next_eligible map can
  override per symbol).
- Ranking: repair + 0.01 * balance[-1] + 0.001 * clip(
  obv_slope5 / volume, -10, 10); ties break by symbol ascending.
  Entries fill the free slots in rank order.
- Execution-price revalidation (ENH-B13-TENSORREC-REPRICE-
  20261024, switch default ON; OFF restores the panel-close rule
  exactly): when a current bar exists, the $5 floor is
  revalidated against its latest close (a current close below 5
  refuses the entry, recorded as the paired shadow control) and
  sizing uses that close instead of the panel close.
- Sizing: budget = min(0.10 * equity, 0.01 * DV20, cash);
  shares = floor(budget / (execution price * 1.001)); shares < 1
  emits nothing. Orders are buy entries at the execution price.

## Exit rules
- The only designed exit is time: a position is sold in full
  when the current panel bar index minus its entry bar index
  reaches 20 native bars (late observation still exits). The
  exit price is the latest bar close on the sleeve's timeframe
  when available.
- No price stop and no profit target in the source policy.

## Data inputs
Declared inputs: tensor, bars, positions. Producers named in the
engine: bars (900s freshness), tensor_bundle (86400s, outputs
tensor), broker_readback (900s, positions), quotes (60s),
options_chain (300s), opening_events (300s).
