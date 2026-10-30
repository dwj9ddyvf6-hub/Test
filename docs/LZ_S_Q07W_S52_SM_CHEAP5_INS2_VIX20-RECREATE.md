# lz_s_q07w_s52_sm_cheap5_ins2_vix20 - Recreation Package

Grade: COMPLETE-CODE (code present in Test)

## Provenance

- Canonical ID: `lz_s_q07w_s52_sm_cheap5_ins2_vix20`
- Canonical name: Q07 w_swing H52 small cheap5+insider2+stress_vix20 (test)
- Aliases: lz_s_q07w_s52_sm_cheap5_ins2_vix20
- Type: trend following; Family: 1w; Algorithm grade in ALL-SLEEVES accounting: PARTIAL
- Accounting source: dwj9ddyvf6-hub/Test `docs/ALL-SLEEVES.json` strategy entry "Q07 w_swing H52 small cheap5+insider2+stress_vix20 (test)" (also `docs/ALL-SLEEVES.md`); doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Q07 w_swing H52 small cheap5+insider2+stress_vix20 (test)" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: md2 catalog entry/exit/strategy text; alias record sources: md2_catalog
- Existing Test doc for this cell: `docs/S_Q07W_S52_SM_CHEAP5_INS2_VIX20-ALGORITHM.md` in dwj9ddyvf6-hub/Test
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (fresh recursive tree taken at batch start, 294,179 bytes of tree listing, plus file reads: sleeves/, sleeves/lazarus/, laz_sleeves/, adapters3/, integration/, desk3/lazarus_q07.py SPECS, desk3/q07_engine.py, laz_sleeves/_common.py (404, not in tree), config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, docs/ ALGORITHM docs); dwj9ddyvf6-hub/Silicon (fresh recursive tree; no q07 path); dwj9ddyvf6-hub/quant-research-backup (fresh recursive tree; no q07 path); dwj9ddyvf6-hub/Midna (fresh recursive tree; no q07 path).
- Accounting algorithm record (verbatim fields): entry: ['[lz_s_q07w_s52_sm_cheap5_ins2_vix20] {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}']; exit: ['[lz_s_q07w_s52_sm_cheap5_ins2_vix20] {"rule": "the sleeve feed fire\'s plan (15% disaster stop (L-130) / time exit; hold = 52 weeks (W52; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}']; filters: ['[lz_s_q07w_s52_sm_cheap5_ins2_vix20] data: sleeve_feed composer (tracker ledger + alt-data tags) :: shadow/paper_sleeve/live/sleeve_fires_v1.json']; gaps: ['sizing not recorded in any consulted source']

## What this strategy is

Q07 w_swing H52 small cheap5+insider2+stress_vix20 (test). A Lazarus Q07 weekly (1w) fire-consumer cell: family w_swing, hold 52 weeks, with the filters named in the canonical name. Universe in accounting: not recorded in consulted sources. Asset class in accounting: not recorded. Timeframe in accounting: not recorded. Creator in accounting: not recorded.

The canonical ID carries the lz_ prefix from the md2 catalog record; the runnable Test sleeve for the same cell, where one exists, uses the same ID without the lz_ prefix. That mapping is stated per package below and is not assumed for cells where no such file exists.

## Full algorithm

Algorithm derived from the code in this repo: the wrapper sleeves/s_q07w_s52_sm_cheap5_ins2_vix20.py (SPEC dict inline) and the shared engine desk3/q07_engine.py (evaluate_q07). The Test ALGORITHM doc for this sleeve exists at docs/S_Q07W_S52_SM_CHEAP5_INS2_VIX20-ALGORITHM.md in Test; where that doc is summary-level, the engine details below are read directly from desk3/q07_engine.py.

## What it trades
A thin wrapper sleeve: evaluate() delegates to desk3/q07_engine.py evaluate_q07(SPEC, view, ctx), with SPEC = {"id": "s_q07w_s52_sm_cheap5_ins2_vix20", "family": "swing", "horizon_wk": 52, "band": "sm", "filters": ('cheap5', 'ins2', 'vix20')}. Long-only equity Lazarus Q07 alt-data confluence lane (catalog section 4.1 family rule): take the Tensor 1W swing signal in the named cap band, apply the named alt-data filters, buy only on a QQQ-down day within 5 sessions of the signal, exit on a 15% stop or at the time horizon. Fail-closed: no fresh fires means no entry, and a filter with no evidence fails closed.

## Spec (SPEC dict in the wrapper, and engine constants in desk3/q07_engine.py)
family="swing", band="sm" (engine CAP_BANDS_USD: sm = $300,000,000 to $2,000,000,000), horizon_wk=52, filters=('cheap5', 'ins2', 'vix20'). Declared inputs in the wrapper: sleeve_fires, bars_1day, vix, positions. Engine constants: SLOT_USD = 1000.0 (1 slot), STOP_PCT = 0.15, MAX_SIGNAL_AGE_SESSIONS = 5, MOM6_SESSIONS = 126, DEEP70_HIGH_SESSIONS = 252, WIKI_LOW_MAX_VIEWS = 1000.

## Entry rules (evaluation order in evaluate_q07)
- Exits are evaluated first (see below). Entries are then blocked entirely while any position is held (the 1 slot is occupied).
- A QQQ-down day is required: at least 2 QQQ daily bars (view bars key "QQQ|1day") and the last QQQ close below the prior close.
- Fires are read from view extra["sleeve_fires"] (params extra may also supply keys). A fire is skipped if its sleeve field differs from the SPEC id, it has no symbol, its symbol is held, its cap_band (when carried) differs from the SPEC band, its mcap_usd (when carried) falls outside the SPEC band range, it has no signal_date, its signal age (QQQ sessions in (signal_date, today]) is under 0 or over 5 sessions, or it has no daily bars.
- Freshest-first (ENH-Q07FRESH-20261024, switch extra.q07_enh[<id>].fresh_first, default ON; OFF restores producer list order): eligible fires are ordered by signal age, freshest first.
- Stale bars (ENH25-Q07-STALEBARS-20261024, switch default ON): a fire whose symbol's last bar is more than 5 sessions before today is refused.
- Filters (all must pass, fail-closed on no evidence; price is the symbol's last daily bar close):
- cheap5: last close < $5.00; no bars / no price fails.
- ins2: insider_buys on the fire >= 2; a missing value counts as 0 and fails.
- vix20: the snapshot vix value >= 20.0; a missing vix value fails closed.
- Sizing: qty = int(1000.0 // price); qty < 1 emits nothing. The entry is an Intent, side buy, position_intent buy_to_open, with stop = round(price * (1 - 0.15), 4) and exit rules stop at that price plus time_bars = horizon_wk x 5 (260). Reason: q07_swing_tensor1w_sm filters=<filters joined by +> signal=<signal_date> age_sessions=<age>. Only one entry is emitted (break after the first passing fire).

## Exit rules
- Stop: a held position (qty > 0) whose last close is at or below avg_price * 0.85 is sold in full, reason q07_stop15.
- Horizon: otherwise, a position whose age in weeks (today minus opened_at, in days / 7) reaches horizon_wk (52 weeks) is sold in full, reason q07_horizon_exit.
- Exits are Intents, side sell, position_intent sell_to_close, in full.

## Data inputs
Declared inputs: sleeve_fires, bars_1day, vix, positions. Fires arrive via the sleeve_feed composer (tracker ledger plus alt-data tags) as the producer key sleeve_fires in the cycle snapshot view extra; the VIX value is view extra vix.

Accounting gaps (not in the record): sizing not recorded in any consulted source

## Files in this repo

- This recreation doc: `docs/LZ_S_Q07W_S52_SM_CHEAP5_INS2_VIX20-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Family strategy card: `strategies/lazarus/lz-q07.md`
- Code in Test:
- `sleeves/s_q07w_s52_sm_cheap5_ins2_vix20.py` (in Test)
- `adapters3/s_q07w_s52_sm_cheap5_ins2_vix20.py` (in Test)
- `integration/s_q07w_s52_sm_cheap5_ins2_vix20_adapter.py` (in Test)
- `desk3/q07_engine.py` (in Test)
- Vendored files: none. Code was already in Test; no file was vendored from another repo for this package.

## Configuration

SPEC in the wrapper: family="swing", band="sm", horizon_wk=52, filters=('cheap5', 'ins2', 'vix20'). Config row in config/sleeves.json: module adapters3.s_q07w_s52_sm_cheap5_ins2_vix20, cadence_s 300, session rth, slice capital_usd 1000.0 / cash_usd 1000.0, bp_buffer_frac 0.02, flat_by_close false, inputs [sleeve_fires, bars_1day, vix, positions], parked true (config row; the dispatcher skips entries while parked, per the config record).

Accounting entry policy for every cell in this batch (verbatim from the accounting entry field): policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day. Exit in accounting: the sleeve feed fire's plan (15% disaster stop / time exit; hold = 52 weeks from fill). Sizing in accounting: not in the record (gap listed).

## Data inputs

Sleeve feed fires from the sleeve_feed composer (tracker ledger + alt-data tags), file shadow/paper_sleeve/live/sleeve_fires_v1.json, as recorded in the accounting filters field; plus sleeve_fires, bars_1day, vix, positions as declared in the wrapper.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Read this doc and `docs/ALL-SLEEVES.json` for the accounting record.
3. Use the code files listed above as the runnable logic: `sleeves/s_q07w_s52_sm_cheap5_ins2_vix20.py` exposes evaluate(view, ctx), which delegates to desk3/q07_engine.py evaluate_q07 with the inline SPEC.
4. Supply the data inputs named above in the view / ctx shape the code expects.
5. Call evaluate(view, ctx) on the desk cycle cadence stated in Configuration; exits are evaluated before entries where the algorithm text says so.
6. Do not change parameter values: use exactly the values in the Full algorithm and Configuration sections. Anything marked 'not in the record' must not be filled by guessing.

## Verification

- No dedicated test file for this specific sleeve ID was named in the Test tree at batch start; verification is by the behavior checklist below, derived only from the algorithm record above.
- Checklist: (a) with no qualifying fire, no entry is emitted; (b) with a qualifying fire and every named filter passing, exactly the entry described above is emitted with the stated sizing and stop; (c) a held position at or below entry x 0.85 (15% stop) exits in full; (d) a held position reaching the stated hold (52 weeks from fill) exits in full; (e) a filter with no evidence fails closed where the algorithm text says fail-closed; (f) parked lanes, where stated, refuse entries and still manage exits.
- Compare any recreation outputs on identical view inputs against the Test code files listed above; matching intents on those cases proves the recreation matches.
