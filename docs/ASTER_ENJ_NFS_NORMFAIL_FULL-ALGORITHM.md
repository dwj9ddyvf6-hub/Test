Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_enj_nfs_normfail_full: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_enj_nfs_normfail_full.py is the per-sleeve
core: evaluate() delegates to the shared engine desk3/aster_batch8.py
evaluate(SLEEVE_ID, view, ctx). It trades ENJUSDT under the Aster
batch 8 negative_funding_squeeze rules. Signal generation and position
management are in that engine; this sleeve implements no math of its own.

## Spec (from CRYPTO_SPECS in desk3/aster_batch8.py)
exit_policy="normalization_failure", capacity="fullcash".
- Symbol: ENJUSDT, 4h bars.
- Config row: cadence_s 3600, session 24h, capital_usd 10000.0,
  cash_usd 10000.0, bp_buffer_frac 0.02, flat_by_close false.
- Inputs: bars, funding, positions.

## Entry rules
- Exits are evaluated first; if any position in ENJUSDT is held, no
  entry is emitted.
- Entry requires an actually available funding observation below 0.
  No funding producer is registered in v3 yet, so this sleeve is
  visibly UNFED in the registry until that producer lands; missing
  funding means no entry, never a fake-fed entry.
- Entry requires at least 21 completed 4h bars, and the last bar close
  must be above the highest high of the prior 20 bars.
- Entry freshness gate (on by default for this exit policy): refuse
  the entry when the last bar lags now, measured from bar close
  (bar time plus 4h), by more than 3600 seconds.
- Sizing: fullcash: quantity is slice cash less the 10bp fee, qty = cash * 0.999 / price.
  Quantity is rounded to 6 decimals; a quantity at or below zero
  emits nothing. Market, day, buy_to_open entry intent.

## Exit rules
- 96h maximum deadline: exit in full when hours held reaches 96.
  This deadline fires for every exit policy, even when bars or
  funding are missing.
- Normalization failure: exit in full when funding is at or above 0 AND the last 4h close is below the lowest low of the prior 3 bars, and only when now is at or after the trigger bar time plus 8 hours (bar end plus 4 hours, plus the 4 hour execution delay in the code).
- A stop exit or target exit is not part of this policy.

## Sizing, session and cadence
- $10,000 slice capital/cash in the config row, cadence 3600 seconds,
  session 24h, not flat by close.

## Data inputs
Declared INPUTS_CRYPTO in the engine: bars, funding, positions.
Producers named in the engine: bars (900s freshness), broker_readback
(900s, positions), quotes (60s). No funding producer is registered.
