# lz_s_q07w_s52_ml_deep70_vix20_wlow - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `lz_s_q07w_s52_ml_deep70_vix20_wlow`
- Canonical name: Q07 w_swing H52 midlarge deep70+stress_vix20+wiki_low (test)
- Aliases: lz_s_q07w_s52_ml_deep70_vix20_wlow
- Type: trend following; Family: 1w; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Q07 w_swing H52 midlarge deep70+stress_vix20+wiki_low (test)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q07 w_swing H52 midlarge deep70+stress_vix20+wiki_low (test)" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Existing Test doc for this cell: `docs/S_Q07W_S52_ML_DEEP70_VIX20_WLOW-ALGORITHM.md` in dwj9ddyvf6-hub/Test
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (fresh recursive tree taken at batch start, 294,179 bytes of tree listing, plus file reads: sleeves/, sleeves/lazarus/, laz_sleeves/, adapters3/, integration/, desk3/lazarus_q07.py SPECS, desk3/q07_engine.py, laz_sleeves/_common.py (404, not in tree), config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, docs/ ALGORITHM docs); dwj9ddyvf6-hub/Silicon (fresh recursive tree; no q07 path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree; no q07 path); dwj9ddyvf6-hub/Midna (fresh recursive tree; no q07 path).
- Accounting algorithm record (verbatim fields): entry: ['[lz_s_q07w_s52_ml_deep70_vix20_wlow] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}']; exit: ['[lz_s_q07w_s52_ml_deep70_vix20_wlow] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}']; filters: ['[lz_s_q07w_s52_ml_deep70_vix20_wlow] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json']; gaps: ['sizing not recorded in any consulted source']

## What this strategy is

Q07 w_swing H52 midlarge deep70+stress_vix20+wiki_low (test). A Lazarus Q07 weekly (1w) fire-consumer cell: family w_swing, hold 52 weeks, with the filters named in the canonical name. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

The canonical ID carries the lz_ prefix from the md2 catalog record; the runnable Test sleeve for the same cell, where one exists, uses the same ID without the lz_ prefix. That mapping is stated per package below and is not assumed for cells where no such file exists.

## Full algorithm

Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_q07w_s52_ml_deep70_vix20_wlow: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/s_q07w_s52_ml_deep70_vix20_wlow.py is the
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
family="swing", band="midlarge", horizon_w=52,
filters=("deep70", "vix20", "wlow").
Catalog note in the wrapper: Q07 Swing H52 midlarge
deep70+stress_vix20+wiki_low (CSV off).
- Inputs: fires, bars, positions. Slots = 1, budget = $1,000,
  parked = True (CSV off: entries are refused, exits are
  still managed; see below).
The wrapper also carries PARAMS derived from SPEC
(family, cap_band="ml", horizon_weeks, filters, parked).

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
  to the spec band (midlarge accepts ml/midlarge/mid_large/mid/large), or its symbol is held.
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
- vix20: a vix tag >= 20.0, else the last close of VIX or
  ^VIX bars >= 20.0; a missing VIX value fails closed.
- wlow: a true wiki_low tag, or wiki_attention == "low".
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

Accounting gaps (not in the record): sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/LZ_S_Q07W_S52_ML_DEEP70_VIX20_WLOW-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family strategy card: `strategies/lazarus/lz-q07.md`
- Code in Test:
- `sleeves/s_q07w_s52_ml_deep70_vix20_wlow.py` (in Test)
- `adapters3/s_q07w_s52_ml_deep70_vix20_wlow.py` (in Test)
- `integration/s_q07w_s52_ml_deep70_vix20_wlow_adapter.py` (in Test)
- `desk3/lazarus_q07.py` (in Test)
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

SPEC in desk3/lazarus_q07.py: family="swing", band="midlarge", horizon_w=52, filters=("deep70", "vix20", "wlow"), slots=1, budget=1000.0, parked=True. Config row in config/sleeves.json: module adapters3.s_q07w_s52_ml_deep70_vix20_wlow, cadence_s 3600, session rth, slice capital_usd 1000.0 / cash_usd 1000.0, bp_buffer_frac 0.02, flat_by_close false, inputs [fires, bars, positions], parked true, producers sleeve_feed_composer (604800s), bars (3600s), broker_readback (3600s).

Accounting entry policy for every cell in this batch (verbatim from the accounting entry field): policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day. Exit in accounting: the sleeve feed fire's plan (15% disaster stop / time exit; hold = 52 weeks from fill). Sizing in accounting: not in the record (gap listed).

## Data inputs

Sleeve feed fires from the sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json, as recorded in the accounting filters field; plus fires, bars, positions as declared in the engine.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc and `docs/ALL-SLEEVES.json` for the accounting record.
3. Use the code files listed above as the runnable logic: `sleeves/s_q07w_s52_ml_deep70_vix20_wlow.py` exposes evaluate(view, ctx), which delegates to desk3/lazarus_q07.py evaluate_sleeve with SPECS["s_q07w_s52_ml_deep70_vix20_wlow"] (parked=True: entries refused, exits managed).
4. Supply the data inputs named above in the view / ctx shape the code expects.
5. Call evaluate(view, ctx) on the desk cycle cadence stated in Configuration; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm record above.
- Checklist: (a) with no qualifying fire, no entry is emitted; (b) with a qualifying fire and every named filter passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or below entry x 0.85 (15% stop) exits in full; (d) a held position reaching the stated hold (52 weeks from fill) exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- Compare any recreation outputs on identical view inputs against the Test code files listed above; matching intents on those cases proves the recreation matches.
