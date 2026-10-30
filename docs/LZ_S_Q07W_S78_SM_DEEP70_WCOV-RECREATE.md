# lz_s_q07w_s78_sm_deep70_wcov - Recreation Package

## Provenance

- Canonical ID: `lz_s_q07w_s78_sm_deep70_wcov`
- Canonical name: Q07 w_swing H78 small deep70+wiki_cov (test)
- Aliases: lz_s_q07w_s78_sm_deep70_wcov
- Type: trend following ; Family: 1w ; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Q07 w_swing H78 small deep70+wiki_cov (test)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q07 w_swing H78 small deep70+wiki_cov (test)" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Existing Test doc: `docs/S_Q07W_S78_SM_DEEP70_WCOV-ALGORITHM.md` in dwj9ddyvf6-hub/Test.
- Code search record: searched Test (tree at batch start; found, see Files below), dwj9ddyvf6-hub/Silicon (recursive tree; no path matching this canonical ID), dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path matching this canonical ID). Code is present in Test, so no vendoring was needed.
- Accounting algorithm record (verbatim fields): entry: ['[lz_s_q07w_s78_sm_deep70_wcov] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}'] ; exit: ['[lz_s_q07w_s78_sm_deep70_wcov] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 78 weeks (W78; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}'] ; filters: ['[lz_s_q07w_s78_sm_deep70_wcov] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json'] ; gaps: ['sizing not recorded in any consulted source']

## What this strategy is

Q07 w_swing H78 small deep70+wiki_cov (test). Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

The full Test algorithm document / strategy card for this strategy is reproduced in the Full algorithm section below. Where the accounting graded the algorithm PARTIAL, gaps named in the accounting are preserved there and below as 'not in the record' rather than filled.

## Full algorithm

Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_q07w_s78_sm_deep70_wcov: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/s_q07w_s78_sm_deep70_wcov.py is the
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
family="swing", band="small", horizon_w=78,
filters=("deep70", "wcov"), slots=2, budget=2265.0,
parked=True.
Catalog note in the wrapper: Q07 Swing H78 small
deep70+wiki_cov (CSV off, parked; exits managed).
- Inputs: fires, bars, positions. Per-slot budget =
  budget / slots = $1,132.50.

## Entry rules
- Because parked = True, entries are refused in the current
  spec: after exits are evaluated, evaluate_sleeve returns
  with no entry. The entry rules below are the engine rules
  that would apply if the lane were unparked.
- Exits are evaluated first (see below).
- Entries require an open slot (slots minus distinct held
  symbols) and a QQQ-down day: extra["qqq_red"] if a bool, else
  market["qqq_red"] if a bool, else QQQ last close below its
  prior close (needs at least 2 QQQ closes).
- Fires are read from view["fires"]. A fire is skipped if it
  has no symbol, its sleeve_id/sleeve (when carried) differs,
  its family does not normalise to the spec family
  (swing accepts swing/w_swing/s), its band/cap_band does not normalise
  to the spec band (small accepts sm/small), or its symbol is held.
- Signal age: sessions since signal_date/fired_at/fire_date/
  date, counted on QQQ bar dates when available else calendar
  days x 5/7, must be present and at most 5 sessions.
- Freshest-first (ENH-Q07FRESH-20261024, switch default ON;
  OFF restores producer list order): when 2 or more candidate
  fires pass the sleeve/family/band/held checks, the slot is
  allocated freshest-signal-first.
- Filters (all must pass, fail-closed on no evidence):
- deep70: an explicit deep70 tag, else
  drawdown_from_high >= 0.30, else price <= 70% of a
  high_52w tag, else price <= 70% of the maximum close in
  bars; no computable evidence fails closed.
- wcov: a true wiki_cov tag, else wiki_views > 0, else a
  true wiki_coverage tag, else wiki_attention in
  (covered, high, spike); no wiki evidence fails closed.
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
  (546 days for 78 weeks) is sold in full, reason
  q07 exit: horizon_78w.
- Exits are market, day, sell_to_close, in full.

## Data inputs
Declared inputs: fires, bars, positions. Producers named in
the engine: sleeve_feed_composer (604800s freshness, outputs
fires), bars (3600s), broker_readback (3600s, positions).


Accounting gaps (not in the record): sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/LZ_S_Q07W_S78_SM_DEEP70_WCOV-RECREATE.md`
- Algorithm doc / strategy card: `docs/S_Q07W_S78_SM_DEEP70_WCOV-ALGORITHM.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Code in Test:
- `sleeves/s_q07w_s78_sm_deep70_wcov.py` (in Test)
- `adapters3/s_q07w_s78_sm_deep70_wcov.py` (in Test)
- `integration/s_q07w_s78_sm_deep70_wcov_adapter.py` (in Test)
- `desk3/lazarus_q07.py` (in Test)
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

Family swing, band small, horizon 78 weeks, filters deep70 and wcov. Slots 2, budget 2265.0 (per-slot $1,132.50), parked True. Inputs fires, bars, positions. Accounting entry policy as in Provenance; sizing in accounting: not in the record.

Other configuration (cadence, state, session) is as stated in the algorithm text above; anything not stated there is not in the record.

## Data inputs

As stated in the algorithm text above. For Q07 lanes: fires from the sleeve_feed composer, bars, and positions / broker readback, as named in that text. For other lanes: the data line in the strategy card reproduced above.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Open `docs/S_Q07W_S78_SM_DEEP70_WCOV-ALGORITHM.md` and this doc for the parameter values.
3. Use the code files listed above as the runnable logic; for Q07 lanes the wrapper's `evaluate(view, ctx)` delegates to the shared engine named in the code list, with the SPEC for this sleeve ID.
4. Supply the data inputs named above in the view / ctx shape the code expects (fires, bars, positions, plus any extra keys the algorithm text names).
5. Call `evaluate(view, ctx)` on each cadence stated in Configuration; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm section.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm text above.
- Checklist: (a) with no qualifying fire / signal, no entry is emitted; (b) with a qualifying signal and all filters passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or beyond the stated stop exits in full; (d) a held position reaching the stated horizon / exit session exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- Compare any recreation's outputs on identical view inputs against the Test code files listed above; matching intents / orders on those cases proves the recreation matches.
