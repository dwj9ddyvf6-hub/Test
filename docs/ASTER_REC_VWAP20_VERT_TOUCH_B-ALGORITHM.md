Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_rec_vwap20_vert_touch_b: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_rec_vwap20_vert_touch_b.py is the per-sleeve
core: evaluate() delegates to the shared engine desk3/aster_b4.py
evaluate(SLEEVE_ID, view, ctx), with INPUTS = INPUTS_COMMON and
PRODUCERS taken from that engine. It trades a debit call vertical
on the first passing symbol in the universe IWM, QQQ, SPY (in that
order) under the VWAP20 recovery rules below. Contract selection,
sizing and exit helpers are reused from desk3/aster_b2.py. Signal
generation and position management are in those engines; this
sleeve implements no math of its own. The sleeve runs on the
shared engine desk3/aster_b4.py (with desk3/aster_b2.py helpers).

## Spec (from SPECS in desk3/aster_b4.py)
book="OPT_VWAP20_VERTICAL_TOUCH_B", family="recovery",
signal="VWAP20", structure="vertical", risk=0.005, dte=(14, 21),
delta=(0.5, 0.6), hold=5, max_debit_width=0.45,
max_premium_spot=0.015, exit_rule="touch".
- Inputs (INPUTS_COMMON): bars, options, positions.
- Slice: $10,000 (SLICE in desk3/aster_b2.py); fees $0.65 per
  contract per leg (FEE_PER_CONTRACT in desk3/aster_b2.py).

## Entry rules
- Exits are evaluated first; if any position with legs is held,
  no entry is emitted (one package per book).
- Entry window 09:35 <= time < 09:40 as coded in
  desk3/aster_b2.py _in_window (a timestamp without a "T" is
  treated as inside the window).
- VWAP20 recovery signal, requiring at least 200 sessions:
  close > SMA200 (mean of the last 200 closes) and close <=
  0.98 x VWAP20, where VWAP20 is the volume-weighted average of
  typical price (H+L+C)/3 over the last 20 sessions; a
  non-positive 20-session volume fails the signal.
- Contract selection (desk3/aster_b2.py _select): calls with
  DTE 14-21 and delta 0.5-0.6, ordered by earliest expiry, then
  delta nearest the band midpoint (0.55), then strike nearest
  spot. The vertical wing is a same-expiry call with strike
  beyond the long, nearest spot x 1.02.
- Caps: vertical debit / width <= 0.45; a debit at or below
  zero emits nothing.
- Sizing: qty = floor(risk x $10,000 / (debit per share x 100 +
  $0.65 x number of legs)), capped by displayed size on every
  leg; qty < 1 emits nothing.
- Execution enhancement (ENH-ASTERB2-MIDLIMIT-20261024, on by
  default): entries and exits are priced as limits at the
  package mid instead of crossing the full spread; the
  market-cross price is recorded as the paired shadow control.

## Exit rules
- Pre-expiry obligation exit when (expiry - current session)
  is <= 1 day.
- Planned session exit when sessions held >= 5 (hold).
- Touch exit: the last bar close for the underlying >= entry_spot x 1.02 (touch_two_percent_recovery_exit).
- Exit execution enhancement (ENH-B11-VWAP20VERT-EXITMID-
  20261024, on by default for the VWAP20 vertical sleeves):
  when the chain prices both legs, the exit is a limit at the
  package mid and price_hint carries that mid; otherwise the
  pre-change market exit stands.
- No price stop and no price target in this policy.

## Sizing, session and cadence
- $10,000 slice, risk fraction 0.005 (risk budget
  $50 before the sizing caps above). No cadence or
  session row is defined in desk3/aster_b4.py itself.

## Data inputs
Declared inputs (INPUTS_COMMON): bars, options, positions.
Producers named in the engine: bars (900s freshness),
options_chain (900s, outputs options), broker_readback (900s,
positions). The engine notes inputs not produced by v3 producers
(OPRA chain, XSP index-regime state) leave the sleeves UNFED in
the registry, never fake-fed.
