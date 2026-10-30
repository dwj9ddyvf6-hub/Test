Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_q07w_c52_sm_cheap5_ins2_mom6: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/s_q07w_c52_sm_cheap5_ins2_mom6.py is the
per-sleeve core: evaluate() delegates to the shared engine
desk3/lazarus_q07.py evaluate_sleeve(SLEEVE_ID, view, ctx),
with SPEC = SPECS[SLEEVE_ID] from that engine. It is a
long-only equity Lazarus Q07 weekly fire-consumer sleeve
(catalog section 4.1 family rule): take the Tensor 1W signal
of the named family in the named cap band, apply the named
alt-data filters, buy only on a QQQ-down day within 5 sessions
of the signal, exit on a 15% stop or at the time horizon.
Fail-closed: no fresh fires means no entry, and a filter with
no evidence fails closed. The sleeve runs on the shared
engine desk3/lazarus_q07.py.

## Spec (from SPECS in desk3/lazarus_q07.py)
family="cyan", band="small", horizon_w=52,
filters=("cheap5", "ins2", "mom6").
Catalog note in the wrapper: Q07 Cyan H52 small
cheap5+insider2+mom6 (CSV ON).
- Inputs: fires, bars, positions. Slots = 1, budget = $1,000,
  parked = False (entries are live, not refused).

## Entry rules
- Exits are evaluated first (see below).
- Entries require an open slot (slots minus distinct held
  symbols) and a QQQ-down day: extra["qqq_red"] if a bool, else
  market["qqq_red"] if a bool, else QQQ last close below its
  prior close (needs at least 2 QQQ closes).
- Fires are read from view["fires"]. A fire is skipped if it
  has no symbol, its sleeve_id/sleeve (when carried) differs,
  its family does not normalise to the spec family (cyan
  accepts cyan/w_cyan/c), its band/cap_band does not normalise
  to the spec band (midlarge accepts ml/midlarge/mid_large/
  mid/large; small accepts sm/small), or its symbol is held.
- Signal age: sessions since signal_date/fired_at/fire_date/
  date, counted on QQQ bar dates when available else calendar
  days x 5/7, must be present and at most 5 sessions.
- Freshest-first (ENH-Q07FRESH-20261024, switch default ON;
  OFF restores producer list order): when 2 or more candidate
  fires pass the sleeve/family/band/held checks, the slot is
  allocated freshest-signal-first.
- Filters (all must pass, fail-closed on no evidence):
- cheap5: the evaluated price is below $5.00 (computed
  from the fire/bars price, no tag).
- ins2: insider_buys >= 2 when that tag is carried, else a
  true ins2 tag; no insider evidence fails closed.
- mom6: mom6_pct tag > 0, else a mom6 tag that is true or
  > 0, else a positive 126-session return from bars (at
  least 127 closes, last above the close 126 sessions back).
- Execution price (ENH-Q07EXEC-20261024, switch default ON;
  OFF restores the fire-price rule): filters, sizing and stop
  are revalidated at the latest bar close; the fire price
  (falling back to the latest close) is the stale/control price.
- Sizing: qty = int((budget / slots) // price); qty < 1 emits
  nothing. Orders are market, day, buy_to_open, with
  stop_price = round(price * (1 - 0.15), 4).

## Exit rules
- Stop: a held position (qty > 0, entry > 0) whose last close
  (or current_price fallback) is at or below entry * 0.85 is
  sold in full, reason q07 exit: stop_15pct.
- Horizon: otherwise, a position whose held calendar days
  (session minus opened_at/entry_date) reach horizon_w x 7
  (364 days for 52 weeks) is sold in full, reason
  q07 exit: horizon_52w.
- Exits are market, day, sell_to_close, in full.

## Data inputs
Declared inputs: fires, bars, positions. Producers named in
the engine: sleeve_feed_composer (604800s freshness, outputs
fires), bars (3600s), broker_readback (3600s, positions).
