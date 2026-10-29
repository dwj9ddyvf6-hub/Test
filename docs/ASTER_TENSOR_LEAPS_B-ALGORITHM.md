Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_tensor_leaps_b: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/aster_tensor_leaps_b.py is the per-sleeve
core: evaluate() delegates to the shared engine
desk3/aster_batch3.py evaluate(SLEEVE_ID, view, ctx), with INPUTS
and PRODUCERS taken from that engine. It buys long-dated call
options (LEAPS) on underlyings flagged by qualified native Tensor
G4 events (the Tensor product is consumed at the sleeve layer;
the Tensor ENGINE itself is untouched). The sleeve runs on the
shared engine desk3/aster_batch3.py.

## Spec (from SPECS / _BOOKS in desk3/aster_batch3.py)
book="OPT_TENSOR_LEAPS_B", family="tensor_leaps", structure="long",
risk_fraction=0.005 (of the $10,000 v3 slice: $50),
max_premium_spot=0.5, DTE band 540-720, delta band 0.6-0.8,
hold_calendar_days=365.
- Inputs: bars, options_chain, quotes, positions.

## Entry rules
- Entry ONLY on a qualified native G4 event: the event must carry
  qualified_native_G4 true and a source_sha256; entry_session
  must equal the calendar session; signal_end >= the book's
  installed_at and signal_end <= available_at < now; and a future
  original_G4_exit_at deadline must exist.
- Contract selection: long calls with DTE 540-720 and delta
  0.6-0.8 (greeks no more than 10s old at selection), earliest
  expiry, then delta nearest the band midpoint, then strike
  nearest spot. The long debit / (spot * 100) must be
  <= max_premium_spot (0.5).
- LEAPS spread gate (ENH-B13-LEAPS-SPREAD-20261024, switch
  default ON; OFF restores the pre-change ask-only pricing rule
  exactly): the chosen contract's quoted spread must be no more
  than 30% of its price (LEAPS_MAX_SPREAD_FRAC = 0.30).
- One package per book: no entry while any package is held.
- Sizing: risk = min(slice_equity * risk_fraction, 5% of the
  $10k slice initial minus outstanding max-loss, slice cash);
  qty = floor(risk / (debit per package + per-leg fees)), capped
  by displayed size on every leg; qty < 1 refuses. tensor_leaps
  keeps the pre-change (ask) execution; the batch-10 mid-limit
  enhancement is scoped to the recovery family only.

## Exit rules
- Exit session = the first session >= entry + 365 calendar days,
  superseded by the original G4 saved deadline, and by a
  qualified G4 exit event for the held event id.
- European-style positions settle at expiry close
  (official_PM_expiry); a pre-expiry obligation exit fires at the
  previous session before expiry, 15 min before close; a verified
  assignment alert also exits. Due exits are priced from current
  OPRA quotes; an unpriceable due exit emits nothing here and is
  named by the desk's obligation surfacing upstream.

## Data inputs
Declared inputs: bars, options_chain, quotes, positions.
Producers named in the engine: bars (3600s freshness),
options_chain (900s, outputs options_chain and options_quotes),
quotes (60s), broker_readback (900s, positions), tensor_bundle
(93600s, outputs tensor). No v3 producer emits OPRA chains or G4
events yet, so in the live registry this sleeve is UNFED by name,
never fed invented data.
