# lz_s_q07w_s52_sm_cheap5_deep70_ins2 - Recreation Package

## Provenance

- Canonical ID: `lz_s_q07w_s52_sm_cheap5_deep70_ins2`
- Canonical name: Q07 w_swing H52 small cheap5+deep70+insider2 (test)
- Aliases: lz_s_q07w_s52_sm_cheap5_deep70_ins2
- Type: trend following ; Family: 1w ; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Q07 w_swing H52 small cheap5+deep70+insider2 (test)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q07 w_swing H52 small cheap5+deep70+insider2 (test)" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Existing Test doc: `docs/S_Q07W_S52_SM_CHEAP5_DEEP70_INS2-ALGORITHM.md` in dwj9ddyvf6-hub/Test.
- Code search record: searched Test (tree at batch start; found, see Files below), dwj9ddyvf6-hub/Silicon (recursive tree; no path matching this canonical ID), dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path matching this canonical ID). Code is present in Test, so no vendoring was needed.
- Accounting algorithm record (verbatim fields): entry: ['[lz_s_q07w_s52_sm_cheap5_deep70_ins2] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}'] ; exit: ['[lz_s_q07w_s52_sm_cheap5_deep70_ins2] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}'] ; filters: ['[lz_s_q07w_s52_sm_cheap5_deep70_ins2] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json'] ; gaps: ['sizing not recorded in any consulted source']

## What this strategy is

Q07 w_swing H52 small cheap5+deep70+insider2 (test). Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

The full Test algorithm document / strategy card for this strategy is reproduced in the Full algorithm section below. Where the accounting graded the algorithm PARTIAL, gaps named in the accounting are preserved there and below as 'not in the record' rather than filled.

## Full algorithm

Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_q07w_s52_sm_cheap5_deep70_ins2: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/s_q07w_s52_sm_cheap5_deep70_ins2.py is the
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

## Spec (SPEC dict in adapters3/s_q07w_s52_sm_cheap5_deep70_ins2.py)
family="swing", band="sm", horizon_wk=52,
filters=("cheap5", "deep70", "ins2").
Catalog note in the wrapper: Tensor 1W swing signal, sm
cap band, filters cheap5+deep70+ins2 (batch 6, authored
for v3; no v2 source exists).
- Declared inputs in the wrapper: sleeve_fires, bars_1day,
  vix, positions. Standard sizing in the engine: 1 slot at
  $1,000 (SLOT_USD = 1000.0), stop 15% (STOP_PCT = 0.15),
  maximum signal age 5 sessions.
- Cap bands in the engine (CAP_BANDS_USD): mi = $0 to
  $300,000,000; sm = $300,000,000 to $2,000,000,000;
  ml = $2,000,000,000 and above. This sleeve uses band
  "sm" ($300,000,000 to $2,000,000,000).

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
- deep70: at least 20 daily bars and last close <= 70% of
  the maximum high over the trailing 252 sessions.
- ins2: insider_buys on the fire >= 2; a missing value
  counts as 0 and fails.
- Sizing: qty = int(1000.0 // price); qty < 1 emits
  nothing. The entry is an Intent, side buy,
  position_intent buy_to_open, with stop =
  round(price * (1 - 0.15), 4) and exit rules stop at that
  price plus time_bars = horizon_wk x 5. Reason string:
  q07_swing_tensor1w_sm filters=<filters joined by +>
  signal=<signal_date> age_sessions=<age>. Only one entry
  is emitted (break after the first passing fire).

## Exit rules
- Stop: a held position (qty > 0) whose last close is at or
  below avg_price * 0.85 is sold in full, reason q07_stop15.
- Horizon: otherwise, a position whose age in weeks
  (today minus opened_at, in days / 7) reaches horizon_wk
  (52 weeks) is sold in full, reason
  q07_horizon_exit.
- Exits are Intents, side sell, position_intent
  sell_to_close, in full.

## Data inputs
Declared inputs: sleeve_fires, bars_1day, vix, positions.
Fires arrive via the sleeve_feed composer (tracker ledger
plus alt-data tags) as the producer key sleeve_fires in the
cycle snapshot view extra; the VIX value is view extra vix.


Accounting gaps (not in the record): sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/LZ_S_Q07W_S52_SM_CHEAP5_DEEP70_INS2-RECREATE.md`
- Algorithm doc / strategy card: `docs/S_Q07W_S52_SM_CHEAP5_DEEP70_INS2-ALGORITHM.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Code in Test:
- `sleeves/s_q07w_s52_sm_cheap5_deep70_ins2.py` (in Test)
- `adapters3/s_q07w_s52_sm_cheap5_deep70_ins2.py` (in Test)
- `integration/s_q07w_s52_sm_cheap5_deep70_ins2_adapter.py` (in Test)
- `desk3/q07_engine.py` (in Test)
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

Family swing, band sm ($300,000,000 to $2,000,000,000 in the engine), horizon 52 weeks, filters cheap5, deep70, ins2. Slots 1, budget $1,000 (SLOT_USD 1000.0), stop 15% (STOP_PCT 0.15), max signal age 5 sessions. Declared inputs sleeve_fires, bars_1day, vix, positions. Accounting entry policy as in Provenance; sizing in accounting: not in the record.

Other configuration (cadence, state, session) is as stated in the algorithm text above; anything not stated there is not in the record.

## Data inputs

As stated in the algorithm text above. For Q07 lanes: fires from the sleeve_feed composer, bars, and positions / broker readback, as named in that text. For other lanes: the data line in the strategy card reproduced above.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Open `docs/S_Q07W_S52_SM_CHEAP5_DEEP70_INS2-ALGORITHM.md` and this doc for the parameter values.
3. Use the code files listed above as the runnable logic; for Q07 lanes the wrapper's `evaluate(view, ctx)` delegates to the shared engine named in the code list, with the SPEC for this sleeve ID.
4. Supply the data inputs named above in the view / ctx shape the code expects (fires, bars, positions, plus any extra keys the algorithm text names).
5. Call `evaluate(view, ctx)` on each cadence stated in Configuration; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm section.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm text above.
- Checklist: (a) with no qualifying fire / signal, no entry is emitted; (b) with a qualifying signal and all filters passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or beyond the stated stop exits in full; (d) a held position reaching the stated horizon / exit session exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- Compare any recreation's outputs on identical view inputs against the Test code files listed above; matching intents / orders on those cases proves the recreation matches.
