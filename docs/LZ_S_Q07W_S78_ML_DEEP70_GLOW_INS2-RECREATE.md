# lz_s_q07w_s78_ml_deep70_glow_ins2 - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `lz_s_q07w_s78_ml_deep70_glow_ins2`
- Canonical name: Q07 w_swing H78 midlarge deep70+gamma_low+insider2 (test)
- Aliases: lz_s_q07w_s78_ml_deep70_glow_ins2
- Type: trend following; Family: 1w; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Q07 w_swing H78 midlarge deep70+gamma_low+insider2 (test)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q07 w_swing H78 midlarge deep70+gamma_low+insider2 (test)" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Existing Test doc for this cell: none (no ALGORITHM doc for this sleeve in Test; the Full algorithm section is derived from the code in this repo, as stated there)
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken at batch start, 4,430 entries, plus file reads: laz_sleeves/, sleeves/, sleeves/lazarus/, adapters3/, integration/ wrappers for each cell, engines/laz_sleeves/_common.py, desk3/lazarus_q07.py SPECS, desk3/q07_engine.py, config/sleeves.json, packages/grokbot/rl64/lz_engine/config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, docs/ ALGORITHM docs, strategies/lazarus/lz-q07.md); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries; no q07 or wait_q14 path); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries; no q07 or wait_q14 path); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries; no q07 or wait_q14 path).
- Accounting algorithm record (verbatim fields): entry: ['[lz_s_q07w_s78_ml_deep70_glow_ins2] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}']; exit: ['[lz_s_q07w_s78_ml_deep70_glow_ins2] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 78 weeks (W78; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}']; filters: ['[lz_s_q07w_s78_ml_deep70_glow_ins2] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json']; gaps: ['sizing not recorded in any consulted source']

## What this strategy is

Q07 w_swing H78 midlarge deep70+gamma_low+insider2 (test). A Lazarus Q07 weekly (1w) fire-consumer cell: family w_swing, with the alt-data filters named in the canonical name, hold 78 weeks. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

The canonical ID carries the lz_ prefix from the md2 catalog record; the runnable Test sleeve for the same cell, where one exists, uses the same ID without the lz_ prefix. That mapping is stated per package below and is not assumed for cells where no such file exists.

## Full algorithm

No separate ALGORITHM doc for this sleeve exists in Test (checked docs/ at batch start). The description below is read directly from the code named in Files in this repo: the wrapper laz_sleeves/s_q07w_s78_ml_deep70_glow_ins2.py and the shared engine engines/laz_sleeves/_common.py (q07_evaluate). Note on the import: the wrapper does `from laz_sleeves._common import q07_evaluate`; a top-level laz_sleeves/_common.py was not found in the Test tree at batch start (GET returned 404), and the shared engine code that was located in Test is at engines/laz_sleeves/_common.py. That gap is recorded here exactly as found; no file was invented to fill it.

## What it trades
A thin wrapper sleeve: evaluate(view, ctx) delegates to q07_evaluate(view, ctx, SLEEVE_ID, band="midlarge", horizon_weeks=78, filters=('deep70', 'glow', 'ins2'), slots=1, slot_usd=1000.0). Long-only equity Lazarus Q07 weekly fire-consumer (catalog section 4.1 family rule): take the Tensor 1W swing signal in the named cap band, apply the named alt-data filters, buy only on a QQQ-down day within 5 sessions of the signal, exit on a 15% stop or at the time horizon. Fires arrive via the desk Tensor bundle producer (ledger substitution LAZ-B7, per the wrapper docstring). Source status in the wrapper docstring: Disabled, parked in v3 config (evaluates, dispatcher skips entries while parked); config/sleeves.json row for this id also carries parked=true.

## Entry rules (evaluation order in q07_evaluate)
- Session is view["now"] date; if it cannot be parsed, no intents.
- Exits are evaluated first (see below), over positions belonging to this sleeve only (position sleeve_id is None or this id, qty != 0).
- Entries are blocked if the held count reaches slots (1) or QQQ is not down (QQQ 1Day bars, last close below prior close, at least 2 bars).
- Fires are read from view["tensor_fires"], a dict keyed by symbol, iterated in sorted symbol order. A fire is skipped if its symbol is held, its family is not exactly "swing", its date cannot be parsed, or its calendar age in days is under 0 or over 7 (the code comment reads this as within 5 sessions of the signal).
- Alt-data tags are read from view["alt_data"][symbol]; the fire is skipped unless tags["mcap_band"] equals the wrapper band ("midlarge").
- The symbol must have 1Day bars. Filters (all must pass; readings are the _common code's own):
- deep70: last daily close <= 0.30 * the maximum high over the last 252 daily bars (the _common code's own reading; bars must be present). Note: this 0.30 reading differs from the deep70 readings in desk3/lazarus_q07.py and desk3/q07_engine.py; the code named here is the truth for this wrapper.
- glow: tags["gamma_low"] is True.
- ins2: int(tags["insider_buys"] or 0) >= 2.
- Stale-bar gate (ENH24-LAZB7-Q07STALE-20261024, switch default ON via extra["<sid>_enh24"]["stale_gate"]): an entry is refused when the symbol's last daily bar is more than 4 calendar days before the session; exits are never gated.
- Sizing: qty = int(1000.0 // last_close); qty < 1 emits nothing. The entry intent is market, day, side buy, price_hint = last close, reason "q07_" + the filter names joined by underscores. Slot guard (ENH-Q07SLOT-20261024, default ON): entry emission stops once held plus emitted entries reach slots.

## Exit rules
- Stop: a held position whose last daily close is at or below avg_price * 0.85 is sold in full, reason q07_stop15.
- Horizon: otherwise, a position whose sessions held (daily bars strictly after opened_at) reach horizon_weeks * 5 (390 sessions for 78 weeks) is sold in full, reason q07_time_horizon.
- Exits are market, day, side sell, in full (absolute qty).

## Data inputs
Declared inputs in the wrapper: bars_1day, positions, tensor_fires, alt_data, vix. The _common engine view keys: bars {"SYM|1Day": bars}, positions, tensor_fires {SYM: {family, date}}, alt_data {SYM: {insider_buys, wiki, gamma_low, ats_z, mcap_band}}, vix (float).

Accounting gaps (not in the record): sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/LZ_S_Q07W_S78_ML_DEEP70_GLOW_INS2-RECREATE.md`
- Algorithm doc: none (no ALGORITHM doc for this sleeve in Test; the Full algorithm section is derived from the code in this repo, as stated there)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family strategy card: `strategies/lazarus/lz-q07.md`
- Code in Test:
- `laz_sleeves/s_q07w_s78_ml_deep70_glow_ins2.py` (in Test)
- `sleeves/lazarus/s_q07w_s78_ml_deep70_glow_ins2.py` (in Test)
- `integration/s_q07w_s78_ml_deep70_glow_ins2_adapter.py` (in Test)
- `engines/laz_sleeves/_common.py` (in Test)
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

config/sleeves.json row for `s_q07w_s78_ml_deep70_glow_ins2` (verbatim): {"id": "s_q07w_s78_ml_deep70_glow_ins2", "module": "laz_sleeves.s_q07w_s78_ml_deep70_glow_ins2", "cadence_s": 86400, "session": "rth", "slice": {"capital_usd": 1000.0, "cash_usd": 1000.0}, "bp_buffer_frac": 0.02, "flat_by_close": false, "flatten_time_et": null, "params": {}, "inputs": ["bars_1day", "positions", "tensor_fires", "alt_data", "vix"], "parked": true}

Accounting entry policy for every cell in this batch (verbatim from the accounting entry field): policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day. Exit in accounting: the sleeve feed fire's plan (15% disaster stop / time exit; hold = 78 weeks from fill). Sizing in accounting: not in the record (gap listed).

## Data inputs

Sleeve feed fires from the sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json, as recorded in the accounting filters field; plus the inputs declared in the Full algorithm section for the code-backed cells. Alt-data tags are the filters named for this cell.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc and `docs/ALL-SLEEVES.json` for the accounting record.
3. Use the code files listed above as the runnable logic: the wrapper for `s_q07w_s78_ml_deep70_glow_ins2` exposes evaluate(view, ctx) delegating to its shared engine as described in the Full algorithm section.
4. Supply the data inputs named above in the view / ctx shape the code expects.
5. Call evaluate(view, ctx) on the desk cycle cadence; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm record above.
- Checklist: (a) with no qualifying fire, no entry is emitted; (b) with a qualifying fire and every named filter passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or below entry x 0.85 (15% stop) exits in full; (d) a held position reaching the stated hold exits in full where a hold is recorded; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- Compare any recreation outputs on identical view inputs against the Test code files listed above; matching intents on those cases proves the recreation matches.
