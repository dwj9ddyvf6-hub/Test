# lz_s_q07w_g52_ml_ins2_wlow - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `lz_s_q07w_g52_ml_ins2_wlow`
- Canonical name: Q07 w_green H52 midlarge insider2+wiki_low (test)
- Aliases: lz_s_q07w_g52_ml_ins2_wlow
- Type: trend following; Family: 1w; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Q07 w_green H52 midlarge insider2+wiki_low (test)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q07 w_green H52 midlarge insider2+wiki_low (test)" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Existing Test doc for this cell: `docs/S_Q07W_G52_ML_INS2_WLOW-ALGORITHM.md` in dwj9ddyvf6-hub/Test
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken at batch start, 4,430 entries, plus file reads: sleeves/, adapters3/, integration/, desk3/lazarus_q07.py SPECS, desk3/q07_engine.py, config/sleeves.json, docs/ ALGORITHM docs, strategies/lazarus/lz-q07.md); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no q07w_g path for any batch-32 cell); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no q07w_g path for any batch-32 cell); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no q07w_g path for any batch-32 cell).
- Accounting algorithm record (verbatim fields): entry: ['[lz_s_q07w_g52_ml_ins2_wlow] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}']; exit: ['[lz_s_q07w_g52_ml_ins2_wlow] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}']; filters: ['[lz_s_q07w_g52_ml_ins2_wlow] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json']; gaps: ['sizing not recorded in any consulted source']

## What this strategy is

Q07 w_green H52 midlarge insider2+wiki_low (test). A Lazarus Q07 weekly (1w) fire-consumer cell: family w_green, midlarge cap band, hold 52 weeks, with the alt-data filters named in the canonical name. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

The canonical ID carries the lz_ prefix from the md2 catalog record; the runnable Test sleeve for the same cell, where one exists, uses the same ID without the lz_ prefix. That mapping is stated per package below and is not assumed for cells where no such file exists.

## Full algorithm

Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_q07w_g52_ml_ins2_wlow: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/s_q07w_g52_ml_ins2_wlow.py is the
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

## Spec (SPEC dict in adapters3/s_q07w_g52_ml_ins2_wlow.py)
family="green", band="ml", horizon_wk=52,
filters=("ins2", "wlow").
Catalog note in the wrapper: Tensor 1W green signal, ml
cap band, filters ins2+wlow (batch 6, authored for v3;
no v2 source exists).
- Declared inputs in the wrapper: sleeve_fires, bars_1day,
  vix, positions. Standard sizing in the engine: 1 slot at
  $1,000 (SLOT_USD = 1000.0), stop 15% (STOP_PCT = 0.15),
  maximum signal age 5 sessions.
- Cap bands in the engine (CAP_BANDS_USD): mi = $0 to
  $300,000,000; sm = $300,000,000 to $2,000,000,000;
  ml = $2,000,000,000 and above. This sleeve uses band
  "ml" ($2,000,000,000 and above).

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
- ins2: insider_buys on the fire >= 2; a missing value
  counts as 0 and fails.
- wlow: a true wiki_low tag on the fire, or
  wiki_views_30d < 1000 (WIKI_LOW_MAX_VIEWS). Missing wiki
  evidence fails closed (ENH-Q07WLOW-20261024, switch
  default ON).
- Sizing: qty = int(1000.0 // price); qty < 1 emits
  nothing. The entry is an Intent, side buy,
  position_intent buy_to_open, with stop =
  round(price * (1 - 0.15), 4) and exit rules stop at that
  price plus time_bars = horizon_wk x 5. Reason string:
  q07_green_tensor1w_ml filters=<filters joined by +>
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

- This recreation doc: `docs/LZ_S_Q07W_G52_ML_INS2_WLOW-RECREATE.md`
- Algorithm doc: `docs/S_Q07W_G52_ML_INS2_WLOW-ALGORITHM.md` in dwj9ddyvf6-hub/Test
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family strategy card: `strategies/lazarus/lz-q07.md`
- Code in Test:
- `sleeves/s_q07w_g52_ml_ins2_wlow.py` (in Test)
- `adapters3/s_q07w_g52_ml_ins2_wlow.py` (in Test)
- `integration/s_q07w_g52_ml_ins2_wlow_adapter.py` (in Test)
- `desk3/q07_engine.py` (in Test)
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

SPEC for this cell: SPEC dict inline in the wrapper: {"id": "s_q07w_g52_ml_ins2_wlow", "family": "green", "horizon_wk": 52, "band": "ml", "filters": ('ins2', 'wlow')}; engine constants in desk3/q07_engine.py: SLOT_USD = 1000.0, STOP_PCT = 0.15, maximum signal age 5 sessions, CAP_BANDS_USD ml = $2,000,000,000 and above.

Accounting entry policy for every cell in this batch (verbatim from the accounting entry field): policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day. Exit in accounting: the sleeve feed fire's plan (15% disaster stop / time exit; hold = 52 weeks from fill). Sizing in accounting: not in the record (gap listed).

## Data inputs

Sleeve feed fires from the sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json, as recorded in the accounting filters field; plus bars and positions / broker readback as named in the Full algorithm section. Alt-data tags are the filters named for this cell.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc and `docs/ALL-SLEEVES.json` for the accounting record.
3. Use the code files listed above as the runnable logic: `sleeves/s_q07w_g52_ml_ins2_wlow.py` exposes evaluate(view, ctx), which delegates to desk3/q07_engine.py evaluate_q07 with the SPEC dict inline in the wrapper.
4. Supply the data inputs named above in the view / ctx shape the code expects (fires, bars, positions).
5. Call evaluate(view, ctx) on the desk cycle cadence; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm record above.
- Checklist: (a) with no qualifying fire, no entry is emitted; (b) with a qualifying fire and every named filter passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or below entry x 0.85 (15% stop) exits in full; (d) a held position reaching the stated hold (52 weeks from fill) exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- Compare any recreation outputs on identical view inputs against the Test code files listed above; matching intents on those cases proves the recreation matches.
