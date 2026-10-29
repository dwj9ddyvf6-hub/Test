Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_etf_core25_m150: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_etf_core25_m150.py is the per-sleeve
core: evaluate() delegates to the shared engine desk3/aster_batch8.py
evaluate(SLEEVE_ID, view, ctx). It is a monthly Aster R19 ETF rotation
sleeve. Selection and target logic are in that engine; this sleeve
implements no math of its own.

## Spec (from ETF_SPECS in desk3/aster_batch8.py)
policy="CORE25", gross=1.5.
- Basket: QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE,
  XLU, XLV, XLY.
- Config row: cadence_s 300, session rth, capital_usd 10000.0,
  cash_usd 10000.0, bp_buffer_frac 0.02, flat_by_close false.
- Inputs: bars, positions, quotes.

## Entry rules
- Evaluation emits intents only inside the 09:35-09:40
  America/New_York window (aware clock stamps are converted to ET;
  naive stamps are read as ET).
- Monthly guard: when positions are held, no rebalance_due flag is
  set, and every held position was entered in the current month, no
  intents are emitted.
- Leader selection: for each basket symbol with at least 127 daily
  bars and a positive close 127 bars back, score is the 126-session
  return close[-1] / close[-127] - 1. The leader is the best score,
  ties broken alphabetically.
- CORE25 weights: 75% QQQ plus 25% leader, combined into QQQ when QQQ is the leader.
- Targets are whole shares: int(gross * equity * weight / price),
  where equity is account_value or net_value from extra when present,
  otherwise slice capital, default $10,000. A target price at or
  below zero emits nothing.
- Gross 1.5 is applied as coded and is never silently capped in
  the sleeve; for gross above 1 the dispatcher buying-power check
  governs execution. Sells (held above target) are listed before
  buys. Market, day intents; entries are buy_to_open, reductions
  and full exits are sell_to_close.

## Exit rules
- No price stop and no price target.
- The designed exit is the next monthly selection: a holding above
  its new target is reduced, and a holding with target zero is
  exited in full.

## Sizing, session and cadence
- $10,000 slice capital in the config row, cadence 300 seconds,
  session rth, not flat by close.

## Data inputs
Declared INPUTS_ETF in the engine: bars, positions, quotes.
Producers named in the engine: bars (900s freshness), broker_readback
(900s, positions), quotes (60s).
