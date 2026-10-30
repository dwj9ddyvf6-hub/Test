# lz_s_q07w_c78_sm_ins2_mom6_vix20: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Q07 w_cyan H78 small insider2+mom6+stress_vix20 (test)", type trend following, family 1w. Algorithm grade PARTIAL in the accounting, with the recorded gap: sizing not recorded in any consulted source. Alias `lz_s_q07w_c78_sm_ins2_mom6_vix20` (md2_catalog status: installed).
- Accounting entry record: {"policy": "fear_day", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": 5, "no_chase_mult": 1.02, "stock_red": true, "qqq_red": true, "order": "capped_limit_day"}. Accounting exit record: {"rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = 78 weeks (W78; calendar weeks after the fire week, desk weekly time exit))", "hold_from": "fill", "hold_unit_kind": "1w", "stop_pct": null, "max_bars": null, "rest": null, "plan_overrides": []}. Accounting data note: sleeve_feed composer (tracker ledger + alt-data tags), fire file shadow/paper_sleeve/live/sleeve_fires_v1.json.
- The sizing the accounting lacked, and the running rules, are held in the code in this repo (named in Files) and in the code-derived Test doc `docs/S_Q07W_C78_SM_INS2_MOM6_VIX20-ALGORITHM.md`; nothing beyond the record and that code is claimed. The Test sleeve id drops the accounting's `lz_` prefix: `s_q07w_c78_sm_ins2_mom6_vix20`.

## What this strategy is

A long-only equity Lazarus Q07 weekly fire-consumer (catalog section 4.1 family rule): take the Tensor 1W signal of the Cyan family in the small cap band, apply the named alt-data filters (insider2+mom6+stress_vix20), buy only on a QQQ-down day within 5 sessions of the signal, exit on a 15% stop or at the 78-week horizon. Fail-closed: no fresh fires means no entry, and a filter with no evidence fails closed.

## Full algorithm

From `docs/S_Q07W_C78_SM_INS2_MOM6_VIX20-ALGORITHM.md`, derived from the code: wrapper `sleeves/s_q07w_c78_sm_ins2_mom6_vix20.py` delegates to `desk3/lazarus_q07.py` evaluate_sleeve(SLEEVE_ID, view, ctx), with SPEC = SPECS[SLEEVE_ID]: family="cyan", band="small", horizon_w=78, filters=- ins2: insider_buys >= 2 when that tag is carried, else a true ins2 tag; no insider evidence fails closed.
- mom6: mom6_pct tag > 0, else a mom6 tag that is true or > 0, else a positive 126-session return from bars (at least 127 closes, last above the close 126 sessions back).
- vix20: a vix tag >= 20.0, else the last close of VIX or ^VIX bars >= 20.0; a missing VIX value fails closed.. Inputs: fires, bars, positions. Slots = 1, budget = $1,000, parked = False.

Evaluation order:

1. Exits first (see step 6).
2. Entries require an open slot (slots minus distinct held symbols) and a QQQ-down day: extra["qqq_red"] if a bool, else market["qqq_red"] if a bool, else QQQ last close below its prior close (needs at least 2 QQQ closes).
3. Fires are read from view["fires"]. A fire is skipped if it has no symbol, its sleeve_id/sleeve (when carried) differs, its family does not normalise to cyan (accepts cyan/w_cyan/c), its band/cap_band does not normalise to small (accepts sm/small), or its symbol is held. Signal age: sessions since signal_date/fired_at/fire_date/date, counted on QQQ bar dates when available else calendar days x 5/7, must be present and at most 5 sessions.
4. Freshest-first (ENH-Q07FRESH-20261024, switch default ON; OFF restores producer list order): when 2 or more candidate fires pass the sleeve/family/band/held checks, the slot is allocated freshest-signal-first.
5. Filters (all must pass, fail-closed on no evidence):
- ins2: insider_buys >= 2 when that tag is carried, else a true ins2 tag; no insider evidence fails closed.
- mom6: mom6_pct tag > 0, else a mom6 tag that is true or > 0, else a positive 126-session return from bars (at least 127 closes, last above the close 126 sessions back).
- vix20: a vix tag >= 20.0, else the last close of VIX or ^VIX bars >= 20.0; a missing VIX value fails closed.
6. Execution price (ENH-Q07EXEC-20261024, switch default ON; OFF restores the fire-price rule): filters, sizing and stop are revalidated at the latest bar close; the fire price (falling back to the latest close) is the stale/control price. Sizing: qty = int((budget / slots) // price); qty < 1 emits nothing. Orders are market, day, buy_to_open, with stop_price = round(price x (1 - 0.15), 4).
7. Exits: stop: a held position (qty > 0, entry > 0) whose last close (or current_price fallback) is at or below entry x 0.85 is sold in full, reason "q07 exit: stop_15pct". Horizon: otherwise, a position whose held calendar days (session minus opened_at/entry_date) reach horizon_w x 7 (546 days for 78 weeks) is sold in full, reason "q07 exit: horizon_78w". Exits are market, day, sell_to_close, in full.

## Files in this repo

- This doc: `docs/LZ_S_Q07W_C78_SM_INS2_MOM6_VIX20-RECREATE.md`
- Sleeve code (already in Test): `sleeves/s_q07w_c78_sm_ins2_mom6_vix20.py`, with copies at `adapters3/s_q07w_c78_sm_ins2_mom6_vix20.py` and `integration/s_q07w_c78_sm_ins2_mom6_vix20_adapter.py`.
- Shared engine that runs the logic: `desk3/lazarus_q07.py` (SPECS row for s_q07w_c78_sm_ins2_mom6_vix20; STOP_FRAC 0.15, WINDOW_SESSIONS 5).
- Code-derived algorithm doc: `docs/S_Q07W_C78_SM_INS2_MOM6_VIX20-ALGORITHM.md`.
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json`, row `s_q07w_c78_sm_ins2_mom6_vix20`.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`.
- Code search: Silicon, quant-research-backup and Midna trees were searched for Q07 / lazarus code; no matching file was found there (the running code is in Test only).

## Configuration

- Test sleeve id: `s_q07w_c78_sm_ins2_mom6_vix20`; roster module `adapters3.s_q07w_c78_sm_ins2_mom6_vix20`; cadence 3600 seconds; session rth.
- Slice capital and cash $1,000; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; parked false.
- Inputs declared in config: fires, bars, positions. Slots 1, budget $1,000, horizon 78 weeks, stop 15%.

## Data inputs

- Fires from the sleeve_feed_composer producer (freshness 604800 s, outputs fires) in the fire shape the engine reads (symbol, family, band, signal_date, price, alt-data tags).
- Bars (producer freshness 3600 s, including QQQ and VIX series) and positions (broker_readback, 3600 s).

## Install and run

1. Clone the Test repo.
2. Place `desk3/lazarus_q07.py` under `desk3/` and the wrapper as `sleeves/s_q07w_c78_sm_ins2_mom6_vix20.py` (or the `adapters3/` copy), keeping the repo layout so imports resolve.
3. Register the roster row for `s_q07w_c78_sm_ins2_mom6_vix20` from `config/sleeves.json` with the Configuration values above.
4. Wire the view: `fires`, `bars` (including QQQ and VIX) and `positions` at the stated freshness; missing filter evidence must fail closed.
5. Call the wrapper's `evaluate(view, ctx)` every 3600 seconds in RTH; exits are evaluated before entries.
6. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in the fresh Test tree. Behaviour checklist from the algorithm above:

- No entry on a non-QQQ-down day, with no open slot, or on a fire older than 5 sessions; no entry when any named filter lacks evidence.
- Entry quantity equals int(1000 // price) at the revalidated latest close (switch on), with stop_price = round(price x 0.85, 4) carried on the intent.
- A held position exits in full at or below entry x 0.85, else at 546 calendar days held; no other exit fires.
