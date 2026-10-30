Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_q07w_s78_mi_cheap5_ins2_mom6: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/s_q07w_s78_mi_cheap5_ins2_mom6.py is the
per-sleeve core: evaluate() delegates to the shared engine
desk3/q07_engine.py evaluate_q07(SPEC, view, ctx), with the
SPEC dict carried inline in the wrapper. It is a long-only
equity Lazarus Q07 alt-data confluence lane (catalog section
4.1 family rule): take the Tensor 1W signal of the named
family in the named cap band, apply the named alt-data
filters, buy only on a QQQ-down day within 5 sessions of the
signal, exit on a 15% stop or at the time horizon.
Fail-closed: no fresh fires means no entry, and a filter with
no evidence fails closed. The sleeve runs on the shared
engine desk3/q07_engine.py.

## Spec (SPEC dict in adapters3/s_q07w_s78_mi_cheap5_ins2_mom6.py)
family="swing", band="mi", horizon_wk=78,
filters=("cheap5", "ins2", "mom6").
Catalog note in the wrapper: Tensor 1W swing signal, mi
cap band, filters cheap5+ins2+mom6 (batch 6, authored
for v3; no v2 source exists).
- Declared inputs in the wrapper: sleeve_fires, bars_1day,
  vix, positions. Standard sizing in the engine: 1 slot at
  $1,000 (SLOT_USD = 1000.0), stop 15% (STOP_PCT = 0.15),
  maximum signal age 5 sessions.
- Cap bands in the engine (CAP_BANDS_USD): mi = $0 to
  $300,000,000; sm = $300,000,000 to $2,000,000,000;
  ml = $2,000,000,000 and above. This sleeve uses band
  "mi" ($0 to $300,000,000).

## Entry rules
- Exits are evaluated first (see below).
- Entries are blocked entirely while any position is held
  (the 1 slot is occupied).
- A QQQ-down day is required: at least 2 QQQ daily bars and
  the last QQQ close below the prior close.
- Fires are read from view extra["sleeve_fires"] (params
  extra may also supply keys). A fire is skipped if its
  sleeve field differs from the spec id, it has no symbol,
  its symbol is held, its cap_band (when carried) differs
  from the spec band, its mcap_usd (when carried) falls
  outside the spec band range, it has no signal_date, its
  signal age (QQQ sessions in (signal_date, today]) is
  under 0 or over 5 sessions, or it has no daily bars.
- Freshest-first (ENH-Q07FRESH-20261024, switch default ON;
  OFF restores producer list order): eligible fires are
  ordered by signal age, freshest first.
- Stale bars (ENH25-Q07-STALEBARS-20261024, switch default
  ON): a fire whose symbol's last bar is more than 5
  sessions before today is refused.
- Filters (all must pass, fail-closed on no evidence;
  prices are the symbol's last daily bar close):
- cheap5: last close < $5.00; no bars / no price fails.
- ins2: insider_buys on the fire >= 2; a missing value
  counts as 0 and fails.
- mom6: at least 127 daily bars and last close above the
  close 126 sessions back; otherwise fails.
- Sizing: qty = int(1000.0 // price); qty < 1 emits
  nothing. The entry is an Intent, side buy,
  position_intent buy_to_open, with stop =
  round(price * (1 - 0.15), 4) and exit rules stop at that
  price plus time_bars = horizon_wk x 5. Reason string:
  q07_swing_tensor1w_mi filters=<filters joined by +>
  signal=<signal_date> age_sessions=<age>. Only one entry
  is emitted (break after the first passing fire).

## Exit rules
- Stop: a held position (qty > 0) whose last close is at or
  below avg_price * 0.85 is sold in full, reason q07_stop15.
- Horizon: otherwise, a position whose age in weeks
  (today minus opened_at, in days / 7) reaches horizon_wk
  (78 weeks) is sold in full, reason
  q07_horizon_exit.
- Exits are Intents, side sell, position_intent
  sell_to_close, in full.

## Data inputs
Declared inputs: sleeve_fires, bars_1day, vix, positions.
Fires arrive via the sleeve_feed composer (tracker ledger
plus alt-data tags) as the producer key sleeve_fires in the
cycle snapshot view extra; the VIX value is view extra vix.
