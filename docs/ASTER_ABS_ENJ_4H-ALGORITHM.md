Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_abs_enj_4h: Algorithm

## What it trades
Four-hour confirmed absorption on ENJUSDT. This sleeve is a thin wrapper
(module adapters3/aster_abs_enj_4h.py in the desk) whose evaluate(view, ctx) delegates
to the shared engine desk3/aster_batch1.py with SLEEVE_ID "aster_abs_enj_4h".
The sleeve runs on the shared engine desk3/aster_batch1.py; the rules
below are the engine absorption rules for this sleeve id.

## Data inputs
Inputs: bars, quotes, positions (engine INPUTS_BY_KIND for kind
"absorption"). Producers named in the engine include bars (900s freshness),
quotes (60s), and broker_readback for positions (900s).

## Entry rules
- Kind: absorption. Symbol: ENJUSDT. Timeframe: 4h bars.
- Decimal EMA spans 20/50, current-inclusive, ported from the source
  absorption advance() routine. 300-bar warmup: no entry before 300 bars.
- Entry on the confirmation bar only in the source rule; the desk engine
  also carries a catch-up enhancement for a confirmation one bar old when
  the current bar still holds the absorption (close at or above the shock
  bar midpoint), with the exit deadline still anchored to the original
  confirmation close.
- Sizing: full available slice cash including a 10bp fee allowance.
- No entry is fabricated when bars are absent or the warmup is incomplete.

## Exit rules
- Exit at confirmation completion plus 16 hours (never resets).
- The 96-hour or other crypto deadlines from other engines do not apply
  to this absorption sleeve.

## Sizing, session and cadence
- Sleeve capital: $10,000. Cadence: 14400 seconds. Session: 24h.
  Flat by close: no.
- Config slice in desk config/sleeves.json matches the engine spec above.
