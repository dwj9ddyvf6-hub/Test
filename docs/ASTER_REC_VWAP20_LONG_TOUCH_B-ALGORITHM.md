Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_rec_vwap20_long_touch_b - VWAP20 recovery long call, touch exit, B tier

## What it trades
Long single-leg call options on the first passing symbol of the universe
IWM, QQQ, SPY (in that order), under the Aster options-recovery family.
The per-sleeve wrapper in `adapters3/` delegates to the shared engine
`desk3/aster_batch3.py`; this sleeve's book is OPT_VWAP20_LONG_TOUCH_B.

## Signal and entry rules
- Recovery signal VWAP20, computed on completed daily bars: at least 200
  completed sessions, last close above its SMA200, and last close at or
  below 0.98 times the 20-session VWAP of typical price (H+L+C)/3.
- Entries only in the 09:35 to 09:40 ET window, market open, with the
  signal session equal to the calendar previous session.
- One package per book: no entry while any package is held.
- Contract selection: DTE 14 to 21, delta 0.5 to 0.6 (greeks at most 10s
  old at selection), earliest expiry first, then delta nearest the band
  midpoint, then strike nearest spot.
- Caps: long debit divided by (spot times 100) at most 0.015 for this
  B book; max_debit_width 0.45 is recorded in the book but applies to
  vertical structures, so its role for a single-leg long is ambiguous
  in the code and is stated here as recorded, not reinterpreted.

## Sizing
- $10,000 slice (config row: capital $10,000, cash $10,000, bp buffer
  fraction 0.02). Risk fraction 0.005 (the B tier, $50 on the slice).
- Risk budget is the minimum of slice equity times risk fraction, 5% of
  the $10k slice initial capital minus outstanding max loss, and slice
  cash. Quantity is floor(risk / (debit per package plus per-leg fees)),
  capped by displayed size on every leg; quantity below 1 refuses.

## Exit rules
- Touch rule: a fresh (at most 5s old, SIP) underlying bid at or above
  entry spot times 1.02 exits early.
- Planned exit at the 5th session counting the entry session as session
  1, due 5 minutes before that session's close, and any time after.
- Pre-expiry obligation exit on the session before expiry, 15 minutes
  before close. European contracts settle at the expiry close.
- A verified assignment alert also exits.

## Session, cadence and inputs
- Config row: cadence 300s, session RTH, not flat by close, not parked.
- Inputs: bars, options_chain, quotes, positions. The batch-3 header
  notes no desk producer emits OPRA chains yet, so in the live registry
  this sleeve is unfed by name rather than fed invented data.
